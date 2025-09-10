import functions_framework
from google.cloud import bigquery
import json
from datetime import datetime

# Initialize BigQuery client
client = bigquery.Client()

# Configure your BigQuery details
PROJECT_ID = "my-project-1706650764881"
DATASET_ID = "step_lotto" 
TABLE_ID = "steps"

@functions_framework.http
def insert_to_bigquery(request):
    """HTTP Cloud Function to insert data from Apple Shortcut into BigQuery"""
    
    # Set CORS headers for the response
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    # Only accept POST requests
    if request.method != 'POST':
        return ('Method not allowed', 405, headers)
    
    try:
        # Parse the JSON data from the request
        if request.is_json:
            data = request.get_json()
        else:
            return ('Invalid JSON', 400, headers)
        
        # Extract the fields from JSON
        name = data.get('name')
        steps = data.get('steps')
        date = data.get('date')
        
        # Validate required fields
        if not all([name, steps, date]):
            return ('Missing required fields: name, steps, date', 400, headers)
        
        # Prepare the row for BigQuery
        row_to_insert = {
            'name': name,
            'steps': int(steps),  # Ensure steps is an integer
            'date': date,  # Assuming date is in correct format (YYYY-MM-DD)
            'timestamp': datetime.utcnow().isoformat()  # Add insertion timestamp
        }
        
        # Get table reference
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        table = client.get_table(table_ref)
        
        # Insert the row
        errors = client.insert_rows_json(table, [row_to_insert])
        
        if errors:
            print(f"BigQuery insert errors: {errors}")
            return (f'Error inserting data: {errors}', 500, headers)
        
        return ('Data inserted successfully', 200, headers)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return (f'Internal server error: {str(e)}', 500, headers)
    

#HELLLLLOOOOOOOO DID THIS WORKKKKK