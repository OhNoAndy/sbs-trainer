"""
program_logic.py - all of the training math for the SBS programs.

Pure functions only: values go in, values come out. This file never imports
Streamlit, so every function can be exercised from the command line with

    python test_program_logic.py

Suggested reading order:
  1. round_to_increment, nearest_percentage_bucket, lookup_by_percentage
  2. calculate_working_weight, calculate_training_max_from_single
  3. get_prescription            - what today's sets look like
  4. calculate_tm_change_percent - the shared training-max engine
  5. log_workout                 - ties it together and records history

The program design belongs to Greg Nuckols / Stronger By Science
(https://www.strongerbyscience.com/program-bundle/). This is an unofficial
personal project that reproduces the spreadsheet math in Python.
"""
import datetime
import math

import defaults


# ---------------------------------------------------------------------------
# 1. Rounding and percentage lookups
# ---------------------------------------------------------------------------
def round_to_increment(value, increment):
    """
    Round a weight to the nearest multiple of the rounding increment.

    Takes: value (float), increment (float such as 2.5 or 5).
    Returns: the rounded float. round_to_increment(343, 2.5) is 342.5.

    Exact halves round up (343.75 with increment 2.5 becomes 345), which is
    what the spreadsheet's MROUND does. Python's built-in round() rounds
    halves to the nearest even number instead, so we do the arithmetic by hand:
    count how many increments fit, add one half, and drop the fraction.
    """
    if increment <= 0:
        return value
    # The tiny 1e-9 protects against floating point noise such as
    # 136.49999999999 when the true answer is 136.5.
    number_of_increments = math.floor(value / increment + 0.5 + 1e-9)
    return round(number_of_increments * increment, 3)


def nearest_percentage_bucket(percentage):
    """
    Snap any percentage to the closest of the 21 buckets 50, 52.5, ... 100.

    Takes: percentage (float, e.g. 71.3).
    Returns: the closest bucket value (float, e.g. 72.5).
    """
    closest = defaults.PERCENTAGE_BUCKETS[0]
    for bucket in defaults.PERCENTAGE_BUCKETS:
        if abs(bucket - percentage) < abs(closest - percentage):
            closest = bucket
    return closest


def bucket_index(percentage):
    """
    Position (0 to 20) of the bucket nearest to a percentage.

    Takes: percentage (float). Returns: an int index into any 21-value table.
    """
    return defaults.PERCENTAGE_BUCKETS.index(nearest_percentage_bucket(percentage))


def lookup_by_percentage(table, percentage):
    """
    Read the entry of a 21-value table that belongs to a percentage.

    Takes: table (list of 21 values in PERCENTAGE_BUCKETS order), percentage.
    Returns: the table entry for the nearest bucket.
    Example: lookup_by_percentage(STRENGTH_REPS_PER_SET, 70) is 5.
    """
    return table[bucket_index(percentage)]


# ---------------------------------------------------------------------------
# 2. Weights and training maxes
# ---------------------------------------------------------------------------
def is_deload_week(week):
    """Takes a week number (1-21). Returns True for the deload weeks 7, 14, 21."""
    return week in defaults.DELOAD_WEEKS


def block_number(week):
    """Takes a week number (1-21). Returns which 7-week block it is in (1, 2 or 3)."""
    return (week - 1) // defaults.WEEKS_PER_BLOCK + 1


def calculate_working_weight(training_max, intensity_percent, rounding_increment):
    """
    The weight to put on the bar.

    Takes: training_max (float, unrounded), intensity_percent (e.g. 70.0),
           rounding_increment (e.g. 2.5).
    Returns: training_max * intensity, rounded to the increment.
    Example: 490 at 70% with increment 2.5 -> 343 -> 342.5.
    """
    exact_weight = training_max * intensity_percent / 100.0
    return round_to_increment(exact_weight, rounding_increment)


def calculate_training_max_from_single(single_weight, single_at_8_percent):
    """
    Turn a heavy single at RPE 8 into a fresh training max.

    Takes: single_weight (float), single_at_8_percent (e.g. 90.0).
    Returns: single_weight / 0.90 (unrounded).
    Example: 460 at 90% -> 511.1.
    """
    return single_weight / (single_at_8_percent / 100.0)


def apply_tm_change(training_max, change_percent):
    """
    Move a training max up or down by a percentage.

    Takes: training_max (float), change_percent (e.g. 1.5 or -5.0).
    Returns: the new, unrounded training max.
    """
    return training_max * (1.0 + change_percent / 100.0)


def estimate_one_rep_max(weight, reps):
    """
    Estimate a one-rep max from a set using the Epley formula.

    Takes: weight (float), reps (int, the number of reps to failure).
    Returns: weight * (1 + reps / 30). A single just returns the weight.
    """
    if reps <= 1:
        return float(weight)
    return weight * (1.0 + reps / 30.0)


