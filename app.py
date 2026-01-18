# ============================================================================
# FILE 1: app.py (Main Entry Point - Simplified)
# ============================================================================
"""
app.py
Streamlit dashboard main entry point.
Delegates rendering to component modules.
"""

import streamlit as st
from src.components import sidebar, landing
from src.components import (
    overview, rating, results, openings,
    opponent, probability, game_length, competitor
)
from src.analyzer import ChessAnalyzer

st.set_page_config(
    page_title="Chess Game Analysis Dashboard",
    layout="wide",
)

# Initialize session state
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


def main():
    st.title("Chess Game Analysis Dashboard")
    st.caption("Fetch games using the sidebar, then explore the analysis views.")

    # Render sidebar
    analysis_view = None
    with st.sidebar:
        if st.session_state.data_loaded:
            analysis_view = sidebar.render_navigation()
            st.markdown("---")
        sidebar.render_data_management()

    # Show landing page if no data loaded
    if not st.session_state.data_loaded:
        landing.render()
        return

    # Filter data
    df = st.session_state.df
    selected_time_controls = st.session_state.get(
        "selected_time_controls",
        df["time_control"].unique().tolist(),
    )

    if not selected_time_controls:
        st.warning(
            "No time controls selected. Please select at least one time control in the sidebar."
        )
        return

    df_filtered = df[df["time_control"].isin(selected_time_controls)].copy()

    if df_filtered.empty:
        st.warning(
            "No games match the selected filters. Please adjust your filters in the sidebar."
        )
        return

    # Create analyzer
    analyzer = ChessAnalyzer(df_filtered)
    stats = analyzer.get_overall_stats()
    
    st.header("Analysis View")

    # Route to appropriate component
    view_map = {
        "Performance Overview": lambda: overview.render(df_filtered, analyzer, st.session_state.username),
        "Rating Trend": lambda: rating.render(analyzer),
        "Results Over Time": lambda: results.render(analyzer),
        "Opening Performance": lambda: openings.render(analyzer),
        "Opponent Strength": lambda: opponent.render(analyzer),
        "Win Probability": lambda: probability.render(df_filtered, analyzer, stats),
        "Game Length": lambda: game_length.render(analyzer),
        "Competitor Analysis": lambda: competitor.render(analyzer),
    }

    if analysis_view in view_map:
        view_map[analysis_view]()


if __name__ == "__main__":
    main()

