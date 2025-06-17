#!/usr/bin/env python3
import click
import json
import requests
import os
from datetime import datetime, timedelta

DEFAULT_BASE_URL = "http://localhost:5000"

@click.group()
@click.option('--base-url', default=DEFAULT_BASE_URL, help='Base URL of the logs_querier API')
@click.pass_context
def cli(ctx, base_url):
    """CLI for interacting with the logs_querier service"""
    ctx.ensure_object(dict)
    ctx.obj['base_url'] = base_url

@cli.command()
@click.pass_context
def health(ctx):
    """Check the health of the logs_querier service"""
    base_url = ctx.obj['base_url']
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        click.echo("✅ Service is healthy!")
        click.echo(f"Status: {data.get('status')}")
        click.echo(f"Service: {data.get('service')}")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Error connecting to service: {e}")
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")

@cli.command()
@click.option('--service', required=True, help='Service name to search logs for')
@click.option('--start', required=True, help='Start time (ISO format: 2024-01-01T00:00:00Z)')
@click.option('--end', required=True, help='End time (ISO format: 2024-01-01T23:59:59Z)')
@click.option('--limit', default=10, help='Number of logs to return (default: 10)')
@click.option('--query', help='Additional query filters')
@click.pass_context
def search(ctx, service, start, end, limit, query):
    """Search logs with specific start and end times"""
    base_url = ctx.obj['base_url']
    
    payload = {
        "service": service,
        "start_time": start,
        "end_time": end,
        "limit": limit
    }
    
    if query:
        payload["query"] = query
    
    try:
        click.echo(f"🔍 Searching logs for service '{service}' from {start} to {end}")
        response = requests.post(f"{base_url}/logs/search", json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            click.echo("✅ Search completed successfully!")
            click.echo(f"Query: {data.get('query')}")
            click.echo(f"Time range: {data.get('time_range', {}).get('start')} to {data.get('time_range', {}).get('end')}")
            
            logs_data = data.get('data', {})
            logs = logs_data.get('logs', [])
            
            if logs:
                click.echo(f"\n📝 Found {len(logs)} logs:")
                for i, log in enumerate(logs[:5], 1):  # Show first 5 logs
                    timestamp = log.get('attributes', {}).get('timestamp', 'Unknown')
                    message = log.get('attributes', {}).get('message', 'No message')[:100]
                    click.echo(f"  {i}. [{timestamp}] {message}...")
                    
                if len(logs) > 5:
                    click.echo(f"  ... and {len(logs) - 5} more logs")
            else:
                click.echo("📝 No logs found for the specified criteria")
                
        else:
            click.echo(f"❌ Search failed: {data.get('error', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Error connecting to service: {e}")
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")

@cli.command()
@click.option('--service', required=True, help='Service name to search logs for')
@click.option('--timerange', 
              type=click.Choice(['15m', '30m', '1h', '4h', '1d', '7d']),
              default='1h',
              help='Time range to search (default: 1h)')
@click.option('--limit', default=10, help='Number of logs to return (default: 10)')
@click.option('--query', help='Additional query filters')
@click.pass_context
def search_timerange(ctx, service, timerange, limit, query):
    """Search logs with relative timerange (e.g., 1h, 30m, 1d)"""
    base_url = ctx.obj['base_url']
    
    payload = {
        "service": service,
        "timerange": timerange,
        "limit": limit
    }
    
    if query:
        payload["query"] = query
    
    try:
        click.echo(f"🔍 Searching logs for service '{service}' for the last {timerange}")
        response = requests.post(f"{base_url}/logs/search/timerange", json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            click.echo("✅ Search completed successfully!")
            click.echo(f"Query: {data.get('query')}")
            click.echo(f"Timerange: {data.get('timerange')}")
            click.echo(f"Time range: {data.get('time_range', {}).get('start')} to {data.get('time_range', {}).get('end')}")
            
            logs_data = data.get('data', {})
            logs = logs_data.get('logs', [])
            
            if logs:
                click.echo(f"\n📝 Found {len(logs)} logs:")
                for i, log in enumerate(logs[:5], 1):  # Show first 5 logs
                    timestamp = log.get('attributes', {}).get('timestamp', 'Unknown')
                    message = log.get('attributes', {}).get('message', 'No message')[:100]
                    click.echo(f"  {i}. [{timestamp}] {message}...")
                    
                if len(logs) > 5:
                    click.echo(f"  ... and {len(logs) - 5} more logs")
            else:
                click.echo("📝 No logs found for the specified criteria")
                
        else:
            click.echo(f"❌ Search failed: {data.get('error', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Error connecting to service: {e}")
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")

@cli.command()
@click.option('--service', required=True, help='Service name to search logs for')
@click.pass_context
def quick_search(ctx, service):
    """Quick search for logs from the last hour for a service"""
    base_url = ctx.obj['base_url']
    
    # Quick search for last hour
    payload = {
        "service": service,
        "timerange": "1h",
        "limit": 5
    }
    
    try:
        click.echo(f"⚡ Quick search for service '{service}' (last hour, 5 logs)")
        response = requests.post(f"{base_url}/logs/search/timerange", json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success'):
            logs_data = data.get('data', {})
            logs = logs_data.get('logs', [])
            
            if logs:
                click.echo(f"✅ Found {len(logs)} recent logs:")
                for i, log in enumerate(logs, 1):
                    timestamp = log.get('attributes', {}).get('timestamp', 'Unknown')
                    message = log.get('attributes', {}).get('message', 'No message')[:80]
                    click.echo(f"  {i}. [{timestamp}] {message}...")
            else:
                click.echo("📝 No recent logs found for this service")
                
        else:
            click.echo(f"❌ Search failed: {data.get('error', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Error connecting to service: {e}")
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")

@cli.command()
@click.option('--lines', default=20, help='Number of lines to show (default: 20)')
@click.option('--follow', '-f', is_flag=True, help='Follow log file (like tail -f)')
def logs(lines, follow):
    """View the logs_querier service logs"""
    # Try to find the log file
    possible_paths = [
        './logs_querier.log',
        '/var/log/logs_querier/logs_querier.log',
        os.path.expanduser('~/logs_querier.log')
    ]
    
    log_file = None
    for path in possible_paths:
        if os.path.exists(path):
            log_file = path
            break
    
    if not log_file:
        click.echo("❌ Could not find logs_querier log file.")
        click.echo("Searched in:")
        for path in possible_paths:
            click.echo(f"  - {path}")
        click.echo("\nThe service may not be running or logs may be disabled.")
        return
    
    click.echo(f"📝 Viewing logs from: {log_file}")
    click.echo("=" * 60)
    
    try:
        if follow:
            # Follow mode (like tail -f)
            import subprocess
            subprocess.run(['tail', '-f', '-n', str(lines), log_file])
        else:
            # Show last N lines
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                
                for line in recent_lines:
                    try:
                        # Try to parse as JSON for pretty printing
                        log_data = json.loads(line.strip())
                        timestamp = log_data.get('timestamp', 'Unknown')
                        level = log_data.get('level', 'INFO')
                        message = log_data.get('message', 'No message')
                        log_type = log_data.get('log_type', 'general')
                        
                        # Color code by level
                        if level == 'ERROR':
                            click.echo(f"❌ [{timestamp}] {level}: {message} (type: {log_type})")
                        elif level == 'WARNING':
                            click.echo(f"⚠️  [{timestamp}] {level}: {message} (type: {log_type})")
                        else:
                            click.echo(f"ℹ️  [{timestamp}] {level}: {message} (type: {log_type})")
                            
                    except json.JSONDecodeError:
                        # If not JSON, just print the line
                        click.echo(line.strip())
                        
    except FileNotFoundError:
        click.echo(f"❌ Log file not found: {log_file}")
    except PermissionError:
        click.echo(f"❌ Permission denied reading log file: {log_file}")
    except Exception as e:
        click.echo(f"❌ Error reading log file: {e}")

@cli.command()
def examples():
    """Show usage examples"""
    click.echo("🚀 logs_querier CLI Examples:\n")
    
    click.echo("1. Check service health:")
    click.echo("   python cli.py health\n")
    
    click.echo("2. Quick search (last hour):")
    click.echo("   python cli.py quick-search --service my-app\n")
    
    click.echo("3. Search with timerange:")
    click.echo("   python cli.py search-timerange --service my-app --timerange 4h --limit 20\n")
    
    click.echo("4. Search with specific timestamps:")
    click.echo("   python cli.py search --service my-app \\")
    click.echo("     --start 2024-01-01T00:00:00Z \\")
    click.echo("     --end 2024-01-01T23:59:59Z \\")
    click.echo("     --limit 50\n")
    
    click.echo("5. Search with additional query filters:")
    click.echo("   python cli.py search-timerange --service my-app \\")
    click.echo("     --timerange 1h \\")
    click.echo("     --query 'status:error'\n")
    
    click.echo("6. View service logs:")
    click.echo("   python cli.py logs --lines 50")
    click.echo("   python cli.py logs --follow  # Follow logs in real-time\n")
    
    click.echo("Available timeranges: 15m, 30m, 1h, 4h, 1d, 7d")

if __name__ == '__main__':
    cli() 