# ---------------------------------------------------------------------------
# 3. Per-lift settings and the daily prescription
# ---------------------------------------------------------------------------
def build_lift_settings(variant, slot, name, starting_max):
    """
    Create the settings dictionary for one lift with every table set to defaults.

    Takes: variant key, slot key (e.g. "squat"), display name, starting 1RM.
    Returns: a dict holding the training max plus every editable table.
    """
    is_main = slot in defaults.MAIN_SLOTS
    if variant == defaults.VARIANT_HYPERTROPHY:
        main_intensities = defaults.HYPERTROPHY_MAIN_INTENSITIES
        auxiliary_offset = defaults.HYPERTROPHY_AUXILIARY_OFFSET
        reps_per_set = defaults.HYPERTROPHY_REPS_PER_SET
        last_set_rep_target = defaults.HYPERTROPHY_LAST_SET_REP_TARGET
    else:
        main_intensities = defaults.STRENGTH_MAIN_INTENSITIES
        auxiliary_offset = defaults.STRENGTH_AUXILIARY_OFFSET
        reps_per_set = defaults.STRENGTH_REPS_PER_SET
        last_set_rep_target = defaults.RTF_LAST_SET_REP_TARGET

    # Auxiliary lifts use the same 21-week shape, a few points lighter.
    intensities = []
    for main_value in main_intensities:
        if is_main:
            intensities.append(main_value)
        else:
            intensities.append(main_value - auxiliary_offset)

    return {
        "slot": slot,
        "name": name,
        "is_main": is_main,
        "starting_max": float(starting_max),
        "training_max": float(starting_max),
        "intensities": intensities,
        "reps_per_set": list(reps_per_set),
        "rir_cutoff": list(defaults.ORIGINAL_RIR_CUTOFF),
        "last_set_rir_target": list(defaults.LAST_SET_RIR_TARGET),
        "last_set_rep_target": list(last_set_rep_target),
        "sets": defaults.DEFAULT_SETS[variant],
        "lower_set_threshold": defaults.ORIGINAL_LOWER_SET_THRESHOLD,
        "upper_set_threshold": defaults.ORIGINAL_UPPER_SET_THRESHOLD,
        "increase_percent": defaults.ORIGINAL_INCREASE_PERCENT,
        "decrease_percent": defaults.ORIGINAL_DECREASE_PERCENT,
        "ladder": list(defaults.DEFAULT_TM_LADDER),
        "single_at_8_percent": defaults.DEFAULT_SINGLE_AT_8_PERCENT,
        "image_path": "",
        "rank_factor": default_rank_factor(name),
        "rank_thresholds": None,
    }


def clean_exercise_name(name):
    """Takes an exercise name. Returns it lowercased with punctuation removed and single spaces."""
    text = str(name).lower()
    for character in ["-", "_", "/", "(", ")", ",", ".", "'"]:
        text = text.replace(character, " ")
    return " ".join(text.split())


def default_rank_factor(name):
    """
    Takes an exercise name. Returns how its max compares with the main lift it
    stands in for (see defaults.VARIATION_RANK_FACTORS), or 1.0 when unknown.
    """
    return defaults.VARIATION_RANK_FACTORS.get(clean_exercise_name(name), 1.0)


def reset_lift_tables_for_variant(lift, variant):
    """
    Put a lift's rep tables, intensities and set count back to a variant's defaults.
    Keeps the name, training max and image. Used when switching variants.

    Takes: lift settings dict, variant key. Returns: nothing (edits the dict).
    """
    fresh = build_lift_settings(variant, lift["slot"], lift["name"], lift["training_max"])
    for key in ["intensities", "reps_per_set", "rir_cutoff", "last_set_rir_target",
                "last_set_rep_target", "sets", "ladder"]:
        lift[key] = fresh[key]


def get_prescription(variant, lift, week, rounding_increment, deload_reps_per_set=defaults.DELOAD_REPS_PER_SET):
    """
    Work out what one lift looks like on a given week.

    Takes: variant key, lift settings dict, week (1-21), rounding increment,
           and the reps to use on deload weeks.
    Returns: a dict with intensity, working_weight, sets, reps_per_set,
             is_deload, and the target that matches the variant:
               original      -> rir_cutoff, lower/upper_set_threshold
               last_set_rir  -> last_set_rir_target
               rtf / hypertrophy -> last_set_rep_target
    """
    intensity = lift["intensities"][week - 1]
    training_max = lift["training_max"]
    prescription = {
        "week": week,
        "is_deload": is_deload_week(week),
        "intensity": intensity,
        "training_max": training_max,
        "working_weight": calculate_working_weight(training_max, intensity, rounding_increment),
        "sets": lift["sets"],
    }

    # Deloads are a hard-coded special case: listed weight, easy sets, no target.
    if prescription["is_deload"]:
        prescription["reps_per_set"] = deload_reps_per_set
        return prescription

    # Everything else is looked up from the intensity, not the week number.
    prescription["reps_per_set"] = lookup_by_percentage(lift["reps_per_set"], intensity)
    if variant == defaults.VARIANT_ORIGINAL:
        prescription["rir_cutoff"] = lookup_by_percentage(lift["rir_cutoff"], intensity)
        prescription["lower_set_threshold"] = lift["lower_set_threshold"]
        prescription["upper_set_threshold"] = lift["upper_set_threshold"]
    elif variant == defaults.VARIANT_LAST_SET_RIR:
        prescription["last_set_rir_target"] = lookup_by_percentage(lift["last_set_rir_target"], intensity)
    else:
        prescription["last_set_rep_target"] = lookup_by_percentage(lift["last_set_rep_target"], intensity)
    return prescription


def get_prescription_for_slot(program, slot, week):
    """
    Convenience wrapper: the prescription for one slot of a whole program dict.

    Takes: program dict, slot key, week. Returns: see get_prescription.
    """
    lift = program["lifts"][slot]
    return get_prescription(program["variant"], lift, week,
                            program["rounding_increment"], program["deload_reps_per_set"])


