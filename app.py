"""
app.py
Streamlit dashboard for Chess.com game analysis.

Structure:
- Sidebar: data fetching only
- Main area: title + Performance Analysis tabs
- Each tab is rendered by a dedicated function
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

from src.data_fetcher import ChessDataFetcher
from src.analyzer import ChessAnalyzer
from src.predictor import ChessPredictor


# ==============================================================================
# Page configuration
# ==============================================================================
st.set_page_config(
    page_title="Chess Game Analysis Dashboard",
    layout="wide",
)


# ==============================================================================
# Session state initialisation
# ==============================================================================
# These guard against Streamlit reruns resetting application state
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "df" not in st.session_state:
    st.session_state.df = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "selected_time_controls" not in st.session_state:
    st.session_state.selected_time_controls = []

if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = None
# ==============================================================================
# Sidebar: data fetching (kept intentionally simple)
# ==============================================================================

def render_sidebar():
    """
    Sidebar is responsible only for fetching fresh data.
    It does not render analysis or visualisations.
    """
    with st.sidebar:
        st.header("Data Management")

        username = st.text_input(
            "Chess.com Username",
            value=st.session_state.username,
            placeholder="Enter username",
            help="Example: RhysLWells, Hikaru, GothamChess",
        )

        st.subheader("Fetch Games")
        
        # Simplified: Just Recent Months or Custom Range
        fetch_mode = st.radio(
            "Fetch Mode",
            ["Recent Months", "Custom Range"],
            help="Choose how to fetch your game data"
        )

        # Configure based on fetch mode
        if fetch_mode == "Recent Months":
            months_back = st.selectbox(
                "Number of Months",
                [1, 3, 6, 12],
                index=1,  # Default to 3 months (index 1)
                help="Fetch only the most recent N months"
            )
            use_archive_discovery = True
            limit_months = months_back
            
        else:  # Custom Range
            c1, c2 = st.columns(2)
            with c1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=90),
                )
            with c2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now(),
                )
            use_archive_discovery = False
            limit_months = None

        fetch_button = st.button(
            "Fetch Games",
            type="primary",
            width='stretch',
        )

        # Fetch and persist data into session state
        # In render_sidebar(), inside the fetch_button block:
        if fetch_button and username:
            with st.spinner("Fetching games from Chess.com..."):
                fetcher = ChessDataFetcher()
                
                try:
                    if use_archive_discovery:
                        st.info(f"Discovering available archives for {username}...")
                        games = fetcher.fetch_all_games(
                            username,
                            limit_months=limit_months
                        )
                    else:
                        games = fetcher.fetch_multiple_months(
                            username,
                            start_date,
                            end_date,
                        )

                    if games:
                        df = fetcher.process_and_save(username, games, mode="json")
                        
                        # Update session state
                        st.session_state.df = df
                        st.session_state.data_loaded = True
                        st.session_state.username = username
                        st.session_state.last_fetch_time = datetime.now()
                        
                        # Show success with date range info
                        if not df.empty:
                            earliest = pd.to_datetime(df['date']).min().strftime('%Y-%m-%d')
                            latest = pd.to_datetime(df['date']).max().strftime('%Y-%m-%d')
                            st.success(
                                f"✅ Loaded {len(df)} games\n\n"
                                f"📅 Date range: {earliest} to {latest}"
                            )
                        else:
                            st.success(f"Loaded {len(df)} games.")
                        
                        # Force immediate rerun to show navigation
                        st.rerun()
                        
                    else:
                        st.error("No games found for this period.")
                        
                except Exception as e:
                    st.error(f"Error fetching games: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

        # Show last fetch time if available
        if hasattr(st.session_state, 'last_fetch_time') and st.session_state.last_fetch_time:
            last_fetch = st.session_state.last_fetch_time
            time_ago = datetime.now() - last_fetch
            
            if time_ago.days > 0:
                time_str = f"{time_ago.days} day(s) ago"
            elif time_ago.seconds > 3600:
                time_str = f"{time_ago.seconds // 3600} hour(s) ago"
            else:
                time_str = f"{time_ago.seconds // 60} minute(s) ago"
                
            st.caption(f"Last fetched: {time_str}")

        # ------------------------------------------------------------------
        # Game Type Filter (only show if data is loaded)
        # ------------------------------------------------------------------
        if st.session_state.data_loaded and st.session_state.df is not None:
            st.divider()
            st.subheader("Filter Games")
            
            df = st.session_state.df
            
            # Get unique time controls from the data
            available_time_controls = sorted(df['time_control'].unique().tolist())
            
            # Multi-select for time controls
            selected_time_controls = st.multiselect(
                "Time Control",
                options=available_time_controls,
                default=available_time_controls,
                help="Select which game types to include in the analysis"
            )
            
            # Store the filter in session state
            st.session_state.selected_time_controls = selected_time_controls
            
            # Show filtered game count
            if selected_time_controls:
                filtered_count = len(df[df['time_control'].isin(selected_time_controls)])
                st.info(f"Analyzing {filtered_count} of {len(df)} games")
            else:
                st.warning("No time controls selected. Please select at least one.")

def render_analysis_navigation():
    """
    Sidebar navigation for selecting analysis views.
    Only shown once data is loaded.
    """
    st.subheader("Analysis Views")

    return st.radio(
        label="Select analysis view",
        options=[
            "Performance Overview",
            "Rating Trend",
            "Results Over Time",
            "Opening Performance",
            "Opponent Strength",
            "Win Probability",
            "Game Length",
            "Competitor Analysis"
        ],
        label_visibility="collapsed",
    )


# ==============================================================================
# Tab renderers
# ==============================================================================

def render_performance_overview(df, analyzer, username):
    """
    High-level performance summary plus:
    - performance by color
    - performance by time control
    - recent games
    - export options
    """
    stats = analyzer.get_overall_stats()

    # --- headline metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Games", stats["total_games"])
    c2.metric("Wins", stats["wins"])
    c3.metric("Losses", stats["losses"])
    c4.metric("Draws", stats["draws"])
    c5.metric("Win Rate", f"{stats['win_rate']:.0f}%")

    st.divider()

    # --- breakdowns
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Performance by Color")
        color_perf = analyzer.get_color_performance()
        st.dataframe(color_perf, width='stretch', hide_index=True)

    with c2:
        st.subheader("Performance by Time Control")
        tc_stats = analyzer.get_time_control_stats()
        st.dataframe(tc_stats, width='stretch', hide_index=True)

    st.divider()

    # --- recent games
    st.subheader("Recent Games")
    st.caption("ECO = Encyclopedia of Chess Openings")

    recent_games = analyzer.get_recent_games(5)

    display_df = recent_games[
        [
            "date",
            "opponent",
            "user_rating",
            "opponent_rating",
            "result_label",
            "user_color",
            "opening",
            # "eco",
            "eco_url",
            "game_url",
        ]
    ].copy()

    display_df.rename(
        columns={
            "date": "Date",
            "opponent": "Opponent",
            "user_rating": "Your Rating",
            "opponent_rating": "Opp Rating",
            "result_label": "Result",
            "user_color": "Color",
            "opening": "Opening",
            "eco": "ECO",
            "eco_url": "ECO Link",
            "game_url": "Game Link",
        },
        inplace=True,
    )

    # Make ECO URL clickable
    display_df["ECO Link"] = display_df["ECO Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">ECO</a>' if pd.notnull(x) and x else ""
    )

    # Make game URL clickable
    display_df["Game Link"] = display_df["Game Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">View</a>' if pd.notnull(x) and x else ""
    )

    st.markdown(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

    st.divider()

    # --- export
    st.subheader("Export Data")

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "Download Games CSV",
            df.to_csv(index=False),
            file_name=f"{username}_games.csv",
            mime="text/csv",
            width='stretch',
        )

    with c2:
        summary = f"""Chess Analysis Summary
