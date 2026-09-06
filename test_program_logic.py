"""
test_program_logic.py - plain assert-based tests for the training math.

Run with:
    python test_program_logic.py

No pytest needed. Every test is a function full of assert statements;
run_all_tests() at the bottom calls them one by one and prints PASS lines.
The expected weights come straight from the original spreadsheet, so a green
run here means the app reproduces the real program.
"""
import defaults
import program_logic as logic


# The example maxes used in the source spreadsheet (pounds).
SPREADSHEET_MAXES = {
    "squat": 490, "bench": 325, "deadlift": 525, "ohp": 200,
    "squat_aux_1": 420, "squat_aux_2": 460, "bench_aux_1": 310,
    "bench_aux_2": 280, "deadlift_aux": 500, "ohp_aux": 245,
}


def close_to(actual, expected, tolerance=0.01):
    """Takes two numbers. Returns True when they differ by less than the tolerance."""
    return abs(actual - expected) <= tolerance


def make_program(variant, frequency=4):
    """Takes a variant key and frequency. Returns a fresh program with the spreadsheet maxes."""
    if variant == defaults.VARIANT_HYPERTROPHY:
        names = defaults.HYPERTROPHY_DEFAULT_LIFT_NAMES
    else:
        names = defaults.STRENGTH_DEFAULT_LIFT_NAMES
    return logic.create_program(variant, "lb", 2.5, frequency, names, SPREADSHEET_MAXES)


# ---------------------------------------------------------------------------
# Rounding and lookups
# ---------------------------------------------------------------------------
def test_round_to_increment():
    assert logic.round_to_increment(343, 2.5) == 342.5
    assert logic.round_to_increment(342.6, 5) == 345
    assert logic.round_to_increment(341.25, 2.5) == 342.5      # exact half rounds up, like MROUND
    assert logic.round_to_increment(343.75, 2.5) == 345
    assert logic.round_to_increment(100.04, 0.1) == 100.0
    assert logic.round_to_increment(100.06, 0.1) == 100.1
    assert logic.round_to_increment(200, 2.5) == 200
    assert logic.round_to_increment(123.4, 0) == 123.4          # increment 0 means "do not round"


def test_percentage_buckets():
    assert len(defaults.PERCENTAGE_BUCKETS) == 21
    assert logic.nearest_percentage_bucket(70) == 70.0
    assert logic.nearest_percentage_bucket(71) == 70.0
    assert logic.nearest_percentage_bucket(71.3) == 72.5
    assert logic.nearest_percentage_bucket(49) == 50.0
    assert logic.nearest_percentage_bucket(120) == 100.0
    assert logic.bucket_index(50) == 0
    assert logic.bucket_index(100) == 20
    assert logic.lookup_by_percentage(defaults.STRENGTH_REPS_PER_SET, 70) == 5
    assert logic.lookup_by_percentage(defaults.ORIGINAL_RIR_CUTOFF, 60) == 4
    assert logic.lookup_by_percentage(defaults.RTF_LAST_SET_REP_TARGET, 95) == 1
    # Every 21-entry table really has 21 entries.
    for table in [defaults.STRENGTH_REPS_PER_SET, defaults.ORIGINAL_RIR_CUTOFF,
                  defaults.LAST_SET_RIR_TARGET, defaults.RTF_LAST_SET_REP_TARGET,
                  defaults.HYPERTROPHY_REPS_PER_SET, defaults.HYPERTROPHY_LAST_SET_REP_TARGET,
                  defaults.STRENGTH_MAIN_INTENSITIES, defaults.HYPERTROPHY_MAIN_INTENSITIES]:
        assert len(table) == 21


# ---------------------------------------------------------------------------
# Prescriptions (numbers taken from the real spreadsheet)
# ---------------------------------------------------------------------------
def test_week_one_squat_original():
    program = make_program(defaults.VARIANT_ORIGINAL)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_ORIGINAL, squat, 1, 2.5)
    assert prescription["intensity"] == 70.0
    assert prescription["working_weight"] == 342.5
    assert prescription["reps_per_set"] == 5
    assert prescription["rir_cutoff"] == 3
    assert prescription["lower_set_threshold"] == 4
    assert prescription["upper_set_threshold"] == 6
    assert prescription["is_deload"] is False


