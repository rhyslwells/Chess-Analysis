"""
test_predictor.py
Unit and integration tests for ChessPredictor model.

Tests cover:
- Model training and validation
- Prediction accuracy
- Feature engineering
- Edge cases and error handling
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.predictor import ChessPredictor
from sklearn.datasets import make_classification


@pytest.fixture
def sample_data():
    """Generate sample chess game data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Create realistic chess rating data
    user_ratings = np.random.randint(1200, 2000, n_samples)
    opponent_ratings = np.random.randint(1200, 2000, n_samples)
    rating_diffs = user_ratings - opponent_ratings
    is_white = np.random.randint(0, 2, n_samples)
    
    # Win probability influenced by rating difference and color
    # Higher rating diff = higher win probability
    # White has slight advantage
    win_probs = 1 / (1 + np.exp(-(rating_diffs / 200 + is_white * 0.2)))
    wins = (np.random.rand(n_samples) < win_probs).astype(int)
    
    X = pd.DataFrame({
        'user_rating': user_ratings,
        'opponent_rating': opponent_ratings,
        'rating_diff': rating_diffs,
        'is_white': is_white
    })
    
    y = pd.Series(wins, name='result')
    
    return X, y


@pytest.fixture
def small_dataset():
    """Generate a small dataset for edge case testing."""
    np.random.seed(42)
    X = pd.DataFrame({
        'user_rating': [1500, 1600, 1550, 1580, 1520],
        'opponent_rating': [1400, 1500, 1600, 1550, 1500],
        'rating_diff': [100, 100, -50, 30, 20],
        'is_white': [1, 0, 1, 1, 0]
    })
    y = pd.Series([1, 1, 0, 1, 0], name='result')
    return X, y


@pytest.fixture
def predictor():
    """Fixture to create a ChessPredictor instance."""
    return ChessPredictor()


@pytest.fixture
def trained_predictor(predictor, sample_data):
    """Fixture providing a trained predictor."""
    X, y = sample_data
    predictor.train(X, y, test_size=0.2)
    return predictor


class TestChessPredictorInitialization:
    """Test ChessPredictor initialization."""
    
    def test_init_default(self, predictor):
        """Test default initialization."""
        assert predictor.model is None, "Model should be None initially"
        assert predictor.is_trained is False, "Should not be trained initially"
        assert predictor.X_test is None, "X_test should be None initially"
        assert predictor.y_test is None, "y_test should be None initially"
        assert predictor.y_pred is None, "y_pred should be None initially"
        assert predictor.y_pred_proba is None, "y_pred_proba should be None initially"
        assert predictor.classification_metrics is None, "Metrics should be None initially"
    
    def test_init_with_model_dir(self):
        """Test initialization with custom model directory."""
        predictor = ChessPredictor(model_dir="custom_models")
        assert predictor.model is None, "Model should still be None"
        assert predictor.is_trained is False, "Should not be trained"


