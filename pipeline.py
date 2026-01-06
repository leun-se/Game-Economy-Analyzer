import json
import sqlite3
from datetime import datetime

def run_pipeline():
    print("--- Starting Robust Pipeline ---")
    clean_data = []
    
    # Database setup
    conn = sqlite3.connect('game_analytics.db')
    cursor = conn.cursor()
    
    # Create table (if it's not already there)
    # Table A: The clean data for analysts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valid_loot(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            item_name TEXT,
            item_value INTEGER
        )
    ''')
    
    # Table B: The "Dead Letter Queue" for rejects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suspicious_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_record TEXT,
            rejection_reason TEXT,
            timestamp TEXT
        )      
    ''')
    
    valid_count = 0
    suspicious_count = 0
    
    # PROCESS DATA
    with open('loot_data.json', 'r') as file:
        for line in file:
            record = json.loads(line)
            val = record['value']
            name = record['item']
            
            # 2. LOGIC: Determine where the data goes
            # Rule: Value cannot be negative or greater than 500
            if 0 <= val <=500 and name != "":
                # PATH A: Success
                cursor.execute("INSERT INTO valid_loot (player_id, item_name, item_value) VALUES (?, ?, ?)",
                                (record['playerId'], record['item'], val))
                valid_count += 1
            else:
                # PATH B: Failure
                # Determine specific reason for the logs
                if val > 500:
                    reason = "VALUE_TOO_HIGH"
                elif val < 0:
                    reason = "VALUE_NEGATIVE"
                else:
                    reason = "MISSING_NAME"
            
                cursor.execute("INSERT INTO suspicious_events (raw_record, rejection_reason, timestamp) VALUES (?, ?, ?)",
                            (str(record), reason, datetime.now().isoformat()))
                suspicious_count += 1
                print(f"Dropping bad record: {record}")
    conn.commit()
    
    print(f"Pipeline Finished: {valid_count} valid records, {suspicious_count} suspicious events.")
    
    # 3. VERIFY: Show the "Hacker" list
    print("\n--- SUSPICIOUS ACTIVITY REPORT ---")
    cursor.execute("SELECT * FROM suspicious_events")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    conn.close()
    
run_pipeline()