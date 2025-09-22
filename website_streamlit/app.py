import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

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

def main():
    st.set_page_config(page_title="Simple Login", page_icon="🔐")
    
    # Configuration - UPDATE THESE WITH YOUR BIGQUERY DETAILS
    PROJECT_ID = "my-project-1706650764881"
    DATASET_ID = "step_lotto"  
    TABLE_ID = "user_steps"  # your table name
    
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
        st.subheader("📊 Your Steps Dashboard")
        
        try:
            # Initialize BigQuery client
            client = init_bigquery_client()
            
            # Add sample data button (for testing - remove in production)
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Add Sample Data", help="Click to add sample step data for testing"):
                    if add_sample_data(client, st.session_state.username, PROJECT_ID, DATASET_ID, TABLE_ID):
                        st.success("Sample data added!")
                        st.rerun()
                    else:
                        st.error("Failed to add sample data.")
            
            # Get user steps data
            steps_df = get_user_steps(client, st.session_state.username, PROJECT_ID, DATASET_ID, TABLE_ID)
            
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

if __name__ == "__main__":
    main()