def test_week_one_sumo_deadlift_auxiliary():
    program = make_program(defaults.VARIANT_ORIGINAL)
    sumo = program["lifts"]["deadlift_aux"]
    assert sumo["is_main"] is False
    prescription = logic.get_prescription(defaults.VARIANT_ORIGINAL, sumo, 1, 2.5)
    assert prescription["intensity"] == 60.0
    assert prescription["working_weight"] == 300
    assert prescription["reps_per_set"] == 7
    assert prescription["rir_cutoff"] == 4


def test_week_two_squat():
    program = make_program(defaults.VARIANT_ORIGINAL)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_ORIGINAL, squat, 2, 2.5)
    assert prescription["intensity"] == 75.0
    assert prescription["working_weight"] == 367.5
    assert prescription["reps_per_set"] == 4
    assert prescription["rir_cutoff"] == 3


def test_incline_press_matches_spreadsheet_screenshot():
    # The instructions show 167.5 for a 280 incline press in week 1 (60%).
    program = make_program(defaults.VARIANT_RTF)
    incline = program["lifts"]["bench_aux_2"]
    prescription = logic.get_prescription(defaults.VARIANT_RTF, incline, 1, 2.5)
    assert prescription["working_weight"] == 167.5
    assert prescription["last_set_rep_target"] == 14


def test_variant_specific_targets():
    program = make_program(defaults.VARIANT_RTF)
    squat = program["lifts"]["squat"]
    rtf = logic.get_prescription(defaults.VARIANT_RTF, squat, 1, 2.5)
    assert rtf["sets"] == 5
    assert rtf["reps_per_set"] == 5
    assert rtf["last_set_rep_target"] == 10
    assert "rir_cutoff" not in rtf

    last_set_rir = logic.get_prescription(defaults.VARIANT_LAST_SET_RIR, squat, 1, 2.5)
    assert last_set_rir["last_set_rir_target"] == 3
    assert last_set_rir["sets"] == 5


def test_hypertrophy_prescription():
    program = make_program(defaults.VARIANT_HYPERTROPHY)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_HYPERTROPHY, squat, 1, 2.5)
    assert prescription["intensity"] == 70.0
    assert prescription["working_weight"] == 342.5
    assert prescription["sets"] == 4
    assert prescription["reps_per_set"] == 10
    assert prescription["last_set_rep_target"] == 12

    leg_press = program["lifts"]["squat_aux_1"]
    aux = logic.get_prescription(defaults.VARIANT_HYPERTROPHY, leg_press, 1, 2.5)
    assert aux["intensity"] == 65.0                 # only 5 points lighter in the hypertrophy template
    assert aux["working_weight"] == 272.5           # 420 * 0.65 = 273 -> 272.5
    assert aux["reps_per_set"] == 12
    assert aux["last_set_rep_target"] == 15


def test_single_at_8():
    new_max = logic.calculate_training_max_from_single(460, 90.0)
    assert round(new_max) == 511
    assert close_to(new_max, 511.11)
    assert logic.calculate_working_weight(new_max, 70.0, 2.5) == 357.5


# ---------------------------------------------------------------------------
# The training-max engine
# ---------------------------------------------------------------------------
def test_ladder_index():
    assert logic.ladder_index_for_difference(-10) == 0
    assert logic.ladder_index_for_difference(-2) == 0
    assert logic.ladder_index_for_difference(-1) == 1
    assert logic.ladder_index_for_difference(0) == 2
    assert logic.ladder_index_for_difference(1) == 3
    assert logic.ladder_index_for_difference(2) == 4
    assert logic.ladder_index_for_difference(3) == 5
    assert logic.ladder_index_for_difference(4) == 6
    assert logic.ladder_index_for_difference(5) == 7
    assert logic.ladder_index_for_difference(12) == 7


def test_rtf_ladder_branches():
    program = make_program(defaults.VARIANT_RTF)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_RTF, squat, 1, 2.5)   # target 10 reps
    expected = {0: -5.0, 8: -5.0, 9: -2.0, 10: 0.0, 11: 0.5, 12: 1.0, 13: 1.5, 14: 2.0, 15: 3.0, 25: 3.0}
    for reps in expected:
        change = logic.calculate_tm_change_percent(defaults.VARIANT_RTF, squat, prescription, {"last_set_reps": reps})
        assert change == expected[reps], (reps, change)


