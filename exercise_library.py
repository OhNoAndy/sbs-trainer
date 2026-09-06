"""
exercise_library.py - the exercise catalog and image lookup.

The catalog (data/exercises.json) and the photos in data/images/ come from
yuhonas/free-exercise-db (https://github.com/yuhonas/free-exercise-db), a
public-domain dataset fetched once by scripts/fetch_exercises.py. Nothing in
this file touches the network, so the app works offline.

How an SBS lift name turns into a picture:
  1. SBS_IMAGE_OVERRIDES - hand-written matches for names that do not line
     up with the dataset ("Paused Squat", "Block Pull", "Close Grip Bench").
  2. An exact match on the cleaned-up name.
  3. A simple fuzzy match: one name contains the other, or they share words.
  4. The placeholder image if nothing matched.
A lift can also point at the user's own image file, which wins over all of that.
"""
import json
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
CATALOG_PATH = os.path.join(DATA_DIR, "exercises.json")
PLACEHOLDER_PATH = os.path.join(IMAGES_DIR, "placeholder.png")

# Cleaned-up SBS name -> dataset id. Keys are written the way normalize_name
# produces them: lowercase, no punctuation, single spaces.
SBS_IMAGE_OVERRIDES = {
    # Squat family
    "squat": "Barbell_Squat",
    "back squat": "Barbell_Squat",
    "high bar squat": "Barbell_Full_Squat",
    "low bar squat": "Barbell_Squat",
    "front squat": "Front_Barbell_Squat",
    "paused squat": "Barbell_Full_Squat",
    "pause squat": "Barbell_Full_Squat",
    "box squat": "Box_Squat",
    "pin squat": "Barbell_Squat",
    "beltless squat": "Barbell_Squat",
    "safety bar squat": "Barbell_Squat",
    "ssb squat": "Barbell_Squat",
    "wide stance squat": "Wide_Stance_Barbell_Squat",
    "wider stance squat": "Wide_Stance_Barbell_Squat",
    "narrow stance squat": "Narrow_Stance_Squats",
    "narrower stance squat": "Narrow_Stance_Squats",
    "tempo squat": "Barbell_Squat",
    "squat with slow eccentric": "Barbell_Squat",
    "half squat": "Barbell_Squat",
    "good morning": "Good_Morning",
    "leg press": "Leg_Press",
    "hack squat": "Hack_Squat",
    "bulgarian split squat": "Split_Squat_with_Dumbbells",
    "lunges": "Barbell_Lunge",
    "lunge": "Barbell_Lunge",
    "zercher squat": "Zercher_Squats",
    "goblet squat": "Goblet_Squat",
    # Bench family
    "bench press": "Barbell_Bench_Press_-_Medium_Grip",
    "bench": "Barbell_Bench_Press_-_Medium_Grip",
    "competition bench": "Barbell_Bench_Press_-_Medium_Grip",
    "close grip bench": "Close-Grip_Barbell_Bench_Press",
    "close grip bench press": "Close-Grip_Barbell_Bench_Press",
    "wide grip bench": "Wide-Grip_Barbell_Bench_Press",
    "wider grip bench": "Wide-Grip_Barbell_Bench_Press",
    "incline press": "Barbell_Incline_Bench_Press_-_Medium_Grip",
    "incline bench": "Barbell_Incline_Bench_Press_-_Medium_Grip",
    "incline bench press": "Barbell_Incline_Bench_Press_-_Medium_Grip",
    "decline bench": "Decline_Barbell_Bench_Press",
    "paused bench": "Barbell_Bench_Press_-_Medium_Grip",
    "long pause bench": "Barbell_Bench_Press_-_Medium_Grip",
    "spoto press": "Barbell_Bench_Press_-_Medium_Grip",
    "board press": "Board_Press",
    "pin press": "Pin_Presses",
    "floor press": "Floor_Press",
    "feet up bench": "Barbell_Bench_Press_-_Medium_Grip",
    "bench with feet up": "Barbell_Bench_Press_-_Medium_Grip",
    "tempo bench": "Barbell_Bench_Press_-_Medium_Grip",
    "bench with slow eccentric": "Barbell_Bench_Press_-_Medium_Grip",
    "slingshot bench": "Bench_Press_-_With_Bands",
    "dumbbell bench": "Dumbbell_Bench_Press",
    "db bench": "Dumbbell_Bench_Press",
    "dumbbell bench press": "Dumbbell_Bench_Press",
    "weighted dips": "Dips_-_Chest_Version",
    "dips": "Dips_-_Triceps_Version",
    # Deadlift family
    "deadlift": "Barbell_Deadlift",
    "conventional deadlift": "Barbell_Deadlift",
    "sumo deadlift": "Sumo_Deadlift",
    "block pull": "Rack_Pulls",
    "block pulls": "Rack_Pulls",
    "rack pull": "Rack_Pulls",
    "rack pulls": "Rack_Pulls",
    "deficit deadlift": "Deficit_Deadlift",
    "paused deadlift": "Barbell_Deadlift",
    "romanian deadlift": "Romanian_Deadlift",
    "rdl": "Romanian_Deadlift",
    "stiff leg deadlift": "Stiff-Legged_Barbell_Deadlift",
    "stiff legged deadlift": "Stiff-Legged_Barbell_Deadlift",
    "snatch grip deadlift": "Snatch_Deadlift",
    "trap bar deadlift": "Trap_Bar_Deadlift",
    # Overhead press family
    "overhead press": "Standing_Military_Press",
    "ohp": "Standing_Military_Press",
    "military press": "Standing_Military_Press",
    "press": "Standing_Military_Press",
    "strict press": "Standing_Military_Press",
    "push press": "Push_Press",
    "seated ohp": "Seated_Barbell_Military_Press",
    "seated press": "Seated_Barbell_Military_Press",
    "behind the neck press": "Standing_Barbell_Press_Behind_Neck",
    "behind the neck ohp": "Standing_Barbell_Press_Behind_Neck",
    "z press": "Seated_Barbell_Military_Press",
    "dumbbell ohp": "Dumbbell_Shoulder_Press",
    "db ohp": "Dumbbell_Shoulder_Press",
    "dumbbell shoulder press": "Dumbbell_Shoulder_Press",
    "log press": "Log_Lift",
    "axle press": "Standing_Military_Press",
    "landmine press": "Standing_Military_Press",
    # Upper back
    "barbell row": "Bent_Over_Barbell_Row",
    "barbell rows": "Bent_Over_Barbell_Row",
    "bent over row": "Bent_Over_Barbell_Row",
    "pendlay row": "Bent_Over_Barbell_Row",
    "dumbbell row": "One-Arm_Dumbbell_Row",
    "db row": "One-Arm_Dumbbell_Row",
    "db rows": "One-Arm_Dumbbell_Row",
    "chest supported row": "Dumbbell_Incline_Row",
    "chest supported rows": "Dumbbell_Incline_Row",
    "t bar row": "T-Bar_Row_with_Handle",
    "t bar rows": "T-Bar_Row_with_Handle",
    "pull up": "Pullups",
    "pull ups": "Pullups",
    "pullup": "Pullups",
    "pullups": "Pullups",
    "weighted pull up": "Pullups",
    "chin up": "Chin-Up",
    "chin ups": "Chin-Up",
    "chinup": "Chin-Up",
    "neutral grip pull up": "V-Bar_Pullup",
    "neutral grip pull ups": "V-Bar_Pullup",
    "lat pulldown": "Wide-Grip_Lat_Pulldown",
    "close grip pulldown": "Close-Grip_Front_Lat_Pulldown",
    "close grip pulldowns": "Close-Grip_Front_Lat_Pulldown",
    "pulldown": "Wide-Grip_Lat_Pulldown",
    "pull downs": "Wide-Grip_Lat_Pulldown",
    "pulldowns": "Wide-Grip_Lat_Pulldown",
    "seated cable row": "Seated_Cable_Rows",
    "cable row": "Seated_Cable_Rows",
    # Common accessories
    "face pull": "Face_Pull",
    "lateral raise": "Side_Lateral_Raise",
    "side raise": "Side_Lateral_Raise",
    "rear delt fly": "Seated_Bent-Over_Rear_Delt_Raise",
    "rear delt raise": "Seated_Bent-Over_Rear_Delt_Raise",
    "barbell curl": "Barbell_Curl",
    "dumbbell curl": "Dumbbell_Bicep_Curl",
    "cable curl": "Standing_Biceps_Cable_Curl",
    "bicep cable curl": "Standing_Biceps_Cable_Curl",
    "dumbbell wrist curl": "Palms-Up_Dumbbell_Wrist_Curl_Over_A_Bench",
    "wrist curl": "Palms-Up_Dumbbell_Wrist_Curl_Over_A_Bench",
    "hammer curl": "Hammer_Curls",
    "triceps pushdown": "Triceps_Pushdown",
    "tricep pushdown": "Triceps_Pushdown",
    "skull crusher": "Lying_Triceps_Press",
    "skullcrusher": "Lying_Triceps_Press",
    "overhead triceps extension": "Standing_Overhead_Barbell_Triceps_Extension",
    "leg curl": "Lying_Leg_Curls",
    "leg extension": "Leg_Extensions",
    "hip thrust": "Barbell_Hip_Thrust",
    "back extension": "Hyperextensions_Back_Extensions",
    "glute ham raise": "Glute_Ham_Raise",
    "calf raise": "Standing_Calf_Raises",
    "hanging leg raise": "Hanging_Leg_Raise",
    "ab wheel": "Ab_Roller",
    "plank": "Plank",
    "cable crunch": "Cable_Crunch",
    "shrug": "Barbell_Shrug",
    "push up": "Pushups",
    "pushup": "Pushups",
    "pec deck": "Butterfly",
    "dumbbell fly": "Dumbbell_Flyes",
}

