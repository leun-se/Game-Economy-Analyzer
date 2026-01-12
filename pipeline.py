import json
import time
import os
import mysql.connector
from datetime import datetime

def get_db_connection():
    # Keep trying till MySQL wakes up
    retries = 10
    while retries > 0:
        try:
            print(f"Attempting to connect to MySQL... ({retries} left)")
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'), 
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            print("Connected to MySQL!")
            return conn
        except mysql.connector.Error as err:
            print(f"Database not ready yet: {err}")
            time.sleep(5)
            retries -= 1
    raise Exception("Could not connect to MySQL after multiple attempts")
    
    
def validate_drop(record):
    """
    Pure Logic Function:
    Takes a record (dict) -> Returns (isValid: bool, Reason: str)
    No database connections here! Just Logic.
    """
    item = record.get("item", "")
    value = record.get("value", 0)
    
    # Rule 1: Missing Name
    if not item or str(item).strip() == "":
        return False, "Missing Item Name"

    # Rule 2: Negative Value
    if value < 0:
        return False, "Negative Gold Value"
    
    # Rule 3: Value too High
    if value > 999999:
        return False, "Value Exceeds Limit"
    
    return True, "Valid"

def run_pipeline():
    print("--- Starting Microservice Pipeline ---")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Table A: Clean Data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valid_loot(
            id INT AUTO_INCREMENT PRIMARY KEY,
            player_id INT,
            item_name VARCHAR(255),
            item_value INT
        )
    ''')
    
    # Create Table B: Dead Letter Queue (Rejects)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suspicious_events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            raw_record TEXT,
            rejection_reason VARCHAR(255),
            timestamp VARCHAR(255)
        )      
    ''')
    
    valid_count = 0
    suspicious_count = 0
    
    # --- 3. Process Data using the Logic Helper ---
    try:
        with open('loot_data.json', 'r') as file:
            for line in file:
                # 1. Parse
                record = json.loads(line)
                
                # 2. VALIDATE (This is the key change!)
                # We delegate the decision to our tested function
                is_valid, reason = validate_drop(record)
                
                # 3. Route
                if is_valid:
                    # PATH A: Success
                    cursor.execute(
                        "INSERT INTO valid_loot (player_id, item_name, item_value) VALUES (%s, %s, %s)",
                        (record.get('playerId', 0), record['item'], record['value'])
                    )
                    valid_count += 1
                else:
                    # PATH B: Failure
                    # We use the 'reason' returned by the function
                    cursor.execute(
                        "INSERT INTO suspicious_events (raw_record, rejection_reason, timestamp) VALUES (%s, %s, %s)",
                        (str(record), reason, datetime.now().isoformat())
                    )
                    suspicious_count += 1
                    print(f"Dropping bad record: {reason}")
                    
        conn.commit()
        print(f"Pipeline Finished: {valid_count} valid, {suspicious_count} suspicious.")
        
    except FileNotFoundError:
        print("Error: loot_data.json not found. Run the Java Generator first.")
    except Exception as e:
        print(f"Pipeline Error: {e}")

    conn.close()
    
run_pipeline()