def describe_prescription(variant, prescription):
    """
    Put a prescription into one short sentence for the workout screen.

    Takes: variant key, prescription dict. Returns: a string such as
           "4 sets of 5, then a 5th set for as many reps as possible (target 10)".
    """
    sets = prescription["sets"]
    reps = prescription["reps_per_set"]
    if prescription["is_deload"]:
        return "Deload: " + str(sets) + " easy sets of " + str(reps) + ", no target"
    if variant == defaults.VARIANT_ORIGINAL:
        return ("Sets of " + str(reps) + " until you reach " + str(prescription["rir_cutoff"])
                + " RIR (target " + str(prescription["lower_set_threshold"]) + "-"
                + str(prescription["upper_set_threshold"]) + " sets)")
    if variant == defaults.VARIANT_LAST_SET_RIR:
        return (str(sets) + " sets of " + str(reps) + ", aim for "
                + str(prescription["last_set_rir_target"]) + " RIR on the last set")
    normal_sets = sets - 1
    return (str(normal_sets) + " sets of " + str(reps) + ", then 1 set for as many reps as possible (target "
            + str(prescription["last_set_rep_target"]) + ")")


# ---------------------------------------------------------------------------
# 4. The training-max engine (shared by every variant)
# ---------------------------------------------------------------------------
def ladder_index_for_difference(difference):
    """
    Turn "how far above the target" into a position in the 8-step ladder.

    Takes: difference (int) = what you did minus the target.
    Returns: an index 0-7 into a lift's "ladder" list:
        difference <= -2  -> 0   (2 or more below target, big drop)
        difference == -1  -> 1   (1 below target, small drop)
        difference ==  0  -> 2   (hit the target, no change)
        difference ==  1  -> 3   (beat by 1) ... and so on ...
        difference >=  5  -> 7   (beat by 5 or more, biggest increase)
    """
    if difference <= -2:
        return 0
    if difference >= 5:
        return 7
    return difference + 2


def calculate_tm_change_percent(variant, lift, prescription, performance):
    """
    The one adjustment engine for all four variants.

    Takes: variant key, lift settings, today's prescription, and a performance
           dict with whichever of these keys the variant needs:
             sets_completed (original, last_set_rir)
             last_set_rir   (last_set_rir)
             last_set_reps  (rtf, hypertrophy)
    Returns: the percent change to apply to the training max, e.g. -5.0 or 1.5.
    """
    # Deload weeks never move the training max, whatever happened.
    if prescription["is_deload"]:
        return 0.0

    if variant == defaults.VARIANT_ORIGINAL:
        # Open-ended sets: too few sets is a drop, extra sets is a raise.
        sets_completed = performance.get("sets_completed", 0)
        if sets_completed < lift["lower_set_threshold"]:
            return lift["decrease_percent"]
        if sets_completed > lift["upper_set_threshold"]:
            return lift["increase_percent"]
        return 0.0

    ladder = lift["ladder"]

    if variant == defaults.VARIANT_LAST_SET_RIR:
        # First check the sets: missing 2+ sets is the worst rung, missing 1 is
        # the second rung. Then compare the last set's RIR with the target.
        sets_missed = prescription["sets"] - performance.get("sets_completed", 0)
        if sets_missed >= 2:
            return ladder[0]
        if sets_missed == 1:
            return ladder[1]
        rir_difference = performance.get("last_set_rir", 0) - prescription["last_set_rir_target"]
        if rir_difference < 0:
            # Any RIR under the target is the same small drop (matches the spreadsheet).
            return ladder[1]
        return ladder[ladder_index_for_difference(rir_difference)]

    # Reps to Failure and Hypertrophy: reps on the last set versus the target.
    rep_difference = performance.get("last_set_reps", 0) - prescription["last_set_rep_target"]
    return ladder[ladder_index_for_difference(rep_difference)]


def format_weight(value, units):
    """Takes a number and a unit string. Returns "342.5 lb" or "100 kg" (no trailing .0)."""
    text = str(round(value, 1))
    if text.endswith(".0"):
        text = text[:-2]
    return text + " " + units


def format_percent(value):
    """Takes 1.5 or -5.0. Returns "1.5%" or "-5%"."""
    text = str(round(value, 2))
    if text.endswith(".0"):
        text = text[:-2]
    return text + "%"


def plural(count, word):
    """Takes 1 and "rep". Returns "1 rep"; with 3 returns "3 reps"."""
    if count == 1:
        return "1 " + word
    return str(count) + " " + word + "s"


def describe_outcome(variant, prescription, performance):
    """
    Say in words how the workout compared with its target.

    Takes: variant key, prescription dict, performance dict.
    Returns: a string such as "You beat the target by 3 reps".
    """
    if prescription["is_deload"]:
        return "Deload week, no target"

    if variant == defaults.VARIANT_ORIGINAL:
        sets_completed = performance.get("sets_completed", 0)
        return ("You completed " + plural(sets_completed, "set") + " (target "
                + str(prescription["lower_set_threshold"]) + "-"
                + str(prescription["upper_set_threshold"]) + ")")

    if variant == defaults.VARIANT_LAST_SET_RIR:
        sets_completed = performance.get("sets_completed", 0)
        if sets_completed < prescription["sets"]:
            return "You completed " + str(sets_completed) + " of " + str(prescription["sets"]) + " sets"
        target = prescription["last_set_rir_target"]
        rir = performance.get("last_set_rir", 0)
        if rir < target:
            return "Your last set had " + str(rir) + " RIR, under the target of " + str(target)
        if rir == target:
            return "Your last set hit the RIR target of " + str(target)
        return "Your last set had " + plural(rir - target, "more rep") + " in reserve than the target of " + str(target)

    target = prescription["last_set_rep_target"]
    reps = performance.get("last_set_reps", 0)
    if reps > target:
        return "You beat the target by " + plural(reps - target, "rep")
    if reps == target:
        return "You hit the target of " + plural(target, "rep") + " exactly"
    return "You fell " + plural(target - reps, "rep") + " short of the target of " + str(target)


