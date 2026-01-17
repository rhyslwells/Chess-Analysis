# ============================================================================
# FILE 12: src/components/competitor.py
# ============================================================================
"""
Competitor analysis component.
"""

import streamlit as st
import numpy as np
import pandas as pd
from src.data_fetcher import ChessDataFetcher
from src.predictor import ChessPredictor


def render(analyzer):
    """Render competitor analysis."""
    st.subheader("Competitor Analysis")
    st.caption(
        "This tab displays current Elo ratings for selected competitors and "
        "predicted probabilities of winning as White or Black based on your "
        "historical performance."
    )

    suggested_users = ["Hikaru", "GothamChess", "MagnusCarlsen"]

    # Input section
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

    # Fetch competitor data
    fetcher = ChessDataFetcher()
    competitor_elos = {u: fetcher.get_current_elo(u, time_control) for u in competitors}

    # Tabs
    tab_elo, tab_pred = st.tabs(["Current Elo Ratings", "Predicted Win Probabilities"])

    with tab_elo:
        _render_elo_ratings(competitor_elos)

    with tab_pred:
        _render_win_probabilities(analyzer, competitor_elos)


def _render_elo_ratings(competitor_elos):
    """Render competitor Elo ratings."""
    st.markdown("### Elo Ratings")
    cols = st.columns(len(competitor_elos))
    for i, (u, e) in enumerate(competitor_elos.items()):
        cols[i].metric(label=u, value=e if e is not None else "N/A")


def _render_win_probabilities(analyzer, competitor_elos):
    """Render predicted win probabilities."""
    st.markdown("### Predicted Win Probabilities (White / Black)")

    # Train predictor
    predictor = ChessPredictor()
    X, y = analyzer.prepare_ml_features()
    predictor.train(X, y)
    user_elo = analyzer.get_overall_stats()["current_elo"]

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
