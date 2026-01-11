# Refinements:
# - I want to remove the Load Save Data button, i only want to fetch new data each time.
# - limit recent games to 5 instead of 10.
# - I need a tooltip for ECO meaning in the recent games table.


"""
app.py
Main Streamlit dashboard for chess game analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.data_fetcher import ChessDataFetcher
from src.analyzer import ChessAnalyzer
from src.predictor import ChessPredictor

# Page configuration
st.set_page_config(
    page_title="Chess Game Analysis Dashboard",
    page_icon="",
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
st.title(" Chess Game Analysis Dashboard")
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
    st.caption(" Example usernames: RhysLWells, Hikaru, MagnusCarlsen")
    
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
    
    fetch_button = st.button(" Fetch Games", type="primary", use_container_width=True)
    
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
                    st.success(f" Loaded {len(df)} games!")
                else:
                    st.error("No games found for this period.")
            except Exception as e:
                st.error(f"Error fetching games: {e}")
    
    # Load existing data
    if username and not fetch_button:
        load_existing = st.button(" Load Saved Data", use_container_width=True)
        if load_existing:
            try:
                fetcher = ChessDataFetcher()
                df = fetcher.load_existing_data(username)
                if df is not None:
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.session_state.username = username
                    st.success(f" Loaded {len(df)} games from file!")
                else:
                    st.warning("No saved data found. Please fetch games first.")
            except Exception as e:
                st.error(f"Error loading data: {e}")

# Main dashboard content
if st.session_state.data_loaded and st.session_state.df is not None:
    df = st.session_state.df
    analyzer = ChessAnalyzer(df)
    
    # Overall Statistics
    st.header(" Performance Overview")
    st.markdown("""
    <small>Your overall performance summary across all fetched games. Win rate is calculated as wins divided by total games.</small>
    """, unsafe_allow_html=True)
    
    stats = analyzer.get_overall_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Games", stats['total_games'], help="Total number of games analyzed")
    col2.metric("Wins", stats['wins'], help="Games you won")
    col3.metric("Losses", stats['losses'], help="Games you lost")
    col4.metric("Draws", stats['draws'], help="Games that ended in a draw")
    col5.metric("Win Rate", f"{stats['win_rate']:.1f}%", help="Percentage of games won (wins ÷ total games)")
    
    col1, col2 = st.columns(2)
    col1.metric("Average Rating", f"{stats['avg_user_rating']:.0f}", 
                help="Your average rating across all analyzed games")
    col2.metric("Avg Opponent Rating", f"{stats['avg_opponent_rating']:.0f}",
                help="Average rating of opponents you faced")
    
    st.divider()
    
    # Charts
    st.header(" Performance Analysis")
    st.markdown("""
    <small>Dive deeper into your chess performance with visualizations showing trends over time, 
    opening effectiveness, and performance against different opponent strengths.</small>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        " Rating Trend", " Results Over Time", " Opening Performance", " Opponent Strength"
    ])
    
    with tab1:
        st.info(" **Analysis**: This chart shows how your rating has changed over time. "
                "Look for upward trends (improvement) or periods of volatility (inconsistent performance).")
        rating_trend = analyzer.get_rating_trend()
        fig = px.line(
            rating_trend,
            x='date',
            y='user_rating',
            title='Rating Progression Over Time',
            labels={'user_rating': 'Rating', 'date': 'Date'}
        )
        fig.update_traces(line_color='#4CAF50')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.info(" **Analysis**: Weekly breakdown of your game results. "
                "Green = Wins, Red = Losses, Gray = Draws. "
                "Look for patterns or streaks in your performance.")
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
        st.info(" **Analysis**: Your most frequently played openings ranked by frequency. "
                "Color indicates win rate (green = high, red = low). "
                "Focus on openings with both high frequency and win rate.")
        opening_stats = analyzer.get_opening_stats(top_n=10)
        fig = px.bar(
            opening_stats,
            x='games',
            y='opening',
            orientation='h',
            title='Top 10 Most Played Openings',
            labels={'games': 'Games Played', 'opening': 'Opening'},
            color='win_rate',
            color_continuous_scale='RdYlGn',
            hover_data={'win_rate': ':.1f'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander(" View Detailed Opening Statistics"):
            st.dataframe(opening_stats, use_container_width=True, hide_index=True)
            st.caption(" **Tip**: Look for openings with low win rates but high game counts - "
                      "these might be opportunities to refine your repertoire!")
    
    with tab4:
        st.info(" **Analysis**: Win rate comparison against opponents of different strengths. "
                "**Lower Rated**: Opponents 100+ points below you | "
                "**Similar Rating**: Within ±100 points | "
                "**Higher Rated**: Opponents 100+ points above you")
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
        st.caption(" **Expected**: Higher win rates against lower-rated opponents, "
                  "lower win rates against higher-rated opponents")
    
    # Additional stats
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(" Performance by Color")
        st.caption("Compare your win rates when playing as White vs Black")
        color_perf = analyzer.get_color_performance()
        st.dataframe(color_perf, use_container_width=True, hide_index=True)
        st.caption(" **Note**: White typically has a slight statistical advantage due to first move")
    
    with col2:
        st.subheader("⏱ Performance by Time Control")
        st.caption("How your performance varies across different time formats")
        tc_stats = analyzer.get_time_control_stats()
        st.dataframe(tc_stats, use_container_width=True, hide_index=True)
        st.caption(" **Tip**: Identify which time controls suit your playing style best")
    
    # Machine Learning Prediction
    st.divider()
    st.header(" Win Probability Predictor")
    st.markdown("""
    <small>Machine learning model trained on your historical games to predict win probability. 
    The model uses logistic regression with features: your rating, opponent rating, rating difference, and color.</small>
    """, unsafe_allow_html=True)
    
    if len(df) >= 20:
        with st.spinner("Training prediction model..."):
            predictor = ChessPredictor()
            X, y = analyzer.prepare_ml_features()
            metrics = predictor.train(X, y)
            
            st.success(f" Model trained on {metrics['n_train_samples'] + metrics['n_test_samples']} games")
            st.caption(" **How it works**: The model learns patterns from your game history - "
                      "how rating differences and color affect your results")
            
            col1, col2 = st.columns(2)
            col1.metric("Training Accuracy", f"{metrics['train_accuracy']:.1%}",
                       help="How well the model predicts outcomes on training data")
            col2.metric("Test Accuracy", f"{metrics['test_accuracy']:.1%}",
                       help="How well the model predicts outcomes on unseen test data")
        
        st.subheader(" Predict Your Chances")
        st.caption("Enter match parameters to estimate your winning probability")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            current_rating = st.number_input(
                "Your Rating",
                min_value=400,
                max_value=5000,
                value=int(stats['avg_user_rating']),
                help="Your current or expected rating for the match"
            )
        with col2:
            opponent_rating = st.number_input(
                "Opponent Rating",
                min_value=400,
                max_value=5000,
                value=int(stats['avg_user_rating']),
                help="Your opponent's rating"
            )
        with col3:
            color_choice = st.selectbox(
                "Your Color", 
                ["White", "Black"],
                help="Which pieces you'll be playing with"
            )
        
        is_white = (color_choice == "White")
        win_prob = predictor.predict_win_probability(
            current_rating, opponent_rating, is_white
        )
        
        st.metric(
            "Predicted Win Probability",
            f"{win_prob:.1%}",
            delta=f"{win_prob - 0.5:.1%} vs 50%",
            help="Probability of winning based on your historical performance patterns"
        )
        
        if win_prob > 0.6:
            st.success(" **Strong Position**: Historical data suggests you're favored to win")
        elif win_prob < 0.4:
            st.warning(" **Challenging Match**: You're the underdog, but upsets happen!")
        else:
            st.info(" **Even Match**: This should be a close, competitive game")
        
        # Win probability curve
        st.subheader(" Win Probability vs Opponent Rating")
        st.caption("How your expected win rate changes across different opponent strengths")
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
        st.caption(" **Interpretation**: The curve shows how rating differences affect your winning chances. "
                  "Steeper curves indicate stronger rating sensitivity.")
    else:
        st.info("ℹ **Insufficient Data**: Need at least 20 games to train a reliable prediction model. Keep playing!")
        st.caption("The machine learning model requires a minimum dataset to identify meaningful patterns in your play")
    
    # Recent Games Table
    st.divider()
    st.header(" Recent Games")
    st.caption("Your most recent games with direct links to review them on Chess.com")
    
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
    st.divider()
    st.subheader(" Export Data")
    st.caption("Download your game data and analysis results for further exploration")
    
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
        if len(df) >= 10:
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
    st.info(" Enter your Chess.com username and fetch your games to get started!")
    
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