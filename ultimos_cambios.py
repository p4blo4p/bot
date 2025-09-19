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
            
            # Get unique GUIDs (URL hashes)
            cursor.execute("SELECT DISTINCT guid FROM CacheEntry WHERE guid IS NOT NULL;")
            unique_guids = cursor.fetchall()
            print(f"Unique URL hashes (GUIDs): {len(unique_guids)}")
            for guid, in unique_guids[:5]:  # Show first 5
                print(f"  - {guid}")
            if len(unique_guids) > 5:
                print(f"  ... and {len(unique_guids) - 5} more")
            
            print()
            
            # Show recent entries with content
            cursor.execute("SELECT guid, timestamp, data, tries FROM CacheEntry ORDER BY timestamp DESC LIMIT 5;")
            recent = cursor.fetchall()
            print("⏰ Recent entries:")
            for guid, ts, data, tries in recent:
                try:
                    dt = datetime.fromtimestamp(ts)
                    content_info = f" (content: {len(data or '')} chars)" if data else " (no content)"
                    retry_info = f" - {tries} retries" if tries > 0 else " - success"
                    print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')}{retry_info} - {guid[:16]}...{content_info}")
                except:
                    print(f"  Invalid timestamp {ts} - {guid}")
            
            # Show success/failure stats
            cursor.execute("SELECT tries, COUNT(*) FROM CacheEntry GROUP BY tries ORDER BY tries;")
            stats = cursor.fetchall()
            print()
            print("📊 Success/failure statistics:")
            for tries, count in stats:
                status = "✅ Successful" if tries == 0 else f"⚠️  {tries} retries"
                print(f"  {status}: {count} entries")
        
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
    print("1. ✅ Your database structure is now supported!")
    print("2. The urlwatch uses GUID hashes instead of storing full URLs for privacy/efficiency")
    print("3. Each GUID represents a unique URL from your urls2watch.yaml file")
    print("4. Try running the updated analysis script: python ultimos_cambios.py")
    print("5. Check timestamp patterns to understand monitoring frequency")
    print("6. Monitor 'tries' column - 0 means success, >0 means fetch failures")

if __name__ == "__main__":
    inspect_database()
    suggest_fixes()
