# ============================================================================
# FILE 11: src/components/game_length.py
# ============================================================================
"""
Game length analysis component.
"""

import streamlit as st
import plotly.express as px


def render(analyzer):
    """Render game length analysis."""
    st.subheader("Game Length Analysis")
    st.caption(
        "Game length is measured as wall-clock duration (seconds) "
        "derived from PGN timestamps."
    )

    # Overall stats
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

    # By result
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

    # Bar chart
    fig = px.bar(
        by_result,
        x="Result",
        y="Average Length (s)",
        color="Result",
        labels={"Average Length (s)": "Average Game Length (seconds)"},
        title="Average Game Length by Result",
    )
    
    fig.update_yaxes(tickformat=".0f")
    st.plotly_chart(fig, width='stretch')

    st.divider()

    # Scatter plot
    _render_length_vs_rating_scatter(analyzer)


def _render_length_vs_rating_scatter(analyzer):
    """Render scatter plot of game length vs opponent rating."""
    st.subheader("Game Length vs Opponent Rating")
    st.caption(
        "Explore how game duration varies with opponent strength and outcome. "
        "Remember to filter by time control in the sidebar for more meaningful insights."
    )

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

    fig_scatter.update_yaxes(tickformat=".0f")
    st.plotly_chart(fig_scatter, width='stretch')