def describe_tm_change(variant, prescription, performance, change_percent, new_training_max, units):
    """
    Build the message shown right after saving a workout.

    Takes: variant key, prescription, performance, the percent change, the new
           training max and the unit string.
    Returns: e.g. "You beat the target by 3 reps - training max going up 1.5% to 497.4 lb".
    """
    outcome = describe_outcome(variant, prescription, performance)
    new_max_text = format_weight(new_training_max, units)
    if change_percent > 0:
        return outcome + " - training max going up " + format_percent(change_percent) + " to " + new_max_text
    if change_percent < 0:
        return outcome + " - training max dropping " + format_percent(abs(change_percent)) + " to " + new_max_text
    return outcome + " - training max stays at " + new_max_text


def estimate_session_one_rep_max(variant, prescription, performance):
    """
    Estimate a 1RM from today's hardest set.

    Takes: variant key, prescription, performance dict.
    Returns: an Epley estimate (float), or None on deload weeks.
    The number of reps "to failure" is the reps done plus the reps in reserve.
    """
    if prescription["is_deload"]:
        return None
    weight = prescription["working_weight"]
    if variant == defaults.VARIANT_ORIGINAL:
        reps_to_failure = prescription["reps_per_set"] + prescription["rir_cutoff"]
    elif variant == defaults.VARIANT_LAST_SET_RIR:
        reps_to_failure = prescription["reps_per_set"] + performance.get("last_set_rir", 0)
    else:
        reps_to_failure = performance.get("last_set_reps", 0)
    return estimate_one_rep_max(weight, reps_to_failure)


def count_total_reps(variant, prescription, performance):
    """
    How many reps were done in total on a lift today (for volume stats).

    Takes: variant key, prescription, performance. Returns: an int.
    """
    reps = prescription["reps_per_set"]
    if prescription["is_deload"]:
        return prescription["sets"] * reps
    if variant == defaults.VARIANT_ORIGINAL or variant == defaults.VARIANT_LAST_SET_RIR:
        return performance.get("sets_completed", 0) * reps
    normal_sets = prescription["sets"] - 1
    return normal_sets * reps + performance.get("last_set_reps", 0)


# ---------------------------------------------------------------------------
# 5. Whole-program helpers: creating, logging, moving through the calendar
# ---------------------------------------------------------------------------
def today_string():
    """Returns today's date as "YYYY-MM-DD"."""
    return datetime.date.today().isoformat()


def build_default_days(frequency, skipped_slots=None, split_style=defaults.SPLIT_FULL_BODY):
    """
    The day-by-day plan for a training frequency.

    Takes: frequency (2-6), an optional list of slot keys to leave out (lifts
    the user does not want to do at all), and the split style: full body (the
    standard templates) or upper/lower (the lower-frequency templates).
    Returns: a list of day dicts, each with the lift slots in order and a
    starter accessory list holding one rowing or pull-up exercise, because the
    main lifts include no pulling. Accessories are free-form: the user logs
    weight, sets and reps and tries to beat them next time.
    """
    if skipped_slots is None:
        skipped_slots = []
    days = []
    split = defaults.SPLITS_BY_STYLE[split_style][frequency]
    for day_index in range(len(split)):
        slots = []
        for slot in split[day_index]:
            if slot not in skipped_slots:
                slots.append(slot)
        row_exercise = defaults.UPPER_BACK_EXERCISES[day_index % len(defaults.UPPER_BACK_EXERCISES)]
        days.append({"slots": slots, "accessories": [row_exercise]})
    return days


def record_training_max(program, slot, week, day, session_number, training_max, reason):
    """
    Append one point to the training-max history (used by the progress chart).

    Takes: program, slot key, week, day, session_number (0 = before the first
           workout, 1 = after the first logged workout, ...), the training max,
           and a reason string.
    Returns: nothing (edits the program dict).
    """
    program["tm_history"].append({
        "slot": slot,
        "week": week,
        "day": day,
        "session": session_number,
        "training_max": training_max,
        "reason": reason,
    })


def create_program(variant, units, rounding_increment, frequency, lift_names, starting_maxes, skipped_slots=None,
                   split_style=defaults.SPLIT_FULL_BODY):
    """
    Build a brand-new program dictionary. This one dict is the app's entire state.

    Takes: variant key, units ("lb"/"kg"), rounding increment, frequency (2-6),
           lift_names (dict slot -> name), starting_maxes (dict slot -> 1RM),
           optionally a list of slots the lifter wants to leave out, and the
           split style (see build_default_days).
    Returns: the program dict, ready to save as JSON. Skipped slots still get
    settings (so they can be added back in Settings) but are not scheduled.
    """
    program = {
        "version": 1,
        "variant": variant,
        "units": units,
        "rounding_increment": float(rounding_increment),
        "frequency": int(frequency),
        "split_style": split_style,
        "current_week": 1,
        "current_day": 1,
        "created_on": today_string(),
        "deload_reps_per_set": defaults.DELOAD_REPS_PER_SET,
        "lifts": {},
        "days": build_default_days(frequency, skipped_slots, split_style),
        "history": [],
        "tm_history": [],
        "image_choices": {},
        "lifter": {"sex": "", "age": 0, "bodyweight": 0.0},
    }
    for slot in defaults.ALL_SLOTS:
        program["lifts"][slot] = build_lift_settings(variant, slot, lift_names[slot], starting_maxes[slot])
        record_training_max(program, slot, 0, 0, 0, float(starting_maxes[slot]), "Starting max")
    return program


