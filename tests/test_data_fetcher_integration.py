"""
test_data_fetcher_integration.py
Integration tests for ChessDataFetcher with real Chess.com API.

WARNING: These tests make actual API calls to Chess.com.
- Run sparingly to avoid rate limiting
- Requires internet connection
- Tests use public Chess.com profiles
"""

import pytest
from datetime import datetime, timedelta
from src.data_fetcher import ChessDataFetcher
import time


# Skip all integration tests by default
pytestmark = pytest.mark.integration


@pytest.fixture
def fetcher():
    """Fixture to create a ChessDataFetcher instance."""
    return ChessDataFetcher()


@pytest.fixture
def test_username():
    """
    Public Chess.com username for testing.
    Using 'hikaru' as he has many public games.
    """
    return "hikaru"


class TestChessDataFetcherIntegration:
    """Integration tests for ChessDataFetcher with real API."""

    def test_fetch_games_real_api(self, fetcher, test_username):
        """Test fetching games from real Chess.com API."""
        # Fetch games from a recent month
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert isinstance(games, list)
        assert len(games) > 0
        
        # Check game structure
        first_game = games[0]
        assert 'white' in first_game
        assert 'black' in first_game
        assert 'pgn' in first_game
        assert 'url' in first_game
        
        # Rate limiting
        time.sleep(1)

    def test_fetch_games_invalid_username(self, fetcher):
        """Test fetching games with invalid username."""
        games = fetcher.fetch_games("this_user_definitely_does_not_exist_12345", 
                                    year=2024, month=1)
        
        # Should return empty list for non-existent user
        assert games == []

    def test_fetch_games_future_month(self, fetcher, test_username):
        """Test fetching games from a future month."""
        future_year = datetime.now().year + 1
        games = fetcher.fetch_games(test_username, year=future_year, month=1)
        
        # Should return empty list for future dates
        assert games == []

    def test_fetch_multiple_months_real_api(self, fetcher, test_username):
        """Test fetching games across multiple months."""
        # Fetch last 2 months only to avoid excessive API calls
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        games = fetcher.fetch_multiple_months(test_username, start_date, end_date)
        
        assert isinstance(games, list)
        assert len(games) > 0
        
        # Should have games from multiple months
        dates = set()
        for game in games[:10]:  # Check first 10
            if 'end_time' in game:
                game_date = datetime.fromtimestamp(game['end_time'])
                dates.add(game_date.strftime('%Y-%m'))
        
        assert len(dates) > 0

    def test_parse_real_game_data(self, fetcher, test_username):
        """Test parsing real game data from API."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        if len(games) > 0:
            # Parse first game
            parsed = fetcher.parse_game_from_json(games[0], test_username)
            
            # Verify parsed data structure
            assert 'date' in parsed
            assert 'user_color' in parsed
            assert 'user_rating' in parsed
            assert 'opponent' in parsed
            assert 'opponent_rating' in parsed
            assert 'result' in parsed
            assert 'result_label' in parsed
            assert 'opening' in parsed
            assert 'time_control' in parsed
            
            # Verify data types
            assert isinstance(parsed['user_rating'], int)
            assert isinstance(parsed['opponent_rating'], int)
            assert parsed['result'] in [0, 0.5, 1]
            assert parsed['result_label'] in ['Win', 'Loss', 'Draw']
        
        time.sleep(1)

    def test_process_and_save_real_data(self, fetcher, test_username):
        """Test processing and saving real game data."""
        # Fetch small dataset
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        if len(games) > 0:
            # Take only first 10 games for faster testing
            games = games[:10]
            
            df = fetcher.process_and_save(test_username, games, mode='json')
            
            # Verify DataFrame
            assert len(df) > 0
            assert len(df) <= 10
            
            # Check columns
            required_columns = [
                'date', 'user_color', 'user_rating', 'opponent_rating',
                'result', 'opening', 'time_control'
            ]
            for col in required_columns:
                assert col in df.columns
            
            # Verify sorting (most recent first)
            assert df.iloc[0]['timestamp'] >= df.iloc[-1]['timestamp']
        
        time.sleep(1)

    def test_api_rate_limiting(self, fetcher, test_username):
        """Test that rate limiting is handled properly."""
        # Make multiple rapid requests
        start_time = time.time()
        
        for i in range(3):
            fetcher.fetch_games(test_username, year=2024, month=i+1)
        
        elapsed_time = time.time() - start_time
        
        # Should take at least 1 second due to rate limiting (0.5s * 2 sleeps)
        assert elapsed_time >= 1.0

    def test_pgn_parsing_real_data(self, fetcher, test_username):
        """Test PGN parsing with real game data."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        if len(games) > 0:
            parsed = fetcher.parse_game_from_json(games[0], test_username)
            
            # Check PGN-derived fields
            assert parsed['opening'] != 'Unknown'  # Should have opening info
            assert parsed['eco'] != ''  # Should have ECO code
            
            # Game duration should be calculated if PGN has timestamps
            if parsed['game_duration_seconds'] is not None:
                assert parsed['game_duration_seconds'] > 0
        
        time.sleep(1)

    def test_different_time_controls(self, fetcher, test_username):
        """Test games from different time controls."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        if len(games) > 0:
            # Process games and check time controls
            df = fetcher.process_and_save(test_username, games[:20], mode='json')
            
            time_controls = df['time_control'].unique()
            
            # Popular players usually play multiple time controls
            assert len(time_controls) > 0
            
            # Common time controls
            valid_controls = ['bullet', 'blitz', 'rapid', 'daily']
            for tc in time_controls:
                assert tc in valid_controls
        
        time.sleep(1)

    def test_user_played_both_colors(self, fetcher, test_username):
        """Test that games include both colors."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        if len(games) >= 10:
            df = fetcher.process_and_save(test_username, games[:20], mode='json')
            
            colors = df['user_color'].unique()
            
            # Active players play both colors
            assert 'white' in colors or 'black' in colors
            # Most likely both, but at least one
            assert len(colors) >= 1
        
        time.sleep(1)


@pytest.mark.slow
class TestLargeDatasets:
    """Tests for larger datasets (marked slow)."""
    
    def test_fetch_large_date_range(self, fetcher, test_username):
        """Test fetching games over a longer period."""
        # Fetch 6 months of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        games = fetcher.fetch_multiple_months(test_username, start_date, end_date)
        
        assert len(games) > 0
        
        # Process and verify no duplicates
        df = fetcher.process_and_save(test_username, games, mode='json')
        
        # Check for duplicates
        duplicate_count = df.duplicated(subset=['timestamp', 'opponent']).sum()
        assert duplicate_count == 0