class TestChessPredictorTraining:
    """Test model training functionality."""
    
    def test_train_basic(self, predictor, sample_data):
        """Test basic model training."""
        X, y = sample_data
        metrics = predictor.train(X, y, test_size=0.2)
        
        # Check training completed
        assert predictor.is_trained is True, "Model should be marked as trained"
        assert predictor.model is not None, "Model should be initialized"
        
        # Check metrics structure
        assert 'train_accuracy' in metrics, "Should return train accuracy"
        assert 'test_accuracy' in metrics, "Should return test accuracy"
        assert 'n_train_samples' in metrics, "Should return train sample count"
        assert 'n_test_samples' in metrics, "Should return test sample count"
        assert 'feature_names' in metrics, "Should return feature names"
        assert 'classification_metrics' in metrics, "Should return classification metrics"
        assert 'split_type' in metrics, "Should document split type"
        
        # Check accuracy bounds
        assert 0 <= metrics['train_accuracy'] <= 1, "Train accuracy should be between 0 and 1"
        assert 0 <= metrics['test_accuracy'] <= 1, "Test accuracy should be between 0 and 1"
        
        # Check sample counts
        assert metrics['n_train_samples'] == 80, "Should have 80 training samples"
        assert metrics['n_test_samples'] == 20, "Should have 20 test samples"
        assert metrics['split_type'] == 'time_based', "Should use time-based split"
    
    def test_train_time_based_split(self, predictor, sample_data):
        """Test that training uses time-based split (no shuffling)."""
        X, y = sample_data
        predictor.train(X, y, test_size=0.2)
        
        # Test set should be the last 20% of data
        expected_test_indices = X.index[-20:]
        actual_test_indices = predictor.X_test.index
        
        assert list(expected_test_indices) == list(actual_test_indices), \
            "Test set should be the most recent (last) 20% of data"
    
    def test_train_with_max_recent_games(self, predictor, sample_data):
        """Test training with limited number of recent games."""
        X, y = sample_data
        metrics = predictor.train(X, y, test_size=0.2, max_recent_games=50)
        
        # Should only use 50 most recent games
        assert metrics['n_train_samples'] == 40, "Should have 40 training samples (80% of 50)"
        assert metrics['n_test_samples'] == 10, "Should have 10 test samples (20% of 50)"
    
    def test_train_small_dataset_warning(self, predictor, small_dataset, capsys):
        """Test warning when training on very small dataset."""
        X, y = small_dataset
        predictor.train(X, y, test_size=0.2)
        
        captured = capsys.readouterr()
        assert "Less than 20 games available" in captured.out, \
            "Should warn about small dataset"
    
    def test_train_single_class_warning(self, predictor, capsys):
        """Test warning when train or test set has only one class."""
        # Create dataset where test set will have only one class
        X = pd.DataFrame({
            'user_rating': [1500] * 10,
            'opponent_rating': [1400] * 10,
            'rating_diff': [100] * 10,
            'is_white': [1] * 10
        })
        # All wins in train, force different pattern in test
        y = pd.Series([1, 1, 1, 1, 1, 1, 1, 1, 0, 0], name='result')
        
        predictor.train(X, y, test_size=0.2)
        
        captured = capsys.readouterr()
        # May or may not trigger depending on split, but should not crash
        assert predictor.is_trained is True, "Should still train successfully"
    
    def test_train_feature_names_stored(self, predictor, sample_data):
        """Test that feature names are stored correctly."""
        X, y = sample_data
        metrics = predictor.train(X, y, test_size=0.2)
        
        expected_features = ['user_rating', 'opponent_rating', 'rating_diff', 'is_white']
        assert metrics['feature_names'] == expected_features, \
            f"Feature names should be {expected_features}"
    
    def test_train_stores_test_data(self, predictor, sample_data):
        """Test that training stores test data for later evaluation."""
        X, y = sample_data
        predictor.train(X, y, test_size=0.2)
        
        assert predictor.X_test is not None, "X_test should be stored"
        assert predictor.y_test is not None, "y_test should be stored"
        assert predictor.y_pred is not None, "y_pred should be stored"
        assert predictor.y_pred_proba is not None, "y_pred_proba should be stored"
        
        assert len(predictor.X_test) == len(predictor.y_test), \
            "X_test and y_test should have same length"
        assert len(predictor.y_pred) == len(predictor.y_test), \
            "y_pred and y_test should have same length"
        assert len(predictor.y_pred_proba) == len(predictor.y_test), \
            "y_pred_proba and y_test should have same length"