def ensure_program_defaults(program):
    """
    Fill in keys that older saved files may not have, so the app never crashes
    on a program.json written by a previous version.

    Takes: program dict. Returns: nothing (edits the dict).
    """
    if "image_choices" not in program:
        program["image_choices"] = {}
    if "deload_reps_per_set" not in program:
        program["deload_reps_per_set"] = defaults.DELOAD_REPS_PER_SET
    if program.get("split_style") not in defaults.SPLIT_STYLES:
        program["split_style"] = defaults.SPLIT_FULL_BODY
    if "lifter" not in program:
        program["lifter"] = {"sex": "", "age": 0, "bodyweight": 0.0}
    for slot in defaults.ALL_SLOTS:
        if slot not in program["lifts"]:
            continue
        lift = program["lifts"][slot]
        if "image_path" not in lift:
            lift["image_path"] = ""
        if "rank_factor" not in lift:
            lift["rank_factor"] = default_rank_factor(lift["name"])
        if "rank_thresholds" not in lift:
            lift["rank_thresholds"] = None
    for day in program["days"]:
        # Older files kept an upper-back exercise in a slot of its own; it is
        # now simply the first accessory of the day.
        if "upper_back" in day:
            if day["upper_back"].strip() != "":
                day["accessories"].insert(0, day["upper_back"].strip())
            del day["upper_back"]


def lift_display_name(program, slot):
    """
    The name to show for a slot.

    Takes: program, slot key. Returns: the lift's name, plus a short slot tag
    when the same exercise fills more than one slot (for example "Squat" as
    the main lift and again as an auxiliary): "Squat (main)", "Squat (aux 1)".
    """
    name = program["lifts"][slot]["name"]
    times_used = 0
    for other_slot in defaults.ALL_SLOTS:
        if program["lifts"][other_slot]["name"].strip().lower() == name.strip().lower():
            times_used += 1
    if times_used > 1:
        return name + " (" + defaults.SHORT_SLOT_LABELS[slot] + ")"
    return name


def scheduled_slots(program):
    """Takes program. Returns the list of slot keys that appear on any training day."""
    slots = []
    for day in program["days"]:
        for slot in day["slots"]:
            slots.append(slot)
    return slots


def build_workout(program, week, day):
    """
    Everything the workout screen needs for one day.

    Takes: program, week, day. Returns: a list of prescription dicts (one per
    main/auxiliary lift on that day) with "slot" and "name" added.
    """
    exercises = []
    day_plan = program["days"][day - 1]
    for slot in day_plan["slots"]:
        prescription = get_prescription_for_slot(program, slot, week)
        prescription["slot"] = slot
        prescription["name"] = lift_display_name(program, slot)
        exercises.append(prescription)
    return exercises


def log_workout(program, week, day, lift_results, accessory_results, session_notes, date_string):
    """
    Save one training session and adjust every training max that was trained.

    Takes:
      program          - the program dict (edited in place)
      week, day        - which session this is
      lift_results     - list of dicts, one per main/aux lift, with keys
                         slot, sets_completed, last_set_rir, last_set_reps,
                         single_at_8 (0/None if not done) and notes
      accessory_results- list of dicts with name, kind, weight, sets, reps
      session_notes    - free text
      date_string      - "YYYY-MM-DD"
    Returns: a list of message strings, one per lift, describing the TM change.
    """
    variant = program["variant"]
    units = program["units"]
    messages = []
    logged_lifts = []
    # This workout becomes history entry number len(history) + 1.
    session_number = len(program["history"]) + 1

    rank_changes = []
    for result in lift_results:
        slot = result["slot"]
        lift = program["lifts"][slot]
        training_max_before = lift["training_max"]
        rank_before = rank_for_lift(program, slot)

        # Optional daily autoregulation: a logged single at RPE 8 replaces the
        # training max for today before the work sets are judged.
        single = result.get("single_at_8")
        if single:
            lift["training_max"] = calculate_training_max_from_single(single, lift["single_at_8_percent"])
            record_training_max(program, slot, week, day, session_number, lift["training_max"],
                                "Single @8 of " + format_weight(single, units))

        prescription = get_prescription_for_slot(program, slot, week)
        change_percent = calculate_tm_change_percent(variant, lift, prescription, result)
        new_training_max = apply_tm_change(lift["training_max"], change_percent)
        message = describe_tm_change(variant, prescription, result, change_percent, new_training_max, units)

        lift["training_max"] = new_training_max
        record_training_max(program, slot, week, day, session_number, new_training_max, message)

        # Ranks are just for fun: note when a lift crossed into another tier.
        rank_after = rank_for_lift(program, slot)
        tier_before = None
        tier_after = None
        if rank_before["available"] and rank_after["available"]:
            tier_before = rank_before["tier"]
            tier_after = rank_after["tier"]
            if tier_after != tier_before:
                rank_changes.append({
                    "slot": slot,
                    "name": lift_display_name(program, slot),
                    "from_tier": tier_before,
                    "to_tier": tier_after,
                    "from_name": rank_before["tier_name"],
                    "to_name": rank_after["tier_name"],
                })

        logged_lifts.append({
            "slot": slot,
            "name": lift_display_name(program, slot),
            "intensity": prescription["intensity"],
            "working_weight": prescription["working_weight"],
            "sets": prescription["sets"],
            "reps_per_set": prescription["reps_per_set"],
            "is_deload": prescription["is_deload"],
            "rir_cutoff": prescription.get("rir_cutoff"),
            "last_set_rir_target": prescription.get("last_set_rir_target"),
            "last_set_rep_target": prescription.get("last_set_rep_target"),
            "sets_completed": result.get("sets_completed"),
            "last_set_rir": result.get("last_set_rir"),
            "last_set_reps": result.get("last_set_reps"),
            "single_at_8": single,
            "total_reps": count_total_reps(variant, prescription, result),
            "estimated_1rm": estimate_session_one_rep_max(variant, prescription, result),
            "training_max_before": training_max_before,
            "training_max_after": new_training_max,
            "tm_change_percent": change_percent,
            "message": message,
            "notes": result.get("notes", ""),
            "rank_before": tier_before,
            "rank_after": tier_after,
        })
        messages.append(lift_display_name(program, slot) + ": " + message)

    for change in rank_changes:
        if change["to_tier"] > change["from_tier"]:
            messages.append("Rank up! " + change["name"] + ": " + change["from_name"] + " -> " + change["to_name"])
        else:
            messages.append("Rank down: " + change["name"] + " is now " + change["to_name"])

    program["history"].append({
        "date": date_string,
        "week": week,
        "day": day,
        "variant": variant,
        "lifts": logged_lifts,
        "accessories": accessory_results,
        "notes": session_notes,
        "rank_changes": rank_changes,
    })
    return messages


