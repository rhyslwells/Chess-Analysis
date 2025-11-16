"""
app.py
Main Streamlit dashboard for chess game analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_fetcher import ChessDataFetcher
from analyzer import ChessAnalyzer
from predictor import ChessPredictor

# Page configuration
st.set_page_config(
    page_title="Chess Game Analysis Dashboard",
    page_icon="♟️",
    layout="wide"
)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'username' not in st.session_state:
    st.session_state.username = ""

# Title and description
st.title("♟️ Chess Game Analysis Dashboard")
st.markdown("Analyze your Chess.com games, track performance trends, and predict outcomes.")

# Sidebar for data fetching
with st.sidebar:
    st.header("Data Management")
    
    username = st.text_input(
        "Chess.com Username",
        value=st.session_state.username,
        placeholder="Enter username",
        help="Try: RhysLWells, Hikaru, or MagnusCarlsen"
    )
    
    # Quick username examples
    st.caption("📝 Example usernames: RhysLWells, Hikaru, MagnusCarlsen")
    
    # Date range selection
    st.subheader("Fetch Games")
    date_option = st.radio(
        "Time Period",
        ["Last Month", "Last 3 Months", "Last 6 Months", "Custom Range"]
    )
    
    if date_option == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=90)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )
    else:
        end_date = datetime.now()
        if date_option == "Last Month":
            start_date = end_date - timedelta(days=30)
        elif date_option == "Last 3 Months":
            start_date = end_date - timedelta(days=90)
        else:  # Last 6 Months
            start_date = end_date - timedelta(days=180)
    
    fetch_button = st.button("🔄 Fetch Games", type="primary", use_container_width=True)
    
    if fetch_button and username:
        with st.spinner("Fetching games from Chess.com..."):
            try:
                fetcher = ChessDataFetcher()
                games = fetcher.fetch_multiple_months(
                    username,
                    start_date,
                    end_date
                )
                
                if games:
                    df = fetcher.process_and_save(username, games, mode='json')
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.session_state.username = username
                    st.success(f"✅ Loaded {len(df)} games!")
                else:
                    st.error("No games found for this period.")
            except Exception as e:
                st.error(f"Error fetching games: {e}")
    
    # Load existing data
    if username and not fetch_button:
        load_existing = st.button("📂 Load Saved Data", use_container_width=True)
        if load_existing:
            try:
                fetcher = ChessDataFetcher()
                df = fetcher.load_existing_data(username)
                if df is not None:
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.session_state.username = username
                    st.success(f"✅ Loaded {len(df)} games from file!")
                else:
                    st.warning("No saved data found. Please fetch games first.")
            except Exception as e:
                st.error(f"Error loading data: {e}")

# Main dashboard content
if st.session_state.data_loaded and st.session_state.df is not None:
    df = st.session_state.df
    analyzer = ChessAnalyzer(df)
    
    # Overall Statistics
    st.header("📊 Performance Overview")
    stats = analyzer.get_overall_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Games", stats['total_games'])
    col2.metric("Wins", stats['wins'])
    col3.metric("Losses", stats['losses'])
    col4.metric("Draws", stats['draws'])
    col5.metric("Win Rate", f"{stats['win_rate']:.1f}%")
    
    col1, col2 = st.columns(2)
    col1.metric("Average Rating", f"{stats['avg_user_rating']:.0f}")
    col2.metric("Avg Opponent Rating", f"{stats['avg_opponent_rating']:.0f}")
    
    # Charts
    st.header("📈 Performance Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Rating Trend", "Results Over Time", "Opening Performance", "Opponent Strength"
    ])
    
    with tab1:
        rating_trend = analyzer.get_rating_trend()
        fig = px.line(
            rating_trend,
            x='date',
            y='user_rating',
            title='Rating Progression',
            labels={'user_rating': 'Rating', 'date': 'Date'}
        )
        fig.update_traces(line_color='#4CAF50')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        results_time = analyzer.get_results_over_time('W')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=results_time.index, y=results_time['Wins'],
                                 mode='lines', name='Wins', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=results_time.index, y=results_time['Losses'],
                                 mode='lines', name='Losses', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=results_time.index, y=results_time['Draws'],
                                 mode='lines', name='Draws', line=dict(color='gray')))
        fig.update_layout(title='Results Over Time (Weekly)', xaxis_title='Date',
                         yaxis_title='Number of Games')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        opening_stats = analyzer.get_opening_stats(top_n=10)
        fig = px.bar(
            opening_stats,
            x='games',
            y='opening',
            orientation='h',
            title='Top 10 Most Played Openings',
            labels={'games': 'Games Played', 'opening': 'Opening'},
            color='win_rate',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(opening_stats, use_container_width=True, hide_index=True)
    
    with tab4:
        opp_strength = analyzer.get_performance_by_opponent_strength()
        fig = px.bar(
            opp_strength,
            x='category',
            y='win_rate',
            title='Win Rate by Opponent Strength',
            labels={'category': 'Opponent Category', 'win_rate': 'Win Rate (%)'},
            color='win_rate',
            color_continuous_scale='RdYlGn',
            text='win_rate'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Additional stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance by Color")
        color_perf = analyzer.get_color_performance()
        st.dataframe(color_perf, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Performance by Time Control")
        tc_stats = analyzer.get_time_control_stats()
        st.dataframe(tc_stats, use_container_width=True, hide_index=True)
    
    # Machine Learning Prediction
    st.header("🤖 Win Probability Predictor")
    
    if len(df) >= 20:
        with st.spinner("Training prediction model..."):
            predictor = ChessPredictor()
            X, y = analyzer.prepare_ml_features()
            metrics = predictor.train(X, y)
            
            st.success(f"✅ Model trained on {metrics['n_train_samples'] + metrics['n_test_samples']} games")
            
            col1, col2 = st.columns(2)
            col1.metric("Training Accuracy", f"{metrics['train_accuracy']:.1%}")
            col2.metric("Test Accuracy", f"{metrics['test_accuracy']:.1%}")
        
        st.subheader("Predict Your Chances")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            current_rating = st.number_input(
                "Your Rating",
                min_value=400,
                max_value=5000,
                value=int(stats['avg_user_rating'])
            )
        with col2:
            opponent_rating = st.number_input(
                "Opponent Rating",
                min_value=400,
                max_value=5000,
                value=int(stats['avg_user_rating'])
            )
        with col3:
            color_choice = st.selectbox("Your Color", ["White", "Black"])
        
        is_white = (color_choice == "White")
        win_prob = predictor.predict_win_probability(
            current_rating, opponent_rating, is_white
        )
        
        st.metric(
            "Predicted Win Probability",
            f"{win_prob:.1%}",
            delta=f"{win_prob - 0.5:.1%} vs 50%"
        )
        
        # Win probability curve
        st.subheader("Win Probability vs Opponent Rating")
        curve_df = predictor.get_win_probability_curve(
            current_rating, is_white=is_white
        )
        
        fig = px.line(
            curve_df,
            x='opponent_rating',
            y='win_probability',
            title=f'Expected Win Rate as {color_choice}',
            labels={'opponent_rating': 'Opponent Rating', 'win_probability': 'Win Probability'}
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="50%")
        fig.update_layout(yaxis_tickformat='.0%')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least 20 games to train prediction model. Keep playing!")
    
    # Recent Games Table
    st.header("🎮 Recent Games")
    
    recent_games = analyzer.get_recent_games(10)
    display_columns = [
        'date', 'opponent', 'user_rating', 'opponent_rating',
        'result_label', 'user_color', 'opening', 'eco', 'game_url'
    ]
    
    # Only include eco if it exists in the dataframe
    if 'eco' not in recent_games.columns:
        display_columns.remove('eco')
    
    display_df = recent_games[display_columns].copy()
    
    # Set column names based on what's available
    if 'eco' in display_columns:
        display_df.columns = [
            'Date', 'Opponent', 'Your Rating', 'Opp Rating',
            'Result', 'Color', 'Opening', 'ECO', 'Game Link'
        ]
    else:
        display_df.columns = [
            'Date', 'Opponent', 'Your Rating', 'Opp Rating',
            'Result', 'Color', 'Opening', 'Game Link'
        ]
    
    # Make game links clickable
    display_df['Game Link'] = display_df['Game Link'].apply(
        lambda x: f'<a href="{x}" target="_blank">View Game</a>' if pd.notna(x) and x else ''
    )
    
    st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Download button for data
    st.subheader("📥 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Games CSV",
            data=csv,
            file_name=f"{st.session_state.username}_games_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        if len(df) >= 20:
            # Create analysis summary
            stats = analyzer.get_overall_stats()
            summary = f"""Chess Analysis Summary - {st.session_state.username}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overall Statistics:
- Total Games: {stats['total_games']}
- Wins: {stats['wins']} ({stats['win_rate']:.1f}%)
- Losses: {stats['losses']}
- Draws: {stats['draws']}
- Average Rating: {stats['avg_user_rating']:.0f}
- Average Opponent Rating: {stats['avg_opponent_rating']:.0f}
"""
            st.download_button(
                label="Download Analysis Summary",
                data=summary,
                file_name=f"{st.session_state.username}_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

else:
    st.info("👈 Enter your Chess.com username and fetch your games to get started!")
    
    st.markdown("""
    ### How to use this dashboard:
    
    1. **Enter your Chess.com username** in the sidebar
    2. **Select a time period** for analysis
    3. **Click 'Fetch Games'** to load your game data
    4. Explore your performance metrics, trends, and predictions!
    
    The dashboard will:
    - Show your win/loss/draw statistics
    - Visualize rating trends over time
    - Analyze your opening repertoire
    - Predict win probabilities using machine learning
    - Provide clickable links to review individual games
    - Allow you to download your data for further analysis
    """)