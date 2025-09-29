import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

@st.cache_resource
def init_bigquery_client():
    """Initialize BigQuery client using service account from secrets"""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(
        credentials=credentials,
        project="my-project-1706650764881"
    )

def check_user_exists(client, email, project_id, dataset_id):
    """Check if email exists in user_ids table and return has_steps status"""
    query = f"""
    SELECT 
        u.user_id,
        EXISTS(
            SELECT 1 
            FROM `{project_id}.{dataset_id}.user_steps` s 
            WHERE s.name = u.user_id
        ) AS has_steps
    FROM `{project_id}.{dataset_id}.user_ids` u
    WHERE u.user_id = @email
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("email", "STRING", email)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    for row in results:
        return True, row.has_steps
    return False, False

def add_user(client, email, first_name, last_name, project_id, dataset_id):
    """Add new user to user_ids table"""
    table_ref = client.dataset(dataset_id, project=project_id).table("user_ids")
    table = client.get_table(table_ref)
    
    # Create row to insert
    rows_to_insert = [{
        "user_id": email,
        "first_name": first_name,
        "last_name": last_name
    }]
    
    errors = client.insert_rows_json(table, rows_to_insert)
    return len(errors) == 0

def show_login_page(project_id, dataset_id):
    """Display the login page with separate Login and Sign Up options"""
    st.title("🔐 Step Lotto")
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # Login Tab
    with tab1:
        st.subheader("Login to your account")
        login_email = st.text_input("Email:", placeholder="your.email@example.com", key="login_email")
        
        if st.button("Login", type="primary", key="login_button"):
            if login_email.strip():
                try:
                    # Initialize BigQuery client
                    client = init_bigquery_client()
                    
                    # Check if user exists and get has_steps status
                    user_exists, has_steps = check_user_exists(client, login_email.strip(), project_id, dataset_id)
                    
                    if user_exists:
                        st.success(f"Welcome back!")
                        st.session_state.logged_in = True
                        st.session_state.username = login_email.strip()
                        
                        # Route based on has_steps status
                        if has_steps:
                            st.session_state.page = "homepage"
                        else:
                            st.session_state.page = "setup_steps"
                        
                        st.rerun()
                    else:
                        st.error("Email not found. Please sign up if you're a new user.")
                        
                except Exception as e:
                    st.error(f"Error connecting to database: {str(e)}")
                    st.info("Make sure your BigQuery credentials are properly configured.")
            else:
                st.warning("Please enter your email.")
    
    # Sign Up Tab
    with tab2:
        st.subheader("Create a new account")
        signup_email = st.text_input("Email:", placeholder="your.email@example.com", key="signup_email")
        signup_first_name = st.text_input("First Name:", placeholder="John", key="signup_first_name")
        signup_last_name = st.text_input("Last Name:", placeholder="Doe", key="signup_last_name")
        
        if st.button("Sign Up", type="primary", key="signup_button"):
            if signup_email.strip() and signup_first_name.strip() and signup_last_name.strip():
                try:
                    # Initialize BigQuery client
                    client = init_bigquery_client()
                    
                    # Check if user already exists
                    user_exists, _ = check_user_exists(client, signup_email.strip(), project_id, dataset_id)
                    
                    if user_exists:
                        st.error("Email already exists. Please login or use a different email.")
                    else:
                        # Add new user
                        if add_user(client, signup_email.strip(), signup_first_name.strip(), 
                                   signup_last_name.strip(), project_id, dataset_id):
                            st.success(f"Account created successfully! Welcome, {signup_first_name}!")
                            st.session_state.logged_in = True
                            st.session_state.username = signup_email.strip()
                            st.session_state.page = "setup_steps"  # New users go to setup
                            st.rerun()
                        else:
                            st.error("Failed to create account. Please try again.")
                            
                except Exception as e:
                    st.error(f"Error connecting to database: {str(e)}")
                    st.info("Make sure your BigQuery credentials are properly configured.")
            else:
                st.warning("Please fill in all fields (email, first name, and last name).")