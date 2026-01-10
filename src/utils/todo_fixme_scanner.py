import os
import re

# --------- Comment markers to scan for ----------
COMMENT_MARKERS = [
    "TODO",
    "FIXME",
    "BUG",
    "HACK",
    "NOTE"
]

pattern = re.compile(r"#\s*(TODO|FIXME|BUG|HACK|NOTE)(.*)", re.IGNORECASE)

# --------- Folders to ignore ----------
IGNORE_FOLDERS = {
    "__pycache__",
    "venv",
    ".git",
    ".history",
    ".venv",
    ".data",
    "chess_analysis.egg-info",
    "data",
    "scripts"  # Prevent scanning the utility folder
}


def scan_todos():
    # Compute project root (parent of scripts/)
    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    log_path = os.path.join(PROJECT_ROOT, "todo_report.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("TODO / FIXME / NOTE Report\n")
        log.write("----------------------------\n\n")

        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Filter ignored folders
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    entries = []
                    for idx, line in enumerate(lines, start=1):
                        m = pattern.search(line)
                        if m:
                            marker = m.group(1).upper()
                            text = m.group(2).strip()
                            entries.append((idx, marker, text))

                    if entries:
                        log.write(f"File: {file_path}\n")
                        for line_no, marker, text in entries:
                            log.write(f"  Line {line_no} [{marker}]: {text}\n")
                        log.write("\n")

                        print(f"Found markers in {file_path}")
                    else:
                        print(f"No markers: {file_path}")

    print(f"\nLog written to: {log_path}")


if __name__ == "__main__":
    scan_todos()
