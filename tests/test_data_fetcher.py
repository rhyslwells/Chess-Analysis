"""
test_data_fetcher.py
Unit tests for ChessDataFetcher class with mocked API responses.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
import io
from src.data_fetcher import ChessDataFetcher


@pytest.fixture
def fetcher():
    """Fixture to create a ChessDataFetcher instance."""
    return ChessDataFetcher()


@pytest.fixture
def sample_game_json():
    """Fixture providing a sample game in Chess.com API JSON format."""
    return {
        'white': {
            'username': 'testuser',
            'rating': 1500,
            'result': 'win'
        },
        'black': {
            'username': 'opponent123',
            'rating': 1480,
            'result': 'checkmated'
        },
        'end_time': 1704067200,  # 2024-01-01 00:00:00 UTC
        'time_class': 'rapid',
        'url': 'https://chess.com/game/12345',
        'pgn': '''[Event "Live Chess"]
[Site "Chess.com"]
[Date "2024.01.01"]
[Round "-"]
[White "testuser"]
[Black "opponent123"]
[Result "1-0"]
[ECO "C41"]
[ECOUrl "https://www.chess.com/openings/Philidor-Defense"]
[Opening "Philidor Defense"]
[WhiteElo "1500"]
[BlackElo "1480"]
[TimeControl "600"]
[EndDate "2024.01.01"]
[EndTime "00:15:00"]
[StartTime "00:00:00"]
[Termination "testuser won by checkmate"]

1. e4 e5 2. Nf3 d6 1-0'''
    }


@pytest.fixture
def sample_pgn_text():
    """Fixture providing sample PGN text."""
    return '''[Event "Live Chess"]
[Site "Chess.com"]
[Date "2024.01.01"]
[White "testuser"]
[Black "opponent456"]
[Result "0-1"]
[WhiteElo "1500"]
[BlackElo "1520"]
[ECO "B20"]
[Opening "Sicilian Defense"]
[TimeControl "180+2"]
[Termination "testuser won on time"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 0-1'''


class TestChessDataFetcher:
    """Test suite for ChessDataFetcher class."""

    # -------------------------------------------------------------------------
    # API Fetching Tests
    # -------------------------------------------------------------------------

    @patch('src.data_fetcher.requests.get')
    def test_fetch_games_success(self, mock_get, fetcher):
        """Test successful game fetching from API."""
        mock_response = Mock()
        mock_response.json.return_value = {'games': [{'id': 1}, {'id': 2}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        games = fetcher.fetch_games('testuser', 2024, 1)

        assert len(games) == 2
        assert games[0]['id'] == 1
        mock_get.assert_called_once()

    @patch('src.data_fetcher.requests.get')
    def test_fetch_games_api_error(self, mock_get, fetcher):
        """Test handling of API errors."""
        mock_get.side_effect = Exception("API Error")

        games = fetcher.fetch_games('testuser', 2024, 1)

        assert games == []

    @patch('src.data_fetcher.requests.get')
    @patch('src.data_fetcher.time.sleep')
    def test_fetch_multiple_months(self, mock_sleep, mock_get, fetcher):
        """Test fetching games across multiple months."""
        mock_response = Mock()
        mock_response.json.return_value = {'games': [{'id': 1}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 15)

        games = fetcher.fetch_multiple_months('testuser', start_date, end_date)

        # Should fetch for Jan, Feb, Mar (3 months)
        assert mock_get.call_count == 3
        assert len(games) == 3

    # -------------------------------------------------------------------------
    # JSON Parsing Tests
    # -------------------------------------------------------------------------

    def test_parse_game_from_json_white_win(self, fetcher, sample_game_json):
        """Test parsing a game where user plays white and wins."""
        result = fetcher.parse_game_from_json(sample_game_json, 'testuser')

        assert result['user_color'] == 'white'
        assert result['user_rating'] == 1500
        assert result['opponent'] == 'opponent123'
        assert result['opponent_rating'] == 1480
        assert result['result'] == 1
        assert result['result_label'] == 'Win'
        assert result['opening'] == 'Philidor Defense'
        assert result['eco'] == 'C41'
        assert result['time_control'] == 'rapid'
        assert result['game_duration_seconds'] == 900  # 15 minutes

    def test_parse_game_from_json_black_loss(self, fetcher, sample_game_json):
        """Test parsing a game where user plays black and loses."""
        result = fetcher.parse_game_from_json(sample_game_json, 'opponent123')

        assert result['user_color'] == 'black'
        assert result['user_rating'] == 1480
        assert result['opponent'] == 'testuser'
        assert result['opponent_rating'] == 1500
        assert result['result'] == 0
        assert result['result_label'] == 'Loss'

    def test_parse_game_from_json_draw(self, fetcher):
        """Test parsing a game that ends in a draw."""
        game_json = {
            'white': {'username': 'user1', 'rating': 1500, 'result': 'stalemate'},
            'black': {'username': 'user2', 'rating': 1500, 'result': 'stalemate'},
            'end_time': 1704067200,
            'time_class': 'blitz',
            'url': 'https://chess.com/game/12345',
            'pgn': '[Result "1/2-1/2"]'
        }

        result = fetcher.parse_game_from_json(game_json, 'user1')

        assert result['result'] == 0.5
        assert result['result_label'] == 'Draw'

    def test_parse_game_from_json_missing_pgn(self, fetcher):
        """Test parsing when PGN data is missing."""
        game_json = {
            'white': {'username': 'testuser', 'rating': 1500, 'result': 'win'},
            'black': {'username': 'opponent', 'rating': 1480, 'result': 'resigned'},
            'end_time': 1704067200,
            'time_class': 'rapid',
            'url': 'https://chess.com/game/12345'
        }

        result = fetcher.parse_game_from_json(game_json, 'testuser')

        assert result['opening'] == 'Unknown'
        assert result['eco'] == ''
        assert result['game_duration_seconds'] is None

    # -------------------------------------------------------------------------
    # PGN Parsing Tests
    # -------------------------------------------------------------------------

    @patch('chess.pgn.read_game')
    def test_parse_game_from_pgn(self, mock_read_game, fetcher, sample_pgn_text):
        """Test parsing a PGN game object."""
        # Create a real chess.pgn.Game object from the sample text
        import chess.pgn
        game = chess.pgn.read_game(io.StringIO(sample_pgn_text))
        
        result = fetcher.parse_game_from_pgn(game, 'testuser')

        assert result['user_color'] == 'white'
        assert result['opponent'] == 'opponent456'
        assert result['result_label'] == 'Loss'
        assert result['opening'] == 'Sicilian Defense'
        assert 'e4' in result['moves_san']

    @patch('builtins.open', new_callable=mock_open)
    @patch('chess.pgn.read_game')
    def test_pgn_to_dataframe(self, mock_read_game, mock_file, fetcher):
        """Test converting PGN file to DataFrame."""
        import chess.pgn
        
        # Create two sample games
        pgn1 = '''[White "testuser"]
[Black "opp1"]
[Result "1-0"]
[WhiteElo "1500"]
[BlackElo "1480"]
[Date "2024.01.01"]

1. e4 e5 1-0'''
        
        pgn2 = '''[White "opp2"]
[Black "testuser"]
[Result "0-1"]
[WhiteElo "1520"]
[BlackElo "1500"]
[Date "2024.01.02"]

1. d4 d5 0-1'''
        
        game1 = chess.pgn.read_game(io.StringIO(pgn1))
        game2 = chess.pgn.read_game(io.StringIO(pgn2))
        
        # Mock read_game to return our games then None
        mock_read_game.side_effect = [game1, game2, None]
        
        df = fetcher.pgn_to_dataframe('dummy_path.pgn', 'testuser')
        
        assert len(df) == 2
        assert df.iloc[0]['user_color'] == 'white'
        assert df.iloc[1]['user_color'] == 'black'

    # -------------------------------------------------------------------------
    # Data Processing Tests
    # -------------------------------------------------------------------------

    def test_process_and_save_json_mode(self, fetcher, sample_game_json):
        """Test processing and saving games in JSON mode."""
        games = [sample_game_json]
        
        df = fetcher.process_and_save('testuser', games, mode='json')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'user_rating' in df.columns
        assert 'opponent_rating' in df.columns
        assert 'result' in df.columns

    def test_process_and_save_removes_duplicates(self, fetcher, sample_game_json):
        """Test that duplicate games are removed."""
        # Create duplicate games
        games = [sample_game_json, sample_game_json.copy()]
        
        df = fetcher.process_and_save('testuser', games, mode='json')
        
        # Should only have 1 game after deduplication
        assert len(df) == 1

    def test_process_and_save_sorts_by_timestamp(self, fetcher):
        """Test that games are sorted by timestamp in descending order."""
        game1 = {
            'white': {'username': 'testuser', 'rating': 1500, 'result': 'win'},
            'black': {'username': 'opp1', 'rating': 1480, 'result': 'checkmated'},
            'end_time': 1704067200,  # Earlier
            'time_class': 'rapid',
            'url': 'https://chess.com/game/1',
            'pgn': ''
        }
        
        game2 = {
            'white': {'username': 'testuser', 'rating': 1505, 'result': 'win'},
            'black': {'username': 'opp2', 'rating': 1490, 'result': 'resigned'},
            'end_time': 1704153600,  # Later
            'time_class': 'rapid',
            'url': 'https://chess.com/game/2',
            'pgn': ''
        }
        
        games = [game1, game2]
        df = fetcher.process_and_save('testuser', games, mode='json')
        
        # Most recent game should be first
        assert df.iloc[0]['timestamp'] == 1704153600
        assert df.iloc[1]['timestamp'] == 1704067200

    # -------------------------------------------------------------------------
    # Edge Cases
    # -------------------------------------------------------------------------

    def test_parse_game_with_timeout_result(self, fetcher):
        """Test parsing a game lost on time."""
        game_json = {
            'white': {'username': 'testuser', 'rating': 1500, 'result': 'timeout'},
            'black': {'username': 'opponent', 'rating': 1480, 'result': 'win'},
            'end_time': 1704067200,
            'time_class': 'blitz',
            'url': 'https://chess.com/game/12345',
            'pgn': ''
        }

        result = fetcher.parse_game_from_json(game_json, 'testuser')

        assert result['result'] == 0
        assert result['result_label'] == 'Loss'

    def test_parse_game_with_abandoned_result(self, fetcher):
        """Test parsing an abandoned game."""
        game_json = {
            'white': {'username': 'testuser', 'rating': 1500, 'result': 'abandoned'},
            'black': {'username': 'opponent', 'rating': 1480, 'result': 'win'},
            'end_time': 1704067200,
            'time_class': 'rapid',
            'url': 'https://chess.com/game/12345',
            'pgn': ''
        }

        result = fetcher.parse_game_from_json(game_json, 'testuser')

        assert result['result'] == 0
        assert result['result_label'] == 'Loss'

    def test_eco_url_fallback(self, fetcher):
        """Test opening name extraction from ECO URL when Opening header is missing."""
        game_json = {
            'white': {'username': 'testuser', 'rating': 1500, 'result': 'win'},
            'black': {'username': 'opponent', 'rating': 1480, 'result': 'checkmated'},
            'end_time': 1704067200,
            'time_class': 'rapid',
            'url': 'https://chess.com/game/12345',
            'pgn': '''[ECO "B20"]
[ECOUrl "https://www.chess.com/openings/sicilian-defense-alapin-variation"]
[Result "1-0"]'''
        }

        result = fetcher.parse_game_from_json(game_json, 'testuser')

        assert result['opening'] == 'Sicilian Defense Alapin Variation'