User: {username}
Generated: {datetime.now():%Y-%m-%d %H:%M}

Games: {stats['total_games']}
Win Rate: {stats['win_rate']:.0f}%
Average Rating: {stats['avg_user_rating']:.0f}
"""
        st.download_button(
            "Download Summary",
            summary,
            file_name=f"{username}_summary.txt",
            mime="text/plain",
            width='stretch',
        )

def render_rating_trend(analyzer):
    """
    Displays rating progression over time and key rating volatility metrics.
    """

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------
    st.markdown(
        """
        ### Rating Trend

        This tab shows your rating progression over time. 
        The chart displays how your rating has changed per game.
        
        Below, key metrics summarise rating volatility.
        """
    )

    # ------------------------------------------------------------------
    # Rating trend data
    # ------------------------------------------------------------------
    rating_trend = analyzer.get_rating_trend()
    stats = analyzer.get_overall_stats()
    volatility_stats = analyzer.get_rating_volatility()

    # ------------------------------------------------------------------
    # Chart: raw rating over time
    # ------------------------------------------------------------------
    fig = px.line(
        rating_trend,
        x="date",
        y="user_rating",
        labels={"date": "Date", "user_rating": "Rating"},
        title="Rating Progression Over Time",
    )

    st.plotly_chart(fig, width='stretch')


    # ------------------------------------------------------------------
    # Volatility details as metrics with tooltips
    # ------------------------------------------------------------------
    st.markdown("### Volatility Metrics")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric(
        "Volatility (std dev.)",
        f"{volatility_stats['volatility']:.2f}",
        help="Standard deviation of single-game rating changes"
    )
    v2.metric(
        "Avg Rating Change",
        f"{volatility_stats['avg_rating_change']:.2f}",
        help="Mean absolute rating change per game"
    )
    v3.metric(
        "Max Gain",
        f"+{volatility_stats['max_rating_gain']:.2f}",
        help="Largest single-game rating increase"
    )
    v4.metric(
        "Max Loss",
        f"{volatility_stats['max_rating_loss']:.2f}",
        help="Largest single-game rating decrease"
    )

def render_results_over_time(analyzer):
    """
    Displays results over time (weekly aggregation) and summary metrics.
    """

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------
    st.markdown(
        """
        ### Results Over Time

        This tab shows your game outcomes aggregated by week. 
        The chart displays the number of wins, losses, and draws per week.  

        Below, key metrics summarize your overall performance over the selected period.
        """
    )

    # ------------------------------------------------------------------
    # Aggregate data
    # ------------------------------------------------------------------
    results_time = analyzer.get_results_over_time("W")
    stats = analyzer.get_overall_stats()  # for headline metrics

    # ------------------------------------------------------------------
    # Chart: wins/losses/draws over time
    # ------------------------------------------------------------------
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=results_time.index, y=results_time["Wins"], mode="lines+markers", name="Wins",
        line=dict(color="green")
    ))
    fig.add_trace(go.Scatter(
        x=results_time.index, y=results_time["Losses"], mode="lines+markers", name="Losses",
        line=dict(color="red")
    ))
    fig.add_trace(go.Scatter(
        x=results_time.index, y=results_time["Draws"], mode="lines+markers", name="Draws",
        line=dict(color="orange")
    ))

    fig.update_layout(
        title="Weekly Results Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Games",
        hovermode="x unified"
    )

    st.plotly_chart(fig, width='stretch')

def render_opening_performance(analyzer):
    """
    Opening frequency and win rate analysis, with example games per opening.
    """

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------
    st.markdown(
        """
        ### Opening performance

        This section summarises how the users results vary across different chess openings.
        Openings are ranked by how frequently they appear in games, and coloured
        by win rate.

        The chart answers two questions:
        - Which openings are played most often
        - Whether those openings tend to produce stronger or weaker results

        Below the chart, example games are provided so you can inspect concrete
        instances of each opening directly on Chess.com.
        """
    )

    # ------------------------------------------------------------------
    # Aggregate opening statistics
    # ------------------------------------------------------------------
    opening_stats = analyzer.get_opening_stats(top_n=10)

    fig = px.bar(
        opening_stats,
        x="games",
        y="opening",
        orientation="h",
        color="win_rate",
        color_continuous_scale="RdYlGn",
        labels={
            "games": "Games Played",
            "opening": "Opening",
            "win_rate": "Win Rate (%)",
        },
    )

    fig.update_layout(
        title="Most Played Openings (Top 10)",
        coloraxis_colorbar=dict(title="Win Rate (%)"),
    )

    st.plotly_chart(fig, width='stretch')

    # ------------------------------------------------------------------
    # Example games per opening (as table)
    # ------------------------------------------------------------------
    st.markdown("### Example games by opening")

    df = analyzer.df
    
    # Build table data
    table_data = []
    for opening in opening_stats["opening"]:
        subset = df[df["opening"] == opening].head(1)
        
        if subset.empty:
            continue
        
        row = subset.iloc[0]
        
        # Format ECO URL link
        if pd.notnull(row['eco_url']) and row['eco_url']:
            eco_link = f'<a href="{row["eco_url"]}" target="_blank">ECO Info</a>'
        else:
            eco_link = "—"
        
        # Format game link
        game_link = f'<a href="{row["game_url"]}" target="_blank">{row["date"].date()} vs {row["opponent"]} ({row["result_label"]})</a>'
        
        table_data.append({
            "Opening": opening,
            "ECO Info": eco_link,
            "Recent Example": game_link
        })
    
    # Create DataFrame and display as HTML table
    table_df = pd.DataFrame(table_data)
    
    st.markdown(
        table_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

def render_opponent_strength(analyzer):
    """
    Win rate grouped by opponent rating bands.
    """

    # ------------------------------------------------------------------
    # Explanation of opponent strength bands
    # ------------------------------------------------------------------
    st.markdown(
        """
        **Opponent strength categories**

        Historical games are grouped using the rating difference (user rating - opponent rating).

        - **Lower Rated**: opponent rating is more than 50 points below yours.
        - **Similar Rating**: opponent rating within ±50 points of yours.
        - **Higher Rated**: opponent rating is more than 50 points above yours.

        Win rate is calculated as wins divided by total games in each group.
        """
    )

    # ------------------------------------------------------------------
    # Data + chart
    # ------------------------------------------------------------------
    opp_strength = analyzer.get_performance_by_opponent_strength()

    fig = px.bar(
        opp_strength,
        x="category",
        y="win_rate",
        color="win_rate",
        text="win_rate",
        color_continuous_scale="RdYlGn",
        labels={"win_rate": "Win Rate (%)"},
    )

    # Force 0 decimal places in bar labels
    fig.update_traces(
    texttemplate="%{text:.0f}%",
    hovertemplate="Win Rate: %{y:.0f}%<extra></extra>")


    fig.update_layout(title="Win Rate by Opponent Strength Category")

    st.plotly_chart(fig, width='stretch')

def render_win_probability(df, analyzer, stats):
    """
    Logistic regression–based win probability curves with full classification metrics.

    The model is trained on historical games and evaluated using standard
    classification metrics. The rating control enables counterfactual exploration
    without retraining the model.
    """

    # Guardrail: insufficient data
    if len(df) < 20:
        st.info("At least 20 games are required for win probability modelling.")
        return

    # ------------------------------------------------------------------
    # Train prediction model
    # ------------------------------------------------------------------
    predictor = ChessPredictor()
    X, y = analyzer.prepare_ml_features()
    training_results = predictor.train(X, y)
    
    metrics = training_results['classification_metrics']
    
    # ------------------------------------------------------------------
    # Win Probability Curves (FIRST - What Users Want)
    # ------------------------------------------------------------------
    st.subheader("Win Probability Predictions")
    st.markdown(
        "Based on your historical games, this model predicts your probability of winning "
        "against opponents of different ratings. Use the controls below to explore different scenarios."
    )
    
    # ------------------------------------------------------------------
    # Rating context
    # ------------------------------------------------------------------
    current_rating = int(stats["current_elo"])
    avg_rating = int(stats["avg_user_rating"])

    st.markdown(
        f"""
        **Your Rating Context**

        - Current rating (most recent game): **{current_rating}**
        - Average rating over this period: **{avg_rating}**
        """
    )

    # ------------------------------------------------------------------
    # Interactive controls
    # ------------------------------------------------------------------
    col1, col2 = st.columns(2)
    
    with col1:
        assumed_rating = st.number_input(
            "Your Rating (what-if scenario)",
            min_value=400,
            max_value=5000,
            value=current_rating,
            step=10,
            help="Explore predictions at different rating levels without retraining the model"
        )
    
    with col2:
        rating_range = st.slider(
            "Opponent Rating Range",
            min_value=100,
            max_value=4000,
            value=(assumed_rating - 200, assumed_rating + 200),
            step=25,
            help="Set the range of opponent ratings to display"
        )

    min_r, max_r = rating_range

    # ------------------------------------------------------------------
    # Plot curves by color
    # ------------------------------------------------------------------
    st.markdown("### Predicted Win Probability by Color")
    
    tab_white, tab_black = st.tabs(["Playing as White", "Playing as Black"])
    
    with tab_white:
        st.caption("Your expected win probability when playing with white pieces")
        curve_white = predictor.get_win_probability_curve(
            assumed_rating,
            is_white=True,
        )
        curve_white = curve_white[
            (curve_white["opponent_rating"] >= min_r)
            & (curve_white["opponent_rating"] <= max_r)
        ]

        fig_white = px.line(
            curve_white,
            x="opponent_rating",
            y="win_probability",
            labels={
                "opponent_rating": "Opponent Rating",
                "win_probability": "Win Probability",
            },
        )
        fig_white.add_hline(y=0.5, line_dash="dash", line_color="gray", 
                           annotation_text="50% (Even odds)")
        fig_white.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig_white, width='stretch')
    
    with tab_black:
        st.caption("Your expected win probability when playing with black pieces")
        curve_black = predictor.get_win_probability_curve(
            assumed_rating,
            is_white=False,
        )
        curve_black = curve_black[
            (curve_black["opponent_rating"] >= min_r)
            & (curve_black["opponent_rating"] <= max_r)
        ]

        fig_black = px.line(
            curve_black,
            x="opponent_rating",
            y="win_probability",
            labels={
                "opponent_rating": "Opponent Rating",
                "win_probability": "Win Probability",
            },
        )
        fig_black.add_hline(y=0.5, line_dash="dash", line_color="gray",
                           annotation_text="50% (Even odds)")
        fig_black.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig_black, width='stretch')

    st.divider()
    
    # ------------------------------------------------------------------
    # Model Details (Expandable - For Interested Users)
    # ------------------------------------------------------------------
    with st.expander("📊 View Model Training & Performance Details", expanded=False):
        st.markdown(
            "This section provides detailed information about how the prediction model was trained "
            "and how accurate its predictions are. These metrics help you understand the reliability "
            "of the win probability predictions shown above."
        )
        
        st.markdown("---")
        
        # ------------------------------------------------------------------
        # Training Information
        # ------------------------------------------------------------------
        st.markdown("### Training Information")
        st.markdown(
            "A **logistic regression** model was trained on your historical games to predict win probability "
            "based on your rating, opponent rating, rating difference, and piece color (white/black). "
            "The data was split into training data (80%) to teach the model patterns, and test data (20%) "
            "to evaluate how well it predicts outcomes on games it hasn't seen before."
        )
        
        info_col1, info_col2 = st.columns(2)
        info_col1.metric("Training Samples", training_results['n_train_samples'])
        info_col2.metric("Test Samples", training_results['n_test_samples'])
        
        st.markdown("---")
        
        # ------------------------------------------------------------------
        # Confusion Matrix Visualization
        # ------------------------------------------------------------------
        st.markdown("### Confusion Matrix")
        st.caption(
            "The confusion matrix shows how the model's predictions compare to actual outcomes. "
            "Each cell shows the number of games in that category. Diagonal cells (top-left and bottom-right) "
            "represent correct predictions, while off-diagonal cells show prediction errors."
        )
        
        cm = metrics['confusion_matrix']
        cm_matrix = np.array([
            [cm['true_negatives'], cm['false_positives']],
            [cm['false_negatives'], cm['true_positives']]
        ])
        
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm_matrix,
            x=['Predicted Loss/Draw', 'Predicted Win'],
            y=['Actual Loss/Draw', 'Actual Win'],
            text=cm_matrix,
            texttemplate='%{text}',
            textfont={"size": 16},
            colorscale='Blues',
            showscale=False
        ))
        
        fig_cm.update_layout(
            title="Confusion Matrix Visualization",
            xaxis_title="Predicted Class",
            yaxis_title="Actual Class",
            height=400
        )
        
        st.plotly_chart(fig_cm, width='stretch')
        
        
        # ------------------------------------------------------------------
        # Per-Class Metrics
        # ------------------------------------------------------------------
        st.markdown("### Per-Class Metrics")
        st.caption(
            "These metrics break down the model's performance for each outcome type. "
            "They show how well the model performs specifically for wins vs losses/draws."
        )
        
        class_report = metrics['classification_report']
        report_df = pd.DataFrame({
            'Class': ['Loss/Draw', 'Win'],
            'Precision': [
                class_report['0']['precision'],
                class_report['1']['precision']
            ],
            'Recall': [
                class_report['0']['recall'],
                class_report['1']['recall']
            ],
            'F1-Score': [
                class_report['0']['f1-score'],
                class_report['1']['f1-score']
            ],
            'Support': [
                class_report['0']['support'],
                class_report['1']['support']
            ]
        })
        
        st.dataframe(
            report_df.style.format({
                'Precision': '{:.1%}',
                'Recall': '{:.1%}',
                'F1-Score': '{:.1%}',
                'Support': '{:.0f}'
            }),
            hide_index=True,
            width='stretch'
        )
        
        # Overall metrics
        st.markdown("### Overall Model Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(
            "Accuracy", 
            f"{metrics['accuracy']:.1%}",
            help="Percentage of all predictions (wins and losses/draws) that were correct"
        )
        col2.metric(
            "Precision", 
            f"{metrics['precision']:.1%}",
            help="When predicting a win, how often the model is correct (fewer false alarms)"
        )
        col3.metric(
            "Recall", 
            f"{metrics['recall']:.1%}",
            help="Of all actual wins, what percentage the model successfully identifies (fewer missed wins)"
        )
        col4.metric(
            "F1 Score", 
            f"{metrics['f1_score']:.1%}",
            help="Balanced measure combining precision and recall (harmonic mean)"
        )
        if metrics['roc_auc'] is not None:
            col5.metric(
                "ROC AUC", 
                f"{metrics['roc_auc']:.3f}",
                help="Model's ability to distinguish between wins and losses (0.5 = random, 1.0 = perfect)"
            )
        
        # Understanding the metrics
        with st.expander("📖 Understanding These Metrics", expanded=False):
            st.markdown("""
            **Why are these different from overall accuracy?**
            
            Overall accuracy tells you what percentage of all predictions were correct, but it doesn't 
            tell you *which types* of predictions the model is good at. Per-class metrics reveal this detail.
            
            For example, you might have 70% overall accuracy, but the model could be:
            - Great at predicting wins (90% precision) but poor at predicting losses (50% precision), or
            - Balanced across both outcome types (70% for each)
            
            **Metric Definitions:**
            
            - **Precision**: When the model predicts this outcome, how often is it correct?  
              *High precision = few false alarms for this outcome type*
            
            - **Recall**: Of all actual occurrences of this outcome, how many does the model catch?  
              *High recall = few missed predictions for this outcome type*
            
            - **F1-Score**: Balance between precision and recall (harmonic mean)  
              *High F1 = good at both catching this outcome and avoiding false predictions*
            
            - **Support**: The number of test games with this actual outcome  
              *Shows how many examples the model had to evaluate*
            """)
            
            st.info(
                "💡 **Tip**: A good model has similar, high metrics for both classes. "
                "If one class has much lower scores, the model struggles more with that outcome type."
            )
def render_game_length_analysis(analyzer):
    """
    Game length analysis based on wall-clock duration.
    """

    st.subheader("Game Length Analysis")
    st.caption(
        "Game length is measured as wall-clock duration (seconds) "
        "derived from PGN timestamps."
    )

    # ------------------------------------------------------------------
    # Overall stats
    # ------------------------------------------------------------------
    stats = analyzer.get_game_length_stats()

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Average", f"{stats['average']:.0f} sec")
    c2.metric("Median", f"{stats['median']:.0f} sec")
    c3.metric("Shortest", f"{stats['shortest']:.0f} sec")
    c4.metric("Longest", f"{stats['longest']:.0f} sec")
    c5.metric(
        "Corr (Length vs Result)",
        f"{stats['length_result_corr']:.2f}",
        help="Positive values mean longer games correlate with better results",
    )

    st.divider()

    # ------------------------------------------------------------------
    # By result
    # ------------------------------------------------------------------
    st.subheader("Game Length by Result")

    by_result = analyzer.get_game_length_by_result()

    st.dataframe(
        by_result[
            [
                "Result",
                "Games",
                "Average Length (s)",
                "Std Dev (s)",
            ]
        ],
        hide_index=True,
        width='stretch',
    )

    # ------------------------------------------------------------------
    # Visual comparison - Bar chart
    # ------------------------------------------------------------------
    fig = px.bar(
        by_result,
        x="Result",
        y="Average Length (s)",
        color="Result",
        labels={"Average Length (s)": "Average Game Length (seconds)"},
        title="Average Game Length by Result",
    )
    
    # Round y-axis labels to nearest second
    fig.update_yaxes(tickformat=".0f")

    st.plotly_chart(fig, width='stretch')

    st.divider()

    # ------------------------------------------------------------------
    # Scatter: Game length vs opponent rating
    # ------------------------------------------------------------------
    st.subheader("Game Length vs Opponent Rating")
    st.caption("Explore how game duration varies with opponent strength and outcome. Remember to filter by time control in the sidebar for more meaningful insights.")

    df = analyzer.df.dropna(subset=["game_duration_seconds", "opponent_rating"])

    fig_scatter = px.scatter(
        df,
        x="opponent_rating",
        y="game_duration_seconds",
        color="result_label",
        color_discrete_map={
            "Win": "green",
            "Loss": "red",
            "Draw": "orange"
        },
        labels={
            "opponent_rating": "Opponent Rating",
            "game_duration_seconds": "Game Length (seconds)",
            "result_label": "Result"
        },
        title="Game Length vs Opponent Rating",
        opacity=0.6,
        hover_data={
            "opponent": True,
            "opening": True,
            "date": True,
            "game_duration_seconds": ":.0f",
            "opponent_rating": True,
        }
    )

    # Round y-axis to nearest second
    fig_scatter.update_yaxes(tickformat=".0f")

    st.plotly_chart(fig_scatter, width='stretch')

def render_competitor_analysis(analyzer):
    """
    Competitor analysis: compare current Elo and predicted win probabilities 
    against selected competitors.
    """
    st.subheader("Competitor Analysis")
    st.caption(
        "This tab displays current Elo ratings for selected competitors and "
        "predicted probabilities of winning as White or Black based on your "
        "historical performance."
    )
    suggested_users = ["Hikaru", "GothamChess", "MagnusCarlsen"]

    # Input section in columns
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_suggested = st.multiselect(
            "Select competitor usernames",
            options=suggested_users,
            default=suggested_users[:3],
            help="Select up to three usernames."
        )
    with col2:
        custom_user = st.text_input(
            "Add another username",
            placeholder="Enter a Chess.com username"
        )

    # Combine selections
    competitors = selected_suggested.copy()
    if custom_user.strip():
        competitors.append(custom_user.strip())

    if not competitors:
        st.info("Select at least one competitor.")
        return

    time_control = st.selectbox(
        "Select game type",
        ["blitz", "rapid", "daily", "bullet"]
    )

    fetcher = ChessDataFetcher()
    competitor_elos = {u: fetcher.get_current_elo(u, time_control) for u in competitors}

    # --- Tabs for Elo vs Predictions ---
    tab_elo, tab_pred = st.tabs(["Current Elo Ratings", "Predicted Win Probabilities"])

    with tab_elo:
        st.markdown("### Elo Ratings")
        cols = st.columns(len(competitors))
        for i, (u, e) in enumerate(competitor_elos.items()):
            cols[i].metric(label=u, value=e if e is not None else "N/A")

    # Train predictor
    predictor = ChessPredictor()
    X, y = analyzer.prepare_ml_features()
    predictor.train(X, y)
    user_elo = analyzer.get_overall_stats()["current_elo"]

    with tab_pred:
        st.markdown("### Predicted Win Probabilities (White / Black)")

        def get_prob_for_elo(curve_df, comp_elo):
            if curve_df.empty:
                return np.nan
            idx = (np.abs(curve_df["opponent_rating"] - comp_elo)).argmin()
            return curve_df.iloc[idx]["win_probability"]

        table_data = []
        for comp_user, comp_elo in competitor_elos.items():
            if comp_elo is None:
                table_data.append({
                    "Competitor": comp_user,
                    "Elo": "N/A",
                    "White Win %": np.nan,
                    "Black Win %": np.nan
                })
                continue

            curve_white = predictor.get_win_probability_curve(user_elo, is_white=True)
            curve_black = predictor.get_win_probability_curve(user_elo, is_white=False)

            table_data.append({
                "Competitor": comp_user,
                "Elo": comp_elo,
                "White Win %": get_prob_for_elo(curve_white, comp_elo),
                "Black Win %": get_prob_for_elo(curve_black, comp_elo)
            })

        prob_df = pd.DataFrame(table_data)
        prob_df["White Win %"] = prob_df["White Win %"].astype(float)
        prob_df["Black Win %"] = prob_df["Black Win %"].astype(float)

        # Style table: gradient coloring
        st.dataframe(
            prob_df.style.background_gradient(
                subset=["White Win %", "Black Win %"], 
                cmap="RdYlGn"
            ).format({
                "White Win %": "{:.0%}",
                "Black Win %": "{:.0%}"
            }),
            width='stretch',
            hide_index=True
        )


# ==============================================================================
# Main application flow
# ==============================================================================

def main():
    # region Header
    st.title("Chess Game Analysis Dashboard")
    st.caption("Fetch games using the sidebar, then explore the analysis views.")
    # endregion

    # region Sidebar
    analysis_view = None
    with st.sidebar:
        # Analysis navigation at the top (only after data is loaded)
        if st.session_state.data_loaded:
            analysis_view = render_analysis_navigation()
            st.markdown("---")

        # Data management and filters below
        render_sidebar()
    # endregion

    # region Landing Page
    if not st.session_state.data_loaded:
        st.markdown(
            """
            ### About this dashboard

            This application is a lightweight, on-demand analysis tool for Chess.com players.
            It allows you to fetch your historical games, explore performance trends, and view
            predictions based on your own data.

            **How it works**
            1. Enter a Chess.com username and date range in the sidebar  
            2. Fetch games on demand  
            3. Explore performance metrics, trends, and win-probability estimates
            """
        )

        with st.expander("Further information about this dashboard", expanded=False):
            st.markdown(
                """
                **Key characteristics**
                - No live data streams or background updates
                - Analysis runs only when you fetch data

                **Game access**
                - Individual games remain accessible via direct links to Chess.com.
                """
            )
        return
    # endregion

    # region Data Filtering
    df = st.session_state.df
    selected_time_controls = st.session_state.get(
        "selected_time_controls",
        df["time_control"].unique().tolist(),
    )

    if not selected_time_controls:
        st.warning(
            "⚠️ No time controls selected. Please select at least one time control in the sidebar."
        )
        return

    df_filtered = df[df["time_control"].isin(selected_time_controls)].copy()

    if df_filtered.empty:
        st.warning(
            "⚠️ No games match the selected filters. Please adjust your filters in the sidebar."
        )
        return
    # endregion

    # region Analysis Setup
    analyzer = ChessAnalyzer(df_filtered)
    stats = analyzer.get_overall_stats()
    st.header("Analysis View")
    # endregion

    # region Analysis Rendering
    if analysis_view == "Performance Overview":
        render_performance_overview(df_filtered, analyzer, st.session_state.username)
    elif analysis_view == "Rating Trend":
        render_rating_trend(analyzer)
    elif analysis_view == "Results Over Time":
        render_results_over_time(analyzer)
    elif analysis_view == "Opening Performance":
        render_opening_performance(analyzer)
    elif analysis_view == "Opponent Strength":
        render_opponent_strength(analyzer)
    elif analysis_view == "Win Probability":
        render_win_probability(df_filtered, analyzer, stats)
    elif analysis_view == "Game Length":
        render_game_length_analysis(analyzer)
    elif analysis_view == "Competitor Analysis":
        render_competitor_analysis(analyzer)
    # endregion


# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
