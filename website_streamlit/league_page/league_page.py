import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px

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

def get_league_members(client, league_id, project_id, dataset_id):
    """Get all members of a specific league"""
    query = f"""
    SELECT player_id
    FROM `{project_id}.{dataset_id}.league_memberships`
    WHERE league_id = @league_id
    ORDER BY player_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league_id", "STRING", league_id)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    # Convert to DataFrame
    df = results.to_dataframe()
    return df

def get_league_member_steps(client, league_id, project_id, dataset_id):
    """Get total steps for each member in the league"""
    query = f"""
    SELECT 
        lm.player_id,
        COALESCE(SUM(us.steps), 0) as total_steps
    FROM `{project_id}.{dataset_id}.league_memberships` lm
    LEFT JOIN `{project_id}.{dataset_id}.user_steps` us ON lm.player_id = us.name
    WHERE lm.league_id = @league_id
    GROUP BY lm.player_id
    ORDER BY total_steps DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league_id", "STRING", league_id)
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    # Convert to DataFrame
    df = results.to_dataframe()
    return df

def show_league_page(league_id, project_id, dataset_id):
    """Display the league page for a specific league"""
    st.title(f"🏆 {league_id}")
    
    # Back button
    if st.button("← Back to Homepage"):
        st.session_state.page = "homepage"
        st.rerun()
    
    st.markdown("---")
    
    try:
        # Initialize BigQuery client
        client = init_bigquery_client()
        
        # Get league members
        members_df = get_league_members(client, league_id, project_id, dataset_id)
        
        if members_df.empty:
            st.warning("This league has no members.")
            return
        
        # Get member steps data
        steps_df = get_league_member_steps(client, league_id, project_id, dataset_id)
        
        # Display league stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Members", len(members_df))
        with col2:
            total_league_steps = steps_df['total_steps'].sum()
            st.metric("Total League Steps", f"{int(total_league_steps):,}")
        with col3:
            if len(steps_df) > 0:
                avg_steps = steps_df['total_steps'].mean()
                st.metric("Average Steps per Member", f"{int(avg_steps):,}")
        
        st.markdown("---")
        
        # Two columns for members table and pie chart
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("👥 League Members")
            
            # Display members with their step counts
            if not steps_df.empty:
                display_df = steps_df.copy()
                display_df['total_steps'] = display_df['total_steps'].apply(lambda x: f"{int(x):,}")
                display_df = display_df.rename(columns={
                    'player_id': 'Member', 
                    'total_steps': 'Total Steps'
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                # Just show member names if no step data
                members_display = members_df.rename(columns={'player_id': 'Member'})
                st.dataframe(members_display, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Steps Distribution")
            
            # Create pie chart only if there are steps
            if not steps_df.empty and steps_df['total_steps'].sum() > 0:
                # Filter out members with 0 steps for a cleaner pie chart
                chart_data = steps_df[steps_df['total_steps'] > 0].copy()
                
                if not chart_data.empty:
                    fig = px.pie(
                        chart_data, 
                        values='total_steps', 
                        names='player_id',
                        title='Total Steps by Member'
                    )
                    
                    fig.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Steps: %{value:,}<br>Percentage: %{percent}<extra></extra>'
                    )
                    
                    fig.update_layout(
                        height=400,
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.05
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No step data available for pie chart.")
            else:
                st.info("No step data available for this league yet.")
        
        # Additional league info
        st.markdown("---")
        st.subheader("ℹ️ League Information")
        
        if not steps_df.empty:
            # Find top performer
            top_performer = steps_df.loc[steps_df['total_steps'].idxmax()]
            if top_performer['total_steps'] > 0:
                st.success(f"🥇 **Top Performer:** {top_performer['player_id']} with {int(top_performer['total_steps']):,} steps!")
            
            # Show some encouragement for members with no steps
            no_steps_members = steps_df[steps_df['total_steps'] == 0]
            if not no_steps_members.empty:
                st.info(f"💪 **Get Moving:** {', '.join(no_steps_members['player_id'].tolist())} - Start tracking your steps to appear on the chart!")
        
    except Exception as e:
        st.error(f"Error loading league data: {str(e)}")
        st.info("Make sure your BigQuery credentials are properly configured and the tables exist.")