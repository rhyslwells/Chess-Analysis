import os
import re

# --------- Emoji removal regex ----------
emoji_pattern = re.compile(
    "[" 
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA70-\U0001FAFF"  # extended pictographs
    "]+",
    flags=re.UNICODE
)

def clean_python_files(root_folder):
    log_path = os.path.join(root_folder, "emoji_clean_log.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("Emoji Cleaning Log\n")
        log.write("------------------\n\n")

        for root, dirs, files in os.walk(root_folder):
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
                        count = len(matches)

                        if count > 0:
                            emoji_count_total += count
                            line_records.append((idx, matches))

                        cleaned_line = emoji_pattern.sub("", line)
                        cleaned_lines.append(cleaned_line)

                    if emoji_count_total > 0:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(cleaned_lines)

                        log.write(f"File: {file_path}\n")
                        log.write(f"Total emojis removed: {emoji_count_total}\n")
                        for line_no, found in line_records:
                            log.write(f"  Line {line_no}: {''.join(found)}\n")
                        log.write("\n")

                        print(f"Cleaned {file_path} (removed {emoji_count_total} emojis)")
                    else:
                        print(f"No emojis: {file_path}")

    print(f"\nLog written to: {log_path}")


if __name__ == "__main__":
    folder = "/path/to/your/folder"
    clean_python_files(folder)
