# Chess Analysis Tests

## Overview

This directory contains unit and integration tests for the Chess Analysis Dashboard project. The tests are organized into two main categories:

1. **Unit Tests**: These tests mock external dependencies (Chess.com API, file I/O) and test the core functionality of individual components in isolation.
2. **Integration Tests**: These tests interact with the actual Chess.com API to verify real-world behavior.

## Test Structure

### Unit Tests

Unit tests use mocking to isolate components and test their logic without external dependencies.

#### `test_data_fetcher.py`
Tests the `ChessDataFetcher` class methods with mocked API responses.

**Test Coverage:**
- **API Fetching**: 
  - `test_fetch_games_success`: Successful game retrieval from API
  - `test_fetch_games_api_error`: Handling of API errors
  - `test_fetch_multiple_months`: Fetching across date ranges
  
- **JSON Parsing**:
  - `test_parse_game_from_json_white_win`: Parsing wins as white
  - `test_parse_game_from_json_black_loss`: Parsing losses as black
  - `test_parse_game_from_json_draw`: Parsing draw outcomes
  - `test_parse_game_from_json_missing_pgn`: Handling missing PGN data
  
- **PGN Parsing**:
  - `test_parse_game_from_pgn`: Converting PGN objects to structured data
  - `test_pgn_to_dataframe`: Processing PGN files into DataFrames
  
- **Data Processing**:
  - `test_process_and_save_json_mode`: Processing API responses
  - `test_process_and_save_removes_duplicates`: Deduplication logic
  - `test_process_and_save_sorts_by_timestamp`: Chronological ordering
  
- **Edge Cases**:
  - `test_parse_game_with_timeout_result`: Timeout handling
  - `test_parse_game_with_abandoned_result`: Abandoned game handling
  - `test_eco_url_fallback`: Opening name extraction from URLs

#### `test_analyzer.py`
Tests the `ChessAnalyzer` class methods with sample game data.

**Test Coverage:**
- **Initialization**:
  - `test_initialization`: Proper setup and derived features
  - `test_derived_features_rating_diff`: Rating difference calculation
  - `test_derived_features_opponent_category`: Opponent strength categorization
  - `test_derived_features_date_conversion`: DateTime handling
  
- **Overall Statistics**:
  - `test_get_overall_stats`: General performance metrics
  - `test_get_overall_stats_win_rate_calculation`: Win rate accuracy
  - `test_get_overall_stats_elo_progression`: Rating change tracking
  - `test_get_overall_stats_empty_dataframe`: Edge case with no data
  
- **Performance Analysis**:
  - `test_get_performance_by_opponent_strength`: Performance vs opponent rating
  - `test_get_color_performance`: White vs Black performance
  - `test_get_time_control_stats`: Performance by time control
  
- **Opening Analysis**:
  - `test_get_opening_stats`: Opening frequency and win rates
  - `test_get_opening_stats_win_rate_calculation`: Percentage calculations
  
- **Rating Analysis**:
  - `test_get_rating_trend`: Rating progression over time
  - `test_get_rating_volatility`: Rating stability metrics
  - `test_get_rating_volatility_with_stable_rating`: Edge case testing
  
- **Time Series**:
  - `test_get_results_over_time_monthly`: Monthly aggregation
  - `test_get_results_over_time_weekly`: Weekly aggregation
  - `test_get_results_over_time_daily`: Daily aggregation
  
- **Game Length**:
  - `test_get_game_length_stats`: Duration statistics
  - `test_get_game_length_by_result`: Duration by outcome
  - `test_get_game_length_stats_without_duration`: Missing data handling
  
- **ML Features**:
  - `test_prepare_ml_features`: Feature matrix preparation
  - `test_prepare_ml_features_target_encoding`: Binary target encoding
  - `test_prepare_ml_features_is_white_encoding`: Color encoding
  
- **Edge Cases**:
  - `test_opponent_category_boundaries`: Rating difference boundaries
  - `test_single_game_dataframe`: Minimum viable dataset

### Integration Tests

Integration tests make real API calls to Chess.com. These tests verify that the application works correctly with live data.