def advance_to_next_day(program):
    """
    Move the program's pointer to the next training day (and week when needed).

    Takes: program. Returns: nothing. Stays on the final day of week 21 so the
    user can choose to start a new cycle.
    """
    if program["current_day"] < program["frequency"]:
        program["current_day"] += 1
    elif program["current_week"] < defaults.TOTAL_WEEKS:
        program["current_day"] = 1
        program["current_week"] += 1


def is_cycle_finished(program):
    """Takes program. Returns True once the last day of week 21 has been logged."""
    last_week = program["current_week"] == defaults.TOTAL_WEEKS
    last_day = program["current_day"] == program["frequency"]
    if not (last_week and last_day):
        return False
    for entry in program["history"]:
        if entry["week"] == defaults.TOTAL_WEEKS and entry["day"] == program["frequency"]:
            return True
    return False


def start_new_cycle(program):
    """
    Go back to week 1 day 1 keeping every training max and all history.

    Takes: program. Returns: nothing.
    """
    program["current_week"] = 1
    program["current_day"] = 1
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        lift["starting_max"] = lift["training_max"]
        record_training_max(program, slot, 0, 0, len(program["history"]), lift["training_max"], "New cycle")


def find_last_accessory_result(program, name):
    """
    The most recent logged weight/sets/reps for an accessory exercise.

    Takes: program, exercise name. Returns: the accessory dict, or None.
    """
    for entry in reversed(program["history"]):
        for accessory in entry["accessories"]:
            if accessory["name"].strip().lower() == name.strip().lower():
                return accessory
    return None


def find_history_entry(program, week, day):
    """Takes program, week, day. Returns the logged entry for that session, or None."""
    for entry in program["history"]:
        if entry["week"] == week and entry["day"] == day:
            return entry
    return None


# ---------------------------------------------------------------------------
# 6. Ranks: each lift measured against strength standards (just for fun)
# ---------------------------------------------------------------------------
def age_coefficient(age):
    """
    Takes an age in years. Returns the powerlifting age coefficient (1.0 for
    ages 23-39, above 1.0 for younger and older lifters, see defaults).
    """
    if age is None or age <= 0:
        return 1.0
    age = int(age)
    if age < 14:
        age = 14
    if age > 90:
        age = 90
    return defaults.AGE_COEFFICIENTS.get(age, 1.0)


def standard_thresholds(rank_type, sex, bodyweight, units):
    """
    The five standard thresholds (beginner, novice, intermediate, advanced,
    elite) for one kind of lift and one lifter.

    Takes: rank type ("squat", "bench", "deadlift", "ohp"), sex ("male"/"female"),
           bodyweight and the units it is in ("lb"/"kg").
    Returns: a list of five weights in those same units.
    The reference ratios are scaled to the lifter's bodyweight with the
    two-thirds power rule, so a heavier lifter needs more weight but not in
    direct proportion.
    """
    ratios = defaults.STANDARD_RATIOS[sex][rank_type]
    reference = defaults.STANDARDS_REFERENCE_BODYWEIGHT_LB[sex]
    bodyweight_lb = bodyweight
    if units == "kg":
        bodyweight_lb = bodyweight / defaults.KG_PER_LB
    scale = (bodyweight_lb / reference) ** defaults.BODYWEIGHT_SCALING_EXPONENT
    thresholds = []
    for ratio in ratios:
        value = ratio * reference * scale
        if units == "kg":
            value = value * defaults.KG_PER_LB
        thresholds.append(value)
    return thresholds


