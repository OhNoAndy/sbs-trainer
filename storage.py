"""
storage.py - saving and loading the program as a JSON file.

The whole app state is one dictionary (see program_logic.create_program).
json.dump writes it to user_data/program.json and json.load reads it back.
That is the entire persistence layer: no database, no ORM.
"""
import datetime
import json
import os

# Paths are built from this file's location so the app works no matter which
# folder you launch "streamlit run app.py" from.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(PROJECT_DIR, "user_data")
PROGRAM_PATH = os.path.join(USER_DATA_DIR, "program.json")
DEMO_PATH = os.path.join(PROJECT_DIR, "data", "demo_program.json")


def save_program(program, path=PROGRAM_PATH):
    """
    Write the program dict to disk as JSON.

    Takes: program dict, optional file path. Returns: nothing.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(program, file, indent=2)


def load_program(path=PROGRAM_PATH):
    """
    Read a program dict back from disk.

    Takes: optional file path. Returns: the dict, or None if the file is missing
    or unreadable.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return None


def program_exists(path=PROGRAM_PATH):
    """Takes an optional path. Returns True when a saved program file exists."""
    return os.path.exists(path)


def backup_program(path=PROGRAM_PATH):
    """
    Copy the saved program to a timestamped backup file before a destructive action.

    Takes: optional path. Returns: the backup file path, or None if nothing to back up.
    """
    program = load_program(path)
    if program is None:
        return None
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(os.path.dirname(path), "program_backup_" + stamp + ".json")
    save_program(program, backup_path)
    return backup_path


def delete_program(path=PROGRAM_PATH):
    """
    Remove the saved program file (a backup is made first).

    Takes: optional path. Returns: the backup path, or None if there was no file.
    """
    backup_path = backup_program(path)
    if os.path.exists(path):
        os.remove(path)
    return backup_path


def load_demo_program():
    """Returns the bundled demo program dict (data/demo_program.json), or None."""
    return load_program(DEMO_PATH)


def program_to_json_text(program):
    """Takes a program dict. Returns it as a JSON string (for the export button)."""
    return json.dumps(program, indent=2)


def program_from_json_text(text):
    """
    Turn uploaded JSON text back into a program dict.

    Takes: a string. Returns: the dict, or None if the text is not a program.
    """
    try:
        program = json.loads(text)
    except ValueError:
        return None
    if not isinstance(program, dict) or "lifts" not in program or "variant" not in program:
        return None
    return program
