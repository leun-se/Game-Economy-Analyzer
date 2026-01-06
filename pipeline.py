import json

def run_pipeline():
    print("--- Starting ETL Pipeline ---")
    clean_data = []
    
    # 1. EXTRACT: Open the file Java created
    with open('loot_data.json', 'r') as file:
        for line in file:
            record = json.loads(line)
            
            # 2. TRANSFORM: Logic to clean the data
            # Rule: Value cannot be negative or greater than 500
            if 0 <= record['value'] <=500:
                # Add a new field: 'category' based on value
                if record['value'] > 400:
                    record['category'] = 'EPIC'
                elif record['value'] > 100:
                    record['category'] = 'RARE'
                else:
                    record['category'] = 'COMMON'
                    
                clean_data.append(record)
            else:
                print(f"Dropping bad record: {record}")
    
    # 3. LOAD: Print valid data (or save to new file)
    print("\n--- Final Clean Database ---")
    for row in clean_data:
        print(row)

run_pipeline()