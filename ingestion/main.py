import functions_framework
from google.cloud import bigquery
import json
from datetime import datetime, timedelta

# Initialize BigQuery client
client = bigquery.Client()

# Configure your BigQuery details
PROJECT_ID = "my-project-1706650764881"
DATASET_ID = "step_lotto" 
TABLE_ID = "user_steps_input"

def json_to_records(data):
    """
    Convert JSON input with steps array to list of records (like DataFrame rows)
    
    Args:
        data (dict): Dictionary with name, steps array, and date
    
    Returns:
        list: List of dictionaries representing rows
    """
    
    # Extract fields
    name = data.get('name')
    steps_array = data.get('steps')
    base_date = data.get('date')
    
    # Validate required fields
    if not all([name, steps_array, base_date]):
        raise ValueError('Missing required fields: name, steps, date')
    
    # Create list of records
    records = []
    base_date_obj = datetime.strptime(base_date, '%Y-%m-%d')
    
    for i, step_count in enumerate(steps_array):
        # Calculate the date for each step count (going backwards from base_date)
        current_date = base_date_obj - timedelta(days=len(steps_array) - 1 - i)
        
        record = {
            'name': name,
            'steps': int(step_count),
            'date': current_date.strftime('%Y-%m-%d'),
            'timestamp': datetime.utcnow().isoformat()
        }
        records.append(record)
    
    return records

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
        
        # Convert JSON to records using the DataFrame logic
        rows_to_insert = json_to_records(data)
        
        # Get table reference
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        table = client.get_table(table_ref)
        
        # Insert all rows
        errors = client.insert_rows_json(table, rows_to_insert)
        
        if errors:
            print(f"BigQuery insert errors: {errors}")
            return (f'Error inserting data: {errors}', 500, headers)
        
        return (f'Successfully inserted {len(rows_to_insert)} rows for {data.get("name")}', 200, headers)
        
    except ValueError as ve:
        print(f"Validation error: {str(ve)}")
        return (f'Validation error: {str(ve)}', 400, headers)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return (f'Internal server error: {str(e)}', 500, headers)