import streamlit as st
from login.login import show_login_page
from homepage.homepage import show_homepage
from create_league.create_league import show_create_league_page
from league_page.league_page import show_league_page

def main():
    st.set_page_config(page_title="Step Lotto", page_icon="🔐")
    
    # Configuration - UPDATE THESE WITH YOUR BIGQUERY DETAILS
    PROJECT_ID = "my-project-1706650764881"
    DATASET_ID = "step_lotto"  
    TABLE_ID = "user_steps"
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'page' not in st.session_state:
        st.session_state.page = "homepage"
    if 'current_league' not in st.session_state:
        st.session_state.current_league = ""
    
    # Route to appropriate page
    if not st.session_state.logged_in:
        show_login_page(PROJECT_ID, DATASET_ID)  # ← REMOVED TABLE_ID
    else:
        if st.session_state.page == "create_league":
            show_create_league_page(PROJECT_ID, DATASET_ID)
        elif st.session_state.page == "league_page":
            show_league_page(st.session_state.current_league, PROJECT_ID, DATASET_ID)
        else:
            show_homepage(PROJECT_ID, DATASET_ID, TABLE_ID)

if __name__ == "__main__":
    main()