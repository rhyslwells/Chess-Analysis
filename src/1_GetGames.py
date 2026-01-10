# -------------------------------------------------------------
# Chess.com Game Fetcher for User "rhyslwells"
#
# This script:
#   1. Queries the Chess.com Published Data API
#   2. Lists all monthly archives for the user
#   3. Downloads each month's games in PGN format
#   4. Stores all PGNs in a folder for later parsing
#
# Notes:
#   - The API is publicly accessible; no key required.
#   - Always include a User-Agent header (good API practice).
#   - You can later parse PGNs using python-chess.
#
# -------------------------------------------------------------

import os
import requests

# -------------------------------------------------------------
# Settings
# -------------------------------------------------------------
USERNAME = "rhyslwells"
OUTPUT_DIR = "../data/chess_com_pgns"

# Good practice for this API
HEADERS = {
    "User-Agent": "Rhys Chess Downloader (contact: your-email@example.com)"
}

# Create output directory if needed
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------------------
# Step 1: Get list of monthly archives
# Endpoint: https://api.chess.com/pub/player/{username}/games/archives
# -------------------------------------------------------------
archives_url = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"
response = requests.get(archives_url, headers=HEADERS)

if response.status_code != 200:
    raise RuntimeError(
        f"Error querying archives. Status code: {response.status_code}"
    )

archives = response.json().get("archives", [])
print(f"Found {len(archives)} month archives for user: {USERNAME}")

# -------------------------------------------------------------
# Step 2: Download each archive's PGN file
# Each month endpoint supports a `/pgn` suffix
# -------------------------------------------------------------
for month_url in archives:
    pgn_url = month_url + "/pgn"
    month = month_url.rsplit("/", 2)[-2] + "_" + month_url.rsplit("/", 1)[-1]
    pgn_path = os.path.join(OUTPUT_DIR, f"{month}.pgn")
    print(f"Downloading PGN for: {month}")

    r = requests.get(pgn_url, headers=HEADERS)
    if r.status_code != 200:
        print(f"  Failed for {month} (status: {r.status_code})")
        continue

    # Write PGN file
    pgn_path = os.path.join(OUTPUT_DIR, f"{month}.pgn")
    with open(pgn_path, "w", encoding="utf-8") as f:
        f.write(r.text)

print("Download complete.")
print(f"PGN files saved in folder: {OUTPUT_DIR}")

# -------------------------------------------------------------
# Merge all PGN files into a single consolidated PGN file
# -------------------------------------------------------------
import glob

INPUT_DIR = "../data/chess_com_pgns"
OUTPUT_FILE = "../data/all_games_merged.pgn"

pgn_files = sorted(glob.glob(f"{INPUT_DIR}/*.pgn"))

with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    for fpath in pgn_files:
        with open(fpath, "r", encoding="utf-8") as infile:
            outfile.write(infile.read())
            outfile.write("\n\n")  # separate games safely

print(f"Combined {len(pgn_files)} PGN files into: {OUTPUT_FILE}")