def strength_percentile(lift, thresholds):
    """
    Where a lift sits among trained lifters, as a percentile.

    Takes: the (age-adjusted) lift and the five thresholds.
    Returns: 0-100. Straight lines join the five anchor points (5, 20, 50, 80,
    95). Above elite, every further advanced-to-elite step halves the remaining
    distance to 100, so the top never quite runs out.
    """
    percentiles = defaults.STANDARD_PERCENTILES
    if lift <= 0:
        return 0.0
    if lift < thresholds[0]:
        return percentiles[0] * lift / thresholds[0]
    for position in range(1, len(thresholds)):
        if lift < thresholds[position]:
            lower_lift = thresholds[position - 1]
            upper_lift = thresholds[position]
            lower_percent = percentiles[position - 1]
            upper_percent = percentiles[position]
            share = (lift - lower_lift) / (upper_lift - lower_lift)
            return lower_percent + share * (upper_percent - lower_percent)
    step = thresholds[4] - thresholds[3]
    steps_beyond_elite = (lift - thresholds[4]) / step
    return 100.0 - 5.0 * (0.5 ** steps_beyond_elite)


def lift_for_percentile(percentile, thresholds):
    """
    The opposite of strength_percentile: the lift needed to reach a percentile.

    Takes: a percentile (0-100) and the five thresholds. Returns: a weight.
    """
    percentiles = defaults.STANDARD_PERCENTILES
    if percentile <= 0:
        return 0.0
    if percentile <= percentiles[0]:
        return thresholds[0] * percentile / percentiles[0]
    for position in range(1, len(thresholds)):
        if percentile <= percentiles[position]:
            lower_lift = thresholds[position - 1]
            upper_lift = thresholds[position]
            lower_percent = percentiles[position - 1]
            upper_percent = percentiles[position]
            share = (percentile - lower_percent) / (upper_percent - lower_percent)
            return lower_lift + share * (upper_lift - lower_lift)
    if percentile >= 99.99:
        percentile = 99.99
    step = thresholds[4] - thresholds[3]
    steps_beyond_elite = math.log(5.0 / (100.0 - percentile), 2)
    return thresholds[4] + steps_beyond_elite * step


def tier_index_for_percentile(percentile):
    """Takes a percentile. Returns the index into defaults.RANK_TIERS it falls in."""
    index = 0
    for position in range(len(defaults.RANK_TIERS)):
        if percentile >= defaults.RANK_TIERS[position]["min_percentile"]:
            index = position
    return index


def lifter_details_complete(program):
    """Takes program. Returns True when sex, age and bodyweight have been entered."""
    lifter = program.get("lifter", {})
    return (lifter.get("sex") in defaults.SEX_CHOICES and lifter.get("age", 0) > 0
            and lifter.get("bodyweight", 0) > 0)


def rank_thresholds_for_lift(program, slot):
    """
    The five thresholds a lift is measured against.

    Takes: program, slot. Returns: (thresholds, custom) where custom is True
    when the lifter typed their own thresholds in for this lift.
    """
    lift = program["lifts"][slot]
    custom = lift.get("rank_thresholds")
    if custom is not None and len(custom) == 5 and min(custom) > 0:
        return list(custom), True
    lifter = program["lifter"]
    rank_type = defaults.RANK_TYPE_BY_SLOT[slot]
    return standard_thresholds(rank_type, lifter["sex"], lifter["bodyweight"], program["units"]), False


def rank_for_lift(program, slot, training_max=None):
    """
    Everything the rank screens need for one lift.

    Takes: program, slot, and optionally a training max to judge instead of
    the lift's current one.
    Returns: a dict with "available" (False until the lifter's details are
    entered) and, when available, percentile, tier (index), tier_name,
    tier_key, effect, progress (0-1 through the current tier), next_tier_name,
    training_max_for_next and gap_to_next in program units.
    The lift's training max stands in for its one-rep max. A variation is first
    turned into its equivalent main lift with the rank factor; custom
    thresholds are taken as already matching the lifter, so no age adjustment
    is applied to them.
    """
    lift = program["lifts"][slot]
    result = {"slot": slot, "name": lift_display_name(program, slot), "available": False}
    if not lifter_details_complete(program):
        return result
    if training_max is None:
        training_max = lift["training_max"]
    thresholds, custom = rank_thresholds_for_lift(program, slot)
    factor = lift.get("rank_factor", 1.0)
    if factor is None or factor <= 0:
        factor = 1.0
    coefficient = 1.0
    if not custom:
        coefficient = age_coefficient(program["lifter"]["age"])
    adjusted = training_max / factor * coefficient
    percentile = strength_percentile(adjusted, thresholds)
    tier = tier_index_for_percentile(percentile)
    lower = defaults.RANK_TIERS[tier]["min_percentile"]
    if tier + 1 < len(defaults.RANK_TIERS):
        upper = defaults.RANK_TIERS[tier + 1]["min_percentile"]
        next_tier_name = defaults.RANK_TIERS[tier + 1]["name"]
        training_max_for_next = lift_for_percentile(upper, thresholds) / coefficient * factor
    else:
        upper = 100.0
        next_tier_name = None
        training_max_for_next = None
    progress = (percentile - lower) / (upper - lower)
    if progress < 0:
        progress = 0.0
    if progress > 1:
        progress = 1.0
    result["available"] = True
    result["training_max"] = training_max
    result["percentile"] = percentile
    result["tier"] = tier
    result["tier_key"] = defaults.RANK_TIERS[tier]["key"]
    result["tier_name"] = defaults.RANK_TIERS[tier]["name"]
    result["effect"] = defaults.RANK_TIERS[tier]["effect"]
    result["progress"] = progress
    result["next_tier_name"] = next_tier_name
    result["training_max_for_next"] = training_max_for_next
    if training_max_for_next is None:
        result["gap_to_next"] = None
    else:
        result["gap_to_next"] = max(0.0, training_max_for_next - training_max)
    result["thresholds"] = thresholds
    result["custom_thresholds"] = custom
    result["rank_factor"] = factor
    return result


