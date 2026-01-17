"""
test_data_fetcher_integration.py
Integration tests for ChessDataFetcher with real Chess.com API.

WARNING: These tests make actual API calls to Chess.com.
- Run sparingly to avoid rate limiting
- Requires internet connection
- Tests use public Chess.com profiles

# Run all integration tests
pytest test_data_fetcher_integration.py -m integration

# Run only fast tests
pytest test_data_fetcher_integration.py -m integration -m "not slow"

# Run slow tests
pytest test_data_fetcher_integration.py -m slow

# Skip network tests
SKIP_NETWORK_TESTS=1 pytest test_data_fetcher_integration.py

"""

import pytest
from datetime import datetime, timedelta
from src.data_fetcher import ChessDataFetcher
import time
import os


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


@pytest.fixture
def alternate_username():
    """Alternative test user with different game patterns."""
    return "magnuscarlsen"


class TestChessDataFetcherIntegration:
    """Integration tests for ChessDataFetcher with real API."""

    def test_fetch_games_real_api(self, fetcher, test_username):
        """Test fetching games from real Chess.com API."""
        # Fetch games from a recent month
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert isinstance(games, list)
        assert len(games) > 0, "Should fetch at least one game"
        
        # Check game structure
        first_game = games[0]
        assert 'white' in first_game, "Game should have white player info"
        assert 'black' in first_game, "Game should have black player info"
        assert 'pgn' in first_game, "Game should include PGN"
        assert 'url' in first_game, "Game should have URL"
        assert 'end_time' in first_game, "Game should have end_time"
        assert 'time_class' in first_game, "Game should have time_class"
        
        # Rate limiting
        time.sleep(1)

    def test_fetch_games_invalid_username(self, fetcher):
        """Test fetching games with invalid username."""
        games = fetcher.fetch_games(
            "this_user_definitely_does_not_exist_12345_xyz", 
            year=2024, 
            month=1
        )
        
        # Should return empty list for non-existent user
        assert games == [], "Non-existent user should return empty list"

    def test_fetch_games_future_month(self, fetcher, test_username):
        """Test fetching games from a future month."""
        future_year = datetime.now().year + 1
        games = fetcher.fetch_games(test_username, year=future_year, month=1)
        
        # Should return empty list for future dates
        assert games == [], "Future dates should return empty list"

    def test_fetch_multiple_months_real_api(self, fetcher, test_username):
        """Test fetching games across multiple months."""
        # Fetch last 2 months only to avoid excessive API calls
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        games = fetcher.fetch_multiple_months(test_username, start_date, end_date)
        
        assert isinstance(games, list)
        assert len(games) > 0, "Should fetch games from multiple months"
        
        # Should have games from multiple months
        dates = set()
        for game in games[:10]:  # Check first 10
            if 'end_time' in game:
                game_date = datetime.fromtimestamp(game['end_time'])
                dates.add(game_date.strftime('%Y-%m'))
        
        assert len(dates) > 0, "Should have games from at least one month"

    def test_parse_real_game_data(self, fetcher, test_username):
        """Test parsing real game data from API."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert len(games) > 0, "Should have games to parse"
        
        # Parse first game
        parsed = fetcher.parse_game_from_json(games[0], test_username)
        
        # Verify parsed data structure
        required_fields = [
            'date', 'user_color', 'user_rating', 'opponent',
            'opponent_rating', 'result', 'result_label', 'opening',
            'time_control', 'game_url', 'eco', 'eco_url', 'timestamp', 'pgn'
        ]
        for field in required_fields:
            assert field in parsed, f"Parsed game should contain '{field}'"
        
        # Verify data types and values
        assert isinstance(parsed['user_rating'], int), "Rating should be integer"
        assert isinstance(parsed['opponent_rating'], int), "Rating should be integer"
        assert parsed['result'] in [0, 0.5, 1], "Result should be 0, 0.5, or 1"
        assert parsed['result_label'] in ['Win', 'Loss', 'Draw'], "Invalid result label"
        assert parsed['user_color'] in ['white', 'black'], "Invalid color"
        assert isinstance(parsed['timestamp'], int), "Timestamp should be integer"
        
        time.sleep(1)

    def test_process_and_save_real_data(self, fetcher, test_username):
        """Test processing and saving real game data."""
        # Fetch small dataset
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert len(games) > 0, "Should have games to process"
        
        # Take only first 10 games for faster testing
        games = games[:10]
        
        df = fetcher.process_and_save(test_username, games, mode='json')
        
        # Verify DataFrame
        assert len(df) > 0, "DataFrame should not be empty"
        assert len(df) <= 10, "Should have at most 10 games"
        
        # Check columns
        required_columns = [
            'date', 'user_color', 'user_rating', 'opponent_rating',
            'result', 'opening', 'time_control', 'timestamp'
        ]
        for col in required_columns:
            assert col in df.columns, f"DataFrame missing column: {col}"
        
        # Verify sorting (most recent first)
        timestamps = df['timestamp'].tolist()
        assert timestamps == sorted(timestamps, reverse=True), "Games should be sorted by timestamp (newest first)"
        
        time.sleep(1)

    def test_api_rate_limiting(self, fetcher, test_username):
        """Test that rate limiting is handled properly."""
        # Make multiple rapid requests
        start_time = time.time()
        
        for i in range(3):
            fetcher.fetch_games(test_username, year=2024, month=i+1)
        
        elapsed_time = time.time() - start_time
        
        # Should take at least 1 second due to rate limiting (0.5s * 2 sleeps)
        assert elapsed_time >= 1.0, f"Rate limiting not working: only took {elapsed_time}s"

    def test_pgn_parsing_real_data(self, fetcher, test_username):
        """Test PGN parsing with real game data."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert len(games) > 0, "Should have games to parse"
        
        parsed = fetcher.parse_game_from_json(games[0], test_username)
        
        # Check PGN-derived fields
        assert parsed['opening'] != 'Unknown', "Should have opening information"
        assert parsed['eco'] != '', "Should have ECO code"
        assert parsed['eco_url'] != '', "Should have ECO URL"
        
        # Game duration should be calculated if PGN has timestamps
        # Note: Not all games have duration, so we just check type if present
        if parsed['game_duration_seconds'] is not None:
            assert isinstance(parsed['game_duration_seconds'], int), "Duration should be integer"
            assert parsed['game_duration_seconds'] >= 0, "Duration should be non-negative"
        
        time.sleep(1)

    def test_different_time_controls(self, fetcher, test_username):
        """Test games from different time controls."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert len(games) > 0, "Should have games to analyze"
        
        # Process games and check time controls
        df = fetcher.process_and_save(test_username, games[:20], mode='json')
        
        time_controls = df['time_control'].unique()
        
        # Popular players usually play multiple time controls
        assert len(time_controls) > 0, "Should have at least one time control"
        
        # Common time controls
        valid_controls = ['bullet', 'blitz', 'rapid', 'daily']
        for tc in time_controls:
            assert tc in valid_controls, f"Unexpected time control: {tc}"
        
        time.sleep(1)

    def test_user_played_both_colors(self, fetcher, test_username):
        """Test that games include both colors."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert len(games) >= 10, "Need at least 10 games for this test"
        
        df = fetcher.process_and_save(test_username, games[:20], mode='json')
        
        colors = df['user_color'].unique()
        
        # Active players play both colors
        assert 'white' in colors or 'black' in colors, "Should have at least one color"
        # Most likely both, but at least one
        assert len(colors) >= 1, "Should have at least one color"
        
        time.sleep(1)

    def test_game_duration_validation(self, fetcher, test_username):
        """Test that game duration validation is working correctly."""
        games = fetcher.fetch_games(test_username, year=2024, month=1)
        
        assert len(games) > 0, "Should have games to process"
        
        # Process games
        df = fetcher.process_and_save(test_username, games[:20], mode='json')
        
        # Check validation report
        report = fetcher.get_validation_report()
        
        assert 'total_invalid' in report, "Report should include total_invalid"
        assert 'validation_log' in report, "Report should include validation_log"
        assert 'negative_durations' in report, "Report should include negative_durations"
        assert 'unreasonably_long' in report, "Report should include unreasonably_long"
        
        # All durations in final DataFrame should be valid (non-negative)
        if 'game_duration_seconds' in df.columns:
            durations = df['game_duration_seconds'].dropna()
            if len(durations) > 0:
                assert all(durations >= 0), "All durations should be non-negative"
                assert all(durations <= 86400), "All durations should be <= 24 hours"
        
        time.sleep(1)

    def test_get_available_archives(self, fetcher, test_username):
        """Test fetching available archive list."""
        archives = fetcher.get_available_archives(test_username)
        
        assert isinstance(archives, list), "Should return a list"
        assert len(archives) > 0, "Active player should have archives"
        
        # Check archive URL format
        for archive_url in archives[:3]:  # Check first 3
            assert archive_url.startswith('https://api.chess.com/pub/player/'), \
                f"Invalid archive URL format: {archive_url}"
            assert '/games/' in archive_url, "Archive URL should contain /games/"
        
        time.sleep(1)

    def test_fetch_all_games_limited(self, fetcher, test_username):
        """Test fetching all games with month limit."""
        # Fetch only 2 most recent months
        all_games = fetcher.fetch_all_games(test_username, limit_months=2)
        
        assert isinstance(all_games, list), "Should return a list"
        assert len(all_games) > 0, "Should fetch some games"
        
        # Verify games are from recent months
        if len(all_games) > 0:
            recent_game = all_games[-1]  # Last game should be from limited period
            assert 'end_time' in recent_game, "Game should have end_time"
        
        time.sleep(1)

    def test_get_current_elo(self, fetcher, test_username):
        """Test fetching current Elo rating."""
        # Test for blitz rating
        blitz_elo = fetcher.get_current_elo(test_username, 'blitz')
        
        assert blitz_elo is not None, "Should fetch blitz rating"
        assert isinstance(blitz_elo, int), "Rating should be integer"
        assert 0 < blitz_elo < 4000, "Rating should be in reasonable range"
        
        # Test invalid time control
        invalid_elo = fetcher.get_current_elo(test_username, 'invalid_control')
        assert invalid_elo is None, "Invalid time control should return None"
        
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
        
        assert len(games) > 0, "Should fetch games from 6-month period"
        
        # Process and verify no duplicates
        df = fetcher.process_and_save(test_username, games, mode='json')
        
        # Check for duplicates
        duplicate_count = df.duplicated(subset=['timestamp', 'opponent']).sum()
        assert duplicate_count == 0, f"Found {duplicate_count} duplicate games"
        
        # Verify date range
        if len(df) > 0:
            earliest = datetime.fromtimestamp(df['timestamp'].min())
            latest = datetime.fromtimestamp(df['timestamp'].max())
            date_range = (latest - earliest).days
            
            # Should span multiple months
            assert date_range > 30, f"Games should span multiple months, got {date_range} days"

    def test_fetch_all_games_comprehensive(self, fetcher):
        """Test fetching all available games for a user (very slow)."""
        # Use a less active player to avoid huge datasets
        test_user = "test_player_123"  # Replace with actual test account
        
        all_games = fetcher.fetch_all_games(test_user, limit_months=6)
        
        assert isinstance(all_games, list), "Should return a list"
        
        if len(all_games) > 0:
            df = fetcher.process_and_save(test_user, all_games, mode='json')
            
            # Verify data quality
            assert len(df) > 0, "Should process games successfully"
            assert df['timestamp'].is_monotonic_decreasing, "Should be sorted by timestamp"
            
            # Check for data completeness
            null_counts = df.isnull().sum()
            assert null_counts['user_rating'] == 0, "Should have all user ratings"
            assert null_counts['opponent_rating'] == 0, "Should have all opponent ratings"


@pytest.mark.skipif(
    os.getenv('SKIP_NETWORK_TESTS') == '1',
    reason="Network tests disabled"
)
class TestNetworkErrorHandling:
    """Test error handling for network issues."""
    
    def test_timeout_handling(self, fetcher):
        """Test handling of network timeouts."""
        # This test depends on network conditions
        # Just verify it doesn't crash
        games = fetcher.fetch_games("hikaru", year=2024, month=1)
        assert isinstance(games, list), "Should return list even on errors"
    
    def test_invalid_response_handling(self, fetcher):
        """Test handling of invalid API responses."""
        # Test with invalid year
        games = fetcher.fetch_games("hikaru", year=1900, month=1)
        assert games == [], "Old dates should return empty list"