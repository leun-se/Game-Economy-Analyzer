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
    
def run_pipeline():
    print("--- Starting Microservice Pipeline ---")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table (if it's not already there)
    # Table A: The clean data for analysts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valid_loot(
            id INT AUTO_INCREMENT PRIMARY KEY,
            player_id INT,
            item_name VARCHAR(255),
            item_value INT
        )
    ''')
    
    # Table B: The "Dead Letter Queue" for rejects
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
                cursor.execute("INSERT INTO valid_loot (player_id, item_name, item_value) VALUES (%s, %s, %s)",
                                (record['playerId'], name, val))
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
            
                cursor.execute("INSERT INTO suspicious_events (raw_record, rejection_reason, timestamp) VALUES (%s, %s, %s)",
                                (str(record), reason, datetime.now().isoformat()))
                suspicious_count += 1
                print(f"Dropping bad record: {record}")
    conn.commit()
    print(f"Pipeline Finished: {valid_count} valid, {suspicious_count} suspicious.")
    
    # 3. VERIFY: Show the "Hacker" list
    print("\n--- SUSPICIOUS ACTIVITY REPORT ---")
    cursor.execute("SELECT * FROM suspicious_events")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    conn.close()
    
run_pipeline()