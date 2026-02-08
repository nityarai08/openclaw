#!/usr/bin/env python3
"""
Kundali Generator CLI

Focused CLI for kundali generation with directory-based output.
Can be used individually or as part of the orchestrated workflow.
"""

import click
import json
import sys
from datetime import datetime, date, time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.data_models import BirthDetails
from .kundali_generator_factory import KundaliGeneratorFactory, GeneratorType
from .birth_details_validator import CoordinateService


@click.group()
def cli():
    """Kundali Generator - Generate horoscopes from birth details."""
    pass


@cli.command()
@click.option('--date', required=True, help='Birth date (YYYY-MM-DD)')
@click.option('--time', required=True, help='Birth time (HH:MM:SS)')
@click.option('--place', required=True, help='Birth place')
@click.option('--latitude', type=float, help='Latitude (optional)')
@click.option('--longitude', type=float, help='Longitude (optional)')
@click.option('--timezone', type=float, help='Timezone offset (optional)')
@click.option('--generator', '-g', type=click.Choice(['auto', 'pyjhora', 'ephemeris']), 
              default='auto', help='Generator type to use')
@click.option('--output-dir', '-o', type=click.Path(), 
              help='Output directory (creates kundali_data.json inside)')
@click.option('--output-file', type=click.Path(), 
              help='Specific output file path (alternative to --output-dir)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def generate(date, time, place, latitude, longitude, timezone, generator, output_dir, output_file, verbose):
    """Generate kundali and save to directory or specific file."""
    
    try:
        # Parse birth details
        birth_date = datetime.strptime(date, "%Y-%m-%d").date()
        birth_time = datetime.strptime(time, "%H:%M:%S").time()
        
        # Combine date and time into a single datetime object
        birth_datetime = datetime.combine(birth_date, birth_time)
        
        # Handle coordinates - lookup if not provided
        final_latitude = latitude
        final_longitude = longitude
        final_timezone = timezone
        
        if latitude is None or longitude is None:
            if verbose:
                click.echo(f"🔍 Looking up coordinates for '{place}'...")
            
            coordinate_service = CoordinateService()
            location_data = coordinate_service.lookup_coordinates(place)
            
            if location_data:
                final_latitude = location_data.latitude
                final_longitude = location_data.longitude
                if timezone is None:
                    final_timezone = location_data.timezone_offset
                
                if verbose:
                    click.echo(f"📍 Found coordinates: {final_latitude:.4f}, {final_longitude:.4f}")
                    click.echo(f"🕐 Timezone offset: {final_timezone:.1f} hours")
            else:
                click.echo(f"⚠️  Could not find coordinates for '{place}'. Using default (0.0, 0.0)")
                final_latitude = 0.0
                final_longitude = 0.0
        
        # Set default timezone if still not available
        if final_timezone is None:
            final_timezone = 0.0
        
        birth_details = BirthDetails(
            date=birth_datetime,
            time=birth_time,
            place=place,
            latitude=final_latitude,
            longitude=final_longitude,
            timezone_offset=final_timezone
        )
        
        if verbose:
            click.echo(f"🔄 Generating kundali for {place} on {birth_date} at {birth_time}")
            click.echo(f"🔧 Using generator: {generator}")
        
        # Create generator
        if generator == "auto":
            gen = KundaliGeneratorFactory.create_generator(GeneratorType.AUTO)
        elif generator == "pyjhora":
            gen = KundaliGeneratorFactory.create_generator(GeneratorType.PYJHORA)
        elif generator == "ephemeris":
            gen = KundaliGeneratorFactory.create_generator(GeneratorType.EPHEMERIS)
        
        # Generate kundali (using correct method name)
        kundali_data = gen.generate_from_birth_details(birth_details)
        
        # Export to JSON
        json_output = gen.export_standardized_json(kundali_data)
        
        # Determine output path
        if output_file:
            output_path = Path(output_file)
        elif output_dir:
            output_path = Path(output_dir) / "kundali_data.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Default to current directory
            output_path = Path("kundali_data.json")
        
        # Write output
        with open(output_path, 'w') as f:
            parsed = json.loads(json_output)
            f.write(json.dumps(parsed, indent=2))
        
        click.echo(f"✅ Kundali saved to: {output_path}")
        
        if verbose:
            parsed = json.loads(json_output)
            click.echo(f"\n📊 Summary:")
            click.echo(f"  Generator: {parsed.get('astronomical_data', {}).get('calculation_method', 'Unknown')}")
            click.echo(f"  Planets: {len(parsed.get('planetary_positions', {}))}")
            click.echo(f"  Divisional Charts: {len(parsed.get('divisional_charts', {}))}")
            if 'D1' in parsed.get('divisional_charts', {}):
                yogas = parsed['divisional_charts']['D1'].get('yogas', [])
                click.echo(f"  Yogas: {len(yogas)}")
    
    except Exception as e:
        click.echo(f"❌ Error generating kundali: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--input-file', '-i', type=click.Path(exists=True),
              help='Path to kundali JSON file')
@click.option('--input-dir', type=click.Path(exists=True),
              help='Directory containing kundali_data.json')
def validate(input_file, input_dir):
    """Validate kundali JSON structure."""
    
    try:
        # Determine input file
        if input_file:
            kundali_file = Path(input_file)
        elif input_dir:
            kundali_file = Path(input_dir) / "kundali_data.json"
        else:
            kundali_file = Path("kundali_data.json")
        
        if not kundali_file.exists():
            click.echo(f"❌ Kundali file not found: {kundali_file}")
            sys.exit(1)
        
        with open(kundali_file, 'r') as f:
            kundali_data = json.load(f)
        
        click.echo(f"🔍 Validating kundali file: {kundali_file}")
        
        # Check required sections
        required_sections = ['birth_details', 'planetary_positions', 'divisional_charts']
        missing_sections = []
        
        for section in required_sections:
            if section not in kundali_data:
                missing_sections.append(section)
        
        if missing_sections:
            click.echo(f"❌ Missing required sections: {', '.join(missing_sections)}")
            sys.exit(1)
        
        # Check planetary positions
        positions = kundali_data.get('planetary_positions', {})
        required_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        missing_planets = [p for p in required_planets if p not in positions]
        
        if missing_planets:
            click.echo(f"❌ Missing planets: {', '.join(missing_planets)}")
            sys.exit(1)
        
        # Check D1 chart
        d1_chart = kundali_data.get('divisional_charts', {}).get('D1', {})
        if not d1_chart:
            click.echo("❌ Missing D1 chart")
            sys.exit(1)
        
        click.echo("✅ Kundali validation successful")
        
        # Show summary
        birth_details = kundali_data.get('birth_details', {})
        click.echo(f"✅ Birth: {birth_details.get('place', 'Unknown')} on {birth_details.get('date', 'Unknown')}")
        click.echo(f"✅ Planets: {len(positions)}")
        click.echo(f"✅ Charts: {len(kundali_data.get('divisional_charts', {}))}")
        
        yogas = d1_chart.get('yogas', [])
        if yogas:
            click.echo(f"✅ Yogas: {len(yogas)} - {', '.join(yogas[:3])}{'...' if len(yogas) > 3 else ''}")
    
    except Exception as e:
        click.echo(f"❌ Error validating kundali: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_generators():
    """List available kundali generators."""
    
    click.echo("Available Kundali Generators:")
    click.echo("=" * 30)
    
    available = KundaliGeneratorFactory.get_available_generators()
    for gen_type, info in available.items():
        status = "✅" if info['available'] else "❌"
        click.echo(f"{status} {gen_type.upper()}: {info['description']}")
        if info['available']:
            click.echo(f"   Features: {', '.join(info.get('features', []))}")
        else:
            click.echo(f"   Issue: {info.get('error', 'Unknown error')}")
        click.echo()


def main():
    """Main entry point for CLI."""
    cli()

if __name__ == '__main__':
    main()