def test_hypertrophy_uses_the_same_ladder():
    program = make_program(defaults.VARIANT_HYPERTROPHY)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_HYPERTROPHY, squat, 1, 2.5)  # target 12 reps
    assert logic.calculate_tm_change_percent(defaults.VARIANT_HYPERTROPHY, squat, prescription, {"last_set_reps": 10}) == -5.0
    assert logic.calculate_tm_change_percent(defaults.VARIANT_HYPERTROPHY, squat, prescription, {"last_set_reps": 11}) == -2.0
    assert logic.calculate_tm_change_percent(defaults.VARIANT_HYPERTROPHY, squat, prescription, {"last_set_reps": 12}) == 0.0
    assert logic.calculate_tm_change_percent(defaults.VARIANT_HYPERTROPHY, squat, prescription, {"last_set_reps": 15}) == 1.5
    assert logic.calculate_tm_change_percent(defaults.VARIANT_HYPERTROPHY, squat, prescription, {"last_set_reps": 17}) == 3.0


def test_last_set_rir_ladder_branches():
    program = make_program(defaults.VARIANT_LAST_SET_RIR)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_LAST_SET_RIR, squat, 1, 2.5)  # 5 sets, RIR target 3
    cases = [
        (3, 5, -5.0),   # 2 sets short: big drop, RIR ignored
        (0, 5, -5.0),
        (4, 5, -2.0),   # 1 set short
        (5, 2, -2.0),   # all sets, 1 RIR under target
        (5, 0, -2.0),   # all sets, way under target: still the small drop
        (5, 3, 0.0),    # hit the target
        (5, 4, 0.5),
        (5, 5, 1.0),
        (5, 6, 1.5),
        (5, 7, 2.0),
        (5, 8, 3.0),
        (5, 12, 3.0),
        (6, 3, 0.0),    # an extra set does not change anything by itself
    ]
    for sets_completed, rir, expected in cases:
        performance = {"sets_completed": sets_completed, "last_set_rir": rir}
        change = logic.calculate_tm_change_percent(defaults.VARIANT_LAST_SET_RIR, squat, prescription, performance)
        assert change == expected, (sets_completed, rir, change)


def test_original_set_thresholds():
    program = make_program(defaults.VARIANT_ORIGINAL)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_ORIGINAL, squat, 1, 2.5)
    expected = {0: -5.0, 3: -5.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 2.0, 12: 2.0}
    for sets_completed in expected:
        change = logic.calculate_tm_change_percent(defaults.VARIANT_ORIGINAL, squat, prescription,
                                                   {"sets_completed": sets_completed})
        assert change == expected[sets_completed], (sets_completed, change)

    # The thresholds and percentages are per-lift editable.
    squat["lower_set_threshold"] = 6
    squat["upper_set_threshold"] = 8
    squat["increase_percent"] = 1.0
    squat["decrease_percent"] = -3.0
    assert logic.calculate_tm_change_percent(defaults.VARIANT_ORIGINAL, squat, prescription, {"sets_completed": 5}) == -3.0
    assert logic.calculate_tm_change_percent(defaults.VARIANT_ORIGINAL, squat, prescription, {"sets_completed": 9}) == 1.0


def test_editable_ladder():
    program = make_program(defaults.VARIANT_RTF)
    squat = program["lifts"]["squat"]
    squat["ladder"] = [-10.0, -4.0, 0.0, 1.0, 2.0, 3.0, 4.0, 6.0]
    prescription = logic.get_prescription(defaults.VARIANT_RTF, squat, 1, 2.5)
    assert logic.calculate_tm_change_percent(defaults.VARIANT_RTF, squat, prescription, {"last_set_reps": 5}) == -10.0
    assert logic.calculate_tm_change_percent(defaults.VARIANT_RTF, squat, prescription, {"last_set_reps": 16}) == 6.0


def test_deload_weeks_never_change_tm():
    terrible = {"sets_completed": 0, "last_set_rir": 0, "last_set_reps": 0}
    amazing = {"sets_completed": 12, "last_set_rir": 12, "last_set_reps": 40}
    for variant in defaults.ALL_VARIANTS:
        program = make_program(variant)
        for slot in ["squat", "deadlift_aux"]:
            lift = program["lifts"][slot]
            for week in [7, 14, 21]:
                assert logic.is_deload_week(week)
                prescription = logic.get_prescription(variant, lift, week, 2.5)
                assert prescription["is_deload"] is True
                assert prescription["reps_per_set"] == defaults.DELOAD_REPS_PER_SET
                assert "rir_cutoff" not in prescription
                assert "last_set_rir_target" not in prescription
                assert "last_set_rep_target" not in prescription
                assert logic.calculate_tm_change_percent(variant, lift, prescription, terrible) == 0.0
                assert logic.calculate_tm_change_percent(variant, lift, prescription, amazing) == 0.0
    for week in [1, 6, 8, 13, 15, 20]:
        assert not logic.is_deload_week(week)


