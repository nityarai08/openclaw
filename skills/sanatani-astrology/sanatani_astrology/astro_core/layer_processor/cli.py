#!/usr/bin/env python3
"""
Layer Processor CLI

Focused CLI for favorability layer processing only.
Provides both CLI and API interface for generating favorability layers from kundali data.
"""

import click
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .layer_engine import LayerProcessingEngine


@click.group()
def cli():
    """Layer Processor - Generate favorability layers from kundali data."""
    pass


@cli.command()
@click.option('--input-dir', '-i', type=click.Path(exists=True),
              help='Input directory containing kundali_data.json')
@click.option('--kundali-file', '-k', type=click.Path(exists=True),
              help='Path to specific kundali JSON file (alternative to --input-dir)')
@click.option('--year', required=True, type=int, help='Year for favorability analysis')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory for layer files')
@click.option('--max-layers', type=int, help='Maximum number of layers to process')
@click.option('--layers', multiple=True, type=int, help='Specific layers to process (e.g., --layers 1 --layers 2)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'both']), 
              default='both', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--rule-file', type=click.Path(exists=True), help='Path to layer scoring rules YAML')
def process(input_dir, kundali_file, year, output_dir, max_layers, layers, format, verbose, rule_file):
    """Process favorability layers from kundali data."""
    
    try:
        # Determine input file
        if kundali_file:
            input_file = Path(kundali_file)
        elif input_dir:
            input_file = Path(input_dir) / "kundali_data.json"
        else:
            input_file = Path("kundali_data.json")
        
        if not input_file.exists():
            click.echo(f"❌ Kundali file not found: {input_file}")
            sys.exit(1)
        
        # Load kundali data
        with open(input_file, 'r') as f:
            kundali_json = f.read()
        
        # Parse as dict for layer processor
        kundali_dict = json.loads(kundali_json)
        
        # Convert to KundaliData object for the engine
        from ..core.data_models import KundaliData, BirthDetails, PlanetaryPosition
        from datetime import datetime
        
        # Create KundaliData from the loaded JSON
        kundali_data = KundaliData()
        kundali_data.schema_version = kundali_dict.get('schema_version', '2.0')
        kundali_data.generation_timestamp = kundali_dict.get('generation_timestamp')
        kundali_data.astronomical_data = kundali_dict.get('astronomical_data', {})
        kundali_data.divisional_charts = kundali_dict.get('divisional_charts', {})
        kundali_data.panchanga = kundali_dict.get('panchanga', {})
        kundali_data.yogas_and_doshas = kundali_dict.get('yogas_and_doshas', {})
        kundali_data.dasha_periods = kundali_dict.get('dasha_periods', {})
        kundali_data.metadata = kundali_dict.get('metadata', {})
        
        # Convert birth details
        birth_dict = kundali_dict.get('birth_details', {})
        if birth_dict:
            birth_date = datetime.fromisoformat(birth_dict['date'])
            # Parse time string properly
            time_str = birth_dict['time']
            if 'T' in time_str:
                birth_time = datetime.fromisoformat(time_str).time()
            else:
                birth_time = datetime.strptime(time_str, '%H:%M:%S').time()
            
            kundali_data.birth_details = BirthDetails(
                date=birth_date,
                time=birth_time,
                place=birth_dict['place'],
                latitude=birth_dict['latitude'],
                longitude=birth_dict['longitude'],
                timezone_offset=birth_dict['timezone_offset']
            )
        
        # Convert planetary positions
        positions_dict = kundali_dict.get('planetary_positions', {})
        for planet, pos_dict in positions_dict.items():
            kundali_data.planetary_positions[planet] = PlanetaryPosition(
                longitude=pos_dict['longitude'],
                rasi=pos_dict['rasi'],
                nakshatra=pos_dict['nakshatra'],
                degree_in_sign=pos_dict['degree_in_sign'],
                retrograde=pos_dict.get('retrograde', False)
            )
        
        if verbose:
            click.echo(f"🔄 Processing kundali from: {input_file}")
            click.echo(f"📅 Analysis year: {year}")
            if max_layers:
                click.echo(f"🔢 Max layers: {max_layers}")
            if layers:
                click.echo(f"🎯 Specific layers: {list(layers)}")
        
        # Initialize layer processor
        engine = LayerProcessingEngine(kundali_data, rule_path=rule_file)
        
        # Process layers
        if layers:
            # Process specific layers
            layer_data = {}
            for layer_id in layers:
                if verbose:
                    click.echo(f"Processing layer {layer_id}...")
                layer_result = engine.process_single_layer(layer_id, year)
                if layer_result:
                    layer_data[layer_id] = layer_result
        else:
            # Process all layers (or limited by max_layers)
            if verbose:
                click.echo("Processing all available layers...")
            
            if max_layers:
                # Get available layers and limit to max_layers
                available_layers = list(engine.get_available_layers())[:max_layers]
                layer_data = engine.process_multiple_layers(available_layers, year)
            else:
                layer_data = engine.process_all_layers(year)
        
        if not layer_data:
            click.echo("❌ No layers were processed successfully")
            sys.exit(1)
        
        # Setup output directory
        if not output_dir:
            if input_dir:
                output_path = Path(input_dir)  # Use same directory as input
            else:
                output_path = Path(".")  # Use current directory
        else:
            output_path = Path(output_dir)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save layer files
        saved_files = []
        
        if format in ['json', 'both']:
            for layer_id, data in layer_data.items():
                layer_file = output_path / f"layer_{layer_id}_data_{year}.json"
                with open(layer_file, 'w') as f:
                    json.dump(data.to_dict(), f, indent=2, default=str)
                saved_files.append(str(layer_file))
                if verbose:
                    click.echo(f"✅ Saved layer {layer_id}: {layer_file}")
        
        if format in ['csv', 'both']:
            # Generate combined CSV manually
            combined_csv = output_path / f"favorability_data_{year}.csv"
            
            # Create CSV data
            import csv
            with open(combined_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                header = ['date', 'day_of_year']
                for layer_id in sorted(layer_data.keys()):
                    header.append(f'layer_{layer_id}_score')
                    header.append(f'layer_{layer_id}_confidence')
                writer.writerow(header)
                
                # Get all dates from first layer
                if layer_data:
                    first_layer = next(iter(layer_data.values()))
                    for daily_score in first_layer.annual_data:
                        row = [daily_score.date, daily_score.day_of_year]
                        
                        # Add scores from all layers for this date
                        for layer_id in sorted(layer_data.keys()):
                            layer = layer_data[layer_id]
                            # Find matching date in this layer
                            matching_score = next(
                                (ds for ds in layer.annual_data if ds.date == daily_score.date),
                                None
                            )
                            if matching_score:
                                row.extend([matching_score.score, matching_score.confidence])
                            else:
                                row.extend([0.5, 0.0])  # Default values
                        
                        writer.writerow(row)
            
            saved_files.append(str(combined_csv))
            if verbose:
                click.echo(f"✅ Saved combined CSV: {combined_csv}")
        
        click.echo(f"✅ Generated {len(layer_data)} layers")
        click.echo(f"📁 Output directory: {output_path.absolute()}")
        
        # Show layer summary
        if verbose:
            click.echo(f"\n📊 Layer Summary:")
            for layer_id, data in layer_data.items():
                layer_info = data.layer_info
                click.echo(f"  Layer {layer_id}: {layer_info.name} ({layer_info.accuracy_rating}% accuracy)")
    
    except Exception as e:
        click.echo(f"❌ Error processing layers: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--layer-dir', required=True, type=click.Path(exists=True),
              help='Directory containing layer JSON files')
@click.option('--year', required=True, type=int, help='Year for the analysis')
@click.option('--output', '-o', type=click.Path(), help='Output CSV file path')
def combine(layer_dir, year, output):
    """Combine individual layer files into a single CSV."""
    
    try:
        layer_path = Path(layer_dir)
        
        # Load all layer files
        layer_data = {}
        for layer_file in layer_path.glob(f"layer_*_data_{year}.json"):
            layer_id = int(layer_file.stem.split('_')[1])
            
            with open(layer_file, 'r') as f:
                layer_dict = json.load(f)
            
            # Convert back to LayerData object
            from ..core.data_models import LayerData, LayerInfo, DailyScore
            
            layer_info = LayerInfo(**layer_dict['layer_info'])
            daily_scores = [DailyScore(**score) for score in layer_dict['annual_data']]
            
            layer_data[layer_id] = LayerData(
                layer_info=layer_info,
                annual_data=daily_scores,
                calculation_metadata=layer_dict.get('calculation_metadata', {})
            )
        
        if not layer_data:
            click.echo(f"❌ No layer files found in {layer_dir}")
            sys.exit(1)
        
        # Generate combined CSV
        if not output:
            output = f"combined_favorability_{year}.csv"
        
        # Manually export combined CSV (avoid engine dependency)
        import csv
        output_path = Path(output)
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['date', 'day_of_year']
            for layer_id in sorted(layer_data.keys()):
                header.append(f'layer_{layer_id}_score')
                header.append(f'layer_{layer_id}_confidence')
            writer.writerow(header)

            # Use dates from the first layer
            first_layer = next(iter(layer_data.values()))
            for daily_score in first_layer.annual_data:
                row = [daily_score.date, daily_score.day_of_year]
                for layer_id in sorted(layer_data.keys()):
                    match = next((ds for ds in layer_data[layer_id].annual_data if ds.date == daily_score.date), None)
                    if match:
                        row.extend([match.score, match.confidence])
                    else:
                        row.extend([0.5, 0.0])
                writer.writerow(row)

        click.echo(f"✅ Combined {len(layer_data)} layers into: {output_path}")
    
    except Exception as e:
        click.echo(f"❌ Error combining layers: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_layers():
    """List available favorability layers."""
    
    click.echo("Available Favorability Layers:")
    click.echo("=" * 35)
    
    # Import the layer registry directly instead of using the engine
    from .layers import get_available_layers
    
    try:
        available_layers = get_available_layers()
        
        for layer_id in sorted(available_layers.keys()):
            layer_class = available_layers[layer_id]
            click.echo(f"Layer {layer_id}: {layer_class.__name__}")
            click.echo(f"  Description: {getattr(layer_class, '__doc__', 'No description available')}")
            click.echo()
    except Exception as e:
        click.echo(f"❌ Error listing layers: {e}")
        # Fallback to basic layer info
        click.echo("Layer 1: Astronomical Facts")
        click.echo("  Description: Basic astronomical calculations")
        click.echo()
        for i in range(2, 11):
            click.echo(f"Layer {i}: Layer {i}")
            click.echo(f"  Description: Favorability layer {i}")
            click.echo()


@cli.command()
@click.option('--layer-file', required=True, type=click.Path(exists=True),
              help='Path to layer JSON file')
def validate(layer_file):
    """Validate layer JSON structure."""
    
    try:
        with open(layer_file, 'r') as f:
            layer_data = json.load(f)
        
        click.echo(f"Validating layer file: {layer_file}")
        
        # Check required sections
        required_sections = ['layer_info', 'annual_data']
        missing_sections = []
        
        for section in required_sections:
            if section not in layer_data:
                missing_sections.append(section)
        
        if missing_sections:
            click.echo(f"❌ Missing required sections: {', '.join(missing_sections)}")
            sys.exit(1)
        
        # Check layer info
        layer_info = layer_data.get('layer_info', {})
        required_info = ['id', 'name', 'accuracy_rating', 'methodology']
        missing_info = [field for field in required_info if field not in layer_info]
        
        if missing_info:
            click.echo(f"❌ Missing layer info fields: {', '.join(missing_info)}")
            sys.exit(1)
        
        # Check annual data
        annual_data = layer_data.get('annual_data', [])
        if not annual_data:
            click.echo("❌ No annual data found")
            sys.exit(1)
        
        # Validate first few entries
        for i, entry in enumerate(annual_data[:3]):
            required_fields = ['date', 'score', 'confidence']
            missing_fields = [field for field in required_fields if field not in entry]
            if missing_fields:
                click.echo(f"❌ Entry {i} missing fields: {', '.join(missing_fields)}")
                sys.exit(1)
        
        click.echo("✅ Layer validation successful")
        click.echo(f"✅ Layer: {layer_info.get('name', 'Unknown')} (ID: {layer_info.get('id', 'Unknown')})")
        click.echo(f"✅ Accuracy: {layer_info.get('accuracy_rating', 0)}%")
        click.echo(f"✅ Data points: {len(annual_data)}")
    
    except Exception as e:
        click.echo(f"❌ Error validating layer: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()

if __name__ == '__main__':
    main()
