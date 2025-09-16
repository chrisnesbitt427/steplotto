import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
import datetime
import random

# Page config
st.set_page_config(
    page_title="Step Lotto", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS matching the mockup design
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .logo {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .pot-amount {
        font-size: 2.5rem;
        color: #FFD700;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .countdown {
        font-size: 1.2rem;
        background: rgba(255,255,255,0.1);
        padding: 10px 20px;
        border-radius: 25px;
        text-align: center;
        margin: 0 auto;
        width: fit-content;
    }
    
    .metric-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255,255,255,0.2);
        height: 100%;
    }
    
    .big-number {
        font-size: 3rem;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
    }
    
    .stat-label {
        text-align: center;
        color: #FFD700;
        margin-bottom: 20px;
    }
    
    .leaderboard-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        margin: 10px 0;
        border-radius: 15px;
        background: rgba(255,255,255,0.1);
    }
    
    .rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500) !important; }
    .rank-2 { background: linear-gradient(135deg, #C0C0C0, #999999) !important; }
    .rank-3 { background: linear-gradient(135deg, #CD7F32, #8B4513) !important; }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        margin-right: 10px;
    }
    
    .win-chance {
        font-size: 1.1rem;
        font-weight: bold;
        color: #4CAF50;
    }
    
    .pot-visual {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        margin: 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        color: #333;
    }
    
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #FFD700;
    }
    
    div[data-testid="metric-container"] > label[data-testid="metric-container-label"] {
        color: white !important;
    }
    
    div[data-testid="metric-container"] > div[data-testid="metric-container-value"] {
        color: #FFD700 !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_steps_data():
    """Load individual steps data"""
    try:
        # Use credentials from Streamlit secrets
        from google.oauth2 import service_account
        
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = bigquery.Client(credentials=credentials, project=st.secrets["gcp_service_account"]["project_id"])
        
        query = """
        SELECT 
            name, 
            SUM(steps) as total_steps 
        FROM `my-project-1706650764881.step_lotto.steps` 
        GROUP BY name
        ORDER BY total_steps DESC
        """
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error loading steps data: {e}")
        # Sample data fallback
        names = ["Chris", "Alice", "Mike", "Sarah", "James", "Emma"]
        data = []
        for i, name in enumerate(names):
            steps = random.randint(8000, 15000) - (i * 1000)
            data.append({"name": name, "total_steps": steps})
        return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_pot_data():
    """Load pot data"""
    try:
        # Use credentials from Streamlit secrets
        from google.oauth2 import service_account
        
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = bigquery.Client(credentials=credentials, project=st.secrets["gcp_service_account"]["project_id"])
        
        query = """
        SELECT 
            date,
            total_steps,
            players,
            daily_pot,
            cumulative_pot
        FROM `my-project-1706650764881.step_lotto.pot` 
        ORDER BY date ASC
        """
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error loading pot data: {e}")
        # Sample data fallback
        dates = pd.date_range(start='2024-01-01', end='2024-01-07', freq='D')
        data = []
        cumulative = 0
        for i, date in enumerate(dates):
            daily = round(random.uniform(0.8, 1.2), 2)
            cumulative += daily
            data.append({
                'date': date.date(),
                'total_steps': random.randint(45000, 65000),
                'players': random.randint(5, 8),
                'daily_pot': daily,
                'cumulative_pot': round(cumulative, 2)
            })
        return pd.DataFrame(data)

def calculate_win_probabilities(steps_df):
    """Calculate win probability for each player"""
    total_steps = steps_df['total_steps'].sum()
    steps_df['win_probability'] = (steps_df['total_steps'] / total_steps * 100).round(1)
    return steps_df

def main():
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown('<div class="logo">🎯 STEP LOTTO</div>', unsafe_allow_html=True)
    
    # Load data
    steps_df = load_steps_data()
    pot_df = load_pot_data()
    
    if not pot_df.empty:
        current_pot = pot_df['cumulative_pot'].iloc[-1]
        st.markdown(f'<div class="pot-amount">£{current_pot:.2f} UP FOR GRABS!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pot-amount">£47.00 UP FOR GRABS!</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="countdown">⏰ 2 days 14 hours until draw</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculate probabilities
    steps_df = calculate_win_probabilities(steps_df)
    
    # Main dashboard grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚶‍♀️ YOUR STATS")
        
        # Assuming user is the top player for demo
        user_stats = steps_df.iloc[0] if not steps_df.empty else {"name": "You", "total_steps": 12847, "win_probability": 23.5}
        
        # Your steps (big number)
        st.markdown(f'<div class="big-number">{user_stats["total_steps"]:,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">steps this week</div>', unsafe_allow_html=True)
        
        # Stats
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            st.metric("Your Share", f"{user_stats['win_probability']:.1f}%")
        with col1_2:
            st.metric("Win Probability", f"{user_stats['win_probability']:.1f}%")
        
        # Progress bar
        st.progress(user_stats['win_probability'] / 100)
        
        # Payment status
        st.success("✅ Paid this week")
    
    with col2:
        st.markdown("### 🏆 LEADERBOARD")
        
        # Top 5 leaderboard
        top_5 = steps_df.head(5)
        
        for i, (_, row) in enumerate(top_5.iterrows()):
            rank = i + 1
            name = row['name']
            steps = int(row['total_steps'])
            probability = row['win_probability']
            
            # CSS class for styling
            rank_class = ""
            if rank == 1:
                rank_class = "rank-1"
            elif rank == 2:
                rank_class = "rank-2"
            elif rank == 3:
                rank_class = "rank-3"
            
            # Create leaderboard item
            st.markdown(f"""
            <div class="leaderboard-item {rank_class}">
                <div style="display: flex; align-items: center;">
                    <div class="avatar">{name[0]}</div>
                    <div>
                        <div style="font-weight: bold;">{name}</div>
                        <div>{steps:,} steps</div>
                    </div>
                </div>
                <div class="win-chance">{probability:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Bottom section
    col3, col4 = st.columns([2, 1])
    
    with col3:
        st.markdown("### 📈 WEEKLY PROGRESS")
        
        if not pot_df.empty:
            # Create line chart of daily steps
            fig = px.line(
                pot_df, 
                x='date', 
                y='total_steps',
                title="Daily Total Steps",
                color_discrete_sequence=['#FFD700']
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_color='white'
            )
            
            fig.update_xaxes(gridcolor='rgba(255,255,255,0.2)')
            fig.update_yaxes(gridcolor='rgba(255,255,255,0.2)')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Total steps this week
            total_weekly_steps = pot_df['total_steps'].sum()
            st.markdown(f'<div style="text-align: center; color: rgba(255,255,255,0.8);">Total steps this week: <strong style="color: #FFD700;">{total_weekly_steps:,}</strong></div>', unsafe_allow_html=True)
        else:
            st.info("📊 Weekly progress chart will appear here")
    
    with col4:
        st.markdown("### 💰 THE POT")
        
        # Pot visualization
        if not pot_df.empty:
            current_pot = pot_df['cumulative_pot'].iloc[-1]
            num_players = pot_df['players'].iloc[-1] if 'players' in pot_df.columns else 7
        else:
            current_pot = 47.0
            num_players = 7
        
        st.markdown(f'<div class="pot-visual">£{current_pot:.0f}</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align: center; margin: 15px 0;">
            <strong>{num_players} players</strong> × £1 each<br>
            <span style="color: rgba(255,255,255,0.7);">per week</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Pot growth chart
        if not pot_df.empty and len(pot_df) > 1:
            st.markdown("**Pot Growth**")
            fig_pot = px.line(
                pot_df, 
                x='date', 
                y='cumulative_pot',
                color_discrete_sequence=['#4CAF50']
            )
            
            fig_pot.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=False,
                height=200,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            fig_pot.update_xaxes(gridcolor='rgba(255,255,255,0.2)', showticklabels=False)
            fig_pot.update_yaxes(gridcolor='rgba(255,255,255,0.2)')
            
            st.plotly_chart(fig_pot, use_container_width=True)

if __name__ == "__main__":
    main()