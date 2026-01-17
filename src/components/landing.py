# ============================================================================
# FILE 4: src/components/landing.py
# ============================================================================
"""
Landing page component shown when no data is loaded.
"""

import streamlit as st


def render():
    """Render the landing page."""
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


