"""
scripts/make_demo_data.py - build data/demo_program.json for presentations.

The demo is a fictional lifter ("Demo Lifter") running the Reps to Failure
program four days a week, currently on week 9 day 3, with every earlier
session logged. Charts and history are therefore full the moment the demo
loads. All numbers are made up but produced by the real program logic, so
the training maxes in the demo are exactly what the app would have computed.

Run from the project folder:
    python scripts/make_demo_data.py
"""
import datetime
import os
import random
import sys

# Let this script import the modules that live one folder up.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

import defaults          # noqa: E402  (import after sys.path change on purpose)
import program_logic as logic  # noqa: E402
import storage           # noqa: E402

START_DATE = datetime.date(2026, 6, 29)      # a Monday, about nine weeks ago
DAY_OFFSETS = [0, 2, 4, 5]                   # Mon, Wed, Fri, Sat
STOP_AT_WEEK = 9
STOP_AFTER_DAY = 2                            # week 9 days 1 and 2 are logged; day 3 is "today"

DEMO_MAXES = {
    "squat": 405, "bench": 275, "deadlift": 455, "ohp": 165,
    "squat_aux_1": 335, "squat_aux_2": 375, "bench_aux_1": 255,
    "bench_aux_2": 235, "deadlift_aux": 425, "ohp_aux": 195,
}

# Outcomes on the last set, relative to the target. Weighted towards small
# wins so the training maxes trend upward like a real block of training.
REP_OUTCOMES = [-2, -1, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 6]

NOTES = ["", "", "", "Felt strong today.", "Long day at work, low energy.", "New PR on the last set!",
         "Slept badly.", "Belt on for the last two sets.", "Smooth reps, bar speed was good."]

ACCESSORY_START = {
    "Barbell Row": 135, "Dumbbell Row": 60, "Chest Supported Row": 90, "T-Bar Row": 90,
    "Leg Curl": 80, "Hanging Leg Raise": 0, "Face Pull": 40, "Triceps Pushdown": 50,
    "Back Extension": 25, "Barbell Curl": 65, "Lateral Raise": 15, "Dumbbell Curl": 25,
}


def session_date(week, day):
    """Takes week and day numbers. Returns the calendar date of that session."""
    return START_DATE + datetime.timedelta(days=(week - 1) * 7 + DAY_OFFSETS[day - 1])


def main():
    """Builds and saves the demo program. Returns nothing."""
    random.seed(7)
    program = logic.create_program(defaults.VARIANT_RTF, "lb", 5.0, 4,
                                   defaults.STRENGTH_DEFAULT_LIFT_NAMES, DEMO_MAXES)
    program["created_on"] = START_DATE.isoformat()
    program["lifter_name"] = "Demo Lifter"
    program["lifter"] = {"sex": "male", "age": 28, "bodyweight": 185.0}   # unlocks the ranks in the demo
    program["days"][0]["accessories"] = ["Barbell Row", "Leg Curl", "Hanging Leg Raise"]
    program["days"][1]["accessories"] = ["Dumbbell Row", "Face Pull", "Triceps Pushdown"]
    program["days"][2]["accessories"] = ["Chest Supported Row", "Back Extension", "Barbell Curl"]
    program["days"][3]["accessories"] = ["T-Bar Row", "Lateral Raise", "Dumbbell Curl"]

    for week in range(1, STOP_AT_WEEK + 1):
        for day in range(1, 5):
            if week == STOP_AT_WEEK and day > STOP_AFTER_DAY:
                break
            results = []
            for exercise in logic.build_workout(program, week, day):
                result = {"slot": exercise["slot"], "single_at_8": None, "notes": random.choice(NOTES)}
                if exercise["is_deload"]:
                    result["sets_completed"] = exercise["sets"]
                else:
                    result["last_set_reps"] = max(0, exercise["last_set_rep_target"] + random.choice(REP_OUTCOMES))
                    # From week 8 the lifter works up to a single at RPE 8 on the main lifts.
                    if week >= 8 and program["lifts"][exercise["slot"]]["is_main"]:
                        training_max = program["lifts"][exercise["slot"]]["training_max"]
                        result["single_at_8"] = logic.round_to_increment(training_max * 0.905, 5.0)
                results.append(result)

            accessories = []
            day_plan = program["days"][day - 1]
            names = day_plan["accessories"]
            for position in range(len(names)):
                name = names[position]
                weight = ACCESSORY_START.get(name, 30) + 5 * ((week - 1) // 2)
                accessories.append({"name": name, "kind": "accessory", "weight": float(weight),
                                    "sets": 3, "reps": random.choice([8, 10, 10, 12])})

            logic.log_workout(program, week, day, results, accessories, "", session_date(week, day).isoformat())
            logic.advance_to_next_day(program)

    storage.save_program(program, storage.DEMO_PATH)
    print("Wrote " + storage.DEMO_PATH)
    print("Sessions logged: " + str(len(program["history"])) + ", now on week "
          + str(program["current_week"]) + " day " + str(program["current_day"]))
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        print("  " + lift["name"] + ": " + str(DEMO_MAXES[slot]) + " -> " + str(round(lift["training_max"], 1)))


if __name__ == "__main__":
    main()
