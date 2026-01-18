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
    # "src",
    # "tests",
    "notebooks"
}

def clean_python_files():
    # Compute PROJECT ROOT (two level up from this script)
    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )

    # Create log in the same directory as this script (src/utils)
    log_path = os.path.join(os.path.dirname(__file__), "emoji_clean_log.txt")

    files_processed = 0
    files_with_emojis = 0

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("Emoji Cleaning Log\n")
        log.write("------------------\n\n")

        for focus_folder in FOCUS_FOLDERS:
            focus_path = os.path.join(PROJECT_ROOT, focus_folder)
            
            # Skip if the focused folder doesn't exist
            if not os.path.exists(focus_path):
                msg = f"Skipping {focus_folder} (doesn't exist)"
                print(msg)
                log.write(f"{msg}\n\n")
                continue
            
            log.write(f"Processing folder: {focus_folder}\n")
            log.write("=" * 50 + "\n\n")
            
            for root, dirs, files in os.walk(focus_path):
                for file in files:
                    if file.endswith(".py") or file.endswith(".md"):
                        file_path = os.path.join(root, file)
                        files_processed += 1

                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                        except Exception as e:
                            error_msg = f"Error reading {file_path}: {e}"
                            print(error_msg)
                            log.write(f"{error_msg}\n\n")
                            continue

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
                            files_with_emojis += 1
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.writelines(cleaned_lines)

                            log.write(f"File: {file_path}\n")
                            log.write(f"Total emojis removed: {emoji_count_total}\n")
                            for ln, found in line_records:
                                log.write(f"  Line {ln}: {''.join(found)}\n")
                            log.write("\n")

                            print(f"✓ Cleaned {file_path} (removed {emoji_count_total} emojis)")
                        else:
                            log.write(f"No emojis found: {file_path}\n\n")
                            print(f"○ No emojis: {file_path}")

        log.write("\n" + "=" * 50 + "\n")
        log.write(f"SUMMARY\n")
        log.write(f"Files processed: {files_processed}\n")
        log.write(f"Files with emojis: {files_with_emojis}\n")

    print(f"\n{'=' * 50}")
    print(f"SUMMARY:")
    print(f"Files processed: {files_processed}")
    print(f"Files with emojis: {files_with_emojis}")
    print(f"Log written to: {log_path}")


if __name__ == "__main__":
    clean_python_files()