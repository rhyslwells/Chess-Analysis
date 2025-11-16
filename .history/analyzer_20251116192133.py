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
            if diff > 100:
                return 'Lower Rated'
            elif diff < -100:
                return 'Higher Rated'
            else:
                return 'Similar Rating'
        
        self.df['opponent_category'] = self.df['rating_diff'].apply(categorize_opponent)
        
        # Convert date to datetime
        self.df['date'] = pd.to_datetime(self.df['date'])
    
    def get_overall_stats(self):
        """Calculate overall performance statistics."""
        total_games = len(self.df)
        wins = (self.df['result'] == 1).sum()
        losses = (self.df['result'] == 0).sum()
        draws = (self.df['result'] == 0.5).sum()
        
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        return {
            'total_games': total_games,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': win_rate,
            'avg_user_rating': self.df['user_rating'].mean(),
            'avg_opponent_rating': self.df['opponent_rating'].mean()
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
                
                results.append({
                    'category': category,
                    'games': total,
                    'wins': wins,
                    'win_rate': win_rate
                })
        
        return pd.DataFrame(results)
    
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
    
    def get_color_performance(self):
        """Analyze performance by color (white vs black)."""
        color_stats = []
        
        for color in ['white', 'black']:
            subset = self.df[self.df['user_color'] == color]
            if len(subset) > 0:
                wins = (subset['result'] == 1).sum()
                total = len(subset)
                win_rate = (wins / total * 100)
                
                color_stats.append({
                    'color': color.capitalize(),
                    'games': total,
                    'wins': wins,
                    'win_rate': win_rate
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