def test_intensity_tables():
    strength = make_program(defaults.VARIANT_RTF)
    hypertrophy = make_program(defaults.VARIANT_HYPERTROPHY)
    for week in range(1, 22):
        main = strength["lifts"]["squat"]["intensities"][week - 1]
        aux = strength["lifts"]["squat_aux_1"]["intensities"][week - 1]
        assert close_to(main - aux, 10.0)
        hyp_main = hypertrophy["lifts"]["squat"]["intensities"][week - 1]
        hyp_aux = hypertrophy["lifts"]["squat_aux_1"]["intensities"][week - 1]
        assert close_to(hyp_main - hyp_aux, 5.0)
        if logic.is_deload_week(week):
            assert main == 60.0 and hyp_main == 60.0
    assert strength["lifts"]["squat"]["intensities"][0] == 70.0
    assert strength["lifts"]["squat"]["intensities"][19] == 95.0      # week 20
    assert hypertrophy["lifts"]["squat"]["intensities"][19] == 82.5   # the hypertrophy ceiling
    assert max(hypertrophy["lifts"]["squat"]["intensities"]) == 82.5
    assert logic.block_number(1) == 1 and logic.block_number(7) == 1
    assert logic.block_number(8) == 2 and logic.block_number(14) == 2
    assert logic.block_number(15) == 3 and logic.block_number(21) == 3


# ---------------------------------------------------------------------------
# Logging a session and moving through the calendar
# ---------------------------------------------------------------------------
def test_log_workout_and_calendar():
    program = make_program(defaults.VARIANT_RTF, frequency=4)
    workout = logic.build_workout(program, 1, 1)
    slots = []
    for exercise in workout:
        slots.append(exercise["slot"])
    assert slots == ["squat", "bench_aux_2", "deadlift_aux"]

    results = [
        {"slot": "squat", "last_set_reps": 13, "single_at_8": None, "notes": ""},        # beat 10 by 3 -> +1.5%
        {"slot": "bench_aux_2", "last_set_reps": 14, "single_at_8": None, "notes": ""},  # hit 14 exactly -> 0
        {"slot": "deadlift_aux", "last_set_reps": 12, "single_at_8": None, "notes": ""}, # 2 short of 14 -> -5%
    ]
    accessories = [{"name": "Barbell Row", "kind": "accessory", "weight": 135, "sets": 3, "reps": 10}]
    messages = logic.log_workout(program, 1, 1, results, accessories, "felt good", "2026-01-05")

    assert len(messages) == 3
    assert "going up 1.5%" in messages[0]
    assert "beat the target by 3 reps" in messages[0]
    assert "stays at" in messages[1]
    assert "dropping 5%" in messages[2]
    assert close_to(program["lifts"]["squat"]["training_max"], 490 * 1.015)
    assert close_to(program["lifts"]["bench_aux_2"]["training_max"], 280)
    assert close_to(program["lifts"]["deadlift_aux"]["training_max"], 475)
    assert len(program["history"]) == 1
    assert program["history"][0]["lifts"][0]["estimated_1rm"] is not None
    assert logic.find_last_accessory_result(program, "barbell row")["weight"] == 135
    assert logic.find_last_accessory_result(program, "Face Pull") is None

    # The calendar pointer moves one day at a time and rolls into the next week.
    assert (program["current_week"], program["current_day"]) == (1, 1)
    logic.advance_to_next_day(program)
    assert (program["current_week"], program["current_day"]) == (1, 2)
    logic.advance_to_next_day(program)
    logic.advance_to_next_day(program)
    logic.advance_to_next_day(program)
    assert (program["current_week"], program["current_day"]) == (2, 1)

    # Next week the squat is heavier because the training max grew.
    week_two_squat = logic.get_prescription_for_slot(program, "squat", 2)
    assert week_two_squat["working_weight"] == logic.round_to_increment(490 * 1.015 * 0.75, 2.5)

    # A single @8 logged in week 2 replaces the training max before judging the sets.
    results = [{"slot": "squat", "last_set_reps": 8, "single_at_8": 460, "notes": ""}]  # 460/0.9 = 511.1, then hit the 75% target of 8 -> no change
    logic.log_workout(program, 2, 1, results, [], "", "2026-01-12")
    assert close_to(program["lifts"]["squat"]["training_max"], 511.11)
    assert program["history"][1]["lifts"][0]["working_weight"] == logic.round_to_increment(511.11 * 0.75, 2.5)


