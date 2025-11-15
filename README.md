# Chess Game Analysis Dashboard

## Overview

This project provides an interactive Streamlit-based dashboard for analysing chess games from Chess.com. It offers on-demand retrieval of user games, performance analysis, opening insights, and a modular machine learning component to support further exploration. The system is designed to be lightweight, easy to deploy, and accessible to users without technical guidance.

A live version of the application is available here:

**[Streamlit Application Link](<insert-link-here>)**

The dashboard accepts **any Chess.com username**, retrieves available games for that player, and performs analysis directly in-app.

---

## Features

### On-Demand Game Retrieval
- Users enter a Chess.com username and optional time window.
- The system fetches all available games using the Chess.com public API.
- Newly fetched games are merged into a local dataset stored on the server.
- Data is stored in simple CSV format for transparency and low overhead.

### Performance Analysis
- Summary statistics for wins, losses, draws.
- Trends against higher- and lower-rated opponents.
- Visualisation of game outcomes over time.
- Aggregated opening usage and success metrics.

### Opening Classifier (Modular ML Feature)
- A standalone Random Forest classifier predicts expected performance for each opening.
- Inputs may include opening name, ECO code, player rating, opponent rating, and game metadata.
- Outputs probability estimates for favourable outcomes.
- Fully modular: the ML component can be added or removed without affecting the dashboard.

### Game Exploration
- Interactive game table with filters.
- Each game includes a direct link to the full record on Chess.com.
- Optional PNG display if game images are retrieved.
- Supports quick inspection without implementing a full chessboard viewer.

### Dashboard Interface
- Built with **Streamlit** for rapid prototyping and end-user accessibility.
- Clear sections for data ingestion, metrics, classifier results, and game browsing.
- Designed to allow future expansion with minimal refactoring.

---

## Installation

### Using uv

1. Install uv if required:

```bash
pip install uv
````

2. Install project dependencies using the `pyproject.toml`:

```bash
uv sync
```

3. Launch the dashboard:

```bash
uv run streamlit run app.py
```

---

## Project Structure | FIX

```
chess-analysis/
├── data/                     # Local CSV game storage
├── app.py                    # Main Streamlit entry point
├── data_ingestion.py         # API calls and local storage logic
├── analysis.py               # Performance metrics and plots
├── opening_classifier.py     # Random Forest classifier module
├── utils.py                  # Helper utilities
├── pyproject.toml            # Project configuration for uv
└── README.md
```

---

## Extensibility

This project is intended as a foundation for more advanced chess analytics. Possible extensions include:

* Time control segmentation.
* Clustering of opponent styles.
* Opening repertoire profiling.
* Anomaly detection in performance.
* Integration of additional APIs (Lichess, FIDE ratings).
* Automated report generation.

The modular structure supports adding new analytical or machine learning components with minimal disruption to existing code.

---

## Contributing

Contributions, extensions, and refactor proposals are welcome. Please open an issue or submit a pull request.