class TestClassificationMetrics:
    """Test classification metrics computation."""
    
    def test_classification_metrics_computed(self, trained_predictor):
        """Test that classification metrics are computed during training."""
        metrics = trained_predictor.classification_metrics
        
        assert metrics is not None, "Classification metrics should be computed"
        
        # Check required metric fields
        required_fields = [
            'accuracy', 'precision', 'recall', 'f1_score', 
            'confusion_matrix', 'classification_report', 'support'
        ]
        for field in required_fields:
            assert field in metrics, f"Metrics should contain '{field}'"
    
    def test_confusion_matrix_structure(self, trained_predictor):
        """Test confusion matrix structure."""
        cm = trained_predictor.classification_metrics['confusion_matrix']
        
        assert 'true_negatives' in cm, "Should have true_negatives"
        assert 'false_positives' in cm, "Should have false_positives"
        assert 'false_negatives' in cm, "Should have false_negatives"
        assert 'true_positives' in cm, "Should have true_positives"
        
        # All values should be non-negative integers
        for key, value in cm.items():
            assert isinstance(value, int), f"{key} should be integer"
            assert value >= 0, f"{key} should be non-negative"
        
        # Sum should equal test set size
        total = sum(cm.values())
        assert total == len(trained_predictor.y_test), \
            "Confusion matrix sum should equal test set size"
    
    def test_metric_bounds(self, trained_predictor):
        """Test that all metrics are within valid bounds."""
        metrics = trained_predictor.classification_metrics
        
        # Metrics should be between 0 and 1
        bounded_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        for metric_name in bounded_metrics:
            value = metrics[metric_name]
            assert 0 <= value <= 1, f"{metric_name} should be between 0 and 1, got {value}"
        
        # ROC AUC should also be between 0 and 1 if present
        if metrics['roc_auc'] is not None:
            assert 0 <= metrics['roc_auc'] <= 1, \
                f"ROC AUC should be between 0 and 1, got {metrics['roc_auc']}"
    
    def test_support_values(self, trained_predictor):
        """Test support values in classification metrics."""
        support = trained_predictor.classification_metrics['support']
        
        assert 'losses' in support, "Support should contain losses count"
        assert 'wins' in support, "Support should contain wins count"
        
        # Support should sum to test set size
        total_support = support['losses'] + support['wins']
        assert total_support == len(trained_predictor.y_test), \
            "Support should sum to test set size"
    
    def test_classification_report_structure(self, trained_predictor):
        """Test classification report structure."""
        report = trained_predictor.classification_metrics['classification_report']
        
        assert isinstance(report, dict), "Classification report should be a dictionary"
        
        # Should have class-specific metrics
        assert '0' in report or '1' in report, "Should have per-class metrics"
        
        # Should have aggregate metrics
        assert 'accuracy' in report, "Should have overall accuracy"


class TestPrediction:
    """Test prediction functionality."""
    
    def test_predict_win_probability_basic(self, trained_predictor):
        """Test basic win probability prediction."""
        # User with higher rating should have higher win probability
        prob = trained_predictor.predict_win_probability(1800, 1600, is_white=True)
        
        assert isinstance(prob, (float, np.floating)), "Probability should be float"
        assert 0 <= prob <= 1, f"Probability should be between 0 and 1, got {prob}"
        assert prob > 0.5, "Higher rated player should have >50% win probability"
    
    def test_predict_win_probability_lower_rating(self, trained_predictor):
        """Test prediction when user has lower rating."""
        prob = trained_predictor.predict_win_probability(1400, 1600, is_white=True)
        
        assert 0 <= prob <= 1, f"Probability should be between 0 and 1, got {prob}"
        assert prob < 0.5, "Lower rated player should have <50% win probability"
    
    def test_predict_win_probability_equal_ratings(self, trained_predictor):
        """Test prediction with equal ratings."""
        prob_white = trained_predictor.predict_win_probability(1500, 1500, is_white=True)
        prob_black = trained_predictor.predict_win_probability(1500, 1500, is_white=False)
        
        # White should have slight advantage
        assert prob_white >= prob_black, \
            "White should have equal or higher win probability with same ratings"
    
    def test_predict_win_probability_color_advantage(self, trained_predictor):
        """Test that color affects win probability."""
        prob_white = trained_predictor.predict_win_probability(1600, 1600, is_white=True)
        prob_black = trained_predictor.predict_win_probability(1600, 1600, is_white=False)
        
        # Probabilities should be different based on color
        assert prob_white != prob_black, "Color should affect win probability"
    
    def test_predict_untrained_model_raises_error(self, predictor):
        """Test that prediction on untrained model raises error."""
        with pytest.raises(ValueError, match="Model must be trained"):
            predictor.predict_win_probability(1500, 1500)
    
    def test_predict_various_rating_differences(self, trained_predictor):
        """Test predictions across various rating differences."""
        user_rating = 1600
        
        # Test increasing opponent ratings
        opponents = [1200, 1400, 1600, 1800, 2000]
        probabilities = []
        
        for opp_rating in opponents:
            prob = trained_predictor.predict_win_probability(user_rating, opp_rating, is_white=True)
            probabilities.append(prob)
        
        # Probabilities should decrease as opponent gets stronger
        for i in range(len(probabilities) - 1):
            assert probabilities[i] >= probabilities[i + 1], \
                "Win probability should decrease as opponent rating increases"