def test_full_cycle_simulation():
    """Run 21 weeks per variant: always hitting the target leaves every TM unchanged."""
    for variant in defaults.ALL_VARIANTS:
        program = make_program(variant, frequency=3)
        for week in range(1, 22):
            for day in range(1, 4):
                results = []
                for exercise in logic.build_workout(program, week, day):
                    result = {"slot": exercise["slot"], "single_at_8": None, "notes": "",
                              "sets_completed": exercise["sets"],
                              "last_set_rir": exercise.get("last_set_rir_target", 0),
                              "last_set_reps": exercise.get("last_set_rep_target", 0)}
                    results.append(result)
                logic.log_workout(program, week, day, results, [], "", "2026-01-01")
                logic.advance_to_next_day(program)
        assert len(program["history"]) == 63
        for slot in defaults.ALL_SLOTS:
            assert close_to(program["lifts"][slot]["training_max"], SPREADSHEET_MAXES[slot]), (variant, slot)
        assert (program["current_week"], program["current_day"]) == (21, 3)
        assert logic.is_cycle_finished(program)
        logic.start_new_cycle(program)
        assert (program["current_week"], program["current_day"]) == (1, 1)

    # Beating the target by 5+ every week for RTF: 18 training weeks x 3% each.
    program = make_program(defaults.VARIANT_RTF, frequency=3)
    for week in range(1, 22):
        for day in range(1, 4):
            results = []
            for exercise in logic.build_workout(program, week, day):
                results.append({"slot": exercise["slot"], "last_set_reps": exercise.get("last_set_rep_target", 0) + 5,
                                "single_at_8": None, "notes": ""})
            logic.log_workout(program, week, day, results, [], "", "2026-01-01")
            logic.advance_to_next_day(program)
    assert close_to(program["lifts"]["squat"]["training_max"], 490 * (1.03 ** 18), 0.5)
    labels, columns = logic.build_training_max_table(program)
    assert labels[0] == "Start" and labels[1] == "W1 D1" and len(labels) == 64
    assert columns["Squat"][0] == 490
    assert columns["Squat"][-1] == round(490 * (1.03 ** 18), 1)
    stats = logic.summary_stats(program)
    assert stats["sessions"] == 63
    assert stats["total_volume"] > 0
    assert len(logic.build_history_rows(program)) == 21 * 10   # 10 lifts per week, no accessories logged


def test_splits_cover_every_lift():
    for split_style in defaults.SPLIT_STYLES:
        for frequency in defaults.FREQUENCY_CHOICES:
            split = defaults.SPLITS_BY_STYLE[split_style][frequency]
            scheduled = []
            for day in split:
                for slot in day:
                    scheduled.append(slot)
            assert len(split) == frequency
            for slot in defaults.MAIN_SLOTS:
                assert scheduled.count(slot) == 1, (split_style, frequency, slot)
            if frequency == 2:
                assert len(scheduled) == 8
                assert "squat_aux_2" not in scheduled and "bench_aux_2" not in scheduled
            else:
                assert sorted(scheduled) == sorted(defaults.ALL_SLOTS), (split_style, frequency)

    # The lower-frequency layout alternates lower and upper days (from the LF spreadsheets).
    lower_frequency = logic.build_default_days(4, [], defaults.SPLIT_UPPER_LOWER)
    assert lower_frequency[0]["slots"] == ["squat", "deadlift_aux", "squat_aux_2"]
    assert lower_frequency[1]["slots"] == ["bench", "ohp_aux", "bench_aux_2"]
    assert lower_frequency[2]["slots"] == ["deadlift", "squat_aux_1"]
    assert lower_frequency[3]["slots"] == ["ohp", "bench_aux_1"]
    program = logic.create_program(defaults.VARIANT_RTF, "lb", 5.0, 5, defaults.STRENGTH_DEFAULT_LIFT_NAMES,
                                   SPREADSHEET_MAXES, [], defaults.SPLIT_UPPER_LOWER)
    assert program["split_style"] == defaults.SPLIT_UPPER_LOWER
    assert program["days"][2]["slots"] == ["deadlift"]
    old_style = make_program(defaults.VARIANT_RTF)
    old_style["split_style"] = "something_removed"
    logic.ensure_program_defaults(old_style)
    assert old_style["split_style"] == defaults.SPLIT_FULL_BODY

    # The setup preset puts every trained slot on exactly one of its six days.
    preset = defaults.SETUP_PRESETS[defaults.PRESET_ANDY]
    assert len(preset["accessories"]) == preset["frequency"]
    for slot in defaults.ALL_SLOTS:
        if slot in preset["skipped_slots"]:
            assert slot not in preset["days"]
        else:
            assert 1 <= preset["days"][slot] <= preset["frequency"], slot
    days = logic.build_default_days(4)
    assert len(days) == 4
    assert days[0]["slots"] == ["squat", "bench_aux_2", "deadlift_aux"]
    assert days[0]["accessories"] == [defaults.UPPER_BACK_EXERCISES[0]]   # a row is suggested on each day
    assert "upper_back" not in days[0]


