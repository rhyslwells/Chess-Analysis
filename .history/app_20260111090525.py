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


# ------------------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Chess Game Analysis Dashboard",
    page_icon="",
    layout="wide"
)


# ------------------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------------------
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "df" not in st.session_state:
    st.session_state.df = None

if "username" not in st.session_state:
    st.session_state.username = ""


# ------------------------------------------------------------------------------
# Title and description
# ------------------------------------------------------------------------------
st.title("Chess Game Analysis Dashboard")
st.markdown(
    """
    Analyze your Chess.com games, track performance trends, and explore
    win probability behaviour.  
    **Start by using the sidebar to fetch games.**
    """
)


# ------------------------------------------------------------------------------
# Sidebar – data fetching only (no load/save)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.header("Data Management")

    username = st.text_input(
        "Chess.com Username",
        value=st.session_state.username,
        placeholder="Enter username",
        help="Examples: RhysLWells, Hikaru, MagnusCarlsen",
    )

    st.caption("Example usernames: RhysLWells, Hikaru, MagnusCarlsen")

    st.subheader("Fetch Games")
    date_option = st.radio(
        "Time Period",
        ["Last Month", "Last 3 Months", "Last 6 Months", "Custom Range"],
    )

    if date_option == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=90),
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
            )
    else:
        end_date = datetime.now()
        if date_option == "Last Month":
            start_date = end_date - timedelta(days=30)
        elif date_option == "Last 3 Months":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=180)

    fetch_button = st.button(
        "Fetch Games",
        type="primary",
        use_container_width=True,
    )

    if fetch_button and username:
        with st.spinner("Fetching games from Chess.com..."):
            fetcher = ChessDataFetcher()
            games = fetcher.fetch_multiple_months(
                username,
                start_date,
                end_date,
            )

            if games:
                df = fetcher.process_and_save(username, games, mode="json")
                st.session_state.df = df
                st.session_state.data_loaded = True
                st.session_state.username = username
                st.success(f"Loaded {len(df)} games.")
            else:
                st.error("No games found for this period.")


# ------------------------------------------------------------------------------
# Main content
# ------------------------------------------------------------------------------
if st.session_state.data_loaded and st.session_state.df is not None:
    df = st.session_state.df
    analyzer = ChessAnalyzer(df)

    # --------------------------------------------------------------------------
    # Performance overview
    # --------------------------------------------------------------------------
    st.header("Performance Overview")
    st.caption("Overall performance summary across all fetched games.")

    stats = analyzer.get_overall_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Games", stats["total_games"])
    c2.metric("Wins", stats["wins"])
    c3.metric("Losses", stats["losses"])
    c4.metric("Draws", stats["draws"])
    c5.metric("Win Rate", f"{stats['win_rate']:.1f}%")

    c1, c2 = st.columns(2)
    c1.metric("Average Rating", f"{stats['avg_user_rating']:.0f}")
    c2.metric("Avg Opponent Rating", f"{stats['avg_opponent_rating']:.0f}")

    st.divider()

    # --------------------------------------------------------------------------
    # Tabs – core analysis
    # --------------------------------------------------------------------------
    st.header("Performance Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Rating Trend",
            "Results Over Time",
            "Opening Performance",
            "Opponent Strength",
        ]
    )

    with tab1:
        rating_trend = analyzer.get_rating_trend()
        fig = px.line(
            rating_trend,
            x="date",
            y="user_rating",
            title="Rating Progression Over Time",
            labels={"user_rating": "Rating", "date": "Date"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        results_time = analyzer.get_results_over_time("W")
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=results_time.index,
                y=results_time["Wins"],
                mode="lines",
                name="Wins",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=results_time.index,
                y=results_time["Losses"],
                mode="lines",
                name="Losses",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=results_time.index,
                y=results_time["Draws"],
                mode="lines",
                name="Draws",
            )
        )
        fig.update_layout(
            title="Results Over Time (Weekly)",
            xaxis_title="Date",
            yaxis_title="Number of Games",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        opening_stats = analyzer.get_opening_stats(top_n=10)
        fig = px.bar(
            opening_stats,
            x="games",
            y="opening",
            orientation="h",
            color="win_rate",
            color_continuous_scale="RdYlGn",
            title="Top 10 Most Played Openings",
            labels={"games": "Games Played", "opening": "Opening"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        opp_strength = analyzer.get_performance_by_opponent_strength()
        fig = px.bar(
            opp_strength,
            x="category",
            y="win_rate",
            color="win_rate",
            color_continuous_scale="RdYlGn",
            text="win_rate",
            title="Win Rate by Opponent Strength",
            labels={"win_rate": "Win Rate (%)"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --------------------------------------------------------------------------
    # Performance by color / time control
    # --------------------------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Performance by Color")
        color_perf = analyzer.get_color_performance()
        st.dataframe(color_perf, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Performance by Time Control")
        tc_stats = analyzer.get_time_control_stats()
        st.dataframe(tc_stats, use_container_width=True, hide_index=True)

    st.divider()

    # --------------------------------------------------------------------------
    # Win probability model
    # --------------------------------------------------------------------------
    st.header("Win Probability")

    if len(df) >= 20:
        predictor = ChessPredictor()
        X, y = analyzer.prepare_ml_features()
        predictor.train(X, y)

        current_rating = st.number_input(
            "Your Rating",
            min_value=400,
            max_value=5000,
            value=int(stats["avg_user_rating"]),
        )

        min_r, max_r = st.slider(
            "Opponent rating range",
            min_value=400,
            max_value=5000,
            value=(current_rating - 400, current_rating + 400),
            step=25,
        )

        # --- White
        st.subheader(
            "How your expected win rate changes across different opponent ratings (White)"
        )
        curve_white = predictor.get_win_probability_curve(
            current_rating,
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
        fig_white.add_hline(y=0.5, line_dash="dash")
        fig_white.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig_white, use_container_width=True)

        # --- Black
        st.subheader(
            "How your expected win rate changes across different opponent ratings (Black)"
        )
        curve_black = predictor.get_win_probability_curve(
            current_rating,
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
        fig_black.add_hline(y=0.5, line_dash="dash")
        fig_black.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig_black, use_container_width=True)

    else:
        st.info("At least 20 games are required to train the model.")

    st.divider()

    # --------------------------------------------------------------------------
    # Recent games (limit = 5)
    # --------------------------------------------------------------------------
    st.header("Recent Games")
    st.caption(
        "ECO = Encyclopedia of Chess Openings (standard opening classification system)"
    )

    recent_games = analyzer.get_recent_games(5)

    display_cols = [
        "date",
        "opponent",
        "user_rating",
        "opponent_rating",
        "result_label",
        "user_color",
        "opening",
        "eco",
        "game_url",
    ]

    if "eco" not in recent_games.columns:
        display_cols.remove("eco")

    display_df = recent_games[display_cols].copy()

    if "eco" in display_df.columns:
        display_df.columns = [
            "Date",
            "Opponent",
            "Your Rating",
            "Opp Rating",
            "Result",
            "Color",
            "Opening",
            "ECO",
            "Game Link",
        ]
    else:
        display_df.columns = [
            "Date",
            "Opponent",
            "Your Rating",
            "Opp Rating",
            "Result",
            "Color",
            "Opening",
            "Game Link",
        ]

    display_df["Game Link"] = display_df["Game Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">View Game</a>'
        if pd.notna(x) and x
        else ""
    )

    st.markdown(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

else:
    st.info("Enter your Chess.com username and fetch games to begin analysis.")