# Little words that do not help tell exercises apart.
IGNORED_WORDS = ["the", "a", "of", "with", "and", "to", "on", "in"]


def load_catalog():
    """
    Read data/exercises.json.

    Returns: a list of exercise dicts (empty if the file has not been fetched yet).
    """
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_name(name):
    """
    Clean a name so that "Close-Grip Bench" and "close grip bench" compare equal.

    Takes: any string. Returns: lowercase words separated by single spaces,
    with punctuation removed.
    """
    text = name.lower()
    for character in ["-", "_", "/", "(", ")", ",", ".", "'", "’"]:
        text = text.replace(character, " ")
    words = text.split()
    return " ".join(words)


def name_words(name):
    """
    Split a name into comparable words, dropping filler and plural endings.

    Takes: a string. Returns: a list of words such as ["rack", "pull"].
    """
    words = []
    for word in normalize_name(name).split():
        if word in IGNORED_WORDS:
            continue
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]
        words.append(word)
    return words


def catalog_by_id(catalog):
    """Takes the catalog list. Returns a dict id -> exercise entry."""
    lookup = {}
    for entry in catalog:
        lookup[entry["id"]] = entry
    return lookup


def catalog_names(catalog):
    """Takes the catalog list. Returns every exercise name, sorted."""
    names = []
    for entry in catalog:
        names.append(entry["name"])
    names.sort()
    return names