def all_ranks(program):
    """Takes program. Returns rank_for_lift for every scheduled slot, in slot order."""
    scheduled = scheduled_slots(program)
    ranks = []
    for slot in defaults.ALL_SLOTS:
        if slot in scheduled:
            ranks.append(rank_for_lift(program, slot))
    return ranks


# ---------------------------------------------------------------------------
# 7. Progress numbers (plain lists and dicts; the app turns them into tables)
# ---------------------------------------------------------------------------
def session_labels(program):
    """
    Labels for the x-axis of the progress charts.

    Takes: program. Returns: ["Start", "W1 D1", "W1 D2", ...] one per logged session.
    """
    labels = ["Start"]
    for entry in program["history"]:
        labels.append("W" + str(entry["week"]) + " D" + str(entry["day"]))
    return labels


def build_training_max_table(program):
    """
    Training max of every lift after every session (for the line chart).

    Takes: program. Returns: (labels, columns) where labels is the list from
    session_labels and columns is a dict lift name -> list of training maxes,
    one per label. A lift that was not trained in a session keeps its value.
    """
    labels = session_labels(program)
    columns = {}
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        values = []
        current_value = lift["starting_max"]
        for session_number in range(len(labels)):
            for record in program["tm_history"]:
                if record["slot"] == slot and record["session"] == session_number:
                    current_value = record["training_max"]
            values.append(round(current_value, 1))
        columns[lift_display_name(program, slot)] = values
    return labels, columns


def build_estimated_max_table(program):
    """
    Estimated 1RM of every lift over time, from the hardest set of each session.

    Takes: program. Returns: (labels, columns) like build_training_max_table,
    using None where a lift had no estimate yet (deloads, untrained lifts).
    """
    labels = session_labels(program)
    columns = {}
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        values = [None]
        for entry in program["history"]:
            estimate = None
            for logged in entry["lifts"]:
                if logged["slot"] == slot and logged["estimated_1rm"] is not None:
                    estimate = round(logged["estimated_1rm"], 1)
            values.append(estimate)
        columns[lift_display_name(program, slot)] = values
    return labels, columns


def build_history_rows(program):
    """
    Flatten the history into one row per logged lift for a table.

    Takes: program. Returns: a list of dicts with plain column names.
    """
    rows = []
    for entry in program["history"]:
        for logged in entry["lifts"]:
            if logged["is_deload"]:
                result_text = "deload"
            elif program["variant"] == defaults.VARIANT_ORIGINAL:
                result_text = str(logged["sets_completed"]) + " sets"
            elif program["variant"] == defaults.VARIANT_LAST_SET_RIR:
                result_text = str(logged["sets_completed"]) + " sets, " + str(logged["last_set_rir"]) + " RIR"
            else:
                result_text = str(logged["last_set_reps"]) + " reps on last set"
            rows.append({
                "Date": entry["date"],
                "Week": entry["week"],
                "Day": entry["day"],
                "Exercise": logged["name"],
                "Weight": logged["working_weight"],
                "Sets x reps": str(logged["sets"]) + " x " + str(logged["reps_per_set"]),
                "Result": result_text,
                "TM change": format_percent(logged["tm_change_percent"]),
                "TM after": round(logged["training_max_after"], 1),
                "Notes": logged["notes"],
            })
        for accessory in entry["accessories"]:
            rows.append({
                "Date": entry["date"],
                "Week": entry["week"],
                "Day": entry["day"],
                "Exercise": accessory["name"],
                "Weight": accessory["weight"],
                "Sets x reps": str(accessory["sets"]) + " x " + str(accessory["reps"]),
                "Result": accessory.get("kind", "accessory"),
                "TM change": "",
                "TM after": None,
                "Notes": "",
            })
    return rows


def calculate_session_volume(entry):
    """
    Total weight lifted in one session: sum of weight x reps over every set.

    Takes: one history entry. Returns: a float.
    """
    volume = 0.0
    for logged in entry["lifts"]:
        volume += logged["working_weight"] * logged["total_reps"]
    for accessory in entry["accessories"]:
        volume += accessory["weight"] * accessory["sets"] * accessory["reps"]
    return volume


def summary_stats(program):
    """
    Headline numbers for the progress page.

    Takes: program. Returns: dict with sessions, current_week, current_day,
    total_volume and total_sets.
    """
    total_volume = 0.0
    total_sets = 0
    for entry in program["history"]:
        total_volume += calculate_session_volume(entry)
        for logged in entry["lifts"]:
            if logged["sets_completed"] is not None:
                total_sets += logged["sets_completed"]
            else:
                total_sets += logged["sets"]
        for accessory in entry["accessories"]:
            total_sets += accessory["sets"]
    return {
        "sessions": len(program["history"]),
        "current_week": program["current_week"],
        "current_day": program["current_day"],
        "total_volume": total_volume,
        "total_sets": total_sets,
    }
