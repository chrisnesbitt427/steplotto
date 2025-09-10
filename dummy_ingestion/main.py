import functions_framework
from google.cloud import bigquery
import random
from datetime import datetime, date
import json

# Initialize BigQuery client
client = bigquery.Client()

# Configure your BigQuery details
PROJECT_ID = "my-project-1706650764881"
DATASET_ID = "step_lotto"
TABLE_ID = "steps"

# List of dummy user names
DUMMY_USERS = [
    "Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince", "Eve Adams",
    "Frank Miller", "Grace Lee", "Henry Ford", "Ivy Chen", "Jack Wilson",
    "Kate Davis", "Liam O'Connor", "Maya Patel", "Noah Williams", "Olivia Taylor"
]

@functions_framework.cloud_event
def generate_dummy_data(cloud_event):
    """Cloud Function triggered by Cloud Scheduler to generate daily dummy step data"""
    
    try:
        # Get today's date
        today = date.today().isoformat()
        
        # Prepare rows for all users
        rows_to_insert = []
        
        for user_name in DUMMY_USERS:
            # Generate random steps between 3000 and 15000
            steps = random.randint(3000, 15000)
            
            row = {
                'name': user_name,
                'steps': steps,
                'date': today,
                'timestamp': datetime.utcnow().isoformat()
            }
            rows_to_insert.append(row)
        
        # Get table reference
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        table = client.get_table(table_ref)
        
        # Insert all rows at once
        errors = client.insert_rows_json(table, rows_to_insert)
        
        if errors:
            print(f"BigQuery insert errors: {errors}")
            raise Exception(f"Error inserting data: {errors}")
        
        print(f"Successfully inserted {len(rows_to_insert)} dummy records for {today}")
        return f"Generated dummy data for {len(DUMMY_USERS)} users on {today}"
        
    except Exception as e:
        print(f"Error generating dummy data: {str(e)}")
        raise e
    
    #hi