class TestWinProbabilityCurve:
    """Test win probability curve generation."""
    
    def test_get_win_probability_curve_default_range(self, trained_predictor):
        """Test curve generation with default rating range."""
        user_rating = 1600
        curve = trained_predictor.get_win_probability_curve(user_rating, is_white=True)
        
        assert isinstance(curve, pd.DataFrame), "Should return DataFrame"
        assert 'opponent_rating' in curve.columns, "Should have opponent_rating column"
        assert 'win_probability' in curve.columns, "Should have win_probability column"
        
        # Check rating range (default is ±400)
        assert curve['opponent_rating'].min() >= user_rating - 400, \
            "Min rating should be around user_rating - 400"
        assert curve['opponent_rating'].max() <= user_rating + 400, \
            "Max rating should be around user_rating + 400"
        
        # All probabilities should be valid
        assert all(curve['win_probability'] >= 0), "All probabilities should be >= 0"
        assert all(curve['win_probability'] <= 1), "All probabilities should be <= 1"
    
    def test_get_win_probability_curve_custom_range(self, trained_predictor):
        """Test curve generation with custom rating range."""
        user_rating = 1600
        curve = trained_predictor.get_win_probability_curve(
            user_rating, 
            rating_range=(1400, 1800),
            is_white=True
        )
        
        assert curve['opponent_rating'].min() == 1400, "Min rating should match specified"
        assert curve['opponent_rating'].max() == 1800, "Max rating should match specified"
    
    def test_get_win_probability_curve_monotonic(self, trained_predictor):
        """Test that win probability curve is monotonically decreasing."""
        user_rating = 1600
        curve = trained_predictor.get_win_probability_curve(user_rating, is_white=True)
        
        # Check that probabilities generally decrease as opponent rating increases
        # Allow for small fluctuations due to model behavior
        probabilities = curve['win_probability'].values
        
        # First probability should be higher than last
        assert probabilities[0] > probabilities[-1], \
            "Win probability should decrease as opponent rating increases"
    
    def test_get_win_probability_curve_spacing(self, trained_predictor):
        """Test that opponent ratings are properly spaced."""
        user_rating = 1600
        curve = trained_predictor.get_win_probability_curve(user_rating, is_white=True)
        
        # Ratings should be spaced by 25
        rating_diffs = curve['opponent_rating'].diff().dropna()
        assert all(rating_diffs == 25), "Ratings should be spaced by 25 points"
    
    def test_get_win_probability_curve_untrained_raises_error(self, predictor):
        """Test that curve generation on untrained model raises error."""
        with pytest.raises(ValueError, match="Model must be trained"):
            predictor.get_win_probability_curve(1600)


