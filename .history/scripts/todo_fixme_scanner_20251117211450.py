import os
import re

COMMENT_MARKERS = [
    "TODO",
    "FIXME",
    "BUG",
    "HACK",
    "NOTE"
]

pattern = re.compile(r"#\s*(TODO|FIXME|BUG|HACK|NOTE)(.*)", re.IGNORECASE)

def scan_todos(root_folder):
    log_path = os.path.join(root_folder, "todo_report.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("TODO / FIXME / NOTE Report\n")
        log.write("----------------------------\n\n")

        for root, dirs, files in os.walk(root_folder):
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
    folder = "/path/to/your/folder"
    scan_todos(folder)
