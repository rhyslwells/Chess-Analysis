"""
predictor.py
Machine learning model for predicting game outcomes.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
from pathlib import Path

class ChessPredictor:
    """Predicts win probability based on historical game data."""
    
    def __init__(self, model_dir="models"):
        """Initialize predictor with model directory."""
        self.model = None
        # self.model_dir = Path(model_dir)
        # self.model_dir.mkdir(exist_ok=True)
        self.is_trained = False
        
    def train(self, X, y, test_size=0.2):
        """
        Train logistic regression model.
        
        Args:
            X: Feature matrix (DataFrame or array)
            y: Target vector (win=1, loss/draw=0)
            test_size: Proportion of data for testing
            
        Returns:
            Dictionary with training metrics
        """
        if len(X) < 20:
            print("Warning: Less than 20 games available. Model may not be reliable.")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        
        # Train model
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)
        
        metrics = {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'feature_names': X.columns.tolist() if hasattr(X, 'columns') else None
        }
        
        return metrics
    
    def predict_win_probability(self, user_rating, opponent_rating, is_white=True):
        """
        Predict probability of winning given ratings and color.
        
        Args:
            user_rating: User's rating
            opponent_rating: Opponent's rating
            is_white: Whether user plays as white
            
        Returns:
            Probability of winning (0-1)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        rating_diff = user_rating - opponent_rating
        features = pd.DataFrame({
            'user_rating': [user_rating],
            'opponent_rating': [opponent_rating],
            'rating_diff': [rating_diff],
            'is_white': [1 if is_white else 0]
        })
        
        prob = self.model.predict_proba(features)[0, 1]
        return prob
    
    def get_win_probability_curve(self, user_rating, rating_range=None, is_white=True):
        """
        Generate win probability curve across opponent ratings.
        
        Args:
            user_rating: User's current rating
            rating_range: Tuple of (min_rating, max_rating), or None for auto
            is_white: Whether user plays as white
            
        Returns:
            DataFrame with opponent ratings and win probabilities
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before generating curves")
        
        if rating_range is None:
            rating_range = (user_rating - 400, user_rating + 400)
        
        opponent_ratings = np.arange(rating_range[0], rating_range[1] + 1, 25)
        probabilities = []
        
        for opp_rating in opponent_ratings:
            prob = self.predict_win_probability(user_rating, opp_rating, is_white)
            probabilities.append(prob)
        
        return pd.DataFrame({
            'opponent_rating': opponent_ratings,
            'win_probability': probabilities
        })
    
    # def save_model(self, username):
    #     """Save trained model to disk."""
    #     if not self.is_trained:
    #         raise ValueError("No trained model to save")
        
    #     model_path = self.model_dir / f"{username}_model.pkl"
    #     with open(model_path, 'wb') as f:
    #         pickle.dump(self.model, f)
    #     print(f"Model saved to {model_path}")
    
    # def load_model(self, username):
    #     """Load trained model from disk."""
    #     model_path = self.model_dir / f"{username}_model.pkl"
    #     if not model_path.exists():
    #         raise FileNotFoundError(f"No saved model found for {username}")
        
    #     with open(model_path, 'rb') as f:
    #         self.model = pickle.load(f)
    #     self.is_trained = True
    #     print(f"Model loaded from {model_path}")
    
    def get_feature_importance(self):
        """Get feature coefficients from logistic regression."""
        if not self.is_trained:
            return None
        
        coefficients = self.model.coef_[0]
        feature_names = ['user_rating', 'opponent_rating', 'rating_diff', 'is_white']
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'coefficient': coefficients,
            'abs_coefficient': np.abs(coefficients)
        }).sort_values('abs_coefficient', ascending=False)
        
        return importance_df
    