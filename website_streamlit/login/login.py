import streamlit as st
from google.cloud import bigquery

@st.cache_resource
def init_bigquery_client():
    """Initialize BigQuery client with proper authentication"""
    try:
        # Check if we're running on Streamlit Cloud
        if "gcp_service_account" in st.secrets:
            # Use service account from secrets
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            client = bigquery.Client(
                credentials=credentials,
                project=st.secrets["gcp_service_account"]["project_id"]
            )
        else:
            # Local development - use default credentials
            client = bigquery.Client(project="my-project-1706650764881")
        
        return client
    except Exception as e:
        st.error(f"Failed to initialize BigQuery client: {str(e)}")
        return None

def check_user_exists(client, username, project_id, dataset_id, table_id):
    """Check if username exists in BigQuery table"""
    query = f"""
    SELECT COUNT(*) as count
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE name = @username
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
    rows_to_insert = [{"name": username}]
    
    errors = client.insert_rows_json(table, rows_to_insert)
    return len(errors) == 0

def show_login_page(project_id, dataset_id, table_id):
    """Display the login page"""
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
                user_exists = check_user_exists(client, username.strip(), project_id, dataset_id, table_id)
                
                if user_exists:
                    st.success(f"Welcome back, {username}!")
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip()
                    st.rerun()
                else:
                    # Add new user
                    if add_user(client, username.strip(), project_id, dataset_id, table_id):
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