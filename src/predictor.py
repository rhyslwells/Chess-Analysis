"""
predictor.py
Machine learning model for predicting game outcomes.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, 
    classification_report, 
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)
import pickle
from pathlib import Path

class ChessPredictor:
    """Predicts win probability based on historical game data."""
    
    def __init__(self, model_dir="models"):
        """Initialize predictor with model directory."""
        self.model = None
        self.is_trained = False
        self.X_test = None
        self.y_test = None
        self.y_pred = None
        self.y_pred_proba = None
        self.classification_metrics = None
        

    def train(self, X, y, test_size=0.2, max_recent_games=None):
        """
        Train logistic regression model with time-aware splitting.
        
        Args:
            X: Feature matrix (DataFrame, must be sorted by date)
            y: Target vector (win=1, loss/draw=0)
            test_size: Proportion of data for testing
            max_recent_games: If set, only use the N most recent games
            
        Returns:
            Dictionary with training metrics
        """
        # Optionally limit to recent games
        if max_recent_games and len(X) > max_recent_games:
            X = X.iloc[-max_recent_games:].copy()
            y = y.iloc[-max_recent_games:].copy()
        
        if len(X) < 20:
            print("Warning: Less than 20 games available. Model may not be reliable.")
        
        # TIME-BASED SPLIT (no random shuffling)
        # Most recent games become test set
        split_idx = int(len(X) * (1 - test_size))
        
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]
        
        # Check for stratification feasibility
        if len(np.unique(y_train)) > 1 and len(np.unique(y_test)) > 1:
            # Both train and test have both classes, proceed normally
            pass
        else:
            print("Warning: Train or test set has only one class. Results may be skewed.")
        
        # Store test data
        self.X_test = X_test
        self.y_test = y_test
        
        # Train model
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Generate predictions on test set
        self.y_pred = self.model.predict(X_test)
        self.y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, self.y_pred)
        
        # Compute classification metrics
        self.classification_metrics = self._compute_classification_metrics()
        
        metrics = {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'feature_names': X.columns.tolist() if hasattr(X, 'columns') else None,
            'classification_metrics': self.classification_metrics,
            'split_type': 'time_based'  # Document the split method
        }
        
        return metrics

    def _compute_classification_metrics(self):
        """
        Compute comprehensive classification metrics on test set.
        
        Returns:
            Dictionary containing classification performance metrics
        """
        if self.y_test is None or self.y_pred is None:
            return None
        
        # Basic metrics
        accuracy = accuracy_score(self.y_test, self.y_pred)
        precision = precision_score(self.y_test, self.y_pred, zero_division=0)
        recall = recall_score(self.y_test, self.y_pred, zero_division=0)
        f1 = f1_score(self.y_test, self.y_pred, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, self.y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        # ROC AUC (if we have probability predictions)
        try:
            roc_auc = roc_auc_score(self.y_test, self.y_pred_proba)
        except:
            roc_auc = None
        
        # Classification report as dict
        class_report = classification_report(
            self.y_test, 
            self.y_pred, 
            output_dict=True,
            zero_division=0
        )
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': {
                'true_negatives': int(tn),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_positives': int(tp)
            },
            'classification_report': class_report,
            'support': {
                'losses': int(np.sum(self.y_test == 0)),
                'wins': int(np.sum(self.y_test == 1))
            }
        }
    
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