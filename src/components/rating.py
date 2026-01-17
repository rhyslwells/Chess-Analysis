# ============================================================================
# FILE 6: src/components/rating.py
# ============================================================================
"""
Rating trend component.
"""

import streamlit as st
import plotly.express as px


def render(analyzer):
    """Render rating trend analysis."""
    st.markdown(
        """
        ### Rating Trend

        This tab shows your rating progression over time. 
        The chart displays how your rating has changed per game.
        
        Below, key metrics summarise rating volatility.
        """
    )

    rating_trend = analyzer.get_rating_trend()
    volatility_stats = analyzer.get_rating_volatility()

    # Chart
    fig = px.line(
        rating_trend,
        x="date",
        y="user_rating",
        labels={"date": "Date", "user_rating": "Rating"},
        title="Rating Progression Over Time",
    )

    st.plotly_chart(fig, width='stretch')

    # Volatility metrics
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


