import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

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

def get_user_steps(client, username, project_id, dataset_id, table_id):
    """Get user steps data from BigQuery"""
    query = f"""
    SELECT 
        DATE(timestamp) as day,
        SUM(steps) as total_steps
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE name = @username
    GROUP BY DATE(timestamp)
    ORDER BY day
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    # Convert to DataFrame
    df = results.to_dataframe()
    return df

def add_sample_data(client, username, project_id, dataset_id, table_id):
    """Add some sample data for demonstration (optional)"""
    table_ref = client.dataset(dataset_id, project=project_id).table(table_id)
    table = client.get_table(table_ref)
    
    # Generate sample data for the last 7 days
    sample_data = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        steps = 5000 + (i * 1000) + (i % 3 * 500)  # Varying step counts
        sample_data.append({
            "user_id": username,
            "timestamp": date.isoformat(),
            "steps": steps
        })
    
    errors = client.insert_rows_json(table, sample_data)
    return len(errors) == 0

def check_league_exists_for_join(client, league_name, project_id, dataset_id):
    """Check if league exists in the leagues table"""
    query = f"""
    SELECT COUNT(*) as count
    FROM `{project_id}.{dataset_id}.leagues`
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

def check_user_already_in_league(client, username, league_name, project_id, dataset_id):
    """Check if user is already a member of the league"""
    query = f"""
    SELECT COUNT(*) as count
    FROM `{project_id}.{dataset_id}.league_memberships`
    WHERE player_id = @username AND league_id = @league_name
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username),
            bigquery.ScalarQueryParameter("league_name", "STRING", league_name)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    for row in results:
        return row.count > 0
    return False

def join_league(client, username, league_name, project_id, dataset_id):
    """Add user to league membership table"""
    table_ref = client.dataset(dataset_id, project=project_id).table("league_memberships")
    table = client.get_table(table_ref)
    
    # Create row to insert
    rows_to_insert = [{"player_id": username, "league_id": league_name}]
    
    errors = client.insert_rows_json(table, rows_to_insert)
    return len(errors) == 0

def get_user_leagues(client, username, project_id, dataset_id):
    """Get leagues that the user is a member of"""
    query = f"""
    SELECT league_id
    FROM `{project_id}.{dataset_id}.league_memberships`
    WHERE player_id = @username
    ORDER BY league_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    # Convert to DataFrame
    df = results.to_dataframe()
    return df

def show_homepage(project_id, dataset_id, table_id):
    """Display the homepage after login"""
    st.title("🏠 Homepage")
    st.write(f"Hello, **{st.session_state.username}**! You are successfully logged in.")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Create League", type="secondary"):
            st.session_state.page = "create_league"
            st.rerun()
    with col2:
        # Join League functionality
        with st.expander("Join League"):
            league_to_join = st.text_input("Enter League Name:", placeholder="League Name", key="join_league_input")
            if st.button("Join", type="primary", key="join_league_btn"):
                if league_to_join.strip():
                    try:
                        client = init_bigquery_client()
                        
                        # Check if league exists
                        if not check_league_exists_for_join(client, league_to_join.strip(), project_id, dataset_id):
                            st.error(f"League '{league_to_join}' does not exist.")
                        # Check if user is already in the league
                        elif check_user_already_in_league(client, st.session_state.username, league_to_join.strip(), project_id, dataset_id):
                            st.warning(f"You are already a member of '{league_to_join}'.")
                        else:
                            # Join the league
                            if join_league(client, st.session_state.username, league_to_join.strip(), project_id, dataset_id):
                                st.success(f"Successfully joined '{league_to_join}'!")
                                st.rerun()
                            else:
                                st.error("Failed to join league. Please try again.")
                    except Exception as e:
                        st.error(f"Error joining league: {str(e)}")
                else:
                    st.warning("Please enter a league name.")
    with col3:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "homepage"
            st.rerun()
    
    # Add some basic homepage content
    st.markdown("---")
    
    # My Leagues section
    st.subheader("🏆 My Leagues")
    
    try:
        # Initialize BigQuery client
        client = init_bigquery_client()
        
        # Get user leagues
        leagues_df = get_user_leagues(client, st.session_state.username, project_id, dataset_id)
        
        if not leagues_df.empty:
            # Display leagues in a nice format with clickable buttons
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("**Your Leagues:**")
                for league in leagues_df['league_id']:
                    if st.button(f"🏆 {league}", key=f"league_{league}"):
                        st.session_state.page = "league_page"
                        st.session_state.current_league = league
                        st.rerun()
            with col2:
                st.metric("Total Leagues", len(leagues_df))
        else:
            st.info("You're not a member of any leagues yet. Create one to get started!")
            
    except Exception as e:
        st.error(f"Error loading leagues: {str(e)}")
    
    st.markdown("---")
    st.subheader("📊 Your Steps Dashboard")
    
    try:
        # Initialize BigQuery client
        client = init_bigquery_client()
        
        # Add sample data button (for testing - remove in production)
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Add Sample Data", help="Click to add sample step data for testing"):
                if add_sample_data(client, st.session_state.username, project_id, dataset_id, table_id):
                    st.success("Sample data added!")
                    st.rerun()
                else:
                    st.error("Failed to add sample data.")
        
        # Get user steps data
        steps_df = get_user_steps(client, st.session_state.username, project_id, dataset_id, table_id)
        
        if not steps_df.empty:
            # Display summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Days Tracked", len(steps_df))
            with col2:
                st.metric("Average Daily Steps", f"{int(steps_df['total_steps'].mean()):,}")
            with col3:
                st.metric("Best Day", f"{int(steps_df['total_steps'].max()):,}")
            
            # Create the steps chart
            fig = px.line(
                steps_df, 
                x='day', 
                y='total_steps',
                title='Your Daily Steps',
                labels={
                    'day': 'Date',
                    'total_steps': 'Steps'
                }
            )
            
            # Customize the chart
            fig.update_traces(
                line=dict(width=3, color='#1f77b4'),
                marker=dict(size=8)
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                hovermode='x unified'
            )
            
            fig.update_xaxes(
                title_font=dict(size=14),
                tickformat='%b %d'
            )
            
            fig.update_yaxes(
                title_font=dict(size=14),
                tickformat=',d'
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Display recent data table
            st.subheader("📅 Recent Activity")
            recent_data = steps_df.tail(10).copy()
            recent_data['day'] = pd.to_datetime(recent_data['day']).dt.strftime('%Y-%m-%d')
            recent_data['total_steps'] = recent_data['total_steps'].apply(lambda x: f"{int(x):,}")
            recent_data = recent_data.rename(columns={'day': 'Date', 'total_steps': 'Steps'})
            st.dataframe(recent_data, use_container_width=True, hide_index=True)
            
        else:
            st.info("No step data found for your account.")
            st.write("Click 'Add Sample Data' to see how the dashboard works, or start tracking your steps!")
            
    except Exception as e:
        st.error(f"Error loading step data: {str(e)}")
        st.info("Make sure your BigQuery credentials are properly configured and the table exists.")