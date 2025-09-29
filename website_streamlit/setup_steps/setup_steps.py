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

def show_setup_steps_page(project_id, dataset_id, table_id):
    """Display the setup steps page for new users"""
    st.title("📱 Setup Your Step Tracking")
    
    st.write(f"Welcome, **{st.session_state.username}**!")
    st.info("To participate in Step Lotto, you need to install our Apple Shortcut to automatically sync your step data.")
    
    st.markdown("---")
    
    # Instructions for installing the shortcut
    st.subheader("🔧 Installation Instructions")
    
    st.markdown("""
    ### Step 1: Install the Shortcut
    Click the button below to open the Step Lotto shortcut in the Shortcuts app on your iPhone:
    """)
    
    # Shortcut link button
    st.link_button(
        "📲 Install Step Lotto Shortcut",
        "https://www.icloud.com/shortcuts/5c0513a22a2c42da8f119d8c0cfd3df2",
        type="primary",
        use_container_width=True
    )
    
    st.markdown("""
    ### Step 2: Configure the Shortcut
    1. Tap **"Add Shortcut"** when prompted
    2. The shortcut will request access to your Health data
    3. Grant permission to read your step count data
    
    ### Step 3: Run the Shortcut
    1. Open the Shortcuts app on your iPhone
    2. Find the "Step Lotto" shortcut
    3. Tap it to run and sync your steps
    
    ### Step 4: Set Up Automation (Optional but Recommended)
    To automatically sync your steps daily:
    1. Go to the **Automation** tab in the Shortcuts app
    2. Create a new automation to run the Step Lotto shortcut daily
    3. This ensures your steps are always up to date!
    """)
    
    st.markdown("---")
    
    # Check if steps have been synced
    st.subheader("✅ Verify Your Setup")
    
    if st.button("Check if Steps are Synced", type="secondary", use_container_width=True):
        try:
            # Initialize BigQuery client
            client = init_bigquery_client()
            
            # Check if user has any steps
            query = f"""
            SELECT COUNT(*) as count
            FROM `{project_id}.{dataset_id}.{table_id}`
            WHERE name = @username
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("username", "STRING", st.session_state.username)
                ]
            )
            
            query_job = client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                if row.count > 0:
                    st.success(f"Great! We found {row.count} step entries for your account. Redirecting to homepage...")
                    st.session_state.page = "homepage"
                    st.rerun()
                else:
                    st.warning("No steps found yet. Please install and run the shortcut, then check again.")
                    
        except Exception as e:
            st.error(f"Error checking steps: {str(e)}")
    
    st.markdown("---")
    
    # Helpful tips
    st.subheader("💡 Need Help?")
    st.markdown("""
    **Troubleshooting:**
    - Make sure you've granted the shortcut permission to access Health data
    - Verify that your iPhone has step data in the Health app
    - Try running the shortcut manually first to test it works
    - The shortcut syncs your steps from the last 7 days automatically
    
    **Important:** You need to have step data synced before you can join or create leagues!
    """)
    
    # Logout option
    st.markdown("---")
    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = "homepage"
        st.rerun()