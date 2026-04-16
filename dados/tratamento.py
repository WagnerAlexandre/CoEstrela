import pandas as pd

target = 1.0
file_path = 'person_ids_04_15_2026.json'

try:
    df = pd.read_json(file_path, lines=True, encoding='utf-8')
    
    # Filter the data
    filtered_df = df[df['popularity'] >= target]
    
    filtered_df.to_json('filtered_people.json', orient='records', force_ascii=False, indent=4)
    
    print(f"Success! Filtered {len(filtered_df)} records.")

except Exception as e:
    print(f"An error occurred: {e}")

