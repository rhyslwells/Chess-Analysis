"""
temporal_validation.py

Diagnostic script to evaluate whether time-based train/test splitting
is better than random splitting for chess game prediction models.

This script helps answer the question:
"Does my chess playing skill/performance change over time enough that
 we should treat games as a time series rather than random samples?"

Usage in IPython:
    # Option 1: Fetch fresh data and analyze
    %run temporal_validation.py
    results = fetch_and_analyze('RhysLWells')
    
    # Option 2: Use data already loaded in session
    results = run_full_analysis(df=your_df)
    
    # Option 3: Quick check only
    quick_check_fresh('RhysLWells')

Requirements:
    - Chess.com API access (for fetching data)
    - Or pass a DataFrame directly
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from pathlib import Path
import sys

# Add parent directory to path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.analyzer import ChessAnalyzer
from src.predictor import ChessPredictor
from src.data_fetcher import ChessDataFetcher


# ==============================================================================
# DATA LOADING - Multiple methods to get chess data
# ==============================================================================

def fetch_fresh_data(username, months_back=3):
    """
    Fetch fresh data from Chess.com API.
    
    Args:
        username: Chess.com username
        months_back: Number of recent months to fetch (default=3)
        
    Returns:
        DataFrame with chess games
    """
    print(f"\nFetching fresh data for {username} (last {months_back} months)...")
    print("=" * 70)
    
    fetcher = ChessDataFetcher()
    
    # Fetch using archive discovery (most recent N months)
    games = fetcher.fetch_all_games(username, limit_months=months_back)
    
    if not games:
        raise ValueError(f"No games found for username '{username}'")
    
    # Process into DataFrame
    df = fetcher.process_and_save(username, games, mode='json')
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"\n Successfully loaded {len(df)} games")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
    return df


def load_chess_data(username):
    """
    Load chess data from various possible file locations/formats.
    
    Tries in order:
    1. data/processed/{username}_games.json
    2. data/processed/{username}_games.csv
    3. data/{username}_games.json
    4. data/{username}_games.csv
    
    Args:
        username: Chess.com username
        
    Returns:
        DataFrame with chess games
    """
    base_path = Path(__file__).parent.parent / 'data'
    
    # Try different locations and formats
    possible_paths = [
        base_path / 'processed' / f'{username}_games.json',
        base_path / 'processed' / f'{username}_games.csv',
        base_path / f'{username}_games.json',
        base_path / f'{username}_games.csv',
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"Loading data from: {path}")
            
            if path.suffix == '.json':
                df = pd.read_json(path)
            elif path.suffix == '.csv':
                df = pd.read_csv(path)
            else:
                continue
            
            # Ensure date column exists and is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'end_time' in df.columns:
                df['date'] = pd.to_datetime(df['end_time'])
            
            df = df.sort_values('date').reset_index(drop=True)
            return df
    
    # If we get here, no file was found
    raise FileNotFoundError(
        f"Could not find chess data for username '{username}'\n"
        f"Searched in:\n" + 
        "\n".join(f"  - {p}" for p in possible_paths) +
        f"\n\nTip: Use fetch_and_analyze('{username}') to fetch fresh data from Chess.com"
    )


# ==============================================================================
# 1. SIMPLE STATISTICAL TEST - Quick check for temporal patterns
# ==============================================================================

def compare_early_late_performance(df, split_ratio=0.5):
    """
    Compare your performance in first half vs second half of games.
    
    This is the quickest way to see if your performance has changed over time.
    If your rating or win rate changed significantly, time-based splitting
    is likely better.
    
    Args:
        df: DataFrame with chess games (must be sorted by date)
        split_ratio: Where to split (0.5 = middle)
        
    Returns:
        Dictionary with comparison statistics
    """
    split_point = int(len(df) * split_ratio)
    
    early_games = df.iloc[:split_point]
    late_games = df.iloc[split_point:]
    
    # Calculate statistics
    stats = {
        'early_win_rate': early_games['result'].mean(),
        'late_win_rate': late_games['result'].mean(),
        'early_rating': early_games['user_rating'].mean(),
        'late_rating': late_games['user_rating'].mean(),
        'early_games': len(early_games),
        'late_games': len(late_games)
    }
    
    stats['rating_change'] = stats['late_rating'] - stats['early_rating']
    stats['win_rate_change'] = stats['late_win_rate'] - stats['early_win_rate']
    
    # Print results
    print("=" * 70)
    print("EARLY vs LATE GAME PERFORMANCE COMPARISON")
    print("=" * 70)
    print(f"\nEarly period ({stats['early_games']} games):")
    print(f"  Win rate: {stats['early_win_rate']:.1%}")
    print(f"  Avg rating: {stats['early_rating']:.0f}")
    
    print(f"\nLate period ({stats['late_games']} games):")
    print(f"  Win rate: {stats['late_win_rate']:.1%}")
    print(f"  Avg rating: {stats['late_rating']:.0f}")
    
    print(f"\nChanges over time:")
    print(f"  Rating change: {stats['rating_change']:+.0f} points")
    print(f"  Win rate change: {stats['win_rate_change']:+.1%}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION:")
    if abs(stats['rating_change']) > 100:
        print("  LARGE rating change detected (>100 points)")
        print("    → Definitely use time-based splitting")
    elif abs(stats['rating_change']) > 50:
        print("  Moderate rating change detected (>50 points)")
        print("    → Time-based splitting recommended")
    else:
        print("  Ratings relatively stable (<50 point change)")
        print("    → Random split may be acceptable, but time-based is still safer")
    print("=" * 70 + "\n")
    
    return stats


# ==============================================================================
# 2. FEATURE DRIFT ANALYSIS - How features change across time periods
# ==============================================================================

def analyze_feature_drift(df, n_periods=4):
    """
    Analyze how features (ratings, win rates) change across time periods.
    
    Splits data into N equal time periods and shows statistics for each.
    Large changes indicate that your skill/performance has evolved,
    making time-based splitting more important.
    
    Args:
        df: DataFrame with chess games (must be sorted by date)
        n_periods: Number of time periods to split into (default=4 for quartiles)
        
    Returns:
        DataFrame with statistics per period
    """
    # Create period labels
    df = df.copy()
    
    # Calculate rating_diff if it doesn't exist
    if 'rating_diff' not in df.columns:
        df['rating_diff'] = df['user_rating'] - df['opponent_rating']
    
    df['period'] = pd.qcut(df.index, q=n_periods, labels=[f'Q{i+1}' for i in range(n_periods)])
    
    # Calculate statistics per period
    drift_stats = df.groupby('period').agg({
        'user_rating': ['mean', 'std', 'min', 'max'],
        'opponent_rating': ['mean', 'std'],
        'rating_diff': ['mean', 'std'],
        'result': ['mean', 'count']  # win rate and game count
    }).round(2)
    
    # Flatten column names
    drift_stats.columns = ['_'.join(col).strip() for col in drift_stats.columns.values]
    drift_stats = drift_stats.rename(columns={
        'result_mean': 'win_rate',
        'result_count': 'games'
    })
    
    print("\n" + "=" * 70)
    print("FEATURE DRIFT ANALYSIS - How your games changed over time")
    print("=" * 70)
    print(drift_stats)
    print("\nKey metrics to watch:")
    print("  - user_rating_mean: Is your rating trending up or down?")
    print("  - win_rate: Is your win rate changing?")
    print("  - Large changes = more important to use time-based splitting")
    print("=" * 70 + "\n")
    
    return drift_stats


# ==============================================================================
# 3. TEMPORAL CROSS-VALIDATION - Test prediction quality over time
# ==============================================================================

def temporal_cross_validation(df, n_splits=5):
    """
    Simulate training on older data and testing on newer data.
    
    This mimics real-world usage: using historical games to predict
    future performance. If accuracy degrades over time, it means
    your skill is changing and time-based splitting is critical.
    
    Args:
        df: DataFrame with chess games (must be sorted by date)
        n_splits: Number of time windows to evaluate
        
    Returns:
        DataFrame with accuracy for each time window
    """
    print("\n" + "=" * 70)
    print("TEMPORAL CROSS-VALIDATION - Training on past to predict future")
    print("=" * 70)
    
    # Prepare features
    analyzer = ChessAnalyzer(df)
    X, y = analyzer.prepare_ml_features()
    
    results = []
    total_games = len(X)
    window_size = total_games // (n_splits + 1)
    
    for i in range(n_splits):
        # Train on all data up to this point
        train_end = window_size * (i + 1)
        test_end = min(window_size * (i + 2), total_games)
        
        X_train = X.iloc[:train_end]
        y_train = y.iloc[:train_end]
        X_test = X.iloc[train_end:test_end]
        y_test = y.iloc[train_end:test_end]
        
        if len(X_test) < 10:
            print(f"  Fold {i+1}: Skipping (too few test samples)")
            continue
        
        # Train model
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train, y_train)
        
        # Evaluate
        acc = model.score(X_test, y_test)
        
        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_pred_proba)
        except:
            auc = None
        
        results.append({
            'fold': i + 1,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'accuracy': acc,
            'auc': auc
        })
        
        print(f"  Fold {i+1}: Train on {len(X_train):4d} games → Test on {len(X_test):3d} games | Accuracy: {acc:.3f}")
    
    results_df = pd.DataFrame(results)
    
    # Analyze trend
    if len(results_df) >= 3:
        acc_values = results_df['accuracy'].values
        trend = np.polyfit(range(len(acc_values)), acc_values, 1)[0]
        
        print("\n" + "-" * 70)
        if trend < -0.02:
            print(" Accuracy DECREASING over time")
            print("   → Your skill is improving! Old games don't predict new performance well.")
            print("   → Time-based splitting is CRITICAL")
        elif trend > 0.02:
            print(" Accuracy INCREASING over time")
            print("   → Unusual pattern. Might indicate declining performance or data issues.")
        else:
            print("  Accuracy relatively STABLE over time")
            print("   → Performance is consistent. Time-based splitting still recommended.")
    
    print("=" * 70 + "\n")
    
    return results_df


# ==============================================================================
# 4. COMPARE RANDOM VS TIME-BASED SPLITTING
# ==============================================================================

def compare_split_methods(df):
    """
    Directly compare random split vs time-based split performance.
    
    This shows you the concrete difference in test accuracy between
    the two methods. Time-based will typically have LOWER test accuracy,
    which is actually good - it means it's a more realistic/harder test.
    
    Args:
        df: DataFrame with chess games (must be sorted by date)
        
    Returns:
        Dictionary with results from both methods
    """
    print("\n" + "=" * 70)
    print("RANDOM SPLIT vs TIME-BASED SPLIT COMPARISON")
    print("=" * 70)
    
    analyzer = ChessAnalyzer(df)
    X, y = analyzer.prepare_ml_features()
    
    # Method 1: Random split (with shuffling)
    print("\n1. RANDOM SPLIT (current method - shuffles all games)")
    from sklearn.model_selection import train_test_split
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    model_random = LogisticRegression(random_state=42, max_iter=1000)
    model_random.fit(X_train_r, y_train_r)
    
    train_acc_r = model_random.score(X_train_r, y_train_r)
    test_acc_r = model_random.score(X_test_r, y_test_r)
    
    print(f"   Training accuracy: {train_acc_r:.3f}")
    print(f"   Test accuracy:     {test_acc_r:.3f}")
    print(f"   Test set contains: mix of old and new games (random)")
    
    # Method 2: Time-based split (chronological)
    print("\n2. TIME-BASED SPLIT (proposed - most recent 20% as test)")
    split_idx = int(len(X) * 0.8)
    
    X_train_t = X.iloc[:split_idx]
    X_test_t = X.iloc[split_idx:]
    y_train_t = y.iloc[:split_idx]
    y_test_t = y.iloc[split_idx:]
    
    model_time = LogisticRegression(random_state=42, max_iter=1000)
    model_time.fit(X_train_t, y_train_t)
    
    train_acc_t = model_time.score(X_train_t, y_train_t)
    test_acc_t = model_time.score(X_test_t, y_test_t)
    
    print(f"   Training accuracy: {train_acc_t:.3f}")
    print(f"   Test accuracy:     {test_acc_t:.3f}")
    print(f"   Test set contains: most recent {len(X_test_t)} games only")
    
    # Comparison
    print("\n" + "-" * 70)
    print("INTERPRETATION:")
    diff = test_acc_r - test_acc_t
    
    if diff > 0.05:
        print(f"  Random split accuracy is {diff:.1%} HIGHER than time-based")
        print("   → Random split is giving you overly optimistic results!")
        print("   → It's testing on easy old games mixed with hard new games")
        print("   → Time-based split is more realistic for predicting future games")
        print("   → RECOMMENDATION: Switch to time-based splitting")
    elif diff > 0.02:
        print(f"  Random split accuracy is {diff:.1%} higher than time-based")
        print("   → Moderate difference suggests time-based is more appropriate")
        print("   → RECOMMENDATION: Use time-based splitting")
    elif diff < -0.02:
        print(f"  Time-based accuracy is {-diff:.1%} HIGHER than random")
        print("   → This is unusual. Your recent games might be easier.")
        print("   → Still recommend time-based for realistic evaluation")
    else:
        print(f"  Both methods give similar accuracy (diff: {diff:.1%})")
        print("   → Either method works, but time-based is more principled")
        print("   → RECOMMENDATION: Use time-based for consistency")
    
    print("=" * 70 + "\n")
    
    return {
        'random_train_acc': train_acc_r,
        'random_test_acc': test_acc_r,
        'time_train_acc': train_acc_t,
        'time_test_acc': test_acc_t,
        'difference': diff
    }


# ==============================================================================
# 5. PREDICTION RESIDUALS OVER TIME - Visual check
# ==============================================================================

def plot_residuals_over_time(df):
    """
    Plot prediction errors chronologically to see if model struggles
    more with recent games than old games.
    
    If errors increase toward recent games (right side of plot),
    it suggests the model trained on all data doesn't generalize
    well to your current playing level.
    
    Args:
        df: DataFrame with chess games (must be sorted by date)
        
    Returns:
        Plotly figure object
    """
    print("\n" + "=" * 70)
    print("RESIDUAL ANALYSIS - Do prediction errors increase over time?")
    print("=" * 70)
    
    # Prepare features and train model on all data
    analyzer = ChessAnalyzer(df)
    X, y = analyzer.prepare_ml_features()
    
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X, y)
    
    # Get predictions
    y_pred_proba = model.predict_proba(X)[:, 1]
    residuals = y - y_pred_proba
    
    # Create plot
    fig = go.Figure()
    
    # Scatter plot of residuals
    fig.add_trace(go.Scatter(
        x=list(range(len(residuals))),
        y=residuals,
        mode='markers',
        marker=dict(
            color=residuals,
            colorscale='RdYlGn',
            size=4,
            opacity=0.6,
            colorbar=dict(title="Residual")
        ),
        name='Prediction Error',
        hovertemplate='Game #%{x}<br>Error: %{y:.3f}<extra></extra>'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash='dash', line_color='black', 
                  annotation_text='Perfect Prediction')
    
    # Add trend line
    z = np.polyfit(range(len(residuals)), residuals, 1)
    p = np.poly1d(z)
    fig.add_trace(go.Scatter(
        x=list(range(len(residuals))),
        y=p(range(len(residuals))),
        mode='lines',
        line=dict(color='red', width=2),
        name='Trend'
    ))
    
    fig.update_layout(
        title='Prediction Errors Over Time (Chronological Order)',
        xaxis_title='Game Number (Older → Newer)',
        yaxis_title='Prediction Error (Actual - Predicted)',
        hovermode='closest',
        height=500
    )
    
    # Calculate statistics
    first_half = residuals[:len(residuals)//2]
    second_half = residuals[len(residuals)//2:]
    
    print(f"\nFirst half avg absolute error:  {np.abs(first_half).mean():.3f}")
    print(f"Second half avg absolute error: {np.abs(second_half).mean():.3f}")
    
    if np.abs(second_half).mean() > np.abs(first_half).mean() + 0.05:
        print("\n  Errors are LARGER for recent games")
        print("   → Model struggles more with new games than old games")
        print("   → Time-based splitting is recommended")
    else:
        print("\n  Errors are relatively consistent across time")
    
    print("=" * 70 + "\n")
    
    return fig


# ==============================================================================
# 6. RUN ALL ANALYSES - Comprehensive report
# ==============================================================================

def load_chess_data(username):
    """
    Load chess data from various possible locations/formats.
    
    Tries in order:
    1. data/processed/{username}_games.json
    2. data/processed/{username}_games.csv
    3. data/{username}_games.json
    4. data/{username}_games.csv
    
    Args:
        username: Chess.com username
        
    Returns:
        DataFrame with chess games
    """
    base_path = Path(__file__).parent.parent / 'data'
    
    # Try different locations and formats
    possible_paths = [
        base_path / 'processed' / f'{username}_games.json',
        base_path / 'processed' / f'{username}_games.csv',
        base_path / f'{username}_games.json',
        base_path / f'{username}_games.csv',
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"Loading data from: {path}")
            
            if path.suffix == '.json':
                df = pd.read_json(path)
            elif path.suffix == '.csv':
                df = pd.read_csv(path)
            else:
                continue
            
            # Ensure date column exists and is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'end_time' in df.columns:
                df['date'] = pd.to_datetime(df['end_time'])
            
            df = df.sort_values('date').reset_index(drop=True)
            return df
    
    # If we get here, no file was found
    raise FileNotFoundError(
        f"Could not find chess data for username '{username}'\n"
        f"Searched in:\n" + 
        "\n".join(f"  - {p}" for p in possible_paths) +
        f"\n\nPlease ensure data exists at one of these locations, or pass a DataFrame directly."
    )


def run_full_analysis(username=None, df=None):
    """
    Run all temporal validation analyses and generate a comprehensive report.
    
    Args:
        username: Chess.com username (will load data from data/processed/)
        df: Or pass DataFrame directly
        
    Returns:
        Dictionary with all results
    """
    # Load data
    if df is None:
        if username is None:
            raise ValueError("Must provide either username or df")
        
        df = load_chess_data(username)
    
    # Ensure date is datetime and sorted
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("TEMPORAL VALIDATION ANALYSIS")
    print("=" * 70)
    print(f"Dataset: {len(df)} games")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print("=" * 70)
    
    results = {}
    
    # Run all analyses
    results['early_late'] = compare_early_late_performance(df)
    results['drift'] = analyze_feature_drift(df)
    results['temporal_cv'] = temporal_cross_validation(df)
    results['split_comparison'] = compare_split_methods(df)
    results['residual_plot'] = plot_residuals_over_time(df)
    
    # Final recommendation
    print("\n" + "=" * 70)
    print("FINAL RECOMMENDATION")
    print("=" * 70)
    
    rating_changed = abs(results['early_late']['rating_change']) > 50
    split_diff = results['split_comparison']['difference'] > 0.03
    
    if rating_changed or split_diff:
        print(" STRONG RECOMMENDATION: Use time-based splitting")
        print("\nReasons:")
        if rating_changed:
            print(f"  • Your rating changed by {results['early_late']['rating_change']:+.0f} points")
        if split_diff:
            print(f"  • Random split gives {results['split_comparison']['difference']:.1%} inflated accuracy")
        print("\nTime-based splitting will:")
        print("   Give more realistic performance estimates")
        print("   Test on your current skill level")
        print("   Better predict future game outcomes")
    else:
        print(" MODERATE RECOMMENDATION: Use time-based splitting")
        print("\nWhile your performance is relatively stable, time-based splitting is still")
        print("best practice for temporal data like chess games.")
    
    print("=" * 70 + "\n")
    
    return results


# ==============================================================================
# CONVENIENCE FUNCTIONS for interactive use
# ==============================================================================

def fetch_and_analyze(username, months_back=3):
    """
    Fetch fresh data from Chess.com and run full analysis.
    
    This is the recommended way to use this script - it fetches
    the latest data directly from Chess.com and analyzes it.
    
    Args:
        username: Chess.com username
        months_back: Number of recent months to fetch (default=3)
        
    Returns:
        Dictionary with all analysis results
    """
    df = fetch_fresh_data(username, months_back)
    return run_full_analysis(df=df)


def quick_check_fresh(username, months_back=3):
    """
    Quick validation check with fresh data from Chess.com.
    
    Args:
        username: Chess.com username
        months_back: Number of recent months to fetch (default=3)
    """
    df = fetch_fresh_data(username, months_back)
    compare_early_late_performance(df)
    compare_split_methods(df)


def quick_check(username=None, df=None):
    """
    Quick validation check - just the essential tests.
    
    Args:
        username: Chess.com username (will try to load from disk)
        df: Or pass DataFrame directly
    """
    if df is None:
        if username is None:
            raise ValueError("Must provide either username or df")
        try:
            df = load_chess_data(username)
        except FileNotFoundError:
            print("\n  No saved data found. Fetching fresh data from Chess.com...")
            df = fetch_fresh_data(username, months_back=3)
    
    compare_early_late_performance(df)
    compare_split_methods(df)


# ==============================================================================
# MAIN - Run when script is executed directly
# ==============================================================================

if __name__ == "__main__":
    # Example usage
    print(__doc__)
    print("\n" + "=" * 70)
    print("USAGE EXAMPLES")
    print("=" * 70)
    print("\n1. Fetch fresh data and analyze (RECOMMENDED):")
    print("   results = fetch_and_analyze('RhysLWells')")
    print("   results = fetch_and_analyze('RhysLWells', months_back=6)")
    
    print("\n2. Quick check with fresh data:")
    print("   quick_check_fresh('RhysLWells')")
    
    print("\n3. Use saved data (if available):")
    print("   results = run_full_analysis('RhysLWells')")
    
    print("\n4. Use DataFrame already loaded:")
    print("   results = run_full_analysis(df=your_dataframe)")
    
    print("\n5. Quick check with saved data:")
    print("   quick_check('RhysLWells')")
    print("=" * 70 + "\n")

# # From notebooks folder
# cd notebooks
# ipython

# # Load the script
# %run temporal_validation.py

# # METHOD 1: Fetch fresh data and analyze (RECOMMENDED)
results = fetch_and_analyze('RhysLWells')
# # Or specify how many months to fetch
# results = fetch_and_analyze('RhysLWells', months_back=6)

# # METHOD 2: Quick check with fresh data
# quick_check_fresh('RhysLWells')
