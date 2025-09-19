#!/usr/bin/env python3
"""
Debug script to inspect urlwatch database structure and contents.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser('~/.cache/urlwatch/cache.db')

def inspect_database():
    """Inspect the database structure and sample data."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return
    
    print(f"🔍 Inspecting database: {DB_PATH}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables found: {[t[0] for t in tables]}")
        print()
        
        # 2. Inspect each table
        for table_name, in tables:
            print(f"🔎 Table: {table_name}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Show sample data (first 5 rows)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                sample_data = cursor.fetchall()
                print("Sample data (first 5 rows):")
                for i, row in enumerate(sample_data, 1):
                    print(f"  Row {i}: {row}")
            
            print()
        
        # 3. Specific queries for CacheEntry table if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CacheEntry';")
        if cursor.fetchone():
            print("🎯 CacheEntry Analysis")
            print("-" * 40)
            
            # Get unique keys (URLs)
            cursor.execute("SELECT DISTINCT key FROM CacheEntry WHERE key IS NOT NULL;")
            unique_keys = cursor.fetchall()
            print(f"Unique URLs/Keys: {len(unique_keys)}")
            for key, in unique_keys[:10]:  # Show first 10
                print(f"  - {key}")
            if len(unique_keys) > 10:
                print(f"  ... and {len(unique_keys) - 10} more")
            
            print()
            
            # Check if timestamp column exists
            cursor.execute("PRAGMA table_info(CacheEntry);")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'timestamp' in columns:
                print("⏰ Timestamp analysis:")
                cursor.execute("SELECT key, timestamp FROM CacheEntry WHERE timestamp IS NOT NULL ORDER BY timestamp DESC LIMIT 5;")
                recent = cursor.fetchall()
                for key, ts in recent:
                    try:
                        dt = datetime.fromtimestamp(ts)
                        print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} - {key}")
                    except:
                        print(f"  Invalid timestamp {ts} - {key}")
            else:
                print("⏰ No timestamp column found")
                
                # Show most recent entries by rowid
                cursor.execute("SELECT key, rowid FROM CacheEntry ORDER BY rowid DESC LIMIT 5;")
                recent = cursor.fetchall()
                print("Most recent entries (by rowid):")
                for key, rowid in recent:
                    print(f"  Entry #{rowid} - {key}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

def suggest_fixes():
    """Suggest fixes based on database structure."""
    print()
    print("💡 Suggestions:")
    print("-" * 40)
    print("1. The updated ultimos_cambios.py script should now work with your CacheEntry table")
    print("2. If you're still having issues, try running urlwatch manually first:")
    print("   urlwatch --urls urls2watch.yaml --verbose")
    print("3. Check that your urls2watch.yaml file is properly formatted")
    print("4. The cache might need time to build up data after first runs")

if __name__ == "__main__":
    inspect_database()
    suggest_fixes()