def test_epley_estimate():
    assert close_to(logic.estimate_one_rep_max(100, 10), 133.33)
    assert logic.estimate_one_rep_max(200, 1) == 200
    assert close_to(logic.estimate_one_rep_max(342.5, 13), 342.5 * (1 + 13 / 30))


def test_messages_and_formatting():
    assert logic.format_weight(342.5, "lb") == "342.5 lb"
    assert logic.format_weight(300.0, "kg") == "300 kg"
    assert logic.format_percent(1.5) == "1.5%"
    assert logic.format_percent(-5.0) == "-5%"
    assert logic.plural(1, "rep") == "1 rep"
    assert logic.plural(3, "rep") == "3 reps"

    program = make_program(defaults.VARIANT_RTF)
    squat = program["lifts"]["squat"]
    prescription = logic.get_prescription(defaults.VARIANT_RTF, squat, 1, 2.5)
    message = logic.describe_tm_change(defaults.VARIANT_RTF, prescription, {"last_set_reps": 13}, 1.5, 497.35, "lb")
    assert message.startswith("You beat the target by 3 reps - training max going up 1.5% to 497.")
    message = logic.describe_tm_change(defaults.VARIANT_RTF, prescription, {"last_set_reps": 9}, -2.0, 480.2, "lb")
    assert message == "You fell 1 rep short of the target of 10 - training max dropping 2% to 480.2 lb"
    message = logic.describe_tm_change(defaults.VARIANT_RTF, prescription, {"last_set_reps": 10}, 0.0, 490, "lb")
    assert message == "You hit the target of 10 reps exactly - training max stays at 490 lb"
    assert logic.describe_prescription(defaults.VARIANT_RTF, prescription) == \
        "4 sets of 5, then 1 set for as many reps as possible (target 10)"

    original = logic.get_prescription(defaults.VARIANT_ORIGINAL, squat, 1, 2.5)
    assert logic.describe_prescription(defaults.VARIANT_ORIGINAL, original) == \
        "Sets of 5 until you reach 3 RIR (target 4-6 sets)"
    deload = logic.get_prescription(defaults.VARIANT_ORIGINAL, squat, 7, 2.5)
    assert logic.describe_prescription(defaults.VARIANT_ORIGINAL, deload) == "Deload: 5 easy sets of 5, no target"


def test_skipped_slots_and_display_names():
    names = dict(defaults.STRENGTH_DEFAULT_LIFT_NAMES)
    program = logic.create_program(defaults.VARIANT_RTF, "lb", 5.0, 4, names, SPREADSHEET_MAXES,
                                   ["ohp", "squat_aux_2"])
    for day in program["days"]:
        assert "ohp" not in day["slots"]
        assert "squat_aux_2" not in day["slots"]
    assert program["days"][3]["slots"] == []          # day 4 was OHP + squat auxiliary 2
    assert "ohp" in program["lifts"]                  # settings are kept so it can be added back
    assert logic.scheduled_slots(program) == ["squat", "bench_aux_2", "deadlift_aux", "bench",
                                              "squat_aux_1", "ohp_aux", "deadlift", "bench_aux_1"]
    assert logic.build_workout(program, 1, 4) == []
    assert program["image_choices"] == {}

    # The same exercise in several slots gets a tag so charts and history stay unambiguous.
    names["squat_aux_1"] = "Squat"
    names["squat_aux_2"] = "squat"
    program = logic.create_program(defaults.VARIANT_RTF, "lb", 5.0, 4, names, SPREADSHEET_MAXES)
    assert logic.lift_display_name(program, "squat") == "Squat (main)"
    assert logic.lift_display_name(program, "squat_aux_1") == "Squat (aux 1)"
    assert logic.lift_display_name(program, "squat_aux_2") == "squat (aux 2)"
    assert logic.lift_display_name(program, "bench") == "Bench Press"
    labels, columns = logic.build_training_max_table(program)
    assert len(columns) == 10
    assert "Squat (aux 1)" in columns
    assert logic.build_workout(program, 1, 2)[1]["name"] == "Squat (aux 1)"
    messages = logic.log_workout(program, 1, 2, [{"slot": "squat_aux_1", "last_set_reps": 20}], [], "", "2026-01-01")
    assert messages[0].startswith("Squat (aux 1): ")


