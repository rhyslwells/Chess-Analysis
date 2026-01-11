"""
analyzer.py
Computes metrics and statistics from chess game data.
"""

import pandas as pd
import numpy as np

class ChessAnalyzer:
    """Analyzes chess game data and computes performance metrics."""
    
    def __init__(self, df):
        """
        Initialize analyzer with game data.
        
        Args:
            df: DataFrame containing game data
        """
        self.df = df.copy()
        self._compute_derived_features()
    
    def _compute_derived_features(self):
        """Add derived features to the dataframe."""
        # Rating difference
        self.df['rating_diff'] = self.df['user_rating'] - self.df['opponent_rating']
        
        # Opponent strength category
        def categorize_opponent(diff):
            if diff > 50:
                return 'Lower Rated'
            elif diff < -50:
                return 'Higher Rated'
            else:
                return 'Similar Rating'
        
        self.df['opponent_category'] = self.df['rating_diff'].apply(categorize_opponent)
        
        # Convert date to datetime
        self.df['date'] = pd.to_datetime(self.df['date'])
        
        # Game number (chronological order)
        self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        self.df['game_num'] = self.df.index
        
        # Extract move count if moves_san column exists
        if 'moves_san' in self.df.columns:
            self.df['move_count'] = self.df['moves_san'].apply(
                lambda x: len(str(x).split()) if pd.notna(x) else 0
            )
        
        # Result category for analysis
        self.df['result_category'] = self.df['result'].apply(
            lambda s: 'Win' if s == 1 else ('Loss' if s == 0 else 'Draw')
        )
    
    def get_overall_stats(self):
        """Calculate overall performance statistics."""
        total_games = len(self.df)
        wins = (self.df['result'] == 1).sum()
        losses = (self.df['result'] == 0).sum()
        draws = (self.df['result'] == 0.5).sum()
        
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        # Elo progression
        starting_elo = self.df.iloc[0]['user_rating'] if len(self.df) > 0 else 0
        current_elo = self.df.iloc[-1]['user_rating'] if len(self.df) > 0 else 0
        elo_change = current_elo - starting_elo
        
        return {
            'total_games': total_games,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': win_rate,
            'avg_user_rating': self.df['user_rating'].mean(),
            'avg_opponent_rating': self.df['opponent_rating'].mean(),
            'starting_elo': starting_elo,
            'current_elo': current_elo,
            'elo_change': elo_change
        }
    
    def get_performance_by_opponent_strength(self):
        """Analyze performance against different opponent strengths."""
        results = []
        
        for category in ['Lower Rated', 'Similar Rating', 'Higher Rated']:
            subset = self.df[self.df['opponent_category'] == category]
            if len(subset) > 0:
                wins = (subset['result'] == 1).sum()
                total = len(subset)
                win_rate = (wins / total * 100)
                avg_score = subset['result'].mean()
                
                results.append({
                    'category': category,
                    'games': total,
                    'wins': wins,
                    'win_rate': win_rate,
                    'avg_score': avg_score
                })
        
        return pd.DataFrame(results)
    
    def get_fine_grained_rating_performance(self):
        """
        Analyze performance by fine-grained rating differences.
        Shows how win rate varies with small rating gaps.
        """
        bins = [-500, -100, -50, -30, -20, -10, 0, 10, 20, 30, 50, 100, 500]
        labels = ['-100+', '-100', '-50', '-30', '-20', '-10', 'Equal', 
                  '+10', '+20', '+30', '+50', '+100']
        
        self.df['rating_bin_fine'] = pd.cut(
            self.df['rating_diff'], 
            bins=bins, 
            labels=labels
        )
        
        rating_stats = self.df.groupby('rating_bin_fine', observed=True).agg({
            'result': ['count', 'mean']
        }).reset_index()
        
        rating_stats.columns = ['rating_bin', 'games', 'avg_score']
        rating_stats['win_rate'] = rating_stats['avg_score'] * 100
        
        return rating_stats.dropna()
    
    def get_opening_stats(self, top_n=10):
        """Analyze performance by opening."""
        opening_groups = self.df.groupby('opening').agg({
            'result': ['count', 'sum', 'mean']
        }).reset_index()
        
        opening_groups.columns = ['opening', 'games', 'wins', 'win_rate']
        opening_groups['win_rate'] = opening_groups['win_rate'] * 100
        opening_groups = opening_groups.sort_values('games', ascending=False).head(top_n)
        
        return opening_groups
    
    def get_rating_trend(self):
        """Get rating progression over time."""
        trend = self.df.sort_values('timestamp')[['date', 'user_rating']].copy()
        trend['date'] = pd.to_datetime(trend['date'])
        return trend
    
    def get_rating_trend_with_smoothing(self, window=20):
        """
        Get rating progression with smoothed trend line.
        
        Args:
            window: Rolling window size for smoothing
            
        Returns:
            DataFrame with date, rating, and smoothed rating
        """
        trend = self.df.sort_values('timestamp')[['date', 'user_rating']].copy()
        trend['date'] = pd.to_datetime(trend['date'])
        trend['elo_smooth'] = trend['user_rating'].rolling(
            window=window, 
            center=True,
            min_periods=1
        ).mean()
        return trend
    
    def get_rating_volatility(self):
        """
        Calculate rating volatility (standard deviation of rating changes).
        
        Returns:
            Dictionary with volatility metrics
        """
        df_sorted = self.df.sort_values('timestamp').copy()
        df_sorted['rating_change'] = df_sorted['user_rating'].diff()
        
        volatility = df_sorted['rating_change'].std()
        avg_change = df_sorted['rating_change'].abs().mean()
        max_gain = df_sorted['rating_change'].max()
        max_loss = df_sorted['rating_change'].min()
        
        return {
            'volatility': volatility,
            'avg_rating_change': avg_change,
            'max_rating_gain': max_gain,
            'max_rating_loss': max_loss
        }
    


    def get_peaks_and_troughs(self):
        """
        Identify local peaks and troughs in rating progression.
        
        Returns:
            Tuple of (peaks_df, troughs_df)
        """
        df_sorted = self.df.sort_values('timestamp').copy()
        
        df_sorted['peak'] = (
            (df_sorted['user_rating'] > df_sorted['user_rating'].shift(1)) & 
            (df_sorted['user_rating'] > df_sorted['user_rating'].shift(-1))
        )
        
        df_sorted['trough'] = (
            (df_sorted['user_rating'] < df_sorted['user_rating'].shift(1)) & 
            (df_sorted['user_rating'] < df_sorted['user_rating'].shift(-1))
        )
        
        peaks = df_sorted[df_sorted['peak']][['date', 'user_rating', 'game_num']]
        troughs = df_sorted[df_sorted['trough']][['date', 'user_rating', 'game_num']]
        
        return peaks, troughs
    
    def get_results_over_time(self, period='M'):
        """
        Get win/loss/draw counts over time periods.
        
        Args:
            period: Pandas frequency string ('D', 'W', 'M')
        """
        df_time = self.df.copy()
        df_time = df_time.set_index('date')
        
        # Group by result type
        wins = df_time[df_time['result'] == 1].resample(period).size()
        losses = df_time[df_time['result'] == 0].resample(period).size()
        draws = df_time[df_time['result'] == 0.5].resample(period).size()
        
        results_df = pd.DataFrame({
            'Wins': wins,
            'Losses': losses,
            'Draws': draws
        }).fillna(0)
        
        return results_df
    
    def get_rolling_win_rate(self, window=20):
        """
        Calculate rolling win rate over time.
        
        Args:
            window: Number of games for rolling window
            
        Returns:
            Series with rolling win rate
        """
        df_sorted = self.df.sort_values('timestamp').copy()
        rolling_wr = df_sorted['result'].rolling(
            window=window, 
            min_periods=1
        ).mean()
        
        return pd.DataFrame({
            'game_num': df_sorted['game_num'],
            'date': df_sorted['date'],
            'user_rating': df_sorted['user_rating'],
            'rolling_win_rate': rolling_wr
        })
    
    def get_rolling_performance_by_rating(self, window=20):
        """
        Get rolling win rate split by opponent strength.
        
        Args:
            window: Number of games for rolling window
            
        Returns:
            DataFrame with rolling performance vs higher/lower rated opponents
        """
        df_sorted = self.df.sort_values('timestamp').copy()
        
        # Create scores only for specific opponent categories
        df_sorted['score_vs_higher'] = df_sorted.apply(
            lambda r: r['result'] if r['rating_diff'] < 0 else np.nan,
            axis=1
        )
        df_sorted['score_vs_lower'] = df_sorted.apply(
            lambda r: r['result'] if r['rating_diff'] > 0 else np.nan,
            axis=1
        )
        
        rolling_higher = df_sorted['score_vs_higher'].rolling(
            window=window, 
            min_periods=1
        ).mean()
        rolling_lower = df_sorted['score_vs_lower'].rolling(
            window=window, 
            min_periods=1
        ).mean()
        
        return pd.DataFrame({
            'game_num': df_sorted['game_num'],
            'date': df_sorted['date'],
            'vs_higher_rated': rolling_higher,
            'vs_lower_rated': rolling_lower
        })
    
    def get_color_performance(self):
        """Analyze performance by color (white vs black)."""
        color_stats = []
        
        for color in ['white', 'black']:
            subset = self.df[self.df['user_color'] == color]
            if len(subset) > 0:
                wins = (subset['result'] == 1).sum()
                total = len(subset)
                win_rate = (wins / total * 100)
                avg_score = subset['result'].mean()
                
                color_stats.append({
                    'color': color.capitalize(),
                    'games': total,
                    'wins': wins,
                    'win_rate': win_rate,
                    'avg_score': avg_score
                })
        
        return pd.DataFrame(color_stats)
    
    def get_time_control_stats(self):
        """Analyze performance by time control."""
        tc_groups = self.df.groupby('time_control').agg({
            'result': ['count', 'sum', 'mean']
        }).reset_index()
        
        tc_groups.columns = ['time_control', 'games', 'wins', 'win_rate']
        tc_groups['win_rate'] = tc_groups['win_rate'] * 100
        tc_groups = tc_groups.sort_values('games', ascending=False)
        
        return tc_groups
    
    def get_game_length_stats(self):
        """
        Analyze game length statistics if move data is available.
        
        Returns:
            Dictionary with game length metrics and correlation with results
        """
        if 'move_count' not in self.df.columns:
            return None
        
        stats = {
            'avg_game_length': self.df['move_count'].mean(),
            'median_game_length': self.df['move_count'].median(),
            'shortest_game': self.df['move_count'].min(),
            'longest_game': self.df['move_count'].max(),
            'length_score_correlation': self.df['move_count'].corr(self.df['result'])
        }
        
        return stats
    
    def get_game_length_by_result(self):
        """
        Analyze average game length by result category.
        
        Returns:
            DataFrame with game length statistics by result
        """
        if 'move_count' not in self.df.columns:
            return None
        
        length_stats = self.df.groupby('result_category')['move_count'].agg([
            'count', 'mean', 'median', 'std'
        ]).reset_index()
        
        length_stats.columns = ['result', 'games', 'avg_length', 'median_length', 'std_length']
        
        return length_stats
    
    def get_recent_games(self, n=10):
        """Get the most recent n games."""
        return self.df.sort_values('timestamp', ascending=False).head(n)
    
    def prepare_ml_features(self):
        """
        Prepare features for machine learning model.
        
        Returns:
            X: Feature matrix
            y: Target vector (1 for win, 0 for loss/draw)
        """
        # Binary classification: win vs not-win
        y = (self.df['result'] == 1).astype(int)
        
        # Features
        features = pd.DataFrame({
            'user_rating': self.df['user_rating'],
            'opponent_rating': self.df['opponent_rating'],
            'rating_diff': self.df['rating_diff'],
            'is_white': (self.df['user_color'] == 'white').astype(int)
        })
        
        return features, y