# ============================================================================
# FILE 7: src/components/results.py
# ============================================================================
"""
Results over time component.
"""

import streamlit as st
import plotly.graph_objects as go


def render(analyzer):
    """Render results over time analysis."""
    st.markdown(
        """
        ### Results Over Time

        This tab shows your game outcomes aggregated by week. 
        The chart displays the number of wins, losses, and draws per week.  

        Below, key metrics summarize your overall performance over the selected period.
        """
    )

    results_time = analyzer.get_results_over_time("W")
    stats = analyzer.get_overall_stats()

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=results_time.index, 
        y=results_time["Wins"], 
        mode="lines+markers", 
        name="Wins",
        line=dict(color="green")
    ))
    fig.add_trace(go.Scatter(
        x=results_time.index, 
        y=results_time["Losses"], 
        mode="lines+markers", 
        name="Losses",
        line=dict(color="red")
    ))
    fig.add_trace(go.Scatter(
        x=results_time.index, 
        y=results_time["Draws"], 
        mode="lines+markers", 
        name="Draws",
        line=dict(color="orange")
    ))

    fig.update_layout(
        title="Weekly Results Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Games",
        hovermode="x unified"
    )

    st.plotly_chart(fig, width='stretch')