#### `test_data_fetcher_integration.py`
Tests `ChessDataFetcher` with real Chess.com API interactions.

**⚠️ Warning**: These tests make actual HTTP requests to Chess.com's API. Run them sparingly to avoid rate limiting.

**Test Coverage:**
- **Real API Calls**:
  - `test_fetch_games_real_api`: Fetching from live API
  - `test_fetch_games_invalid_username`: Non-existent user handling
  - `test_fetch_games_future_month`: Future date handling
  - `test_fetch_multiple_months_real_api`: Multi-month fetching
  
- **Data Parsing**:
  - `test_parse_real_game_data`: Real game data structure
  - `test_process_and_save_real_data`: End-to-end processing
  - `test_pgn_parsing_real_data`: PGN field extraction
  
- **API Behavior**:
  - `test_api_rate_limiting`: Rate limit compliance
  - `test_different_time_controls`: Multiple game types
  - `test_user_played_both_colors`: Color variety
  
- **Large Datasets** (marked `@pytest.mark.slow`):
  - `test_fetch_large_date_range`: Extended date ranges

**Test Username**: Tests use the public profile `"hikaru"` which has extensive game history.

## Running the Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-mock pytest-cov
```

### Run All Unit Tests

```bash
pytest test_data_fetcher.py test_analyzer.py -v
```

### Run Specific Test File

```bash
pytest test_data_fetcher.py -v
pytest test_analyzer.py -v
```

### Run Specific Test Function

```bash
pytest test_data_fetcher.py::TestChessDataFetcher::test_fetch_games_success -v
```

### Run Integration Tests

Integration tests are marked with `@pytest.mark.integration` and skipped by default.

To run integration tests:
```bash
pytest test_data_fetcher_integration.py -v -m integration
```

**⚠️ Important**: Integration tests make real API calls. Be mindful of:
- Rate limiting (tests include delays)
- Internet connectivity requirements
- Potential for API changes breaking tests

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Only Fast Tests

Skip slow integration tests:
```bash
pytest -v -m "not slow"
```

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.integration`: Tests requiring real API calls
- `@pytest.mark.slow`: Tests that take longer to execute

View all markers:
```bash
pytest --markers
```

## Continuous Integration

For CI/CD pipelines, run only unit tests to avoid API rate limits:

```bash
pytest test_data_fetcher.py test_analyzer.py --cov=src --cov-report=xml
```

## Test Data

### Unit Test Fixtures

Unit tests use fixtures that create realistic sample data:

- `sample_game_json`: Mock Chess.com API response
- `sample_pgn_text`: Sample PGN format game
- `sample_games_df`: 20-game DataFrame with varied outcomes
- `analyzer`: Initialized `ChessAnalyzer` instance

### Integration Test Data

Integration tests use public Chess.com profiles:
- Default username: `"hikaru"` (professional player with extensive history)
- You can modify `test_username` fixture to use different profiles

## Troubleshooting

### Integration Tests Failing

**Problem**: `test_data_fetcher_integration.py` tests fail

**Solutions**:
1. Check internet connection
2. Verify Chess.com API is accessible
3. Try a different username if current one is private/deleted
4. Increase sleep delays if hitting rate limits

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Run tests from project root:
```bash
cd /path/to/chess-analysis-dashboard
pytest tests/
```

Or add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Mock Warnings

**Problem**: Warnings about mock objects

**Solution**: This is normal. Mocks simulate external dependencies. Warnings can be suppressed:
```bash
pytest -p no:warnings
```

## Contributing Tests

When adding new features:

1. **Write unit tests first** (TDD approach)
2. Mock external dependencies
3. Test edge cases and error conditions
4. Add integration tests only if verifying external API behavior
5. Update this README with new test descriptions

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<functionality>_<scenario>`

Example: `test_parse_game_from_json_black_loss`

## Code Coverage Goals

Aim for:
- **Unit tests**: >90% coverage of `src/` modules
- **Integration tests**: Focus on critical paths and API interactions

Check current coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Chess.com API documentation](https://www.chess.com/news/view/published-data-api)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)