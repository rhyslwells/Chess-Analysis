# -------------------------------------------------------------
# Convert a merged PGN file into a CSV of game-level records
# -------------------------------------------------------------
import chess.pgn
import pandas as pd

INPUT_PGN = "../data/all_games_merged.pgn"
OUTPUT_CSV = "../data/all_games_merged.csv"

records = []

with open(INPUT_PGN, "r", encoding="utf-8") as f:
    while True:
        game = chess.pgn.read_game(f)
        if game is None:   # No more games
            break
        
        headers = game.headers

        # Extract SAN moves for readability
        moves = []
        node = game
        board = game.board()
        while node.variations:
            next_node = node.variation(0)
            san = board.san(next_node.move)
            moves.append(san)
            board.push(next_node.move)
            node = next_node

        record = {
            "date": headers.get("UTCDate"),
            "time": headers.get("UTCTime"),
            "white": headers.get("White"),
            "black": headers.get("Black"),
            "white_elo": headers.get("WhiteElo"),
            "black_elo": headers.get("BlackElo"),
            "result": headers.get("Result"),
            "time_control": headers.get("TimeControl"),
            "eco": headers.get("ECO"),
            "opening": headers.get("Opening"),
            "termination": headers.get("Termination"),
            "moves_san": " ".join(moves)
        }

        records.append(record)

# Convert to DataFrame
df = pd.DataFrame(records)

# Save to CSV
df.to_csv(OUTPUT_CSV, index=False)

print(f"Saved {len(df)} games to {OUTPUT_CSV}")
df.head()
