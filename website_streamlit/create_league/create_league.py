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

def check_league_exists(client, league_name, project_id, dataset_id, leagues_table):
    """Check if league name already exists in BigQuery table"""
    query = f"""
    SELECT COUNT(*) as count
    FROM `{project_id}.{dataset_id}.{leagues_table}`
    WHERE league_id = @league_name
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league_name", "STRING", league_name)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    for row in results:
        return row.count > 0
    return False

def create_league(client, league_name, project_id, dataset_id, leagues_table):
    """Add new league to BigQuery leagues table"""
    table_ref = client.dataset(dataset_id, project=project_id).table(leagues_table)
    table = client.get_table(table_ref)
    
    # Create row to insert
    rows_to_insert = [{"league_id": league_name}]
    
    errors = client.insert_rows_json(table, rows_to_insert)
    return len(errors) == 0

def add_league_membership(client, username, league_name, project_id, dataset_id, memberships_table):
    """Add user to league membership table"""
    table_ref = client.dataset(dataset_id, project=project_id).table(memberships_table)
    table = client.get_table(table_ref)
    
    # Create row to insert
    rows_to_insert = [{"player_id": username, "league_id": league_name}]
    
    errors = client.insert_rows_json(table, rows_to_insert)
    return len(errors) == 0

def show_create_league_page(project_id, dataset_id):
    """Display the create league page"""
    st.title("🏆 Create League")
    
    # Back button
    if st.button("← Back to Homepage"):
        st.session_state.page = "homepage"
        st.rerun()
    
    st.markdown("---")
    
    # League name input
    league_name = st.text_input("Enter league name:", placeholder="My Awesome League")
    
    # Create league button
    if st.button("Create League", type="primary"):
        if league_name.strip():
            try:
                # Initialize BigQuery client
                client = init_bigquery_client()
                
                # Check if league already exists
                league_exists = check_league_exists(client, league_name.strip(), project_id, dataset_id, "leagues")
                
                if league_exists:
                    st.error(f"League '{league_name}' already exists. Please choose a different name.")
                else:
                    # Create the league
                    league_created = create_league(client, league_name.strip(), project_id, dataset_id, "leagues")
                    
                    if league_created:
                        # Add user to league membership
                        membership_added = add_league_membership(
                            client, 
                            st.session_state.username, 
                            league_name.strip(), 
                            project_id, 
                            dataset_id, 
                            "league_memberships"
                        )
                        
                        if membership_added:
                            st.success(f"League '{league_name}' created successfully! You are now a member.")
                            st.info("Returning to homepage in 3 seconds...")
                            # Optional: Auto redirect after success
                            # st.session_state.page = "homepage"
                            # st.rerun()
                        else:
                            st.error("League created but failed to add you as a member. Please contact support.")
                    else:
                        st.error("Failed to create league. Please try again.")
                        
            except Exception as e:
                st.error(f"Error creating league: {str(e)}")
                st.info("Make sure your BigQuery credentials are properly configured and the tables exist.")
        else:
            st.warning("Please enter a league name.")
    
    # Show some helpful info
    st.markdown("---")
    st.info("💡 **Tip:** League names should be unique and descriptive. You'll be automatically added as the first member of your new league!")