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


# ==============================================================================
# Page configuration
# ==============================================================================
st.set_page_config(
    page_title="Chess Game Analysis Dashboard",
    layout="wide",
)


# ==============================================================================
# Session state
# ==============================================================================
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "df" not in st.session_state:
    st.session_state.df = None

if "username" not in st.session_state:
    st.session_state.username = ""


# ==============================================================================
# Title
# ==============================================================================
st.title("Chess Game Analysis Dashboard")
st.caption("Use the sidebar to fetch games before exploring the analysis.")


# ==============================================================================
# Sidebar (unchanged)
# ==============================================================================
with st.sidebar:
    st.header("Data Management")

    username = st.text_input(
        "Chess.com Username",
        value=st.session_state.username,
        placeholder="Enter username",
    )

    st.subheader("Fetch Games")
    date_option = st.radio(
        "Time Period",
        ["Last Month", "Last 3 Months", "Last 6 Months", "Custom Range"],
    )

    if date_option == "Custom Range":
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


# ==============================================================================
# Main analysis
# ==============================================================================
if not st.session_state.data_loaded:
    st.info("Fetch games using the sidebar to begin analysis.")
    st.stop()

df = st.session_state.df
analyzer = ChessAnalyzer(df)


# ==============================================================================
# Performance Analysis (tabs only)
# ==============================================================================
st.header("Performance Analysis")

tabs = st.tabs(
    [
        "Performance Overview",
        "Rating Trend",
        "Results Over Time",
        "Opening Performance",
        "Opponent Strength",
        "Win Probability",
    ]
)


# ------------------------------------------------------------------------------
# Tab 1: Performance overview
# ------------------------------------------------------------------------------
with tabs[0]:
    stats = analyzer.get_overall_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Games", stats["total_games"])
    c2.metric("Wins", stats["wins"])
    c3.metric("Losses", stats["losses"])
    c4.metric("Draws", stats["draws"])
    c5.metric("Win Rate", f"{stats['win_rate']:.1f}%")

    st.divider()

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

    st.subheader("Recent Games")
    st.caption(
        "ECO = Encyclopedia of Chess Openings (standard opening classification system)"
    )

    recent_games = analyzer.get_recent_games(5)

    cols = [
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
        cols.remove("eco")

    display_df = recent_games[cols].copy()

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
        lambda x: f'<a href="{x}" target="_blank">View</a>' if x else ""
    )

    st.markdown(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Export Data")

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "Download Games CSV",
            df.to_csv(index=False),
            file_name=f"{st.session_state.username}_games.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c2:
        summary = f"""Chess Analysis Summary
User: {st.session_state.username}
Generated: {datetime.now():%Y-%m-%d %H:%M}

Games: {stats['total_games']}
Win Rate: {stats['win_rate']:.1f}%
Average Rating: {stats['avg_user_rating']:.0f}
"""
        st.download_button(
            "Download Summary",
            summary,
            file_name=f"{st.session_state.username}_summary.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ------------------------------------------------------------------------------
# Tab 2: Rating trend
# ------------------------------------------------------------------------------
with tabs[1]:
    rating_trend = analyzer.get_rating_trend()
    fig = px.line(
        rating_trend,
        x="date",
        y="user_rating",
        labels={"date": "Date", "user_rating": "Rating"},
        title="Rating Progression",
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------------------
# Tab 3: Results over time
# ------------------------------------------------------------------------------
with tabs[2]:
    results_time = analyzer.get_results_over_time("W")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=results_time.index, y=results_time["Wins"], name="Wins"))
    fig.add_trace(
        go.Scatter(x=results_time.index, y=results_time["Losses"], name="Losses")
    )
    fig.add_trace(
        go.Scatter(x=results_time.index, y=results_time["Draws"], name="Draws")
    )
    fig.update_layout(
        title="Results Over Time (Weekly)",
        xaxis_title="Date",
        yaxis_title="Games",
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------------------
# Tab 4: Opening performance
# ------------------------------------------------------------------------------
with tabs[3]:
    opening_stats = analyzer.get_opening_stats(top_n=10)
    fig = px.bar(
        opening_stats,
        x="games",
        y="opening",
        orientation="h",
        color="win_rate",
        color_continuous_scale="RdYlGn",
        labels={"games": "Games", "opening": "Opening"},
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------------------
# Tab 5: Opponent strength
# ------------------------------------------------------------------------------
with tabs[4]:
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
    fig.update_traces(texttemplate="%{text:.1f}%")
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------------------
# Tab 6: Win probability
# ------------------------------------------------------------------------------
with tabs[5]:
    if len(df) < 20:
        st.info("At least 20 games are required for win probability modelling.")
        st.stop()

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
        max_value=3500,
        value=(current_rating - 100, current_rating + 100),
        step=25,
    )

    for is_white, label in [(True, "White"), (False, "Black")]:
        st.subheader(
            f"How your expected win rate changes across opponent ratings ({label})"
        )

        curve = predictor.get_win_probability_curve(
            current_rating,
            is_white=is_white,
        )

        curve = curve[
            (curve["opponent_rating"] >= min_r)
            & (curve["opponent_rating"] <= max_r)
        ]

        fig = px.line(
            curve,
            x="opponent_rating",
            y="win_probability",
            labels={
                "opponent_rating": "Opponent Rating",
                "win_probability": "Win Probability",
            },
        )
        fig.add_hline(y=0.5, line_dash="dash")
        fig.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
