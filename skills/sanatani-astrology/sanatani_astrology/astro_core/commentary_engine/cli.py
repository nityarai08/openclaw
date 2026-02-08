"""
Command-line interface for the Consolidated Commentary Engine.

This module provides CLI commands for generating classical Vedic astrology
commentary based on established literature with no randomization.
"""

import click
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from .consolidated_commentary_engine import ConsolidatedCommentaryEngine
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from commentary_engine.consolidated_commentary_engine import ConsolidatedCommentaryEngine


@click.group()
def cli():
    """Consolidated Commentary Engine for Classical Vedic Astrology."""
    pass


@cli.command()
@click.option('--input-dir', '-i', type=click.Path(exists=True),
              help='Input directory containing kundali_data.json')
@click.option('--kundali-file', '-k', type=click.Path(exists=True),
              help='Path to specific kundali JSON file (alternative to --input-dir)')
@click.option('--output-dir', '-o', type=click.Path(), 
              help='Output directory (creates commentary.json inside)')
@click.option('--output-file', type=click.Path(), 
              help='Specific output file path (alternative to --output-dir)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with analysis details')
def generate(input_dir, kundali_file, output_dir, output_file, verbose):
    """Generate consolidated commentary based on classical Vedic astrology."""
    
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
            kundali_data = json.load(f)
        
        if verbose:
            click.echo(f"🔄 Loaded kundali data from {input_file}")
        
        # Initialize consolidated engine
        engine = ConsolidatedCommentaryEngine()
        
        if verbose:
            click.echo("Generating consolidated commentary based on classical principles...")
        
        # Generate commentary
        commentary_json = engine.generate_comprehensive_commentary(kundali_data)
        
        # Determine output path
        if output_file:
            output_path = Path(output_file)
        elif output_dir:
            output_path = Path(output_dir) / "commentary.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        elif input_dir:
            output_path = Path(input_dir) / "commentary.json"
        else:
            output_path = Path("commentary.json")
        
        # Write output
        with open(output_path, 'w') as f:
            json.dump(commentary_json, f, indent=2)
        
        click.echo(f"✅ Commentary written to {output_path}")
        
        # Show summary
        if verbose:
            metadata = commentary_json.get('metadata', {})
            click.echo(f"\nSummary:")
            click.echo(f"  Word count: {metadata.get('word_count', 0)}")
            click.echo(f"  Confidence score: {metadata.get('confidence_score', 0):.2f}")
            click.echo(f"  Analysis type: {metadata.get('analysis_type', 'Unknown')}")
            click.echo(f"  Methodology: {metadata.get('methodology', 'Unknown')}")
    
    except Exception as e:
        click.echo(f"Error generating consolidated commentary: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--kundali-file', '-k', required=True, type=click.Path(exists=True),
              help='Path to kundali JSON file')
def validate(kundali_file):
    """Validate kundali data structure for commentary generation."""
    
    try:
        # Load kundali data
        with open(kundali_file, 'r') as f:
            kundali_data = json.load(f)
        
        click.echo(f"Validating kundali data from {kundali_file}")
        
        # Check required sections
        required_sections = ['birth_details', 'planetary_positions', 'divisional_charts']
        missing_sections = []
        
        for section in required_sections:
            if section not in kundali_data:
                missing_sections.append(section)
        
        if missing_sections:
            click.echo(f"❌ Missing required sections: {', '.join(missing_sections)}")
            sys.exit(1)
        
        # Check D1 chart
        d1_chart = kundali_data.get('divisional_charts', {}).get('D1', {})
        if not d1_chart:
            click.echo("❌ Missing D1 chart data")
            sys.exit(1)
        
        positions = d1_chart.get('planetary_positions', {})
        if not positions:
            click.echo("❌ Missing planetary positions in D1 chart")
            sys.exit(1)
        
        # Check planetary data completeness
        required_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        missing_planets = []
        
        for planet in required_planets:
            if planet not in positions:
                missing_planets.append(planet)
            else:
                planet_data = positions[planet]
                required_fields = ['house', 'dignity', 'rasi']
                for field in required_fields:
                    if field not in planet_data:
                        click.echo(f"⚠️  Planet {planet} missing field: {field}")
        
        if missing_planets:
            click.echo(f"❌ Missing planets: {', '.join(missing_planets)}")
            sys.exit(1)
        
        click.echo("✅ Kundali data validation successful")
        click.echo(f"✅ Found {len(positions)} planetary positions")
        
        # Show birth details
        birth_details = kundali_data.get('birth_details', {})
        if birth_details:
            click.echo(f"✅ Birth details: {birth_details.get('place', 'Unknown')} on {birth_details.get('date', 'Unknown')}")
        
        # Show yogas if available
        yogas = d1_chart.get('yogas', [])
        if yogas:
            click.echo(f"✅ Found {len(yogas)} yogas: {', '.join(yogas[:3])}{'...' if len(yogas) > 3 else ''}")
    
    except Exception as e:
        click.echo(f"Error validating kundali data: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()

if __name__ == '__main__':
    main()