def test_ensure_program_defaults():
    program = make_program(defaults.VARIANT_RTF)
    del program["image_choices"]
    del program["deload_reps_per_set"]
    del program["lifts"]["squat"]["image_path"]
    program["days"][0]["upper_back"] = "Pull-Up"           # the old separate slot
    logic.ensure_program_defaults(program)
    assert program["image_choices"] == {}
    assert program["deload_reps_per_set"] == defaults.DELOAD_REPS_PER_SET
    assert program["lifts"]["squat"]["image_path"] == ""
    assert program["days"][0]["accessories"][0] == "Pull-Up"   # moved to the front of the accessories
    assert "upper_back" not in program["days"][0]


def test_rank_standards():
    thresholds = logic.standard_thresholds("squat", "male", 180, "lb")
    rounded = []
    for value in thresholds:
        rounded.append(round(value))
    assert rounded == [135, 225, 270, 360, 450]
    for position in range(5):
        assert close_to(logic.strength_percentile(thresholds[position], thresholds), defaults.STANDARD_PERCENTILES[position])
    assert close_to(logic.strength_percentile(300, thresholds), 60)            # a third of the way from 270 (50) to 360 (80)
    assert close_to(logic.strength_percentile(67.5, thresholds), 2.5)           # half of beginner
    assert logic.strength_percentile(0, thresholds) == 0
    step = thresholds[4] - thresholds[3]
    assert close_to(logic.strength_percentile(thresholds[4] + step, thresholds), 97.5)        # Legend I
    assert close_to(logic.strength_percentile(thresholds[4] + 3 * step, thresholds), 99.375)  # Legend III
    for percentile in [2.5, 5, 30, 60, 80, 95, 97.5, 99]:
        lift = logic.lift_for_percentile(percentile, thresholds)
        assert close_to(logic.strength_percentile(lift, thresholds), percentile, 0.001), percentile
    heavier = logic.standard_thresholds("squat", "male", 220, "lb")
    assert 450 < heavier[4] < 450 * 220 / 180                                  # more, but not in proportion
    kilograms = logic.standard_thresholds("squat", "male", 180 * defaults.KG_PER_LB, "kg")
    assert close_to(kilograms[4] / defaults.KG_PER_LB, 450, 0.01)
    for sex in defaults.SEX_CHOICES:
        for rank_type in ["squat", "bench", "deadlift", "ohp"]:
            values = logic.standard_thresholds(rank_type, sex, 150, "lb")
            assert values == sorted(values) and values[0] > 0


def test_rank_tiers_and_age():
    expected = {0: "Mortal", 4.9: "Mortal", 5: "Initiate", 12.5: "Vanguard", 20: "Warden", 35: "Colossus",
                50: "Titan", 65: "Atlas", 80: "Demigod", 95: "Transcendent", 97.5: "Legend I",
                98.75: "Legend II", 99.4: "Legend III", 100: "Legend III"}
    for percentile in expected:
        assert defaults.RANK_TIERS[logic.tier_index_for_percentile(percentile)]["name"] == expected[percentile], percentile
    assert len(defaults.RANK_TIERS) == 12
    assert logic.age_coefficient(30) == 1.0
    assert logic.age_coefficient(0) == 1.0
    assert logic.age_coefficient(60) == 1.34
    assert logic.age_coefficient(16) == 1.13
    assert logic.age_coefficient(95) == logic.age_coefficient(90)
    assert logic.default_rank_factor("Front Squat") == 0.85
    assert logic.default_rank_factor("Squat") == 1.0
    assert logic.default_rank_factor("Some New Lift") == 1.0