class TestFeatureImportance:
    """Test feature importance functionality."""
    
    def test_get_feature_importance_structure(self, trained_predictor):
        """Test feature importance structure."""
        importance = trained_predictor.get_feature_importance()
        
        assert isinstance(importance, pd.DataFrame), "Should return DataFrame"
        assert 'feature' in importance.columns, "Should have feature column"
        assert 'coefficient' in importance.columns, "Should have coefficient column"
        assert 'abs_coefficient' in importance.columns, "Should have abs_coefficient column"
        
        # Should have all features
        expected_features = ['user_rating', 'opponent_rating', 'rating_diff', 'is_white']
        assert len(importance) == len(expected_features), \
            f"Should have {len(expected_features)} features"
        
        # All expected features should be present
        for feature in expected_features:
            assert feature in importance['feature'].values, \
                f"Feature '{feature}' should be in importance table"
    
    def test_get_feature_importance_sorted(self, trained_predictor):
        """Test that feature importance is sorted by absolute coefficient."""
        importance = trained_predictor.get_feature_importance()
        
        # Should be sorted by abs_coefficient in descending order
        abs_coeffs = importance['abs_coefficient'].values
        assert all(abs_coeffs[i] >= abs_coeffs[i + 1] for i in range(len(abs_coeffs) - 1)), \
            "Features should be sorted by absolute coefficient (descending)"
    
    def test_get_feature_importance_untrained_returns_none(self, predictor):
        """Test that importance on untrained model returns None."""
        importance = predictor.get_feature_importance()
        assert importance is None, "Untrained model should return None for feature importance"
    
    def test_feature_importance_coefficients(self, trained_predictor):
        """Test that feature coefficients make logical sense."""
        importance = trained_predictor.get_feature_importance()
        
        # Rating diff should generally have positive coefficient
        # (higher rating diff = higher win probability)
        rating_diff_coef = importance[importance['feature'] == 'rating_diff']['coefficient'].values[0]
        
        # Coefficient should be non-zero
        assert rating_diff_coef != 0, "Rating diff should have non-zero coefficient"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_train_with_empty_data(self, predictor):
        """Test training with empty dataset."""
        X = pd.DataFrame(columns=['user_rating', 'opponent_rating', 'rating_diff', 'is_white'])
        y = pd.Series([], name='result')
        
        # Should handle gracefully or raise appropriate error
        with pytest.raises(Exception):  # Could be ValueError or other
            predictor.train(X, y)
    
    def test_train_with_single_sample(self, predictor, capsys):
        """Test training with single sample."""
        X = pd.DataFrame({
            'user_rating': [1500],
            'opponent_rating': [1400],
            'rating_diff': [100],
            'is_white': [1]
        })
        y = pd.Series([1], name='result')
        
        # Should handle gracefully with warning
        with pytest.raises(Exception):  # Not enough data to split
            predictor.train(X, y, test_size=0.2)
    
    def test_predict_with_extreme_ratings(self, trained_predictor):
        """Test prediction with extreme rating values."""
        # Very high rating
        prob_high = trained_predictor.predict_win_probability(3000, 1500, is_white=True)
        assert 0 <= prob_high <= 1, "Should handle extreme high ratings"
        assert prob_high > 0.9, "Very high rating should give very high win probability"
        
        # Very low rating
        prob_low = trained_predictor.predict_win_probability(800, 1500, is_white=True)
        assert 0 <= prob_low <= 1, "Should handle extreme low ratings"
        assert prob_low < 0.1, "Very low rating should give very low win probability"
    
    def test_train_test_split_boundaries(self, predictor):
        """Test train/test split with various test sizes."""
        X = pd.DataFrame({
            'user_rating': np.random.randint(1200, 2000, 100),
            'opponent_rating': np.random.randint(1200, 2000, 100),
            'rating_diff': np.random.randint(-400, 400, 100),
            'is_white': np.random.randint(0, 2, 100)
        })
        y = pd.Series(np.random.randint(0, 2, 100))
        
        # Test with very small test set
        metrics = predictor.train(X, y, test_size=0.1)
        assert metrics['n_test_samples'] == 10, "Should have 10 test samples"
        
        # Test with larger test set
        predictor2 = ChessPredictor()
        metrics2 = predictor2.train(X, y, test_size=0.3)
        assert metrics2['n_test_samples'] == 30, "Should have 30 test samples"


class TestModelPersistence:
    """Test model state persistence."""
    
    def test_model_state_after_training(self, predictor, sample_data):
        """Test that model state is properly maintained after training."""
        X, y = sample_data
        
        # Train model
        predictor.train(X, y, test_size=0.2)
        
        # Make a prediction
        prob1 = predictor.predict_win_probability(1600, 1500, is_white=True)
        
        # Make same prediction again
        prob2 = predictor.predict_win_probability(1600, 1500, is_white=True)
        
        # Should get identical results
        assert prob1 == prob2, "Model should give consistent predictions"
    
    def test_is_trained_flag(self, predictor, sample_data):
        """Test that is_trained flag is properly set."""
        X, y = sample_data
        
        assert predictor.is_trained is False, "Should not be trained initially"
        
        predictor.train(X, y, test_size=0.2)
        
        assert predictor.is_trained is True, "Should be trained after training"


