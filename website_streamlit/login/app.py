import streamlit as st
from google.cloud import bigquery
import pandas as pd

# Initialize BigQuery client
@st.cache_resource
def init_bigquery_client():
    """Initialize BigQuery client - make sure you have credentials set up"""
    return bigquery.Client()

def check_user_exists(client, username, project_id, dataset_id, table_id):
    """Check if username exists in BigQuery table"""
    query = f"""
    SELECT COUNT(*) as count
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE user_id = @username
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    for row in results:
        return row.count > 0
    return False

def add_user(client, username, project_id, dataset_id, table_id):
    """Add new user to BigQuery table"""
    table_ref = client.dataset(dataset_id, project=project_id).table(table_id)
    table = client.get_table(table_ref)
    
    # Create row to insert
    rows_to_insert = [{"user_id": username}]
    
    errors = client.insert_rows_json(table, rows_to_insert)
    return len(errors) == 0

def main():
    st.set_page_config(page_title="Simple Login", page_icon="🔐")
    
    # Configuration - UPDATE THESE WITH YOUR BIGQUERY DETAILS
    PROJECT_ID = "my-project-1706650764881"
    DATASET_ID = "step_lotto"  
    TABLE_ID = "users"  # your table name
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    
    # Login page
    if not st.session_state.logged_in:
        st.title("🔐 Login")
        
        # Username input
        username = st.text_input("Enter your username:", placeholder="Username")
        
        # Login button
        if st.button("Login / Sign In", type="primary"):
            if username.strip():
                try:
                    # Initialize BigQuery client
                    client = init_bigquery_client()
                    
                    # Check if user exists
                    user_exists = check_user_exists(client, username.strip(), PROJECT_ID, DATASET_ID, TABLE_ID)
                    
                    if user_exists:
                        st.success(f"Welcome back, {username}!")
                        st.session_state.logged_in = True
                        st.session_state.username = username.strip()
                        st.rerun()
                    else:
                        # Add new user
                        if add_user(client, username.strip(), PROJECT_ID, DATASET_ID, TABLE_ID):
                            st.success(f"New user created! Welcome, {username}!")
                            st.session_state.logged_in = True
                            st.session_state.username = username.strip()
                            st.rerun()
                        else:
                            st.error("Failed to create user. Please try again.")
                            
                except Exception as e:
                    st.error(f"Error connecting to database: {str(e)}")
                    st.info("Make sure your BigQuery credentials are properly configured.")
            else:
                st.warning("Please enter a username.")
    
    # Homepage (after login)
    else:
        st.title("🏠 Homepage")
        st.write(f"Hello, **{st.session_state.username}**! You are successfully logged in.")
        
        # Logout button
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
        
        # Add some basic homepage content
        st.markdown("---")
        st.subheader("Welcome to your dashboard!")
        st.write("This is your homepage. You can add more features here.")

if __name__ == "__main__":
    main()