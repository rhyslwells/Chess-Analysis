"""
test_analyzer.py
Unit tests for ChessAnalyzer class.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.analyzer import ChessAnalyzer


@pytest.fixture
def sample_games_df():
    """Fixture providing a sample DataFrame of chess games."""
    base_date = datetime(2024, 1, 1)
    
    games = []
    for i in range(20):
        game = {
            'date': (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
            'timestamp': int((base_date + timedelta(days=i)).timestamp()) + i,
            'user_color': 'white' if i % 2 == 0 else 'black',
            'user_rating': 1500 + (i * 2),  # Rating increases
            'opponent': f'opponent{i}',
            'opponent_rating': 1480 + (i * 2),
            'result': 1 if i % 3 == 0 else (0 if i % 3 == 1 else 0.5),
            'result_label': 'Win' if i % 3 == 0 else ('Loss' if i % 3 == 1 else 'Draw'),
            'opening': f'Opening{i % 5}',  # 5 different openings
            'eco': f'A{i:02d}',
            'eco_url': f'https://chess.com/openings/opening{i}',
            'time_control': 'rapid' if i % 2 == 0 else 'blitz',
            'game_url': f'https://chess.com/game/{i}',
            'game_duration_seconds': 600 + (i * 10),
            'pgn': f'1. e4 e5 {i}',
            'moves_san': f'e4 e5 Nf3 {"Nc6 " * i}'
        }
        games.append(game)
    
    return pd.DataFrame(games)


@pytest.fixture
def analyzer(sample_games_df):
    """Fixture providing a ChessAnalyzer instance."""
    return ChessAnalyzer(sample_games_df)


class TestChessAnalyzer:
    """Test suite for ChessAnalyzer class."""

    # -------------------------------------------------------------------------
    # Initialization Tests
    # -------------------------------------------------------------------------

    def test_initialization(self, sample_games_df):
        """Test that analyzer initializes correctly."""
        analyzer = ChessAnalyzer(sample_games_df)
        
        assert analyzer.df is not None
        assert len(analyzer.df) == 20
        assert 'rating_diff' in analyzer.df.columns
        assert 'opponent_category' in analyzer.df.columns
        assert 'game_num' in analyzer.df.columns

    def test_derived_features_rating_diff(self, analyzer):
        """Test that rating difference is calculated correctly."""
        assert 'rating_diff' in analyzer.df.columns
        assert analyzer.df.iloc[0]['rating_diff'] == (1500 - 1480)

    def test_derived_features_opponent_category(self, analyzer):
        """Test opponent strength categorization."""
        df = analyzer.df
        
        # Check that categories are assigned
        assert 'opponent_category' in df.columns
        categories = df['opponent_category'].unique()
        assert len(categories) > 0
        assert all(cat in ['Lower Rated', 'Similar Rating', 'Higher Rated'] 
                  for cat in categories)

    def test_derived_features_date_conversion(self, analyzer):
        """Test that dates are converted to datetime."""
        assert pd.api.types.is_datetime64_any_dtype(analyzer.df['date'])

    def test_derived_features_move_count(self, analyzer):
        """Test move count extraction from moves_san."""
        assert 'move_count' in analyzer.df.columns
        assert analyzer.df['move_count'].iloc[0] > 0

    # -------------------------------------------------------------------------
    # Overall Stats Tests
    # -------------------------------------------------------------------------

    def test_get_overall_stats(self, analyzer):
        """Test overall statistics calculation."""
        stats = analyzer.get_overall_stats()
        
        assert stats['total_games'] == 20
        assert stats['wins'] + stats['losses'] + stats['draws'] == 20
        assert 0 <= stats['win_rate'] <= 100
        assert stats['avg_user_rating'] > 0
        assert stats['avg_opponent_rating'] > 0

    def test_get_overall_stats_win_rate_calculation(self, analyzer):
        """Test win rate calculation accuracy."""
        stats = analyzer.get_overall_stats()
        
        # With i % 3 == 0 pattern, we expect ~7 wins out of 20 games
        expected_wins = len([i for i in range(20) if i % 3 == 0])
        assert stats['wins'] == expected_wins
        assert abs(stats['win_rate'] - (expected_wins / 20 * 100)) < 0.01

    def test_get_overall_stats_elo_progression(self, analyzer):
        """Test ELO progression tracking."""
        stats = analyzer.get_overall_stats()
        
        # Starting ELO should be 1500 (first game)
        assert stats['starting_elo'] == 1500
        # Current ELO should be higher (last game has rating 1500 + 19*2)
        assert stats['current_elo'] == 1538
        assert stats['elo_change'] == 38

    def test_get_overall_stats_empty_dataframe(self):
        """Test stats with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'user_rating', 'result'])
        analyzer = ChessAnalyzer(empty_df)
        stats = analyzer.get_overall_stats()
        
        assert stats['total_games'] == 0
        assert stats['win_rate'] == 0

    # -------------------------------------------------------------------------
    # Performance Analysis Tests
    # -------------------------------------------------------------------------

    def test_get_performance_by_opponent_strength(self, analyzer):
        """Test performance breakdown by opponent strength."""
        perf = analyzer.get_performance_by_opponent_strength()
        
        assert isinstance(perf, pd.DataFrame)
        assert 'category' in perf.columns
        assert 'games' in perf.columns
        assert 'win_rate' in perf.columns
        assert perf['games'].sum() <= 20  # May not have all categories

    def test_get_color_performance(self, analyzer):
        """Test performance breakdown by color."""
        color_perf = analyzer.get_color_performance()
        
        assert isinstance(color_perf, pd.DataFrame)
        assert len(color_perf) == 2  # White and Black
        assert 'color' in color_perf.columns
        assert set(color_perf['color']) == {'White', 'Black'}
        assert color_perf['games'].sum() == 20

    def test_get_time_control_stats(self, analyzer):
        """Test performance breakdown by time control."""
        tc_stats = analyzer.get_time_control_stats()
        
        assert isinstance(tc_stats, pd.DataFrame)
        assert 'time_control' in tc_stats.columns
        assert 'games' in tc_stats.columns
        assert tc_stats['games'].sum() == 20

    # -------------------------------------------------------------------------
    # Opening Analysis Tests
    # -------------------------------------------------------------------------

    def test_get_opening_stats(self, analyzer):
        """Test opening statistics calculation."""
        opening_stats = analyzer.get_opening_stats(top_n=5)
        
        assert isinstance(opening_stats, pd.DataFrame)
        assert len(opening_stats) <= 5
        assert 'opening' in opening_stats.columns
        assert 'games' in opening_stats.columns
        assert 'win_rate' in opening_stats.columns
        
        # Check sorted by games played
        assert opening_stats['games'].is_monotonic_decreasing

    def test_get_opening_stats_win_rate_calculation(self, analyzer):
        """Test that opening win rates are correctly calculated."""
        opening_stats = analyzer.get_opening_stats(top_n=10)
        
        # Win rate should be percentage (0-100)
        assert all(0 <= wr <= 100 for wr in opening_stats['win_rate'])

    # -------------------------------------------------------------------------
    # Rating Analysis Tests
    # -------------------------------------------------------------------------

    def test_get_rating_trend(self, analyzer):
        """Test rating trend over time."""
        trend = analyzer.get_rating_trend()
        
        assert isinstance(trend, pd.DataFrame)
        assert 'date' in trend.columns
        assert 'user_rating' in trend.columns
        assert len(trend) == 20
        assert pd.api.types.is_datetime64_any_dtype(trend['date'])

    def test_get_rating_volatility(self, analyzer):
        """Test rating volatility metrics."""
        volatility = analyzer.get_rating_volatility()
        
        assert 'volatility' in volatility
        assert 'avg_rating_change' in volatility
        assert 'max_rating_gain' in volatility
        assert 'max_rating_loss' in volatility
        
        assert volatility['volatility'] >= 0
        assert volatility['avg_rating_change'] >= 0

    def test_get_rating_volatility_with_stable_rating(self):
        """Test volatility with perfectly stable rating."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'timestamp': [1, 2, 3],
            'user_rating': [1500, 1500, 1500],
            'opponent_rating': [1500, 1500, 1500],
            'user_color': ['white', 'black', 'white'],
            'opponent': ['opp1', 'opp2', 'opp3'],
            'result': [1, 0, 0.5],
            'result_label': ['Win', 'Loss', 'Draw'],
            'opening': ['A', 'B', 'C'],
            'eco': ['E00', 'E01', 'E02'],
            'eco_url': ['url1', 'url2', 'url3'],
            'time_control': ['rapid', 'rapid', 'rapid'],
            'game_url': ['url1', 'url2', 'url3'],
            'game_duration_seconds': [600, 700, 800],
            'pgn': ['pgn1', 'pgn2', 'pgn3'],
        })
        
        analyzer = ChessAnalyzer(df)
        volatility = analyzer.get_rating_volatility()
        
        # With constant rating, rating changes should be 0
        assert volatility['avg_rating_change'] == 0
        assert volatility['max_rating_gain'] == 0
        assert volatility['max_rating_loss'] == 0

    # -------------------------------------------------------------------------
    # Time Series Tests
    # -------------------------------------------------------------------------

    def test_get_results_over_time_monthly(self, analyzer):
        """Test results aggregation by month."""
        results = analyzer.get_results_over_time(period='M')
        
        assert isinstance(results, pd.DataFrame)
        assert 'Wins' in results.columns
        assert 'Losses' in results.columns
        assert 'Draws' in results.columns

    def test_get_results_over_time_weekly(self, analyzer):
        """Test results aggregation by week."""
        results = analyzer.get_results_over_time(period='W')
        
        assert isinstance(results, pd.DataFrame)
        assert len(results) > 0

    def test_get_results_over_time_daily(self, analyzer):
        """Test results aggregation by day."""
        results = analyzer.get_results_over_time(period='D')
        
        assert isinstance(results, pd.DataFrame)
        # Should have entries for each day with games
        assert len(results) == 20  # One game per day in sample data

    # -------------------------------------------------------------------------
    # Game Length Tests
    # -------------------------------------------------------------------------

    def test_get_game_length_stats(self, analyzer):
        """Test game length statistics."""
        stats = analyzer.get_game_length_stats()
        
        assert stats is not None
        assert 'average' in stats
        assert 'median' in stats
        assert 'shortest' in stats
        assert 'longest' in stats
        assert 'length_result_corr' in stats
        
        assert stats['shortest'] <= stats['median'] <= stats['longest']
        assert -1 <= stats['length_result_corr'] <= 1

    def test_get_game_length_by_result(self, analyzer):
        """Test game length breakdown by result."""
        length_stats = analyzer.get_game_length_by_result()
        
        assert isinstance(length_stats, pd.DataFrame)
        assert 'Result' in length_stats.columns
        assert 'Games' in length_stats.columns
        assert 'Average Length (s)' in length_stats.columns

    def test_get_game_length_stats_without_duration(self):
        """Test game length stats when duration data is missing."""
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'timestamp': [1],
            'user_rating': [1500],
            'opponent_rating': [1500],
            'user_color': ['white'],
            'opponent': ['opp1'],
            'result': [1],
            'result_label': ['Win'],
            'opening': ['Opening'],
            'eco': ['E00'],
            'eco_url': ['url'],
            'time_control': ['rapid'],
            'game_url': ['url'],
            'pgn': ['pgn'],
        })
        
        analyzer = ChessAnalyzer(df)
        
        # Should handle missing game_duration_seconds gracefully
        stats = analyzer.get_game_length_stats()
        # Will have NaN values but shouldn't crash
        assert stats is not None

    # -------------------------------------------------------------------------
    # ML Feature Preparation Tests
    # -------------------------------------------------------------------------

    def test_prepare_ml_features(self, analyzer):
        """Test ML feature preparation."""
        X, y = analyzer.prepare_ml_features()
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y) == 20
        
        # Check feature columns
        assert 'user_rating' in X.columns
        assert 'opponent_rating' in X.columns
        assert 'rating_diff' in X.columns
        assert 'is_white' in X.columns
        
        # Check target is binary
        assert set(y.unique()).issubset({0, 1})

    def test_prepare_ml_features_target_encoding(self, analyzer):
        """Test that wins are encoded as 1, non-wins as 0."""
        X, y = analyzer.prepare_ml_features()
        
        wins = (analyzer.df['result'] == 1).sum()
        assert y.sum() == wins

    def test_prepare_ml_features_is_white_encoding(self, analyzer):
        """Test that color is correctly encoded as binary."""
        X, y = analyzer.prepare_ml_features()
        
        white_games = (analyzer.df['user_color'] == 'white').sum()
        assert X['is_white'].sum() == white_games

    # -------------------------------------------------------------------------
    # Recent Games Tests
    # -------------------------------------------------------------------------

    def test_get_recent_games(self, analyzer):
        """Test retrieving recent games."""
        recent = analyzer.get_recent_games(n=5)
        
        assert len(recent) == 5
        # Should be sorted by timestamp descending
        assert recent.iloc[0]['timestamp'] > recent.iloc[4]['timestamp']

    def test_get_recent_games_more_than_available(self, analyzer):
        """Test requesting more games than available."""
        recent = analyzer.get_recent_games(n=100)
        
        # Should return all 20 games
        assert len(recent) == 20

    # -------------------------------------------------------------------------
    # Edge Cases
    # -------------------------------------------------------------------------

    def test_opponent_category_boundaries(self):
        """Test opponent categorization boundary conditions."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
            'timestamp': [1, 2, 3, 4],
            'user_rating': [1500, 1500, 1500, 1500],
            'opponent_rating': [1449, 1450, 1550, 1551],  # Test boundaries
            'user_color': ['white'] * 4,
            'opponent': ['opp1', 'opp2', 'opp3', 'opp4'],
            'result': [1, 1, 0, 0],
            'result_label': ['Win'] * 2 + ['Loss'] * 2,
            'opening': ['Opening'] * 4,
            'eco': ['E00'] * 4,
            'eco_url': ['url'] * 4,
            'time_control': ['rapid'] * 4,
            'game_url': ['url'] * 4,
            'pgn': ['pgn'] * 4,
        })
        
        analyzer = ChessAnalyzer(df)
        
        # 1449: diff = 51 -> Lower Rated
        # 1450: diff = 50 -> Similar Rating (boundary)
        # 1550: diff = -50 -> Similar Rating (boundary)
        # 1551: diff = -51 -> Higher Rated
        
        assert analyzer.df.iloc[0]['opponent_category'] == 'Lower Rated'
        assert analyzer.df.iloc[1]['opponent_category'] == 'Similar Rating'
        assert analyzer.df.iloc[2]['opponent_category'] == 'Similar Rating'
        assert analyzer.df.iloc[3]['opponent_category'] == 'Higher Rated'

    def test_single_game_dataframe(self):
        """Test analyzer with single game."""
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'timestamp': [1],
            'user_rating': [1500],
            'opponent_rating': [1480],
            'user_color': ['white'],
            'opponent': ['opponent1'],
            'result': [1],
            'result_label': ['Win'],
            'opening': ['Opening'],
            'eco': ['E00'],
            'eco_url': ['url'],
            'time_control': ['rapid'],
            'game_url': ['url'],
            'pgn': ['pgn'],
        })
        
        analyzer = ChessAnalyzer(df)
        stats = analyzer.get_overall_stats()
        
        assert stats['total_games'] == 1
        assert stats['wins'] == 1
        assert stats['win_rate'] == 100.0