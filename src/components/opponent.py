# ============================================================================
# FILE 9: src/components/opponent.py
# ============================================================================
"""
Opponent strength component.
"""

import streamlit as st
import plotly.express as px


def render(analyzer):
    """Render opponent strength analysis."""
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

    fig.update_traces(
        texttemplate="%{text:.0f}%",
        hovertemplate="Win Rate: %{y:.0f}%<extra></extra>"
    )

    fig.update_layout(title="Win Rate by Opponent Strength Category")

    st.plotly_chart(fig, width='stretch')

