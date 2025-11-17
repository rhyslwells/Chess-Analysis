import os
import re

LONG_COMMENT_LIMIT = 100

code_like_pattern = re.compile(
    r"#\s*(def |class |import |from |for |while |if |elif |else:|try:|except|return )",
    re.IGNORECASE
)

todo_pattern = re.compile(r"#\s*(TODO|FIXME|BUG|HACK|NOTE)(.*)", re.IGNORECASE)

def check_comment_health(root_folder):
    log_path = os.path.join(root_folder, "comment_health_report.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("Comment Health Report\n")
        log.write("---------------------\n\n")

        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    long_comments = []
                    commented_code = []
                    empty_comments = []
                    streaks = []

                    current_streak = 0

                    for idx, line in enumerate(lines, start=1):
                        stripped = line.strip()

                        if stripped.startswith("#"):
                            # Comment streak counter
                            current_streak += 1

                            # Empty comment
                            if stripped == "#":
                                empty_comments.append(idx)

                            # Long comment
                            if len(stripped) > LONG_COMMENT_LIMIT:
                                long_comments.append((idx, len(stripped)))

                            # Commented-out code detection
                            if code_like_pattern.search(stripped):
                                commented_code.append((idx, stripped))

                        else:
                            # End streak
                            if current_streak >= 8:
                                streaks.append((idx - current_streak, current_streak))
                            current_streak = 0

                    # If file ended during a streak
                    if current_streak >= 8:
                        streaks.append((len(lines) - current_streak + 1, current_streak))

                    # Only log if issues found
                    if any([long_comments, commented_code, empty_comments, streaks]):
                        log.write(f"File: {file_path}\n")

                        if long_comments:
                            log.write("  Long comments:\n")
                            for line_no, length in long_comments:
                                log.write(f"    Line {line_no}: {length} chars\n")

                        if commented_code:
                            log.write("  Commented-out code:\n")
                            for line_no, text in commented_code:
                                log.write(f"    Line {line_no}: {text}\n")

                        if empty_comments:
                            log.write("  Empty comments (dangling '#'):\n")
                            for line_no in empty_comments:
                                log.write(f"    Line {line_no}\n")

                        if streaks:
                            log.write("  High-density comment blocks:\n")
                            for start_line, count in streaks:
                                log.write(f"    Lines {start_line}-{start_line+count-1}: {count} consecutive comments\n")

                        log.write("\n")
                        print(f"Issues found in: {file_path}")
                    else:
                        print(f"No issues: {file_path}")

    print(f"\nLog written to: {log_path}")


if __name__ == "__main__":
    folder = "/path/to/your/folder"
    check_comment_health(folder)
