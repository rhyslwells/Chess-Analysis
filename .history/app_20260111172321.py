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
        date_option = st.radio(
            "Time Period",
            ["Last Month", "Last 3 Months", "Last 6 Months", "Custom Range"],
        )

        # Resolve date range based on selection
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

        # Fetch and persist data into session state
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
    c5.metric("Win Rate", f"{stats['win_rate']:.1f}%")

    st.divider()

    # --- breakdowns
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

    # --- recent games
    st.subheader("Recent Games")
    st.caption("ECO = Encyclopedia of Chess Openings")

    recent_games = analyzer.get_recent_games(5)

    columns = [
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
        columns.remove("eco")

    display_df = recent_games[columns].copy()

    display_df.columns = [
        "Date",
        "Opponent",
        "Your Rating",
        "Opp Rating",
        "Result",
        "Color",
        "Opening",
    ] + (["ECO"] if "eco" in columns else []) + ["Game Link"]

    display_df["Game Link"] = display_df["Game Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">View</a>' if x else ""
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
            use_container_width=True,
        )

    with c2:
        summary = f"""Chess Analysis Summary
User: {username}
Generated: {datetime.now():%Y-%m-%d %H:%M}

Games: {stats['total_games']}
Win Rate: {stats['win_rate']:.1f}%
Average Rating: {stats['avg_user_rating']:.0f}
"""
        st.download_button(
            "Download Summary",
            summary,
            file_name=f"{username}_summary.txt",
            mime="text/plain",
            use_container_width=True,
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
        ### Rating Trend Overview

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

    st.plotly_chart(fig, use_container_width=True)


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
    """Weekly aggregation of wins, losses, and draws."""
    results_time = analyzer.get_results_over_time("W")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=results_time.index, y=results_time["Wins"], name="Wins"))
    fig.add_trace(go.Scatter(x=results_time.index, y=results_time["Losses"], name="Losses"))
    fig.add_trace(go.Scatter(x=results_time.index, y=results_time["Draws"], name="Draws"))

    fig.update_layout(
        title="Results Over Time (Weekly)",
        xaxis_title="Date",
        yaxis_title="Games",
    )

    st.plotly_chart(fig, use_container_width=True)


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

    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Example games per opening
    # ------------------------------------------------------------------
    st.markdown("### Example games by opening")

    df = analyzer.df

    for opening in opening_stats["opening"]:
        subset = df[df["opening"] == opening].head(1)

        if subset.empty:
            continue

        st.markdown(f"**{opening}**")

        for _, row in subset.iterrows():
            st.markdown(
                f"- [{row['date'].date()} vs {row['opponent']} ({row['result_label']})]({row['game_url']})"
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

    st.plotly_chart(fig, use_container_width=True)


def render_win_probability(df, analyzer, stats):
    """
    Logistic regression–based win probability curves.

    The model is trained on historical games.
    The rating control below enables counterfactual exploration
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
    predictor.train(X, y)

    # ------------------------------------------------------------------
    # Rating context (derived consistently with analyzer)
    # ------------------------------------------------------------------
    current_rating = int(stats["current_elo"])
    avg_rating = int(stats["avg_user_rating"])

    st.markdown(
        f"""
        **Rating context**

        - Current rating (most recent game): **{current_rating}**
        - Average rating over selected period: **{avg_rating}**

        The model is trained on your historical games.
        The control below allows exploration of *what-if* rating scenarios
        without retraining the model.
        """
    )

    # ------------------------------------------------------------------
    # Counterfactual rating input
    # ------------------------------------------------------------------
    assumed_rating = st.number_input(
        "Assumed player rating (what-if)",
        min_value=400,
        max_value=5000,
        value=current_rating,
        step=10,
        help="Used only to generate win probability curves."
    )

    min_r, max_r = st.slider(
        "Opponent rating range",
        min_value=400,
        max_value=3000,
        value=(assumed_rating - 100, assumed_rating + 100),
        step=10,
    )

    # ------------------------------------------------------------------
    # Plot curves by colour
    # ------------------------------------------------------------------
    for is_white, label in [(True, "White"), (False, "Black")]:
        st.subheader(
            f"Expected win probability vs opponent rating ({label})"
        )

        curve = predictor.get_win_probability_curve(
            assumed_rating,
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

# ==============================================================================
# Main application flow
# ==============================================================================
def main():
    st.title("Chess Game Analysis Dashboard")
    st.caption("Fetch games using the sidebar, then explore the analysis tabs.")

    render_sidebar()

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



    df = st.session_state.df
    analyzer = ChessAnalyzer(df)
    stats = analyzer.get_overall_stats()

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

    with tabs[0]:
        render_performance_overview(df, analyzer, st.session_state.username)
    with tabs[1]:
        render_rating_trend(analyzer)
    with tabs[2]:
        render_results_over_time(analyzer)
    with tabs[3]:
        render_opening_performance(analyzer)
    with tabs[4]:
        render_opponent_strength(analyzer)
    with tabs[5]:
        render_win_probability(df, analyzer, stats)


# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