def test_rank_for_lift():
    program = make_program(defaults.VARIANT_RTF)                     # squat training max 490 lb
    assert logic.rank_for_lift(program, "squat")["available"] is False   # no lifter details yet
    program["lifter"] = {"sex": "male", "age": 30, "bodyweight": 180.0}
    rank = logic.rank_for_lift(program, "squat")
    assert rank["available"] is True
    assert rank["tier_name"] == "Transcendent"                        # 490 sits between elite 450 and Legend I 540
    assert 95 < rank["percentile"] < 97.5
    assert rank["next_tier_name"] == "Legend I"
    assert close_to(rank["training_max_for_next"], 540, 0.01)
    assert close_to(rank["gap_to_next"], 50, 0.01)
    assert rank["effect"] == "electric"

    front_squat = logic.rank_for_lift(program, "squat_aux_1")         # Front Squat 420 at factor 0.85 counts as a 494 squat
    assert program["lifts"]["squat_aux_1"]["rank_factor"] == 0.85
    assert front_squat["tier_name"] == "Transcendent"

    program["lifter"]["age"] = 60                                      # the same lift counts for more at 60
    assert logic.rank_for_lift(program, "squat")["percentile"] > rank["percentile"]

    program["lifts"]["squat"]["rank_thresholds"] = [200, 300, 400, 500, 600]   # typed in from a calculator
    custom = logic.rank_for_lift(program, "squat")
    assert custom["custom_thresholds"] is True
    assert close_to(custom["percentile"], 77)                          # 490 is 90% of the way from 400 (50) to 500 (80)
    assert custom["tier_name"] == "Atlas"
    assert close_to(custom["progress"], 0.8)                           # 77 is 12/15 of the way through Atlas (65-80)

    ranks = logic.all_ranks(program)
    assert len(ranks) == 10
    assert ranks[0]["slot"] == "squat"


def test_rank_changes_when_logging():
    program = make_program(defaults.VARIANT_RTF)
    program["lifter"] = {"sex": "male", "age": 30, "bodyweight": 180.0}
    # A single @8 of 500 lifts the squat training max to 555.6, past the Legend I line at 540.
    results = [{"slot": "squat", "last_set_reps": 10, "single_at_8": 500, "notes": ""}]
    messages = logic.log_workout(program, 1, 1, results, [], "", "2026-01-05")
    assert messages[-1] == "Rank up! Squat: Transcendent -> Legend I"
    assert program["history"][0]["rank_changes"][0]["to_name"] == "Legend I"
    assert program["history"][0]["lifts"][0]["rank_before"] == 8
    assert program["history"][0]["lifts"][0]["rank_after"] == 9
    # Falling 3 reps short the next week drops the max 5% and the rank with it.
    results = [{"slot": "squat", "last_set_reps": 5, "single_at_8": None, "notes": ""}]
    messages = logic.log_workout(program, 2, 1, results, [], "", "2026-01-12")
    assert messages[-1] == "Rank down: Squat is now Transcendent"
    # Without lifter details there are no rank messages at all.
    plain = make_program(defaults.VARIANT_RTF)
    messages = logic.log_workout(plain, 1, 1, [{"slot": "squat", "last_set_reps": 15, "single_at_8": None, "notes": ""}], [], "", "2026-01-05")
    assert len(messages) == 1
    assert plain["history"][0]["rank_changes"] == []


def run_all_tests():
    """Runs every test function above and prints a PASS line for each."""
    tests = [
        test_round_to_increment,
        test_percentage_buckets,
        test_week_one_squat_original,
        test_week_one_sumo_deadlift_auxiliary,
        test_week_two_squat,
        test_incline_press_matches_spreadsheet_screenshot,
        test_variant_specific_targets,
        test_hypertrophy_prescription,
        test_single_at_8,
        test_ladder_index,
        test_rtf_ladder_branches,
        test_hypertrophy_uses_the_same_ladder,
        test_last_set_rir_ladder_branches,
        test_original_set_thresholds,
        test_editable_ladder,
        test_deload_weeks_never_change_tm,
        test_intensity_tables,
        test_log_workout_and_calendar,
        test_full_cycle_simulation,
        test_splits_cover_every_lift,
        test_epley_estimate,
        test_messages_and_formatting,
        test_skipped_slots_and_display_names,
        test_ensure_program_defaults,
        test_rank_standards,
        test_rank_tiers_and_age,
        test_rank_for_lift,
        test_rank_changes_when_logging,
    ]
    for test in tests:
        test()
        print("PASS " + test.__name__)
    print("All " + str(len(tests)) + " tests passed.")


if __name__ == "__main__":
    run_all_tests()
