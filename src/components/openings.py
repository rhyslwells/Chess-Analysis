# ============================================================================
# FILE 8: src/components/openings.py
# ============================================================================
"""
Opening performance component.
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def render(analyzer):
    """Render opening performance analysis."""
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

    opening_stats = analyzer.get_opening_stats(top_n=10)

    # Chart
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

    st.plotly_chart(fig, width='stretch')

    # Example games
    _render_example_games(analyzer, opening_stats)


def _render_example_games(analyzer, opening_stats):
    """Render example games table."""
    st.markdown("### Example games by opening")

    df = analyzer.df
    table_data = []
    
    for opening in opening_stats["opening"]:
        subset = df[df["opening"] == opening].head(1)
        
        if subset.empty:
            continue
        
        row = subset.iloc[0]
        
        if pd.notnull(row['eco_url']) and row['eco_url']:
            eco_link = f'<a href="{row["eco_url"]}" target="_blank">ECO Info</a>'
        else:
            eco_link = "—"
        
        game_link = f'<a href="{row["game_url"]}" target="_blank">{row["date"].date()} vs {row["opponent"]} ({row["result_label"]})</a>'
        
        table_data.append({
            "Opening": opening,
            "ECO Info": eco_link,
            "Recent Example": game_link
        })
    
    table_df = pd.DataFrame(table_data)
    
    st.markdown(
        table_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )


