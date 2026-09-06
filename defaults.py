"""
defaults.py - every default number the SBS programs use, as named constants.

The program design belongs to Greg Nuckols / Stronger By Science:
    https://www.strongerbyscience.com/program-bundle/
This app is an unofficial personal project. This file only records the
default numbers so the app can reproduce the spreadsheet math, and every
value here can be changed per lift on the Settings page.

Conventions used everywhere in this project:
  * Percentages are stored as plain percentages: 70 means 70%, never 0.7.
    "intensity 70" then reads the same way in the code as it does in the gym.
  * Tables that depend on the intensity have exactly 21 entries, one for each
    percentage bucket from 50% to 100% in 2.5% steps (see PERCENTAGE_BUCKETS).
  * Tables that depend on the week have exactly 21 entries, one per week.
"""

# ---------------------------------------------------------------------------
# Program variants
# ---------------------------------------------------------------------------
VARIANT_ORIGINAL = "original"
VARIANT_LAST_SET_RIR = "last_set_rir"
VARIANT_RTF = "rtf"
VARIANT_HYPERTROPHY = "hypertrophy"

# The order the setup page lists them in. RTF first: the program author
# reports it has produced the best results for the most people.
ALL_VARIANTS = [VARIANT_RTF, VARIANT_HYPERTROPHY, VARIANT_LAST_SET_RIR, VARIANT_ORIGINAL]

# The three strength variants share intensities and rep tables.
STRENGTH_VARIANTS = [VARIANT_ORIGINAL, VARIANT_LAST_SET_RIR, VARIANT_RTF]

VARIANT_NAMES = {
    VARIANT_ORIGINAL: "SBS Strength Program (Original)",
    VARIANT_LAST_SET_RIR: "SBS Strength Program - Last Set RIR",
    VARIANT_RTF: "SBS Strength Program - Reps to Failure (RTF)",
    VARIANT_HYPERTROPHY: "SBS Hypertrophy Template",
}

# Written in our own words; the official instructions are not copied here.
VARIANT_DESCRIPTIONS = {
    VARIANT_ORIGINAL: (
        "Open-ended sets. Keep doing sets of the prescribed reps until you reach "
        "the RIR (reps in reserve) cutoff, then log how many sets you finished. "
        "Too few sets lowers your training max, extra sets raise it."
    ),
    VARIANT_LAST_SET_RIR: (
        "Fixed number of sets (5 by default). After the final set you rate how many "
        "reps you had left in the tank. More reps in reserve than the target raises "
        "your training max; fewer lowers it."
    ),
    VARIANT_RTF: (
        "Fixed number of sets (5 by default): the first four at the prescribed reps, "
        "the last one for as many reps as possible. Beat the last-set rep target and "
        "your training max goes up; fall short and it comes down."
    ),
    VARIANT_HYPERTROPHY: (
        "Same idea as Reps to Failure but with 4 sets (3 normal + 1 to failure), "
        "higher reps, and a lower intensity ceiling of 82.5%. Aimed at muscle growth."
    ),
}

# ---------------------------------------------------------------------------
# Structure of the 21-week cycle
# ---------------------------------------------------------------------------
TOTAL_WEEKS = 21
WEEKS_PER_BLOCK = 7
DELOAD_WEEKS = (7, 14, 21)

# During a deload week every variant just does its normal number of sets at the
# listed weight, 5 reps per set, with no RIR/rep target and no training max change.
DELOAD_REPS_PER_SET = 5

# ---------------------------------------------------------------------------
# Percentage buckets: 50% to 100% in 2.5% steps (21 values)
# ---------------------------------------------------------------------------
PERCENTAGE_BUCKETS = [
    50.0, 52.5, 55.0, 57.5, 60.0, 62.5, 65.0, 67.5, 70.0, 72.5, 75.0,
    77.5, 80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0, 97.5, 100.0,
]

# ---------------------------------------------------------------------------
# Weekly intensity (percent of training max) for the four main lifts.
# Weeks 7, 14 and 21 are deloads at 60%.
# ---------------------------------------------------------------------------
STRENGTH_MAIN_INTENSITIES = [
    70.0, 75.0, 80.0, 72.5, 77.5, 82.5, 60.0,   # block 1 (weeks 1-7)
    75.0, 80.0, 85.0, 77.5, 82.5, 87.5, 60.0,   # block 2 (weeks 8-14)
    80.0, 85.0, 90.0, 85.0, 90.0, 95.0, 60.0,   # block 3 (weeks 15-21)
]

HYPERTROPHY_MAIN_INTENSITIES = [
    70.0, 72.5, 75.0, 72.5, 75.0, 77.5, 60.0,   # block 1
    72.5, 75.0, 77.5, 75.0, 77.5, 80.0, 60.0,   # block 2
    75.0, 77.5, 80.0, 77.5, 80.0, 82.5, 60.0,   # block 3
]

# Auxiliary lifts follow the same shape at a lower intensity: subtract this
# many percentage points from the main-lift number for the same week.
STRENGTH_AUXILIARY_OFFSET = 10.0
HYPERTROPHY_AUXILIARY_OFFSET = 5.0

# ---------------------------------------------------------------------------
# Tables indexed by percentage bucket (21 values each, same order as
# PERCENTAGE_BUCKETS: 50, 52.5, 55, ... 100)
# ---------------------------------------------------------------------------
# How many reps to do on every set (strength family).
STRENGTH_REPS_PER_SET = [8, 8, 8, 8, 7, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1]

# Original only: stop doing sets once you reach this many reps in reserve.
ORIGINAL_RIR_CUTOFF = [5, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 0, 0]

# Last Set RIR only: how many reps in reserve the final set should have.
LAST_SET_RIR_TARGET = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0, 0]

# RTF only: rep target for the final set taken to failure.
RTF_LAST_SET_REP_TARGET = [18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 2, 1, 1, 1]

# Hypertrophy: reps on the normal sets and the rep target for the last set.
HYPERTROPHY_REPS_PER_SET = [20, 18, 17, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 2, 2, 1, 1]
HYPERTROPHY_LAST_SET_REP_TARGET = [25, 23, 21, 19, 18, 16, 15, 13, 12, 11, 10, 9, 8, 6, 5, 4, 3, 2, 2, 1, 1]

# ---------------------------------------------------------------------------
# Sets and training-max adjustment defaults
# ---------------------------------------------------------------------------
# Sets per exercise. The Original variant is open-ended in normal weeks, so its
# number is only used during deloads.
DEFAULT_SETS = {
    VARIANT_ORIGINAL: 5,
    VARIANT_LAST_SET_RIR: 5,
    VARIANT_RTF: 5,
    VARIANT_HYPERTROPHY: 4,
}

# Original variant: finish fewer sets than the lower threshold and the training
# max drops; finish more than the upper threshold and it rises.
ORIGINAL_LOWER_SET_THRESHOLD = 4
ORIGINAL_UPPER_SET_THRESHOLD = 6
ORIGINAL_INCREASE_PERCENT = 2.0
ORIGINAL_DECREASE_PERCENT = -5.0

# The graded "ladder" shared by Last Set RIR, RTF and Hypertrophy.
# Index 0 is the worst outcome, index 7 the best. See
# program_logic.ladder_index_for_difference for how an outcome picks its index.
TM_LADDER_LABELS = [
    "2+ below target",
    "1 below target",
    "Hit target",
    "Beat by 1",
    "Beat by 2",
    "Beat by 3",
    "Beat by 4",
    "Beat by 5+",
]
DEFAULT_TM_LADDER = [-5.0, -2.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0]

# A heavy single at RPE 8 (about 2 reps in reserve) is normally close to 90% of
# a true max, so single_weight / 0.90 gives a fresh training max for the day.
DEFAULT_SINGLE_AT_8_PERCENT = 90.0

DEFAULT_ROUNDING_INCREMENT = 2.5
ROUNDING_CHOICES = [0.1, 1.0, 2.5, 5.0]
UNIT_CHOICES = ["lb", "kg"]

# ---------------------------------------------------------------------------
# Lift slots and training splits
# ---------------------------------------------------------------------------
MAIN_SLOTS = ["squat", "bench", "deadlift", "ohp"]
AUXILIARY_SLOTS = ["squat_aux_1", "squat_aux_2", "bench_aux_1", "bench_aux_2", "deadlift_aux", "ohp_aux"]
ALL_SLOTS = MAIN_SLOTS + AUXILIARY_SLOTS

SLOT_LABELS = {
    "squat": "Squat (main)",
    "bench": "Bench (main)",
    "deadlift": "Deadlift (main)",
    "ohp": "Overhead press (main)",
    "squat_aux_1": "Squat auxiliary 1",
    "squat_aux_2": "Squat auxiliary 2",
    "bench_aux_1": "Bench auxiliary 1",
    "bench_aux_2": "Bench auxiliary 2",
    "deadlift_aux": "Deadlift auxiliary",
    "ohp_aux": "Overhead press auxiliary",
}

# Which slots are trained on which day, for each training frequency.
# Every lift is trained exactly once per week. The 2x split leaves out
# squat_aux_2 and bench_aux_2, just like the source spreadsheet.
TRAINING_SPLITS = {
    2: [
        ["squat", "bench", "deadlift_aux", "ohp_aux"],
        ["deadlift", "ohp", "squat_aux_1", "bench_aux_1"],
    ],
    3: [
        ["squat", "deadlift_aux", "bench_aux_2"],
        ["bench", "ohp", "squat_aux_1"],
        ["deadlift", "bench_aux_1", "squat_aux_2", "ohp_aux"],
    ],
    4: [
        ["squat", "bench_aux_2", "deadlift_aux"],
        ["bench", "squat_aux_1", "ohp_aux"],
        ["deadlift", "bench_aux_1"],
        ["ohp", "squat_aux_2"],
    ],
    5: [
        ["squat", "ohp_aux"],
        ["bench", "squat_aux_1"],
        ["deadlift", "bench_aux_1"],
        ["ohp", "squat_aux_2"],
        ["bench_aux_2", "deadlift_aux"],
    ],
    6: [
        ["squat", "bench_aux_1"],
        ["ohp_aux", "deadlift_aux"],
        ["bench", "squat_aux_1"],
        ["bench_aux_2", "squat_aux_2"],
        ["deadlift"],
        ["ohp"],
    ],
}
FREQUENCY_CHOICES = [2, 3, 4, 5, 6]

# Default exercise names for each slot. The hypertrophy template ships with
# machine-friendly auxiliaries; the strength variants use barbell variations.
STRENGTH_DEFAULT_LIFT_NAMES = {
    "squat": "Squat",
    "bench": "Bench Press",
    "deadlift": "Deadlift",
    "ohp": "Overhead Press",
    "squat_aux_1": "Front Squat",
    "squat_aux_2": "Paused Squat",
    "bench_aux_1": "Close Grip Bench",
    "bench_aux_2": "Incline Press",
    "deadlift_aux": "Sumo Deadlift",
    "ohp_aux": "Push Press",
}

HYPERTROPHY_DEFAULT_LIFT_NAMES = {
    "squat": "Squat",
    "bench": "Bench Press",
    "deadlift": "Block Pull",
    "ohp": "Overhead Press",
    "squat_aux_1": "Leg Press",
    "squat_aux_2": "Hack Squat",
    "bench_aux_1": "Incline Press",
    "bench_aux_2": "Dumbbell Bench",
    "deadlift_aux": "Romanian Deadlift",
    "ohp_aux": "Dumbbell OHP",
}

# Placeholder starting maxes shown in the setup wizard. Conservative on purpose:
# the program corrects a low guess within a few weeks.
DEFAULT_STARTING_MAXES = {
    "lb": {
        "squat": 225.0, "bench": 155.0, "deadlift": 275.0, "ohp": 95.0,
        "squat_aux_1": 185.0, "squat_aux_2": 205.0, "bench_aux_1": 145.0,
        "bench_aux_2": 135.0, "deadlift_aux": 255.0, "ohp_aux": 115.0,
    },
    "kg": {
        "squat": 100.0, "bench": 70.0, "deadlift": 125.0, "ohp": 45.0,
        "squat_aux_1": 85.0, "squat_aux_2": 90.0, "bench_aux_1": 65.0,
        "bench_aux_2": 60.0, "deadlift_aux": 115.0, "ohp_aux": 52.5,
    },
}

# Dropdown suggestions for each kind of slot. Free text is always allowed too.
SQUAT_VARIATIONS = [
    "Squat", "High Bar Squat", "Low Bar Squat", "Front Squat", "Paused Squat",
    "Box Squat", "Pin Squat", "Beltless Squat", "Safety Bar Squat", "Wide Stance Squat",
    "Narrow Stance Squat", "Tempo Squat", "Half Squat", "Good Morning", "Leg Press",
    "Hack Squat", "Bulgarian Split Squat", "Lunges", "Zercher Squat",
]
BENCH_VARIATIONS = [
    "Bench Press", "Close Grip Bench", "Wide Grip Bench", "Incline Press", "Decline Bench",
    "Paused Bench", "Spoto Press", "Board Press", "Pin Press", "Floor Press",
    "Feet Up Bench", "Tempo Bench", "Slingshot Bench", "Dumbbell Bench", "Weighted Dips",
]
DEADLIFT_VARIATIONS = [
    "Deadlift", "Conventional Deadlift", "Sumo Deadlift", "Block Pull", "Rack Pull",
    "Deficit Deadlift", "Paused Deadlift", "Romanian Deadlift", "Stiff Leg Deadlift",
    "Snatch Grip Deadlift", "Trap Bar Deadlift",
]
OHP_VARIATIONS = [
    "Overhead Press", "Push Press", "Seated OHP", "Behind The Neck Press", "Z Press",
    "Incline Press", "Dumbbell OHP", "Log Press", "Axle Press", "Landmine Press",
]

# Which suggestion list belongs to which slot.
SLOT_VARIATIONS = {
    "squat": SQUAT_VARIATIONS,
    "bench": BENCH_VARIATIONS,
    "deadlift": DEADLIFT_VARIATIONS,
    "ohp": OHP_VARIATIONS,
    "squat_aux_1": SQUAT_VARIATIONS,
    "squat_aux_2": SQUAT_VARIATIONS,
    "bench_aux_1": BENCH_VARIATIONS,
    "bench_aux_2": BENCH_VARIATIONS,
    "deadlift_aux": DEADLIFT_VARIATIONS,
    "ohp_aux": OHP_VARIATIONS,
}

# Upper-back work: one slot every training day, no prescribed progression.
UPPER_BACK_EXERCISES = [
    "Barbell Row", "Dumbbell Row", "Chest Supported Row", "T-Bar Row",
    "Pull-Up", "Chin-Up", "Neutral Grip Pull-Up", "Lat Pulldown", "Seated Cable Row",
]

# Accessory ideas for the "add accessory" dropdown. Free text is allowed too.
ACCESSORY_SUGGESTIONS = [
    "Face Pull", "Lateral Raise", "Rear Delt Fly", "Barbell Curl", "Dumbbell Curl",
    "Hammer Curl", "Triceps Pushdown", "Skull Crusher", "Overhead Triceps Extension",
    "Leg Curl", "Leg Extension", "Hip Thrust", "Back Extension", "Glute Ham Raise",
    "Calf Raise", "Hanging Leg Raise", "Ab Wheel", "Plank", "Cable Crunch", "Shrug",
    "Dips", "Push-Up", "Pec Deck", "Dumbbell Fly",
]

# Which main lift each auxiliary slot belongs to. Used by the setup option
# "use my main lifts for the auxiliary slots too".
PARENT_SLOT = {
    "squat_aux_1": "squat",
    "squat_aux_2": "squat",
    "bench_aux_1": "bench",
    "bench_aux_2": "bench",
    "deadlift_aux": "deadlift",
    "ohp_aux": "ohp",
}

# Short tags added to a lift's name when the same exercise fills more than one
# slot, so "Squat (main)" and "Squat (aux 1)" stay apart in charts and history.
SHORT_SLOT_LABELS = {
    "squat": "main",
    "bench": "main",
    "deadlift": "main",
    "ohp": "main",
    "squat_aux_1": "aux 1",
    "squat_aux_2": "aux 2",
    "bench_aux_1": "aux 1",
    "bench_aux_2": "aux 2",
    "deadlift_aux": "aux",
    "ohp_aux": "aux",
}

# ---------------------------------------------------------------------------
# Split styles
# ---------------------------------------------------------------------------
# The standard SBS templates are full-body: a movement pattern shows up two or
# three times a week (the main lift plus lighter auxiliaries), often on
# back-to-back days. The SBS "lower frequency" templates keep every number the
# same and only rearrange the days upper/lower style, so a pattern is trained
# on alternating days instead. Both layouts are copied from the spreadsheets.
SPLIT_FULL_BODY = "full_body"
SPLIT_UPPER_LOWER = "upper_lower"
SPLIT_STYLES = [SPLIT_FULL_BODY, SPLIT_UPPER_LOWER]
SPLIT_STYLE_NAMES = {
    SPLIT_FULL_BODY: "Full body (SBS default)",
    SPLIT_UPPER_LOWER: "Upper / lower (SBS lower-frequency templates)",
}
SPLIT_STYLE_DESCRIPTIONS = {
    SPLIT_FULL_BODY: ("Each movement pattern two or three times a week, often on back-to-back days, "
                      "with the extra exposures 10 points lighter."),
    SPLIT_UPPER_LOWER: ("Lower-body and upper-body days alternate, so squats never follow squats. "
                        "Same lifts and same numbers, just grouped differently."),
}
LOWER_FREQUENCY_SPLITS = {
    2: TRAINING_SPLITS[2],
    3: [
        ["squat", "deadlift", "squat_aux_1"],
        ["bench", "ohp", "bench_aux_1"],
        ["ohp_aux", "squat_aux_2", "bench_aux_2", "deadlift_aux"],
    ],
    4: [
        ["squat", "deadlift_aux", "squat_aux_2"],
        ["bench", "ohp_aux", "bench_aux_2"],
        ["deadlift", "squat_aux_1"],
        ["ohp", "bench_aux_1"],
    ],
    5: [
        ["squat", "squat_aux_2"],
        ["bench", "ohp_aux", "bench_aux_2"],
        ["deadlift"],
        ["ohp", "bench_aux_1"],
        ["squat_aux_1", "deadlift_aux"],
    ],
    6: [
        ["squat", "squat_aux_2"],
        ["bench", "bench_aux_1"],
        ["deadlift"],
        ["ohp"],
        ["squat_aux_1", "deadlift_aux"],
        ["bench_aux_2", "ohp_aux"],
    ],
}
SPLITS_BY_STYLE = {
    SPLIT_FULL_BODY: TRAINING_SPLITS,
    SPLIT_UPPER_LOWER: LOWER_FREQUENCY_SPLITS,
}

# ---------------------------------------------------------------------------
# Setup presets: a whole setup form filled in at once
# ---------------------------------------------------------------------------
# "SBS defaults" is the spreadsheet as shipped. "Andy's Routine" is the routine
# this app's author runs: six days, no overhead press, the main lifts filling
# the auxiliary slots too, and a fixed list of accessories on each day. A
# preset only fills in the form; the main lifts still follow the program's
# intensities, reps, targets and training-max rules, and every field can be
# changed before pressing Create.
PRESET_SBS = "sbs_defaults"
PRESET_ANDY = "andys_routine"
PRESET_KEYS = [PRESET_SBS, PRESET_ANDY]
PRESET_NAMES = {
    PRESET_SBS: "SBS defaults",
    PRESET_ANDY: "Andy's Routine",
}
PRESET_DESCRIPTIONS = {
    PRESET_SBS: "The templates as Stronger By Science ships them: four main lifts, six auxiliary variations, full-body days.",
    PRESET_ANDY: ("Six days, no overhead press, no variations. Squat and deadlift on Monday, Wednesday and Friday with "
                  "back, core and hip work; bench on Tuesday, Thursday and Saturday with incline, dips, shoulders and arms."),
}

ANDY_LOWER_DAY = ["Pull-Up", "Close Grip Pulldown", "Barbell Row", "Ab Wheel", "Hip Thrust"]
ANDY_UPPER_DAY = ["Incline Bench Press", "Weighted Dips", "Lateral Raise", "Rear Delt Fly", "Cable Curl",
                  "Hammer Curl", "Overhead Triceps Extension", "Triceps Pushdown", "Dumbbell Wrist Curl"]
SETUP_PRESETS = {
    PRESET_ANDY: {
        "variant": VARIANT_RTF,
        "units": "lb",
        "rounding_increment": 5.0,
        "frequency": 6,
        "split_style": SPLIT_UPPER_LOWER,
        "same_lifts": True,
        "skipped_slots": ["ohp", "ohp_aux"],
        "lift_names": {"squat": "Squat", "bench": "Bench Press", "deadlift": "Sumo Deadlift", "ohp": "Overhead Press"},
        # slot -> day. Heavy squat Monday with the lighter deadlift, heavy deadlift
        # Friday with the lighter squat, the way the SBS layouts pair them.
        "days": {
            "squat": 1, "deadlift_aux": 1,
            "bench": 2,
            "squat_aux_1": 3,
            "bench_aux_1": 4,
            "deadlift": 5, "squat_aux_2": 5,
            "bench_aux_2": 6,
        },
        "accessories": [
            ANDY_LOWER_DAY,
            ANDY_UPPER_DAY,
            ["Romanian Deadlift"] + ANDY_LOWER_DAY,
            ANDY_UPPER_DAY,
            ANDY_LOWER_DAY,
            ANDY_UPPER_DAY,
        ],
    },
}

# ---------------------------------------------------------------------------
# Ranks: where each lift stands against strength standards (just for fun)
# ---------------------------------------------------------------------------
# Strength calculators usually name five levels and place them at these
# percentiles of trained lifters: beginner 5, novice 20, intermediate 50,
# advanced 80, elite 95. The app splits those into ten named tiers, with three
# Legend steps inside the top 2.5%.
STANDARD_PERCENTILES = [5.0, 20.0, 50.0, 80.0, 95.0]

RANK_TIERS = [
    {"key": "mortal", "name": "Mortal", "min_percentile": 0.0, "effect": "none"},
    {"key": "initiate", "name": "Initiate", "min_percentile": 5.0, "effect": "none"},
    {"key": "vanguard", "name": "Vanguard", "min_percentile": 12.5, "effect": "none"},
    {"key": "warden", "name": "Warden", "min_percentile": 20.0, "effect": "none"},
    {"key": "colossus", "name": "Colossus", "min_percentile": 35.0, "effect": "none"},
    {"key": "titan", "name": "Titan", "min_percentile": 50.0, "effect": "shine"},
    {"key": "atlas", "name": "Atlas", "min_percentile": 65.0, "effect": "shine"},
    {"key": "demigod", "name": "Demigod", "min_percentile": 80.0, "effect": "electric"},
    {"key": "transcendent", "name": "Transcendent", "min_percentile": 95.0, "effect": "electric"},
    {"key": "legend_1", "name": "Legend I", "min_percentile": 97.5, "effect": "aurora"},
    {"key": "legend_2", "name": "Legend II", "min_percentile": 98.75, "effect": "aurora"},
    {"key": "legend_3", "name": "Legend III", "min_percentile": 99.375, "effect": "aurora"},
]

# Which strength standard each slot is measured against.
RANK_TYPE_BY_SLOT = {
    "squat": "squat", "squat_aux_1": "squat", "squat_aux_2": "squat",
    "bench": "bench", "bench_aux_1": "bench", "bench_aux_2": "bench",
    "deadlift": "deadlift", "deadlift_aux": "deadlift",
    "ohp": "ohp", "ohp_aux": "ohp",
}
RANK_TYPE_NAMES = {"squat": "squat", "bench": "bench press", "deadlift": "deadlift", "ohp": "overhead press"}

# Approximate standards: the one-rep max as a multiple of bodyweight for an
# adult lifter at the reference bodyweight, at the five percentiles above.
# Calibrated to commonly cited strength standards, not copied from any site.
# A lifter can replace them per lift with exact thresholds from a standards
# calculator (see rank_thresholds in the lift settings).
STANDARDS_REFERENCE_BODYWEIGHT_LB = {"male": 180.0, "female": 140.0}
STANDARD_RATIOS = {
    "male": {
        "squat": [0.75, 1.25, 1.5, 2.0, 2.5],
        "bench": [0.5, 0.75, 1.0, 1.35, 1.7],
        "deadlift": [0.9, 1.3, 1.8, 2.3, 2.8],
        "ohp": [0.4, 0.55, 0.75, 1.0, 1.2],
    },
    "female": {
        "squat": [0.45, 0.7, 1.05, 1.45, 1.9],
        "bench": [0.32, 0.47, 0.68, 0.93, 1.2],
        "deadlift": [0.6, 0.9, 1.25, 1.7, 2.15],
        "ohp": [0.22, 0.32, 0.47, 0.65, 0.82],
    },
}
SEX_CHOICES = ["male", "female"]
SEX_NAMES = {"male": "Male", "female": "Female"}

# Heavier lifters lift more, but not in proportion: strength grows with about
# bodyweight to the power of two thirds (allometric scaling).
BODYWEIGHT_SCALING_EXPONENT = 0.667
KG_PER_LB = 0.45359237

# Age coefficients as used in powerlifting: Foster for young lifters, McCulloch
# for masters. A lift is multiplied by the coefficient before it is compared
# with the standards, so a 60-year-old's 300 counts like a 30-year-old's 402.
# Ages 23 to 39 have no adjustment.
AGE_COEFFICIENTS = {
    14: 1.23, 15: 1.18, 16: 1.13, 17: 1.08, 18: 1.06, 19: 1.04, 20: 1.03, 21: 1.02, 22: 1.01,
    40: 1.0, 41: 1.01, 42: 1.02, 43: 1.031, 44: 1.043, 45: 1.055, 46: 1.068, 47: 1.082,
    48: 1.097, 49: 1.113, 50: 1.13, 51: 1.147, 52: 1.165, 53: 1.184, 54: 1.204, 55: 1.225,
    56: 1.246, 57: 1.268, 58: 1.291, 59: 1.315, 60: 1.34, 61: 1.366, 62: 1.393, 63: 1.421,
    64: 1.45, 65: 1.48, 66: 1.511, 67: 1.543, 68: 1.576, 69: 1.61, 70: 1.645, 71: 1.681,
    72: 1.718, 73: 1.756, 74: 1.795, 75: 1.835, 76: 1.876, 77: 1.918, 78: 1.961, 79: 2.005,
    80: 2.05, 81: 2.096, 82: 2.143, 83: 2.19, 84: 2.238, 85: 2.287, 86: 2.337, 87: 2.388,
    88: 2.44, 89: 2.494, 90: 2.549,
}

# How a variation compares with its main lift: the variation's max divided by
# the factor is the equivalent main-lift max. Rough conventional ratios, keyed
# by the cleaned-up exercise name; editable per lift, and 1.0 for anything else.
VARIATION_RANK_FACTORS = {
    "front squat": 0.85, "paused squat": 0.9, "pause squat": 0.9, "high bar squat": 0.95,
    "low bar squat": 1.0, "box squat": 0.95, "pin squat": 0.9, "beltless squat": 0.95,
    "safety bar squat": 0.9, "tempo squat": 0.9, "half squat": 1.2, "leg press": 2.0,
    "hack squat": 1.3, "bulgarian split squat": 0.5, "lunges": 0.5, "zercher squat": 0.8,
    "goblet squat": 0.4, "good morning": 0.5,
    "close grip bench": 0.9, "wide grip bench": 1.0, "incline press": 0.8, "incline bench press": 0.8,
    "decline bench": 1.05, "paused bench": 0.95, "spoto press": 0.95, "board press": 1.05,
    "pin press": 0.95, "floor press": 0.95, "feet up bench": 0.9, "tempo bench": 0.9,
    "slingshot bench": 1.1, "dumbbell bench": 0.75, "weighted dips": 1.0,
    "sumo deadlift": 1.0, "conventional deadlift": 1.0, "block pull": 1.1, "rack pull": 1.2,
    "deficit deadlift": 0.9, "paused deadlift": 0.9, "romanian deadlift": 0.85,
    "stiff leg deadlift": 0.8, "snatch grip deadlift": 0.85, "trap bar deadlift": 1.1,
    "push press": 1.2, "seated ohp": 0.95, "behind the neck press": 0.85, "z press": 0.8,
    "dumbbell ohp": 0.7, "log press": 0.9, "axle press": 0.95, "landmine press": 0.6,
}
