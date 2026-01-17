"""
data_fetcher.py
Handles fetching game data from Chess.com API and storing it locally.
"""

import requests
import chess.pgn
import io
import pandas as pd
from datetime import datetime
import time

class ChessDataFetcher:
    """Fetches and processes chess game data from Chess.com API."""

    BASE_URL = "https://api.chess.com/pub/player"
    HEADERS = {
        "User-Agent": "Chess Analysis Dashboard (Python/requests)"
    }

    def __init__(self):
        self.invalid_duration_count = 0
        self.duration_validation_log = []


    def get_available_archives(self, username):
        """
        Fetch the list of all available monthly game archives for a user.
        
        Returns:
            List of archive URLs (e.g., ['https://api.chess.com/pub/player/username/games/2025/01', ...])
        """
        url = f"{self.BASE_URL}/{username}/games/archives"
        try:
            print(f"Fetching archive list for {username}...")
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            archives = data.get('archives', [])
            print(f"Found {len(archives)} available monthly archives")
            if archives:
                print(f"Earliest archive: {archives[0]}")
                print(f"Latest archive: {archives[-1]}")
            return archives
        except requests.exceptions.RequestException as e:
            print(f"Error fetching archive list: {e}")
            return []


    def fetch_games_from_archive_url(self, archive_url):
        """
        Fetch games directly from a Chess.com archive URL.
        
        Args:
            archive_url: Full URL to a monthly archive
            
        Returns:
            List of game dictionaries
        """
        try:
            print(f"Fetching games from archive: {archive_url}")
            response = requests.get(archive_url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            games = data.get('games', [])
            print(f"Retrieved {len(games)} games from archive")
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching games from {archive_url}: {e}")
            return []


    def fetch_all_games(self, username, limit_months=None):
        """
        Fetch ALL available games for a username by querying the archive list.
        
        Args:
            username: Chess.com username
            limit_months: Optional limit to only fetch the N most recent months
            
        Returns:
            List of all games across all available monthly archives
        """
        archives = self.get_available_archives(username)
        
        if not archives:
            print("No archives found for user")
            return []
        
        # Optionally limit to recent months only
        if limit_months and limit_months > 0:
            archives = archives[-limit_months:]
            print(f"Limited to most recent {limit_months} months")
        
        all_games = []
        for i, archive_url in enumerate(archives, 1):
            print(f"Processing archive {i}/{len(archives)}")
            games = self.fetch_games_from_archive_url(archive_url)
            all_games.extend(games)
            
            # Rate limiting
            if i < len(archives):
                time.sleep(0.5)
        
        print(f"Total games fetched: {len(all_games)}")
        return all_games


    # ----------------------------
    # Fetching games from API
    # ----------------------------
    def fetch_games(self, username, year=None, month=None):
        """Fetch games for a username from Chess.com API for a given month."""
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month

        url = f"{self.BASE_URL}/{username}/games/{year}/{month:02d}"
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('games', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching games: {e}")
            return []


    def fetch_multiple_months(self, username, start_date, end_date):
        """Fetch games across multiple months."""
        all_games = []
        current = start_date

        while current <= end_date:
            print(f"Fetching games for {current.year}-{current.month:02d}...")
            games = self.fetch_games(username, current.year, current.month)
            all_games.extend(games)

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

            time.sleep(0.5)  # Rate limiting

        return all_games

    def get_current_elo(self, username: str, time_control: str = "blitz") -> int | None:
        """
        Fetch current Elo for a given username and time control.
        Returns None if not available.
        """
        url = f"https://api.chess.com/pub/player/{username}/stats"
        headers = {
            "User-Agent": "Chess Analysis Dashboard (Python/requests)"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            stats = response.json()

            control_map = {
                "bullet": "chess_bullet",
                "blitz": "chess_blitz",
                "rapid": "chess_rapid",
                "daily": "chess_daily"
            }

            key = control_map.get(time_control.strip().lower())
            if not key:
                return None

            last_rating_info = stats.get(key, {}).get("last")
            if not last_rating_info:
                return None

            rating = last_rating_info.get("rating")
            return rating

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Elo for {username}: {e}")
            return None


    def _validate_game_duration(self, duration_seconds, game_url='', opponent=''):
        """
        Validate that game duration is non-negative and within reasonable bounds.
        
        Args:
            duration_seconds: Calculated game duration in seconds
            game_url: URL of the game (for logging)
            opponent: Opponent username (for logging)
            
        Returns:
            Validated duration in seconds, or None if invalid
        """
        if duration_seconds is None:
            return None
            
        # Check for negative duration
        if duration_seconds < 0:
            self.invalid_duration_count += 1
            log_entry = {
                'reason': 'negative_duration',
                'duration': duration_seconds,
                'game_url': game_url,
                'opponent': opponent
            }
            self.duration_validation_log.append(log_entry)
            print(f"Invalid game duration: {duration_seconds}s (negative) - Game URL: {game_url}")
            return None
        
        # Check for unreasonably long games (e.g., > 24 hours = 86400 seconds)
        # This catches timezone issues or date calculation errors
        MAX_REASONABLE_DURATION = 86400  # 24 hours
        if duration_seconds > MAX_REASONABLE_DURATION:
            self.invalid_duration_count += 1
            log_entry = {
                'reason': 'unreasonably_long',
                'duration': duration_seconds,
                'game_url': game_url,
                'opponent': opponent
            }
            self.duration_validation_log.append(log_entry)
            print(f"Invalid game duration: {duration_seconds}s (>{MAX_REASONABLE_DURATION}s) - Game URL: {game_url}")
            return None
            
        return duration_seconds


    # ----------------------------
    # PGN parsing
    # ----------------------------

    def parse_game_from_json(self, game_data, username):
        """
        Parse a single game from JSON API response into structured format.
        """

        # --- Determine user color ---
        white_player = game_data['white']['username'].lower()
        black_player = game_data['black']['username'].lower()
        user_color = 'white' if white_player == username.lower() else 'black'
        opponent_color = 'black' if user_color == 'white' else 'white'

        # --- Ratings ---
        user_rating = game_data[user_color]['rating']
        opponent_rating = game_data[opponent_color]['rating']
        opponent_username = game_data[opponent_color]['username']

        # --- Result ---
        result_str = game_data[user_color].get('result', 'unknown')
        if result_str == 'win':
            result = 1
            result_label = 'Win'
        elif result_str in ['checkmated', 'resigned', 'timeout', 'abandoned']:
            result = 0
            result_label = 'Loss'
        else:
            result = 0.5
            result_label = 'Draw'

        # --- PGN parsing ---
        pgn_text = game_data.get('pgn', '')
        opening = 'Unknown'
        eco = ''
        eco_url = 'https://www.chess.com/openings/Undefined'
        game_duration_seconds = None

        try:
            game = chess.pgn.read_game(io.StringIO(pgn_text))
            if game:
                headers = game.headers

                eco = headers.get('ECO', '')
                eco_url = headers.get(
                    'ECOUrl',
                    'https://www.chess.com/openings/Undefined'
                )

                # Opening resolution logic (DO NOT overwrite blindly)
                if 'Opening' in headers and headers['Opening'].strip():
                    opening = headers['Opening']
                elif eco_url:
                    opening = (
                        eco_url
                        .rstrip('/')
                        .split('/')[-1]
                        .replace('-', ' ')
                        .title()
                    )

                # --- Time calculation with improved validation ---
                start_time_str = headers.get('StartTime')   # HH:MM:SS
                end_date_str = headers.get('EndDate')       # YYYY.MM.DD
                end_time_str = headers.get('EndTime')       # HH:MM:SS (optional)
                start_date_str = headers.get('StartDate')   # YYYY.MM.DD (if available)

                if start_time_str and end_date_str:
                    try:
                        # Use StartDate if available, otherwise assume same as EndDate
                        if start_date_str:
                            start_dt = datetime.strptime(
                                f"{start_date_str} {start_time_str}",
                                "%Y.%m.%d %H:%M:%S"
                            )
                        else:
                            # Assume game started on same date as it ended
                            start_dt = datetime.strptime(
                                f"{end_date_str} {start_time_str}",
                                "%Y.%m.%d %H:%M:%S"
                            )

                        if end_time_str:
                            end_dt = datetime.strptime(
                                f"{end_date_str} {end_time_str}",
                                "%Y.%m.%d %H:%M:%S"
                            )
                        else:
                            # Fallback to API end_time
                            end_dt = datetime.fromtimestamp(game_data['end_time'])

                        # Calculate duration
                        raw_duration = int((end_dt - start_dt).total_seconds())
                        
                        # Handle midnight crossing: if duration is negative but small,
                        # the game likely crossed midnight
                        if raw_duration < 0 and raw_duration > -3600:
                            # Add 24 hours worth of seconds
                            raw_duration += 86400
                        
                        # Validate the duration
                        game_duration_seconds = self._validate_game_duration(
                            raw_duration,
                            game_url=game_data.get('url', ''),
                            opponent=opponent_username
                        )
                        
                    except ValueError as e:
                        print(f"Date parsing error for game vs {opponent_username}: {e}")
                        game_duration_seconds = None

        except Exception as e:
            print(f"PGN parsing error: {e}")


        # --- Timestamp ---
        end_time = datetime.fromtimestamp(game_data['end_time'])

        return {
            'date': end_time.strftime('%Y-%m-%d'),
            'timestamp': game_data['end_time'],
            'user_color': user_color,
            'user_rating': user_rating,
            'opponent': opponent_username,
            'opponent_rating': opponent_rating,
            'result': result,
            'result_label': result_label,
            'opening': opening,
            'eco': eco,
            'eco_url': eco_url,
            'time_control': game_data.get('time_class', 'unknown'),
            'game_url': game_data.get('url', ''),
            'game_duration_seconds': game_duration_seconds,
            'pgn': pgn_text,
        }

       
    def parse_game_from_pgn(self, game, username):
        """
        Parse a chess.pgn.Game object into structured format.
        
        Args:
            game: chess.pgn.Game object
            username: User's chess.com username
            
        Returns:
            Dictionary with parsed game information
        """
        headers = game.headers
        
        # Determine user color
        white_player = headers.get('White', '').lower()
        black_player = headers.get('Black', '').lower()
        user_color = 'white' if white_player == username.lower() else 'black'
        opponent_color = 'black' if user_color == 'white' else 'white'
        
        # Get ratings
        user_rating = int(headers.get('WhiteElo' if user_color == 'white' else 'BlackElo', 0))
        opponent_rating = int(headers.get('BlackElo' if user_color == 'white' else 'WhiteElo', 0))
        opponent_username = headers.get('Black' if user_color == 'white' else 'White', 'Unknown')
        
        # Determine result from user perspective
        result_str = headers.get('Result', '*')
        if result_str == '1-0':
            result = 1 if user_color == 'white' else 0
            result_label = 'Win' if user_color == 'white' else 'Loss'
        elif result_str == '0-1':
            result = 0 if user_color == 'white' else 1
            result_label = 'Loss' if user_color == 'white' else 'Win'
        elif result_str == '1/2-1/2':
            result = 0.5
            result_label = 'Draw'
        else:
            result = 0.5
            result_label = 'Unknown'
        
        # Extract moves in SAN notation
        moves = []
        board = game.board()
        node = game
        while node.variations:
            next_node = node.variation(0)
            san = board.san(next_node.move)
            moves.append(san)
            board.push(next_node.move)
            node = next_node
        
        # Parse date
        date_str = headers.get('UTCDate', headers.get('Date', ''))
        try:
            date_obj = datetime.strptime(date_str, '%Y.%m.%d')
            timestamp = int(date_obj.timestamp())
            date_formatted = date_obj.strftime('%Y-%m-%d')
        except:
            timestamp = 0
            date_formatted = date_str
        
        return {
            'date': date_formatted,
            'timestamp': timestamp,
            'user_color': user_color,
            'user_rating': user_rating,
            'opponent': opponent_username,
            'opponent_rating': opponent_rating,
            'result': result,
            'result_label': result_label,
            'opening': headers.get('Opening', 'Unknown'),
            'eco': headers.get('ECO', ''),
            'time_control': headers.get('TimeControl', 'unknown'),
            'game_url': headers.get('Link', ''),
            'termination': headers.get('Termination', ''),
            'moves_san': ' '.join(moves)
        }
    

    def pgn_to_dataframe(self, pgn_path, username):
        """Convert a PGN file to a pandas DataFrame."""
        records = []
        with open(pgn_path, 'r', encoding='utf-8') as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                record = self.parse_game_from_pgn(game, username)
                records.append(record)
        return pd.DataFrame(records)

    # ----------------------------
    # Process and save
    # ----------------------------
    def process_and_save(self, username, games, mode='json'):
        """
        Process games and save to CSV.
        
        Args:
            username: Chess.com username
            games: List of raw game data (JSON) or path to PGN file
            mode: 'json' for API data or 'pgn' for PGN file
            
        Returns:
            DataFrame of processed games
        """
        # Reset validation counters
        self.invalid_duration_count = 0
        self.duration_validation_log = []
        
        if mode == 'pgn':
            # games should be a path to PGN file
            df = self.pgn_to_dataframe(games, username)
        else:
            # games is a list of JSON game objects
            processed_games = [self.parse_game_from_json(game, username) for game in games]
            df = pd.DataFrame(processed_games)
        
        # Sort by date
        df = df.sort_values('timestamp', ascending=False)
        
        # Remove duplicates based on timestamp and opponent
        initial_count = len(df)
        df = df.drop_duplicates(subset=['timestamp', 'opponent'], keep='first')
        duplicates_removed = initial_count - len(df)
        
        # Filter out games with invalid (None) durations
        if 'game_duration_seconds' in df.columns:
            games_before_filter = len(df)
            df = df[df['game_duration_seconds'].notna()]
            invalid_games_removed = games_before_filter - len(df)
            
            # Log validation summary
            if self.invalid_duration_count > 0 or invalid_games_removed > 0:
                print(f"\n{'='*60}")
                print(f"GAME DURATION VALIDATION SUMMARY")
                print(f"{'='*60}")
                print(f"Games with invalid durations detected: {self.invalid_duration_count}")
                print(f"Games removed from dataset: {invalid_games_removed}")
                print(f"Duplicates removed: {duplicates_removed}")
                print(f"Final valid games: {len(df)}")
                
                if self.duration_validation_log:
                    print(f"\nInvalid duration breakdown:")
                    negative_count = sum(1 for log in self.duration_validation_log if log['reason'] == 'negative_duration')
                    long_count = sum(1 for log in self.duration_validation_log if log['reason'] == 'unreasonably_long')
                    if negative_count > 0:
                        print(f"  - Negative durations: {negative_count}")
                    if long_count > 0:
                        print(f"  - Unreasonably long (>24h): {long_count}")
                print(f"{'='*60}\n")
        
        return df
    
    def get_validation_report(self):
        """
        Get a detailed report of all validation issues encountered.
        
        Returns:
            Dictionary containing validation statistics and log entries
        """
        return {
            'total_invalid': self.invalid_duration_count,
            'validation_log': self.duration_validation_log,
            'negative_durations': sum(1 for log in self.duration_validation_log if log['reason'] == 'negative_duration'),
            'unreasonably_long': sum(1 for log in self.duration_validation_log if log['reason'] == 'unreasonably_long')
        }