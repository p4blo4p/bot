#!/usr/bin/env python3
"""
Enhanced script to analyze urlwatch database and generate comprehensive reports.
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# --- Configuration ---
DB_PATH = os.path.expanduser('~/.cache/urlwatch/cache.db')
LOGS_DIR = Path('logs')
OUTPUT_FILE = LOGS_DIR / 'ultimos_cambios.txt'
JSON_OUTPUT = LOGS_DIR / 'ultimos_cambios.json'

def ensure_logs_directory():
    """Create logs directory if it doesn't exist."""
    LOGS_DIR.mkdir(exist_ok=True)

def check_database_exists():
    """Check if the urlwatch database exists."""
    if not os.path.exists(DB_PATH):
        print("INFO: urlwatch database not found at:", DB_PATH)
        print("      This is normal on first execution.")
        
        # Create empty report files for consistency
        ensure_logs_directory()
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"Database not found - First execution at {datetime.now()}\n")
            f.write("urlwatch will create the database after first run.\n")
        
        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "database_not_found",
                "timestamp": datetime.now().isoformat(),
                "message": "First execution - database will be created after first urlwatch run"
            }, f, indent=2)
        
        return False
    return True

def get_database_info():
    """Get comprehensive information from urlwatch database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Available tables: {tables}")
        
        # Check if snapshots table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshots';")
        if not cursor.fetchone():
            # Try alternative table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = [table[0] for table in cursor.fetchall()]
            print(f"Snapshots table not found. Available tables: {all_tables}")
            return None
        
        # Get last changes with more details
        query = """
            SELECT url, MAX(timestamp) as last_change, COUNT(*) as total_snapshots
            FROM snapshots
            GROUP BY url
            ORDER BY MAX(timestamp) DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Get recent activity (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).timestamp()
        recent_query = """
            SELECT url, timestamp, COUNT(*) as changes_count
            FROM snapshots
            WHERE timestamp > ?
            GROUP BY url, DATE(timestamp, 'unixepoch')
            ORDER BY timestamp DESC;
        """
        cursor.execute(recent_query, (seven_days_ago,))
        recent_activity = cursor.fetchall()
        
        return {
            'last_changes': results,
            'recent_activity': recent_activity,
            'total_urls': len(results)
        }
        
    except sqlite3.Error as e:
        print(f"ERROR: Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def format_timestamp(unix_timestamp):
    """Convert Unix timestamp to readable format."""
    try:
        dt = datetime.fromtimestamp(unix_timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Invalid timestamp"

def generate_text_report(data):
    """Generate detailed text report."""
    if not data:
        return "No data available to generate report.\n"
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f"URLWATCH MONITORING REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Summary
    report_lines.append(f"📊 SUMMARY:")
    report_lines.append(f"   • Total URLs monitored: {data['total_urls']}")
    report_lines.append(f"   • Recent activity (7 days): {len(data['recent_activity'])} changes")
    report_lines.append("")
    
    # Last changes for each URL
    report_lines.append("📅 LAST CHANGE PER URL (most recent first):")
    report_lines.append("-" * 80)
    
    for url, timestamp, snapshots_count in data['last_changes']:
        formatted_date = format_timestamp(timestamp)
        days_ago = (datetime.now() - datetime.fromtimestamp(timestamp)).days
        report_lines.append(f"{formatted_date} ({days_ago} days ago) - {snapshots_count} snapshots")
        report_lines.append(f"   {url}")
        report_lines.append("")
    
    # Recent activity
    if data['recent_activity']:
        report_lines.append("🔥 RECENT ACTIVITY (last 7 days):")
        report_lines.append("-" * 80)
        for url, timestamp, changes in data['recent_activity']:
            formatted_date = format_timestamp(timestamp)
            report_lines.append(f"{formatted_date} - {changes} changes")
            report_lines.append(f"   {url}")
            report_lines.append("")
    else:
        report_lines.append("🔥 RECENT ACTIVITY: No changes detected in the last 7 days")
        report_lines.append("")
    
    return "\n".join(report_lines)

def generate_json_report(data):
    """Generate JSON report for programmatic access."""
    if not data:
        return {
            "status": "no_data",
            "timestamp": datetime.now().isoformat(),
            "message": "No data available"
        }
    
    json_data = {
        "status": "success",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_urls": data['total_urls'],
            "recent_changes_7d": len(data['recent_activity'])
        },
        "urls": []
    }
    
    for url, timestamp, snapshots_count in data['last_changes']:
        url_data = {
            "url": url,
            "last_change": {
                "timestamp": timestamp,
                "formatted": format_timestamp(timestamp),
                "days_ago": (datetime.now() - datetime.fromtimestamp(timestamp)).days
            },
            "total_snapshots": snapshots_count
        }
        json_data["urls"].append(url_data)
    
    # Add recent activity
    json_data["recent_activity"] = []
    for url, timestamp, changes in data['recent_activity']:
        json_data["recent_activity"].append({
            "url": url,
            "timestamp": timestamp,
            "formatted": format_timestamp(timestamp),
            "changes_count": changes
        })
    
    return json_data

def main():
    """Main execution function."""
    ensure_logs_directory()
    
    if not check_database_exists():
        print("Exiting: Database not found (this is normal on first run)")
        return 0
    
    print("Analyzing urlwatch database...")
    data = get_database_info()
    
    if not data:
        print("ERROR: Could not retrieve data from database")
        return 1
    
    # Generate text report
    text_report = generate_text_report(data)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(text_report)
    print(f"✅ Text report saved to: {OUTPUT_FILE}")
    
    # Generate JSON report
    json_report = generate_json_report(data)
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON report saved to: {JSON_OUTPUT}")
    
    # Print summary to console
    if data['last_changes']:
        print(f"\n📊 Found {len(data['last_changes'])} monitored URLs")
        print(f"🔥 Recent activity: {len(data['recent_activity'])} changes in last 7 days")
        
        most_recent = data['last_changes'][0]
        most_recent_date = format_timestamp(most_recent[1])
        print(f"🕐 Most recent change: {most_recent_date}")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