def find_exercise(name, catalog):
    """
    Find the catalog entry that best matches an exercise name.

    Takes: the name typed by the user, the catalog list.
    Returns: (entry, how) where how is "override", "exact", "contains",
             "words" or "none" (entry is None in that last case).
    """
    if not catalog or not name or not name.strip():
        return None, "none"
    cleaned = normalize_name(name)
    by_id = catalog_by_id(catalog)

    # 1. Hand-written overrides for SBS wording.
    if cleaned in SBS_IMAGE_OVERRIDES and SBS_IMAGE_OVERRIDES[cleaned] in by_id:
        return by_id[SBS_IMAGE_OVERRIDES[cleaned]], "override"

    # 2. Exact match on the cleaned-up name.
    for entry in catalog:
        if normalize_name(entry["name"]) == cleaned:
            return entry, "exact"

    # 3. One name contains the other. Prefer the shortest catalog name,
    #    which is usually the plain version of the exercise.
    best_entry = None
    for entry in catalog:
        entry_name = normalize_name(entry["name"])
        if len(cleaned) >= 4 and (cleaned in entry_name or entry_name in cleaned):
            if best_entry is None or len(entry_name) < len(normalize_name(best_entry["name"])):
                best_entry = entry
    if best_entry is not None:
        return best_entry, "contains"

    # 4. Shared words: at least half of the typed words must appear.
    query_words = name_words(name)
    if len(query_words) == 0:
        return None, "none"
    best_score = 0.0
    for entry in catalog:
        entry_words = name_words(entry["name"])
        shared = 0
        for word in query_words:
            if word in entry_words:
                shared += 1
        score = shared / len(query_words)
        shorter_name = best_entry is not None and len(entry["name"]) < len(best_entry["name"])
        if score > best_score or (score == best_score and score > 0 and shorter_name):
            best_score = score
            best_entry = entry
    if best_score >= 0.5:
        return best_entry, "words"
    return None, "none"


def image_path_for_entry(entry):
    """
    Full path of a catalog entry's photo.

    Takes: an exercise entry (or None). Returns: the path, or "" if no file exists.
    """
    if entry is None or not entry.get("image"):
        return ""
    path = os.path.join(IMAGES_DIR, entry["image"])
    if os.path.exists(path):
        return path
    return ""


def find_image_path(name, catalog, custom_path="", chosen_id=""):
    """
    The image to show for an exercise name.

    Takes: the exercise name, the catalog list, an optional path to the user's
    own image file (which wins when it exists), and an optional catalog id the
    user picked by hand in Settings (which wins over the automatic match).
    Returns: a file path, or "" if not even the placeholder is available.
    """
    if custom_path and os.path.exists(custom_path):
        return custom_path
    if chosen_id:
        chosen_path = image_path_for_entry(catalog_by_id(catalog).get(chosen_id))
        if chosen_path:
            return chosen_path
    entry, how = find_exercise(name, catalog)
    path = image_path_for_entry(entry)
    if path:
        return path
    if os.path.exists(PLACEHOLDER_PATH):
        return PLACEHOLDER_PATH
    return ""


def describe_match(name, catalog, custom_path="", chosen_id=""):
    """
    Explain which picture an exercise uses (for the Settings page).

    Takes: name, catalog, optional custom path, optional hand-picked catalog id.
    Returns: a short sentence.
    """
    if custom_path and os.path.exists(custom_path):
        return "Using your own image: " + os.path.basename(custom_path)
    if chosen_id and chosen_id in catalog_by_id(catalog):
        return "Using the library picture you picked: \"" + catalog_by_id(catalog)[chosen_id]["name"] + "\""
    entry, how = find_exercise(name, catalog)
    if entry is None or image_path_for_entry(entry) == "":
        return "No match in the exercise library, showing the placeholder"
    if how == "override":
        return "Matched to \"" + entry["name"] + "\" (built-in SBS name mapping)"
    if how == "exact":
        return "Matched to \"" + entry["name"] + "\" (exact name)"
    return "Best guess: \"" + entry["name"] + "\" (fuzzy match)"
