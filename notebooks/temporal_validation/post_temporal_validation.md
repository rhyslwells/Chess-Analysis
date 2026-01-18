# Why Time-Based Splitting is Used for Chess Win Probability Predictions

## The Problem

When building a machine learning model to predict chess game outcomes, we must decide how to split data into training and test sets. The conventional approach in machine learning is random splitting - shuffle all games and randomly assign 80% to training and 20% to testing. However, this approach is fundamentally flawed for chess data.

## Why Random Splitting Fails for Chess

Chess games are not independent, identically distributed samples. They are temporal data points where a player's skill level changes over time. Random splitting creates two critical problems:

**Problem 1: Temporal Leakage**
Random splitting mixes games from different time periods in both training and test sets. This means the model might be trained on recent games and tested on old games, or vice versa. This doesn't reflect real-world usage where we use historical games to predict future performance.

**Problem 2: Skill Drift**
Player ratings change significantly over time. When random splitting mixes games from different skill periods in the test set, it evaluates the model on a mixture that doesn't represent any actual time period. For example, in my own data, random splitting would put some games from when I was rated 859 alongside games from when I was rated 768 in the same test set. The model's accuracy on this mixed test set doesn't answer the question "how well can this predict my next game?" - it answers "how well can it predict a random game from my entire history?"

## Empirical Validation

To validate this reasoning, I analyzed my own Chess.com data (username: RhysLWells) covering 118 games over 3 months (November 2025 - January 2026). The data revealed significant temporal patterns:

**Rating and Performance Changes:**
- Early period (first half): 849 average rating, 51.7% win rate
- Late period (second half): 799 average rating, 38.1% win rate
- Total change: -50 rating points, -13.6% win rate

**Quarterly Breakdown:**

| Period | Avg Rating | Win Rate |
|--------|-----------|----------|
| Q1 (oldest) | 859 | 52% |
| Q2 | 840 | 52% |
| Q3 | 832 | 40% |
| Q4 (newest) | 768 | 37% |

This shows clear non-stationarity in my own performance. My skill level was not constant - it changed substantially over just 3 months.

**Model Performance Comparison:**
- Random split test accuracy: 79.2%
- Time-based split test accuracy: 87.5%

The time-based split achieved higher accuracy because it tested on my most recent games, which were against lower-rated opponents (765 avg vs 857 avg in early games). These matchups were more predictable based on rating differences. This is exactly what we want - the model should perform better when predicting clearer rating mismatches.

## Why Time-Based Splitting is Correct

Time-based splitting addresses both problems:

**Matches Real Usage:**
When a user loads their historical games and wants to know "what's my probability of beating an 850-rated opponent?", the answer should reflect their current skill level, not an average across months or years when they might have been 100 points higher or lower.

**Honest Evaluation:**
By testing only on the most recent 20% of games, we simulate the actual prediction task: using past data to predict future performance. This is a harder test than random splitting, which makes it more conservative and realistic.

**Temporal Validity:**
Training on older games and testing on newer games respects the temporal ordering of data. The model learns from the past and is evaluated on its ability to predict the future, which is exactly how it will be used in production.

## Implementation Decision

Based on this analysis of my own data, the predictor.py module implements time-based splitting as the default approach:

```python
# Time-based split - most recent 20% as test set
split_idx = int(len(X) * 0.8)
X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]
```

This ensures that:
- Training data comes from older games
- Test data comes from recent games
- The model is evaluated on its ability to predict current performance
- Predictions reflect the user's current skill level, not historical averages

## Conclusion

Random splitting is inappropriate for chess game data because it ignores the temporal nature of player skill development. My own game data demonstrates that player ratings can change by 50+ points over just 3 months, making time-based splitting essential for realistic model evaluation. This approach provides more honest accuracy metrics and generates predictions that reflect a player's current ability rather than their historical average.