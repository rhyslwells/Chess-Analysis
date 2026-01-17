# ============================================================================
# FILE 5: src/components/overview.py
# ============================================================================
"""
Performance overview component.
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def render(df, analyzer, username):
    """Render performance overview."""
    stats = analyzer.get_overall_stats()

    # Headline metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Games", stats["total_games"])
    c2.metric("Wins", stats["wins"])
    c3.metric("Losses", stats["losses"])
    c4.metric("Draws", stats["draws"])
    c5.metric("Win Rate", f"{stats['win_rate']:.0f}%")

    st.divider()

    # Breakdowns
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Performance by Color")
        color_perf = analyzer.get_color_performance()
        st.dataframe(color_perf, width='stretch', hide_index=True)

    with c2:
        st.subheader("Performance by Time Control")
        tc_stats = analyzer.get_time_control_stats()
        st.dataframe(tc_stats, width='stretch', hide_index=True)

    st.divider()

    # Recent games
    _render_recent_games(analyzer)

    st.divider()

    # Export options
    _render_export_options(df, username, stats)


def _render_recent_games(analyzer):
    """Render recent games table."""
    st.subheader("Recent Games")
    st.caption("ECO = Encyclopedia of Chess Openings")

    recent_games = analyzer.get_recent_games(5)

    display_df = recent_games[
        [
            "date",
            "opponent",
            "user_rating",
            "opponent_rating",
            "result_label",
            "user_color",
            "opening",
            "eco_url",
            "game_url",
        ]
    ].copy()

    display_df.rename(
        columns={
            "date": "Date",
            "opponent": "Opponent",
            "user_rating": "Your Rating",
            "opponent_rating": "Opp Rating",
            "result_label": "Result",
            "user_color": "Color",
            "opening": "Opening",
            "eco_url": "ECO Link",
            "game_url": "Game Link",
        },
        inplace=True,
    )

    display_df["ECO Link"] = display_df["ECO Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">ECO</a>' if pd.notnull(x) and x else ""
    )

    display_df["Game Link"] = display_df["Game Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">View</a>' if pd.notnull(x) and x else ""
    )

    st.markdown(
        display_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )


def _render_export_options(df, username, stats):
    """Render export buttons."""
    st.subheader("Export Data")

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "Download Games CSV",
            df.to_csv(index=False),
            file_name=f"{username}_games.csv",
            mime="text/csv",
            width='stretch',
        )

    with c2:
        summary = f"""Chess Analysis Summary
User: {username}
Generated: {datetime.now():%Y-%m-%d %H:%M}

Games: {stats['total_games']}
Win Rate: {stats['win_rate']:.0f}%
Average Rating: {stats['avg_user_rating']:.0f}
"""
        st.download_button(
            "Download Summary",
            summary,
            file_name=f"{username}_summary.txt",
            mime="text/plain",
            width='stretch',
        )


