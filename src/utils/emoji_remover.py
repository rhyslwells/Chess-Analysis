import os
import re

# --------- Emoji/symbol removal regex (expanded) ----------
emoji_pattern = re.compile(
    "[" 
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA70-\U0001FAFF"  # extended pictographs
    "\u2600-\u26FF"          # miscellaneous symbols (includes ⚪ ⚫)
    "\uFE0F"                 # variation selector
    "]+",
    flags=re.UNICODE
)

# --------- Folders to focus on ----------
FOCUS_FOLDERS = {
    "src",
    "tests",
    "notebooks",
}

def clean_python_files():
    # Compute PROJECT ROOT (two level up from this script)
    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )

    log_path = os.path.join(PROJECT_ROOT, "emoji_clean_log.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("Emoji Cleaning Log\n")
        log.write("------------------\n\n")

        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Get the relative path from project root
            rel_path = os.path.relpath(root, PROJECT_ROOT)
            
            # Check if current directory or any parent is in FOCUS_FOLDERS
            path_parts = rel_path.split(os.sep)
            is_focused = any(part in FOCUS_FOLDERS for part in path_parts)
            
            # Skip if not in a focused folder (unless we're at root level)
            if rel_path != "." and not is_focused:
                continue

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    emoji_count_total = 0
                    line_records = []
                    cleaned_lines = []

                    for idx, line in enumerate(lines, start=1):
                        matches = emoji_pattern.findall(line)
                        if matches:
                            emoji_count_total += len(matches)
                            line_records.append((idx, matches))
                        cleaned_lines.append(emoji_pattern.sub("", line))

                    # Only rewrite if emojis found
                    if emoji_count_total > 0:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(cleaned_lines)

                        log.write(f"File: {file_path}\n")
                        log.write(f"Total emojis removed: {emoji_count_total}\n")
                        for ln, found in line_records:
                            log.write(f"  Line {ln}: {''.join(found)}\n")
                        log.write("\n")

                        print(f"Cleaned {file_path} (removed {emoji_count_total} emojis)")
                    else:
                        print(f"No emojis: {file_path}")

    print(f"\nLog written to: {log_path}")


if __name__ == "__main__":
    clean_python_files()