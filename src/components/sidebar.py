# ============================================================================
# FILE 3: src/components/sidebar.py
# ============================================================================
"""
Sidebar components for data management and navigation.
"""

import streamlit as st
from datetime import datetime, timedelta
from src.data_fetcher import ChessDataFetcher
import pandas as pd


def render_navigation():
    """Render analysis view selection."""
    st.subheader("Analysis Views")
    
    return st.radio(
        label="Select analysis view",
        options=[
            "Performance Overview",
            "Rating Trend",
            "Results Over Time",
            "Opening Performance",
            "Opponent Strength",
            "Win Probability",
            "Game Length",
            "Competitor Analysis"
        ],
        label_visibility="collapsed",
    )


def render_data_management():
    """Render data fetching and filtering controls."""
    st.header("Data Management")

    username = st.text_input(
        "Chess.com Username",
        value=st.session_state.username,
        placeholder="Enter username",
        help="Example: RhysLWells, Hikaru, GothamChess",
    )

    st.subheader("Fetch Games")
    
    fetch_mode = st.radio(
        "Fetch Mode",
        ["Recent Months", "Custom Range"],
        help="Choose how to fetch your game data"
    )

    if fetch_mode == "Recent Months":
        months_back = st.selectbox(
            "Number of Months",
            [1, 3, 6, 12],
            index=1,
            help="Fetch only the most recent N months"
        )
        use_archive_discovery = True
        limit_months = months_back
        start_date = end_date = None
    else:
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
        use_archive_discovery = False
        limit_months = None

    fetch_button = st.button("Fetch Games", type="primary", width='stretch')

    if fetch_button and username:
        _fetch_games(username, use_archive_discovery, limit_months, start_date, end_date)

    _show_last_fetch_time()
    
    if st.session_state.data_loaded and st.session_state.df is not None:
        _render_filters()


def _fetch_games(username, use_archive_discovery, limit_months, start_date, end_date):
    """Handle game fetching logic."""
    with st.spinner("Fetching games from Chess.com..."):
        fetcher = ChessDataFetcher()
        
        try:
            if use_archive_discovery:
                st.info(f"Discovering available archives for {username}...")
                games = fetcher.fetch_all_games(username, limit_months=limit_months)
            else:
                games = fetcher.fetch_multiple_months(username, start_date, end_date)

            if games:
                df = fetcher.process_and_save(username, games, mode="json")
                
                st.session_state.df = df
                st.session_state.data_loaded = True
                st.session_state.username = username
                st.session_state.last_fetch_time = datetime.now()
                
                if not df.empty:
                    earliest = pd.to_datetime(df['date']).min().strftime('%Y-%m-%d')
                    latest = pd.to_datetime(df['date']).max().strftime('%Y-%m-%d')
                    st.success(
                        f"Loaded {len(df)} games\n\n"
                        f"Date range: {earliest} to {latest}"
                    )
                else:
                    st.success(f"Loaded {len(df)} games.")
                
                st.rerun()
            else:
                st.error("No games found for this period.")
                
        except Exception as e:
            st.error(f"Error fetching games: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


def _show_last_fetch_time():
    """Display time since last fetch."""
    if hasattr(st.session_state, 'last_fetch_time') and st.session_state.last_fetch_time:
        last_fetch = st.session_state.last_fetch_time
        time_ago = datetime.now() - last_fetch
        
        if time_ago.days > 0:
            time_str = f"{time_ago.days} day(s) ago"
        elif time_ago.seconds > 3600:
            time_str = f"{time_ago.seconds // 3600} hour(s) ago"
        else:
            time_str = f"{time_ago.seconds // 60} minute(s) ago"
            
        st.caption(f"Last fetched: {time_str}")


def _render_filters():
    """Render game type filters."""
    st.divider()
    st.subheader("Filter Games")
    
    df = st.session_state.df
    available_time_controls = sorted(df['time_control'].unique().tolist())
    
    selected_time_controls = st.multiselect(
        "Time Control",
        options=available_time_controls,
        default=available_time_controls,
        help="Select which game types to include in the analysis"
    )
    
    st.session_state.selected_time_controls = selected_time_controls
    
    if selected_time_controls:
        filtered_count = len(df[df['time_control'].isin(selected_time_controls)])
        st.info(f"Analyzing {filtered_count} of {len(df)} games")
    else:
        st.warning("No time controls selected. Please select at least one.")
    
    st.divider()
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Games as CSV",
        data=csv,
        file_name=f"{st.session_state.username}_chess_games.csv",
        mime="text/csv",
        width='stretch'
    )


