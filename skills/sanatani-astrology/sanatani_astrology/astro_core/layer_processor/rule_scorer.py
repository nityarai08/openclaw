"""
Generic YAML-driven scoring evaluator for layer daily weights.

This module reads per-layer scoring specs from the layer rules YAML and
computes a normalized score [0,1] from a provided feature context.

Supported factor types:
- direct: use feature value directly (assumed 0..1)
- map: look up a discrete feature in a score table (with default)
- average_maps: average of multiple map lookups (e.g., Rahu/Ketu houses)

Supported modifiers (applied in order on the factor's score):
- multiply: multiply by a constant when a simple condition matches
- add: add a constant when a condition matches

Simple conditions:
- equals: {feature, equals}
- in: {feature, in}
- exists: {feature, exists: true}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import ast
import math


def _get_by_path(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


@dataclass
class FactorSpec:
    id: str
    type: str  # direct | map | average_maps
    weight: float
    key: Optional[str] = None  # for direct
    map: Optional[Dict[str, Any]] = None  # feature, table, default
    maps: Optional[List[Dict[str, Any]]] = None  # for average_maps
    modifiers: Optional[List[Dict[str, Any]]] = None
    formula: Optional[str] = None


class LayerRuleScorer:
    """Evaluates per-layer scoring based on a scoring spec dict (from YAML)."""

    def __init__(self, scoring_spec: Dict[str, Any]):
        self.aggregation: str = scoring_spec.get('aggregation', 'weighted_sum')
        # Optional root-level formula to compute final score
        self.formula: Optional[str] = scoring_spec.get('formula')
        raw_factors = scoring_spec.get('factors', []) or []
        self.factors: List[FactorSpec] = []
        for raw in raw_factors:
            self.factors.append(FactorSpec(
                id=str(raw.get('id') or raw.get('key') or 'factor'),
                type=str(raw.get('type', 'direct')),
                weight=float(raw.get('weight', 0.0)),
                key=raw.get('key'),
                map=raw.get('map'),
                maps=raw.get('maps'),
                modifiers=raw.get('modifiers'),
                formula=raw.get('formula'),
            ))
        # Safe evaluator with limited functions
        self._evaluator = _SafeExpressionEvaluator()

    def score(self, features: Dict[str, Any], env: Optional[Dict[str, Any]] = None) -> float:
        if self.aggregation != 'weighted_sum':
            # Fallback: treat as weighted sum
            pass

        # Compute factor values first (so root formula can reference them)
        factor_values: Dict[str, float] = {}
        for f in self.factors:
            val = self._eval_factor(f, features, env, factor_values)
            factor_values[f.id] = max(0.0, min(1.0, float(val)))

        # If a root formula is present, evaluate it with variables
        if self.formula:
            vars = _merge_vars(features, factor_values, env)
            try:
                out = self._evaluator.eval(self.formula, vars)
                return _clamp01(out)
            except Exception:
                # Fall back to weighted sum if formula fails
                pass

        # Default weighted sum
        total = 0.0
        for f in self.factors:
            total += factor_values.get(f.id, 0.5) * f.weight
        return _clamp01(total)

    def _eval_factor(self, f: FactorSpec, features: Dict[str, Any], env: Optional[Dict[str, Any]] = None, prev_values: Optional[Dict[str, float]] = None) -> float:
        base = 0.5
        try:
            # Per-factor formula takes precedence if supplied
            if hasattr(f, 'formula') and f.formula:
                vars = _merge_vars(features, prev_values or {}, env)
                base = _to_float(self._evaluator.eval(getattr(f, 'formula'), vars), 0.5)
            elif f.type == 'direct':
                key = f.key or f.id
                base = _to_float(_get_by_path(features, key, 0.5))
            elif f.type == 'map':
                m = f.map or {}
                feat = m.get('feature', f.id)
                default = float(m.get('default', 0.5))
                raw_val = _get_by_path(features, feat, None)
                table = m.get('table', {}) or {}
                base = _map_lookup(table, raw_val, default)
            elif f.type == 'average_maps':
                vals: List[float] = []
                for m in f.maps or []:
                    feat = m.get('feature', f.id)
                    default = float(m.get('default', 0.5))
                    raw_val = _get_by_path(features, feat, None)
                    table = m.get('table', {}) or {}
                    vals.append(_map_lookup(table, raw_val, default))
                base = sum(vals) / len(vals) if vals else 0.5
            else:
                base = 0.5
        except Exception:
            base = 0.5

        # Apply modifiers
        for mod in f.modifiers or []:
            if _condition_matches(mod.get('condition', {}), features):
                op = (mod.get('op') or 'multiply').lower()
                if op == 'multiply':
                    try:
                        base *= float(mod.get('value', 1.0))
                    except Exception:
                        pass
                elif op == 'add':
                    try:
                        base += float(mod.get('value', 0.0))
                    except Exception:
                        pass
                elif op == 'blend':
                    # blend with another feature value: new = (1-a)*base + a*feat
                    try:
                        alpha = float(mod.get('alpha', 0.5))
                        with_key = mod.get('with')
                        other = _to_float(_get_by_path(features, with_key, 0.5)) if with_key else 0.5
                        base = (1 - alpha) * base + alpha * other
                    except Exception:
                        pass

        return max(0.0, min(1.0, base))


def _merge_vars(features: Dict[str, Any], factor_values: Dict[str, float], env: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    vars: Dict[str, Any] = {}
    # Expose features both flattened at top level and under 'features'
    vars.update(features or {})
    vars['features'] = features or {}
    # Expose computed factor values both flattened and under 'factors'
    for k, v in (factor_values or {}).items():
        vars[k] = v
    vars['factors'] = factor_values or {}
    # Additional environment: kundali dict, date info
    if env:
        if 'kundali' in env:
            vars['kundali'] = env['kundali']
        if 'date' in env:
            vars['date'] = env['date']
        if 'day_of_year' in env:
            vars['day_of_year'] = env['day_of_year']
    # Common constants and helper funcs
    vars.update(_default_eval_env())
    return vars


def _default_eval_env() -> Dict[str, Any]:
    def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        try:
            return max(lo, min(hi, float(x)))
        except Exception:
            return 0.0

    def mean(seq: List[float]) -> float:
        try:
            l = list(seq)
            return sum(l) / len(l) if l else 0.0
        except Exception:
            return 0.0

    def val(path: str, default: Any = None, *, source: Optional[Dict[str, Any]] = None) -> Any:
        # Fetch by dotted path in either 'features' or 'kundali' by default, or a provided source
        from_src = source if source is not None else None
        # We'll create closures to current vars at runtime in evaluator
        # This function will be rebound by _SafeExpressionEvaluator with captured context if needed
        return default

    return {
        'min': min,
        'max': max,
        'abs': abs,
        'clamp': clamp,
        'mean': mean,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'pi': math.pi,
        'e': math.e,
        'val': val,
    }


def _clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.5


class _SafeExpressionEvaluator:
    """Safely evaluate arithmetic/boolean expressions against a variable mapping."""

    def __init__(self):
        # Names allowed as functions/constants are injected via vars
        pass

    def eval(self, expr: str, vars: Dict[str, Any]) -> Any:
        # Bind val() with access to features/kundali from vars
        def bound_val(path: str, default: Any = None, *, source: Optional[Dict[str, Any]] = None) -> Any:
            if source is not None:
                return _get_by_path(source, path, default)
            # prefer features, then kundali
            got = _get_by_path(vars.get('features', {}), path, None)
            if got is not None:
                return got
            return _get_by_path(vars.get('kundali', {}), path, default)
        # Inject bound function
        local_vars = dict(vars)
        local_vars['val'] = bound_val

        node = ast.parse(expr, mode='eval')
        return self._eval_node(node.body, local_vars)

    def _eval_node(self, node: ast.AST, vars: Dict[str, Any]) -> Any:
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, vars)
            right = self._eval_node(node.right, vars)
            return self._apply_binop(node.op, left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, vars)
            return self._apply_unaryop(node.op, operand)
        if isinstance(node, ast.BoolOp):
            vals = [self._eval_node(v, vars) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(bool(v) for v in vals)
            if isinstance(node.op, ast.Or):
                return any(bool(v) for v in vals)
            raise ValueError('Unsupported boolean operator')
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, vars)
            result = True
            for op, comp in zip(node.ops, node.comparators):
                right = self._eval_node(comp, vars)
                result = result and self._apply_compare(op, left, right)
                left = right
            return result
        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, vars)
            return self._eval_node(node.body if test else node.orelse, vars)
        if isinstance(node, ast.Call):
            func = self._eval_node(node.func, vars)
            args = [self._eval_node(a, vars) for a in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value, vars) for kw in node.keywords}
            if callable(func):
                return func(*args, **kwargs)
            raise ValueError('Call to non-callable')
        if isinstance(node, ast.Attribute):
            val = self._eval_node(node.value, vars)
            if isinstance(val, dict):
                return val.get(node.attr)
            # allow getattr on simple namespaces like math if provided
            if hasattr(val, node.attr):
                return getattr(val, node.attr)
            return None
        if isinstance(node, ast.Subscript):
            val = self._eval_node(node.value, vars)
            key = self._eval_node(node.slice, vars) if hasattr(node, 'slice') else None
            try:
                return val[key]
            except Exception:
                return None
        if isinstance(node, ast.Name):
            return vars.get(node.id, 0.0)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):  # legacy Py <3.8
            return node.n
        if isinstance(node, ast.Str):  # legacy
            return node.s
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elt, vars) for elt in node.elts)
        if isinstance(node, ast.List):
            return [self._eval_node(elt, vars) for elt in node.elts]
        if isinstance(node, ast.Dict):
            return {self._eval_node(k, vars): self._eval_node(v, vars) for k, v in zip(node.keys, node.values)}
        raise ValueError(f'Unsupported expression element: {type(node).__name__}')

    def _apply_binop(self, op, left, right):
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.Pow):
            return left ** right
        raise ValueError('Unsupported binary operator')

    def _apply_unaryop(self, op, operand):
        if isinstance(op, ast.UAdd):
            return +operand
        if isinstance(op, ast.USub):
            return -operand
        if isinstance(op, ast.Not):
            return not operand
        raise ValueError('Unsupported unary operator')

    def _apply_compare(self, op, left, right):
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
        raise ValueError('Unsupported compare operator')


def _to_float(val: Any, default: float = 0.5) -> float:
    try:
        return float(val)
    except Exception:
        return default


def _map_lookup(table: Dict[Any, Any], raw_val: Any, default: float) -> float:
    if raw_val is None:
        return default
    # Try direct match (key may be int or str)
    if raw_val in table:
        try:
            return float(table[raw_val])
        except Exception:
            return default
    # Try stringified key
    key = str(raw_val)
    if key in table:
        try:
            return float(table[key])
        except Exception:
            return default
    return default


def _condition_matches(cond: Dict[str, Any], features: Dict[str, Any]) -> bool:
    if not cond:
        return False
    feat = cond.get('feature')
    if not feat:
        return False
    op = cond.get('op') or ('equals' if 'equals' in cond else 'exists')
    op = op.lower()
    if op == 'exists':
        return _get_by_path(features, feat, None) is not None
    if 'equals' in cond or op == 'equals':
        return _get_by_path(features, feat, None) == cond.get('equals')
    if 'in' in cond or op == 'in':
        val = _get_by_path(features, feat, None)
        return val in (cond.get('in') or [])
    # boolean convenience
    if 'is_true' in cond:
        return bool(_get_by_path(features, feat, False)) is True
    if 'is_false' in cond:
        return bool(_get_by_path(features, feat, True)) is False
    return False