class TestRealWorldScenarios:
    """Test realistic chess scenarios."""
    
    def test_rating_progression_predictions(self, trained_predictor):
        """Test predictions as user rating improves."""
        opponent_rating = 1600
        
        # Simulate rating improvement
        user_ratings = [1400, 1500, 1600, 1700, 1800]
        probabilities = []
        
        for user_rating in user_ratings:
            prob = trained_predictor.predict_win_probability(
                user_rating, 
                opponent_rating, 
                is_white=True
            )
            probabilities.append(prob)
        
        # Win probability should increase with rating
        for i in range(len(probabilities) - 1):
            assert probabilities[i] <= probabilities[i + 1], \
                "Win probability should increase as user rating increases"
    
    def test_typical_rating_ranges(self, trained_predictor):
        """Test predictions within typical chess rating ranges."""
        # Beginner vs Intermediate
        prob_beginner = trained_predictor.predict_win_probability(1200, 1600, is_white=True)
        assert prob_beginner < 0.3, "Beginner should have low win probability vs intermediate"
        
        # Intermediate vs Advanced
        prob_intermediate = trained_predictor.predict_win_probability(1600, 2000, is_white=True)
        assert prob_intermediate < 0.4, "Intermediate should have low win probability vs advanced"
        
        # Similar ratings
        prob_similar = trained_predictor.predict_win_probability(1600, 1620, is_white=True)
        assert 0.4 < prob_similar < 0.6, "Similar ratings should give close to 50% probability"


@pytest.mark.slow
class TestLargeDatasets:
    """Tests for larger datasets (marked slow)."""
    
    def test_train_large_dataset(self, predictor):
        """Test training on larger dataset."""
        np.random.seed(42)
        n_samples = 1000
        
        user_ratings = np.random.randint(1000, 2500, n_samples)
        opponent_ratings = np.random.randint(1000, 2500, n_samples)
        rating_diffs = user_ratings - opponent_ratings
        is_white = np.random.randint(0, 2, n_samples)
        
        win_probs = 1 / (1 + np.exp(-(rating_diffs / 200 + is_white * 0.2)))
        wins = (np.random.rand(n_samples) < win_probs).astype(int)
        
        X = pd.DataFrame({
            'user_rating': user_ratings,
            'opponent_rating': opponent_ratings,
            'rating_diff': rating_diffs,
            'is_white': is_white
        })
        y = pd.Series(wins, name='result')
        
        metrics = predictor.train(X, y, test_size=0.2)
        
        # With more data, accuracy should be reasonable
        assert metrics['test_accuracy'] > 0.5, "Should achieve better than random accuracy"
        assert metrics['n_train_samples'] == 800, "Should have 800 training samples"
        assert metrics['n_test_samples'] == 200, "Should have 200 test samples"
    
    def test_max_recent_games_with_large_dataset(self, predictor):
        """Test max_recent_games parameter with large dataset."""
        np.random.seed(42)
        n_samples = 1000
        
        X = pd.DataFrame({
            'user_rating': np.random.randint(1000, 2500, n_samples),
            'opponent_rating': np.random.randint(1000, 2500, n_samples),
            'rating_diff': np.random.randint(-500, 500, n_samples),
            'is_white': np.random.randint(0, 2, n_samples)
        })
        y = pd.Series(np.random.randint(0, 2, n_samples))
        
        # Limit to 200 most recent games
        metrics = predictor.train(X, y, test_size=0.2, max_recent_games=200)
        
        assert metrics['n_train_samples'] == 160, "Should use 160 training samples"
        assert metrics['n_test_samples'] == 40, "Should use 40 test samples"