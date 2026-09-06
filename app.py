"""
app.py - the Streamlit user interface for SBS Trainer.

Run with:
    streamlit run app.py

This file only draws screens and reads inputs. The training math lives in
program_logic.py, saving in storage.py and pictures in exercise_library.py.
The whole app state is one dictionary called "program". It is kept in
st.session_state (loaded from user_data/program.json once per browser session)
and written back to disk after every change.

The program design belongs to Greg Nuckols / Stronger By Science
(https://www.strongerbyscience.com/program-bundle/). This app is an unofficial
personal project and is not affiliated with or endorsed by SBS.
"""
import os

import pandas as pd
import streamlit as st

import defaults
import exercise_library
import program_logic as logic
import storage

st.set_page_config(page_title="SBS Trainer", page_icon="🏋️", layout="centered")

SBS_URL = "https://www.strongerbyscience.com/program-bundle/"
CREDIT_MARKDOWN = (
    "Program design by **Greg Nuckols / Stronger By Science** "
    "([SBS program bundle](" + SBS_URL + ")). "
    "This app is an unofficial personal project, not affiliated with or endorsed by "
    "Stronger By Science."
)

PAGE_HOME = "Home"
PAGE_SETUP = "Setup"
PAGE_WORKOUT = "Today's Workout"
PAGE_RANKS = "Ranks"
PAGE_PROGRESS = "Progress"
PAGE_SETTINGS = "Settings"
PAGES = [PAGE_HOME, PAGE_SETUP, PAGE_WORKOUT, PAGE_RANKS, PAGE_PROGRESS, PAGE_SETTINGS]

# Streamlit can colour text with :blue[...] and friends; one colour per rank tier.
TIER_TEXT_COLORS = {
    "mortal": "gray", "initiate": "gray", "vanguard": "blue", "warden": "green", "colossus": "green",
    "titan": "violet", "atlas": "orange", "demigod": "orange", "transcendent": "red",
    "legend_1": "rainbow", "legend_2": "rainbow", "legend_3": "rainbow",
}

USER_IMAGES_DIR = os.path.join(storage.USER_DATA_DIR, "images")


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
@st.cache_data
def load_catalog():
    """Returns the exercise catalog list, read from disk once and cached."""
    return exercise_library.load_catalog()


def get_program():
    """
    The active program dict, loaded from JSON the first time it is needed.

    Returns: the program dict, or None when no program has been created yet.
    """
    if "program" not in st.session_state:
        program = storage.load_program()
        if program is not None:
            logic.ensure_program_defaults(program)
        st.session_state["program"] = program
        st.session_state["generation"] = 0
    return st.session_state["program"]


def replace_program(program):
    """
    Swap in a different program (new, demo, imported, or None) and save it.

    Takes: a program dict or None. Returns: nothing.
    """
    if program is not None:
        logic.ensure_program_defaults(program)
    st.session_state["program"] = program
    # Bumping the generation number changes every widget key, so old widget
    # values do not leak into the new program's screens.
    st.session_state["generation"] = st.session_state.get("generation", 0) + 1
    if program is None:
        storage.delete_program()          # makes a backup first
    else:
        storage.backup_program()          # keep a copy of whatever was there
        storage.save_program(program)


def save_program():
    """Writes the active program to user_data/program.json. Returns nothing."""
    storage.save_program(st.session_state["program"])


def widget_key(name):
    """
    Build a widget key that changes whenever the program is replaced.

    Takes: a short name. Returns: a string key for Streamlit widgets.
    """
    return "g" + str(st.session_state.get("generation", 0)) + "_" + name


def go_to_page(page):
    """Takes a page name. Switches the sidebar navigation to it and reruns."""
    st.session_state["next_page"] = page
    st.rerun()


def variant_name(variant):
    """Takes a variant key. Returns its display name (used by radio buttons)."""
    return defaults.VARIANT_NAMES[variant]


def slot_label(program, slot):
    """Takes program and slot key. Returns e.g. "Front Squat (Squat auxiliary 1)"."""
    return program["lifts"][slot]["name"] + " (" + defaults.SLOT_LABELS[slot] + ")"


def show_image(name, lift=None, width=560):
    """
    Draw the start-and-finish picture strip for an exercise name.

    Takes: exercise name, optional lift settings (for an uploaded image), width
    in pixels. The user's own upload wins, then a library picture they picked
    in Settings, then the automatic name match. Returns: nothing.
    """
    program = get_program()
    custom_path = ""
    if lift is not None:
        custom_path = lift.get("image_path", "")
    chosen_id = ""
    if program is not None:
        chosen_id = program["image_choices"].get(name, "")
    path = exercise_library.find_image_path(name, load_catalog(), custom_path, chosen_id)
    if path:
        st.image(path, width=width)
    else:
        st.caption("(no image: run python scripts/fetch_exercises.py)")


def accessory_choices():
    """Returns the accessory dropdown list: rows and pull-ups, our other suggestions, then the whole library."""
    choices = list(defaults.UPPER_BACK_EXERCISES) + list(defaults.ACCESSORY_SUGGESTIONS)
    for name in exercise_library.catalog_names(load_catalog()):
        if name not in choices:
            choices.append(name)
    return choices


def split_style_name(split_style):
    """Takes a split style key. Returns its display name (used by radio buttons)."""
    return defaults.SPLIT_STYLE_NAMES[split_style]


def sex_label(value):
    """Takes "Not set", "male" or "female". Returns the text to show in a dropdown."""
    if value in defaults.SEX_NAMES:
        return defaults.SEX_NAMES[value]
    return "Not set"


def ordinal(number):
    """Takes a whole number. Returns it with its suffix: 1st, 2nd, 3rd, 4th, 11th, 91st."""
    number = int(number)
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return str(number) + suffix


def tier_text(tier_key, tier_name):
    """Takes a tier key and name. Returns the name wrapped in Streamlit's colour markup."""
    return ":" + TIER_TEXT_COLORS.get(tier_key, "gray") + "[**" + tier_name + "**]"


def draw_lifter_form(program, key_prefix):
    """
    Draw sex, age and bodyweight inputs with a save button (used by Ranks and Settings).

    Takes: program, a prefix that keeps the widget keys apart. Returns: nothing.
    """
    lifter = program["lifter"]
    sex_options = ["Not set", "male", "female"]
    current_sex = lifter.get("sex") if lifter.get("sex") in defaults.SEX_CHOICES else "Not set"
    column_sex, column_age, column_weight = st.columns(3)
    sex = column_sex.selectbox("Sex", sex_options, index=sex_options.index(current_sex), format_func=sex_label,
                               key=widget_key(key_prefix + "_sex"))
    age = column_age.number_input("Age", min_value=0, max_value=100, value=int(lifter.get("age", 0)), step=1,
                                  key=widget_key(key_prefix + "_age"))
    bodyweight = column_weight.number_input("Bodyweight (" + program["units"] + ")", min_value=0.0, max_value=1000.0,
                                            value=float(lifter.get("bodyweight", 0.0)), step=0.5,
                                            key=widget_key(key_prefix + "_bodyweight"))
    if st.button("Save my details", key=widget_key(key_prefix + "_save_lifter"), type="primary"):
        if sex == "Not set" or age <= 0 or bodyweight <= 0:
            st.error("Please fill in sex, age and bodyweight.")
        else:
            program["lifter"] = {"sex": sex, "age": int(age), "bodyweight": float(bodyweight)}
            save_program()
            st.rerun()


def draw_tier_ladder():
    """Draws the list of rank tiers with their percentiles. Returns nothing."""
    with st.expander("The ladder"):
        st.caption("Five common levels sit at the 5th, 20th, 50th, 80th and 95th percentiles of trained lifters "
                   "(beginner, novice, intermediate, advanced, elite). This app splits them into ten tiers, with "
                   "three Legend steps inside the top 2.5%. The standards are approximate; any lift can use your "
                   "own thresholds from a standards calculator instead (Settings, Lifts).")
        lines = []
        for position in range(len(defaults.RANK_TIERS) - 1, -1, -1):
            tier = defaults.RANK_TIERS[position]
            lines.append("- " + tier_text(tier["key"], tier["name"]) + " · top "
                         + str(round(100 - tier["min_percentile"], 2)) + "%")
        st.markdown("\n".join(lines))


def slots_used_by_split(frequency, split_style=defaults.SPLIT_FULL_BODY):
    """Takes a frequency and split style. Returns the list of slots that split actually trains."""
    used = []
    for day in defaults.SPLITS_BY_STYLE[split_style][frequency]:
        for slot in day:
            used.append(slot)
    return used


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def draw_sidebar():
    """Draws navigation, presentation buttons and the credit. Returns the chosen page."""
    if "next_page" in st.session_state:
        st.session_state["page"] = st.session_state.pop("next_page")

    st.sidebar.title("🏋️ SBS Trainer")
    program = get_program()
    if program is None:
        st.sidebar.caption("No program yet. Start on the Setup page.")
    else:
        st.sidebar.caption(defaults.VARIANT_NAMES[program["variant"]])
        st.sidebar.caption("Week " + str(program["current_week"]) + " of " + str(defaults.TOTAL_WEEKS)
                           + " · Day " + str(program["current_day"]) + " of " + str(program["frequency"]))

    # First visit of a browser session: land on the workout page when a
    # program exists (fewest taps at the gym), otherwise on Home.
    if "page" not in st.session_state:
        if program is None:
            st.session_state["page"] = PAGE_HOME
        else:
            st.session_state["page"] = PAGE_WORKOUT
    page = st.sidebar.radio("Go to", PAGES, key="page")

    st.sidebar.divider()
    st.sidebar.markdown("**Presentation mode**")
    if st.sidebar.button("Load demo data"):
        demo = storage.load_demo_program()
        if demo is None:
            st.sidebar.error("data/demo_program.json is missing. Run python scripts/make_demo_data.py")
        else:
            replace_program(demo)
            go_to_page(PAGE_WORKOUT)
    confirm_reset = st.sidebar.checkbox("Confirm reset", key="confirm_reset")
    if st.sidebar.button("Reset to empty", disabled=not confirm_reset):
        replace_program(None)
        go_to_page(PAGE_HOME)
    st.sidebar.caption("A backup copy is written to user_data/ before a reset.")

    st.sidebar.divider()
    st.sidebar.markdown(CREDIT_MARKDOWN)
    st.sidebar.caption("Exercise photos: free-exercise-db (public domain).")
    return page


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------
def page_home():
    """Draws the landing page. Returns nothing."""
    st.title("SBS Trainer")
    st.markdown(CREDIT_MARKDOWN)
    program = get_program()

    if program is None:
        st.info("No program yet. Setting one up takes about a minute, or load the demo "
                "data from the sidebar to look around first.")
        if st.button("Set up my program", type="primary"):
            go_to_page(PAGE_SETUP)
    else:
        week = program["current_week"]
        day = program["current_day"]
        names = []
        for exercise in logic.build_workout(program, week, day):
            names.append(exercise["name"])
        st.markdown("**Current program:** " + defaults.VARIANT_NAMES[program["variant"]] + "  \n"
                    "**Next session:** Week " + str(week) + ", Day " + str(day)
                    + " (" + ", ".join(names) + ")  \n"
                    "**Sessions logged:** " + str(len(program["history"])))
        if st.button("Go to today's workout", type="primary"):
            go_to_page(PAGE_WORKOUT)
        if logic.lifter_details_complete(program):
            parts = []
            for rank in logic.all_ranks(program):
                parts.append(rank["name"] + " " + tier_text(rank["tier_key"], rank["tier_name"]))
            st.markdown("**Ranks:** " + " · ".join(parts))

    st.subheader("How the program works")
    st.markdown(
        "- **21 weeks, three 7-week blocks.** Each block is heavier than the last with fewer "
        "reps per set. Weeks 7, 14 and 21 are deloads: easy sets, no targets.\n"
        "- **Training max (TM).** Every lift has a number that generates its weights. It starts "
        "at the max you enter and moves up or down every week based on how the session went. "
        "It is not your real 1RM, so a conservative guess is fine.\n"
        "- **Working weight** = training max × this week's percentage, rounded to your plates.\n"
        "- **Reps and targets** are looked up from the percentage you are lifting, not the week "
        "number, so any change you make to the intensities still produces sensible sets.\n"
        "- **Four variants** share the same structure and differ only in what you log: sets until "
        "an RIR cutoff, sets plus last-set RIR, or reps on a final set to failure.\n"
        "- **Single @8 (optional).** Work up to a heavy single at RPE 8 before your sets, log it, "
        "and the app recalculates today's training max from it.\n"
        "- **Accessories** (rows, pull-ups, arm and core work) have no prescribed progression. "
        "Log what you did and try to beat it next time."
    )
    for variant in defaults.ALL_VARIANTS:
        with st.expander(defaults.VARIANT_NAMES[variant]):
            st.write(defaults.VARIANT_DESCRIPTIONS[variant])


# ---------------------------------------------------------------------------
# Setup page
# ---------------------------------------------------------------------------
SKIP_OPTION = "Skip this slot"
OTHER_OPTION = "Other (type a name)"


def preset_name(preset_key):
    """Takes a preset key. Returns its display name (used by radio buttons)."""
    return defaults.PRESET_NAMES[preset_key]


def lift_name_picker(slot, default_name, widget_suffix, skip_by_default=False):
    """
    A dropdown of suggested exercises for a slot, with a free-text choice and a
    "skip" choice for lifts the person does not want to do at all.

    Takes: slot key, the default name, a suffix that makes the widget key unique
    (the variant and preset, so the defaults refresh when either changes), and
    whether the slot starts out skipped.
    Returns: the chosen name, or None when the slot is skipped.
    """
    options = list(defaults.SLOT_VARIATIONS[slot])
    if default_name not in options:
        options.insert(0, default_name)
    options.append(OTHER_OPTION)
    options.append(SKIP_OPTION)
    starting = default_name
    if skip_by_default:
        starting = SKIP_OPTION
    choice = st.selectbox(defaults.SLOT_LABELS[slot], options, index=options.index(starting),
                          key="setup_pick_" + slot + "_" + widget_suffix)
    if choice == SKIP_OPTION:
        return None
    if choice == OTHER_OPTION:
        typed = st.text_input("Exercise name for " + defaults.SLOT_LABELS[slot],
                              key="setup_typed_" + slot + "_" + widget_suffix)
        if typed.strip() == "":
            return default_name
        return typed.strip()
    return choice


def show_split_preview(frequency, split_style):
    """Takes a frequency and split style. Draws which slots land on which day. Returns nothing."""
    lines = []
    split = defaults.SPLITS_BY_STYLE[split_style][frequency]
    for day_index in range(len(split)):
        labels = []
        for slot in split[day_index]:
            labels.append(defaults.SLOT_LABELS[slot])
        lines.append("**Day " + str(day_index + 1) + ":** " + ", ".join(labels))
    st.markdown("  \n".join(lines))
    st.caption("Every lift is trained exactly once a week, so more days per week means fewer lifts "
               "per day. Each day also gets whatever accessories you add.")


def setup_slot_name(slot, lift_names):
    """
    Takes a slot key and the slot -> name dict. Returns the lift's name, marked
    "(lighter)" when an auxiliary slot repeats its main lift.
    """
    parent = defaults.PARENT_SLOT.get(slot)
    if parent is not None and lift_names[slot] == lift_names[parent]:
        return lift_names[slot] + " (lighter)"
    return lift_names[slot]


def page_setup():
    """Draws the setup wizard. Returns nothing."""
    st.title("Set up a program")
    existing = get_program()
    if existing is not None:
        st.warning("You already have a program. Creating a new one replaces it "
                   "(a backup copy is saved in user_data/ first).")
    else:
        with st.expander("Already have a backup file? Restore it instead"):
            uploaded = st.file_uploader("Program JSON file", type=["json"], key=widget_key("restore_program"))
            if uploaded is not None:
                restored = storage.program_from_json_text(uploaded.getvalue().decode("utf-8"))
                if restored is None:
                    st.error("That file does not look like an SBS Trainer program.")
                elif st.button("Restore this program"):
                    replace_program(restored)
                    go_to_page(PAGE_WORKOUT)

    # A preset fills in every default below. Widget keys include the preset name,
    # so switching presets rebuilds the widgets with the new defaults.
    st.subheader("Start from")
    preset_key = st.radio("Preset", defaults.PRESET_KEYS, format_func=preset_name, key="setup_preset")
    st.caption(defaults.PRESET_DESCRIPTIONS[preset_key])
    st.caption("A preset only fills in the form. The main lifts always follow the program's intensities, "
               "reps, targets and training-max rules.")
    preset = defaults.SETUP_PRESETS.get(preset_key, {})

    st.subheader("1. Pick a program variant")
    variant = st.radio("Variant", defaults.ALL_VARIANTS, format_func=variant_name,
                       index=defaults.ALL_VARIANTS.index(preset.get("variant", defaults.VARIANT_RTF)),
                       key="setup_variant_" + preset_key)
    st.caption(defaults.VARIANT_DESCRIPTIONS[variant])

    st.subheader("2. Units and rounding")
    column_units, column_rounding = st.columns(2)
    units = column_units.radio("Units", defaults.UNIT_CHOICES, horizontal=True,
                               index=defaults.UNIT_CHOICES.index(preset.get("units", "lb")),
                               key="setup_units_" + preset_key)
    if units == "lb":
        default_rounding = 5.0
    else:
        default_rounding = 2.5
    default_rounding = preset.get("rounding_increment", default_rounding)
    rounding = column_rounding.selectbox("Rounding increment", defaults.ROUNDING_CHOICES,
                                         index=defaults.ROUNDING_CHOICES.index(default_rounding),
                                         key="setup_rounding_" + units + "_" + preset_key)
    st.caption("5 for pound plates, 2.5 for kilo plates, 0.1 if you would rather round in your head.")

    st.subheader("3. About you (for ranks, optional)")
    st.caption("Ranks compare each lift with strength standards for lifters of your sex, age and bodyweight. "
               "Just for fun; it changes nothing in the program. Leave it blank to skip, or fill it in later on "
               "the Ranks page.")
    column_sex, column_age, column_weight = st.columns(3)
    sex_choice = column_sex.selectbox("Sex", ["Not set", "male", "female"], format_func=sex_label,
                                      key="setup_sex_" + preset_key)
    age = column_age.number_input("Age", min_value=0, max_value=100, value=0, step=1, key="setup_age_" + preset_key)
    bodyweight = column_weight.number_input("Bodyweight (" + units + ")", min_value=0.0, max_value=1000.0, value=0.0,
                                            step=0.5, key="setup_bodyweight_" + units + "_" + preset_key)

    st.subheader("4. Training days and split")
    frequency = st.radio("Days per week", defaults.FREQUENCY_CHOICES, horizontal=True,
                         index=defaults.FREQUENCY_CHOICES.index(preset.get("frequency", 4)),
                         key="setup_frequency_" + preset_key)
    split_style = st.radio("Split style", defaults.SPLIT_STYLES, format_func=split_style_name,
                           index=defaults.SPLIT_STYLES.index(preset.get("split_style", defaults.SPLIT_FULL_BODY)),
                           key="setup_split_style_" + preset_key)
    st.caption(defaults.SPLIT_STYLE_DESCRIPTIONS[split_style])
    show_split_preview(frequency, split_style)
    st.caption("The split style only decides which day each lift lands on; step 6 lets you change any of it.")

    st.subheader("5. Lifts and starting maxes")
    st.markdown(
        "Enter a real or estimated one-rep max for each lift. **Conservative numbers are fine**: "
        "the program raises a training max that is too low within a few weeks, and lowers one "
        "that is too high just as quickly. For pull-ups or dips, count bodyweight plus added weight."
    )
    same_lifts = st.checkbox("Keep it simple: use my four main lifts for the auxiliary slots too, no variations",
                             value=preset.get("same_lifts", False), key="setup_same_lifts_" + preset_key)
    st.caption("Choose \"" + SKIP_OPTION + "\" in a dropdown to leave a lift out entirely. "
               "You can add it back later in Settings.")
    if variant == defaults.VARIANT_HYPERTROPHY:
        default_names = dict(defaults.HYPERTROPHY_DEFAULT_LIFT_NAMES)
    else:
        default_names = dict(defaults.STRENGTH_DEFAULT_LIFT_NAMES)
    for slot in preset.get("lift_names", {}):
        default_names[slot] = preset["lift_names"][slot]
    default_maxes = defaults.DEFAULT_STARTING_MAXES[units]
    used_slots = slots_used_by_split(frequency, split_style)
    picker_suffix = variant + "_" + preset_key

    lift_names = {}
    starting_maxes = {}
    skipped = []
    for slot in defaults.ALL_SLOTS:
        lift_names[slot] = default_names[slot]
        starting_maxes[slot] = default_maxes[slot]
        if slot not in used_slots:
            continue   # the 2x split never trains this slot, so skip the inputs
        if same_lifts and slot in defaults.PARENT_SLOT:
            # Auxiliary slot copies its main lift (main slots come first in ALL_SLOTS).
            parent = defaults.PARENT_SLOT[slot]
            lift_names[slot] = lift_names[parent]
            starting_maxes[slot] = starting_maxes[parent]
            if parent in skipped:
                skipped.append(slot)
            continue
        column_name, column_max = st.columns([2, 1])
        with column_name:
            chosen = lift_name_picker(slot, default_names[slot], picker_suffix,
                                      slot in preset.get("skipped_slots", []))
        if chosen is None:
            skipped.append(slot)
            column_max.caption("Skipped")
            continue
        lift_names[slot] = chosen
        with column_max:
            starting_maxes[slot] = st.number_input(
                "1RM (" + units + ")", min_value=1.0, max_value=2000.0, value=float(default_maxes[slot]),
                step=float(rounding), key="setup_max_" + slot + "_" + units + "_" + preset_key)
    if same_lifts:
        summary = []
        for slot in defaults.AUXILIARY_SLOTS:
            if slot in used_slots and slot not in skipped:
                summary.append(defaults.SLOT_LABELS[slot] + " = " + lift_names[slot])
        st.caption("Auxiliary slots: " + "; ".join(summary)
                   + ". They start from the same max and train a little lighter than the main slot.")

    st.subheader("6. Which day each lift lands on")
    st.caption("Prefilled from the split style. Change any lift's day here. Every lift keeps its own training max, "
               "intensity and reps wherever it goes, and the other days stay exactly as they are.")
    style_plans = logic.build_default_days(frequency, skipped, split_style)
    style_day = {}
    for day_index in range(len(style_plans)):
        for slot in style_plans[day_index]["slots"]:
            style_day[slot] = day_index + 1
    for slot in preset.get("days", {}):
        if preset["days"][slot] <= frequency:
            style_day[slot] = preset["days"][slot]
    day_numbers = list(range(1, frequency + 1))
    chosen_day = {}
    editor_columns = st.columns(2)
    position = 0
    for slot in defaults.ALL_SLOTS:
        if slot not in used_slots or slot in skipped:
            continue
        label = setup_slot_name(slot, lift_names) + " · " + defaults.SLOT_LABELS[slot]
        column = editor_columns[position % 2]
        chosen_day[slot] = column.selectbox(label, day_numbers, index=style_day.get(slot, 1) - 1,
                                            key="setup_day_" + slot + "_" + str(frequency) + "_" + split_style + "_" + preset_key)
        position += 1
    day_plans = logic.build_default_days(frequency, skipped, split_style)
    for day_index in range(len(day_plans)):
        day_plans[day_index]["slots"] = []
        for slot in defaults.ALL_SLOTS:
            if chosen_day.get(slot) == day_index + 1:
                day_plans[day_index]["slots"].append(slot)

    st.subheader("7. Accessories")
    st.caption("Anything you want to do after the main lifts: rows, pull-ups, arm and core work. "
               "The main lifts include no pulling, so a row or pull-up is suggested on each day. "
               "Accessories have no prescribed progression: you log what you did and try to beat it "
               "next time. Everything here can be changed later in Settings.")
    choices = accessory_choices()
    preset_accessories = preset.get("accessories", [])
    for day_index in range(len(day_plans)):
        day = day_plans[day_index]
        if day_index < len(preset_accessories):
            day["accessories"] = list(preset_accessories[day_index])
        for name in day["accessories"]:
            if name not in choices:
                choices.append(name)
        names = []
        for slot in day["slots"]:
            names.append(setup_slot_name(slot, lift_names))
        if len(names) == 0:
            st.markdown("**Day " + str(day_index + 1) + ":** no main lifts on this day")
        else:
            st.markdown("**Day " + str(day_index + 1) + ":** " + ", ".join(names))
        key_suffix = str(day_index) + "_" + str(frequency) + "_" + preset_key
        picked = st.multiselect("Accessories", choices, default=day["accessories"], key="setup_acc_" + key_suffix)
        extra = st.text_input("Other accessories, comma separated", key="setup_acc_extra_" + key_suffix)
        day["accessories"] = list(picked)
        for name in extra.split(","):
            if name.strip() != "":
                day["accessories"].append(name.strip())

    st.subheader("8. Create")
    st.caption("Everything else (rep tables, intensities, thresholds, exercise order) starts at the "
               "program defaults and can be changed later on the Settings page.")
    if existing is None:
        confirmed = True
    else:
        confirmed = st.checkbox("Replace my current program")
    if st.button("Create program", type="primary", disabled=not confirmed):
        program = logic.create_program(variant, units, rounding, frequency, lift_names, starting_maxes, skipped, split_style)
        program["days"] = day_plans
        lifter_sex = ""
        if sex_choice in defaults.SEX_CHOICES:
            lifter_sex = sex_choice
        program["lifter"] = {"sex": lifter_sex, "age": int(age), "bodyweight": float(bodyweight)}
        replace_program(program)
        go_to_page(PAGE_WORKOUT)


# ---------------------------------------------------------------------------
# Today's workout
# ---------------------------------------------------------------------------
def draw_exercise_card(program, exercise, week, day):
    """
    Draw one main/auxiliary lift with its picture, prescription and log inputs.

    Takes: program, the prescription dict from build_workout, week, day.
    Returns: the performance dict to hand to log_workout.
    """
    slot = exercise["slot"]
    lift = program["lifts"][slot]
    variant = program["variant"]
    units = program["units"]
    rounding = program["rounding_increment"]
    key_suffix = slot + "_" + str(week) + "_" + str(day)

    st.divider()
    st.subheader(exercise["name"])
    show_image(lift["name"], lift)
    with st.expander("Heavy single @8 first? (optional)"):
        single = st.number_input(
            "Weight of today's single at RPE 8 (0 = skipped)", min_value=0.0, max_value=3000.0,
            value=0.0, step=float(rounding), key=widget_key("single_" + key_suffix))
        if single > 0:
            preview_lift = dict(lift)
            preview_lift["training_max"] = logic.calculate_training_max_from_single(
                single, lift["single_at_8_percent"])
            exercise = logic.get_prescription(variant, preview_lift, week, rounding,
                                              program["deload_reps_per_set"])
            st.caption("A single of " + logic.format_weight(single, units) + " at "
                       + logic.format_percent(lift["single_at_8_percent"]) + " gives a training max of "
                       + logic.format_weight(preview_lift["training_max"], units) + " for today.")
    column_weight, column_plan = st.columns([1, 2])
    column_weight.metric("Working weight", logic.format_weight(exercise["working_weight"], units))
    with column_plan:
        st.markdown("**" + logic.describe_prescription(variant, exercise) + "**")
        st.caption(logic.format_percent(exercise["intensity"]) + " of training max "
                   + logic.format_weight(exercise["training_max"], units))

    result = {"slot": slot, "single_at_8": None, "notes": ""}
    if single > 0:
        result["single_at_8"] = single

    if exercise["is_deload"]:
        st.caption("Deload: nothing to rate. Do the sets and move on.")
        result["sets_completed"] = exercise["sets"]
    elif variant == defaults.VARIANT_ORIGINAL:
        result["sets_completed"] = st.number_input(
            "Sets completed before reaching " + str(exercise["rir_cutoff"]) + " RIR",
            min_value=0, max_value=30, value=int(exercise["lower_set_threshold"]), step=1,
            key=widget_key("sets_" + key_suffix))
    elif variant == defaults.VARIANT_LAST_SET_RIR:
        column_sets, column_rir = st.columns(2)
        result["sets_completed"] = column_sets.number_input(
            "Sets completed", min_value=0, max_value=30, value=int(exercise["sets"]), step=1,
            key=widget_key("sets_" + key_suffix))
        result["last_set_rir"] = column_rir.number_input(
            "RIR on the last set", min_value=0, max_value=20, value=int(exercise["last_set_rir_target"]),
            step=1, key=widget_key("rir_" + key_suffix))
    else:
        result["last_set_reps"] = st.number_input(
            "Reps on your last set (to failure)", min_value=0, max_value=100,
            value=int(exercise["last_set_rep_target"]), step=1, key=widget_key("reps_" + key_suffix))

    if not exercise["is_deload"]:
        # Live preview so the lifter sees what saving will do to the training max.
        change = logic.calculate_tm_change_percent(variant, lift, exercise, result)
        preview_max = logic.apply_tm_change(exercise["training_max"], change)
        st.caption("If you save this: " + logic.describe_tm_change(variant, exercise, result, change, preview_max, units))

    result["notes"] = st.text_input("Notes", key=widget_key("note_" + key_suffix), placeholder="optional")
    return result


def draw_accessory_section(program, week, day):
    """
    Draw the day's accessories with free-form weight/sets/reps inputs.

    Takes: program, week, day. Returns: a list of accessory result dicts.
    """
    st.divider()
    st.subheader("Accessories")
    st.caption("No prescribed progression here. Last session's numbers are filled in as the target to beat. "
               "Leave sets at 0 to skip an exercise today.")
    units = program["units"]
    rounding = program["rounding_increment"]
    day_plan = program["days"][day - 1]

    planned = []
    for name in day_plan["accessories"]:
        planned.append({"name": name, "kind": "accessory"})

    results = []
    for position in range(len(planned)):
        name = planned[position]["name"]
        kind = planned[position]["kind"]
        last = logic.find_last_accessory_result(program, name)
        key_suffix = kind + "_" + str(position) + "_" + str(week) + "_" + str(day)

        column_image, column_inputs = st.columns([1, 2])
        with column_image:
            show_image(name, None, width=320)
        with column_inputs:
            st.markdown("**" + name + "**")
            if last is None:
                st.caption("First time logging this exercise.")
                last_weight, last_sets, last_reps = 0.0, 3, 10
            else:
                st.caption("Last time: " + logic.format_weight(last["weight"], units) + " × "
                           + str(last["sets"]) + " sets × " + str(last["reps"]) + " reps")
                last_weight, last_sets, last_reps = float(last["weight"]), int(last["sets"]), int(last["reps"])
            column_weight, column_sets, column_reps = st.columns(3)
            weight = column_weight.number_input("Weight", min_value=0.0, max_value=3000.0, value=last_weight,
                                                step=float(rounding), key=widget_key("acc_w_" + key_suffix))
            sets = column_sets.number_input("Sets", min_value=0, max_value=20, value=last_sets, step=1,
                                            key=widget_key("acc_s_" + key_suffix))
            reps = column_reps.number_input("Reps", min_value=0, max_value=100, value=last_reps, step=1,
                                            key=widget_key("acc_r_" + key_suffix))
        if sets > 0:
            results.append({"name": name, "kind": kind, "weight": float(weight), "sets": int(sets), "reps": int(reps)})

    with st.expander("Add an accessory to this training day"):
        options = ["(pick one)"] + accessory_choices()
        choice = st.selectbox("From the library", options, key=widget_key("acc_pick_" + str(day)))
        typed = st.text_input("Or type any name", key=widget_key("acc_typed_" + str(day)))
        if st.button("Add to day " + str(day)):
            new_name = typed.strip()
            if new_name == "" and choice != "(pick one)":
                new_name = choice
            if new_name != "":
                day_plan["accessories"].append(new_name)
                save_program()
                st.rerun()
    return results


def page_workout():
    """Draws today's workout with logging. Returns nothing."""
    program = get_program()
    if program is None:
        st.warning("No program yet.")
        if st.button("Go to Setup"):
            go_to_page(PAGE_SETUP)
        return

    saved_messages = st.session_state.pop("last_save_messages", None)
    if saved_messages is not None:
        st.success("Workout saved. Training max changes:")
        ranked_up = False
        for message in saved_messages:
            if message.startswith("Rank up!"):
                ranked_up = True
            st.info(message)
        if ranked_up:
            st.balloons()

    if logic.is_cycle_finished(program):
        st.success("You finished all 21 weeks. Test your maxes, then start the next cycle - "
                   "your current training maxes carry over.")
        if st.button("Start a new 21-week cycle", type="primary"):
            logic.start_new_cycle(program)
            save_program()
            st.rerun()

    week = program["current_week"]
    day = program["current_day"]
    st.title("Week " + str(week) + " · Day " + str(day))
    st.caption("Block " + str(logic.block_number(week)) + " of 3 · " + defaults.VARIANT_NAMES[program["variant"]]
               + " · every lift comes up once a week, so a " + str(program["frequency"])
               + "-day split has only a few lifts per day")
    if logic.is_deload_week(week):
        st.warning("Deload week: lighter weights, easy sets, no rep-out or RIR target, and the "
                   "training maxes do not change.")
    previous = logic.find_history_entry(program, week, day)
    if previous is not None:
        st.warning("This session was already logged on " + previous["date"]
                   + ". Saving again adds a second entry.")

    lift_results = []
    for exercise in logic.build_workout(program, week, day):
        lift_results.append(draw_exercise_card(program, exercise, week, day))
    accessory_results = draw_accessory_section(program, week, day)

    st.divider()
    session_notes = st.text_area("Session notes (optional)", key=widget_key("session_notes_" + str(week) + "_" + str(day)))
    column_save, column_skip = st.columns(2)
    if column_save.button("Save workout", type="primary"):
        messages = logic.log_workout(program, week, day, lift_results, accessory_results,
                                     session_notes, logic.today_string())
        logic.advance_to_next_day(program)
        save_program()
        st.session_state["last_save_messages"] = messages
        st.rerun()
    if column_skip.button("Skip this day without logging"):
        logic.advance_to_next_day(program)
        save_program()
        st.rerun()

    with st.expander("Jump to a different week or day"):
        column_week, column_day = st.columns(2)
        new_week = column_week.number_input("Week", min_value=1, max_value=defaults.TOTAL_WEEKS, value=week, step=1)
        new_day = column_day.number_input("Day", min_value=1, max_value=program["frequency"], value=day, step=1)
        if st.button("Go there"):
            program["current_week"] = int(new_week)
            program["current_day"] = int(new_day)
            save_program()
            st.rerun()


# ---------------------------------------------------------------------------
# Ranks page (just for fun)
# ---------------------------------------------------------------------------
def page_ranks():
    """Draws each lift's rank, progress to the next tier, and the ladder. Returns nothing."""
    program = get_program()
    if program is None:
        st.warning("No program yet. Set one up first, or load the demo data from the sidebar.")
        return
    st.title("Ranks")
    if not logic.lifter_details_complete(program):
        st.info("Each lift gets a rank from its training max, compared with strength standards for lifters of "
                "your sex, age and bodyweight. Just for fun; nothing here changes the program.")
        draw_lifter_form(program, "ranks")
        draw_tier_ladder()
        return
    lifter = program["lifter"]
    units = program["units"]
    st.caption("Standards for a " + str(lifter["age"]) + "-year-old " + defaults.SEX_NAMES[lifter["sex"]].lower()
               + " at " + logic.format_weight(lifter["bodyweight"], units) + ", adjusted for bodyweight and age. "
               "Each lift is ranked by its training max, so ranks move with your training.")
    for rank in logic.all_ranks(program):
        st.markdown("### " + rank["name"] + " · " + tier_text(rank["tier_key"], rank["tier_name"]))
        st.progress(rank["progress"], text="About the " + ordinal(round(rank["percentile"])) + " percentile · training max "
                    + logic.format_weight(rank["training_max"], units))
        if rank["next_tier_name"] is None:
            st.caption("Top of the ladder.")
        else:
            st.caption(logic.format_weight(rank["gap_to_next"], units) + " more on the training max to reach "
                       + rank["next_tier_name"] + ".")
        if rank["custom_thresholds"]:
            st.caption("Using your own thresholds for this lift.")
        elif rank["rank_factor"] != 1:
            st.caption("Counted as " + logic.format_weight(rank["training_max"] / rank["rank_factor"], units)
                       + " on the main lift (factor " + str(rank["rank_factor"]) + ").")
    draw_tier_ladder()


# ---------------------------------------------------------------------------
# Progress page
# ---------------------------------------------------------------------------
def chart_columns_for_choice(program, choice, all_columns):
    """
    Which lifts to plot for a dropdown choice.

    Takes: program, the choice string, the list of every lift column name.
    Returns: a list of column names.
    """
    if choice == "Main lifts":
        names = []
        for slot in defaults.MAIN_SLOTS:
            names.append(logic.lift_display_name(program, slot))
        return names
    if choice == "All lifts":
        return all_columns
    return [choice]


def page_progress():
    """Draws charts, history and stats. Returns nothing."""
    program = get_program()
    if program is None:
        st.warning("No program yet. Set one up first, or load the demo data from the sidebar.")
        return
    st.title("Progress")
    units = program["units"]
    stats = logic.summary_stats(program)
    column_1, column_2, column_3, column_4 = st.columns(4)
    column_1.metric("Sessions logged", stats["sessions"])
    column_2.metric("Current week", str(stats["current_week"]) + " / " + str(defaults.TOTAL_WEEKS))
    column_3.metric("Total volume", "{:,.0f} ".format(stats["total_volume"]) + units)
    column_4.metric("Total sets", stats["total_sets"])

    if len(program["history"]) == 0:
        st.info("Log a workout and the charts will appear here.")
        return

    labels, tm_columns = logic.build_training_max_table(program)
    all_names = list(tm_columns.keys())
    choices = ["Main lifts", "All lifts"] + all_names

    st.subheader("Training max over time")
    tm_choice = st.selectbox("Show", choices, key="progress_tm_choice")
    tm_frame = pd.DataFrame(tm_columns, index=labels)
    st.line_chart(tm_frame[chart_columns_for_choice(program, tm_choice, all_names)])
    st.caption("One point per logged session. A lift that was not trained keeps its previous value.")

    st.subheader("Estimated 1RM trend")
    labels, e1rm_columns = logic.build_estimated_max_table(program)
    e1rm_choice = st.selectbox("Show", choices, key="progress_e1rm_choice")
    # Each lift is trained about once a week, so its estimates sit several sessions
    # apart; interpolate() draws the line through the sessions in between.
    e1rm_frame = pd.DataFrame(e1rm_columns, index=labels, dtype="float").interpolate(limit_area="inside")
    st.line_chart(e1rm_frame[chart_columns_for_choice(program, e1rm_choice, all_names)])
    st.caption("Epley estimate from the hardest set of each session: weight × (1 + reps to failure ÷ 30). "
               "Deload weeks give no estimate, so the line just continues to the next one.")

    st.subheader("Workout history")
    rows = logic.build_history_rows(program)
    history_frame = pd.DataFrame(rows)
    st.dataframe(history_frame.iloc[::-1], hide_index=True)

    st.download_button("Download my program as JSON", data=storage.program_to_json_text(program),
                       file_name="sbs_program.json", mime="application/json")


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------
def settings_general(program):
    """Draws the General tab (variant, units, rounding, frequency, calendar). Returns nothing."""
    variant = st.selectbox("Program variant", defaults.ALL_VARIANTS, format_func=variant_name,
                           index=defaults.ALL_VARIANTS.index(program["variant"]), key=widget_key("set_variant"))
    reset_tables = False
    if variant != program["variant"]:
        st.caption(defaults.VARIANT_DESCRIPTIONS[variant])
        reset_tables = st.checkbox("Also reset every lift's rep tables, intensities, set count and ladder to "
                                   "this variant's defaults (training maxes are kept)", value=True)

    column_units, column_rounding = st.columns(2)
    units = column_units.radio("Units", defaults.UNIT_CHOICES, horizontal=True,
                               index=defaults.UNIT_CHOICES.index(program["units"]), key=widget_key("set_units"))
    rounding = column_rounding.number_input("Rounding increment", min_value=0.1, max_value=25.0,
                                            value=float(program["rounding_increment"]), step=0.1,
                                            key=widget_key("set_rounding"))

    frequency = st.radio("Training days per week", defaults.FREQUENCY_CHOICES, horizontal=True,
                         index=defaults.FREQUENCY_CHOICES.index(program["frequency"]), key=widget_key("set_frequency"))
    split_style = st.radio("Split style", defaults.SPLIT_STYLES, format_func=split_style_name,
                           index=defaults.SPLIT_STYLES.index(program["split_style"]), key=widget_key("set_split_style"))
    st.caption(defaults.SPLIT_STYLE_DESCRIPTIONS[split_style])
    if frequency != program["frequency"] or split_style != program["split_style"]:
        st.caption("Changing the days or the split style rebuilds the training days from that layout "
                   "(accessory names are reset too).")

    column_week, column_day, column_deload = st.columns(3)
    week = column_week.number_input("Current week", min_value=1, max_value=defaults.TOTAL_WEEKS,
                                    value=int(program["current_week"]), step=1, key=widget_key("set_week"))
    day = column_day.number_input("Current day", min_value=1, max_value=int(frequency),
                                  value=min(int(program["current_day"]), int(frequency)), step=1, key=widget_key("set_day"))
    deload_reps = column_deload.number_input("Reps per set on deload weeks", min_value=1, max_value=20,
                                             value=int(program["deload_reps_per_set"]), step=1, key=widget_key("set_deload_reps"))

    if st.button("Save general settings", type="primary"):
        if variant != program["variant"]:
            program["variant"] = variant
            if reset_tables:
                for slot in defaults.ALL_SLOTS:
                    logic.reset_lift_tables_for_variant(program["lifts"][slot], variant)
        program["units"] = units
        program["rounding_increment"] = float(rounding)
        if frequency != program["frequency"] or split_style != program["split_style"]:
            program["frequency"] = int(frequency)
            program["split_style"] = split_style
            program["days"] = logic.build_default_days(int(frequency), [], split_style)
        program["current_week"] = int(week)
        program["current_day"] = int(day)
        program["deload_reps_per_set"] = int(deload_reps)
        save_program()
        st.success("Saved.")
        st.rerun()


def settings_lifts(program):
    """Draws the Lifts tab (names, training maxes, sets, thresholds, ladder). Returns nothing."""
    variant = program["variant"]
    units = program["units"]
    scheduled = logic.scheduled_slots(program)
    edits = {}
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        title = defaults.SLOT_LABELS[slot] + ": " + lift["name"]
        if slot not in scheduled:
            title = title + "  (not scheduled - add it on the Training days tab)"
        with st.expander(title):
            edit = {}
            edit["name"] = st.text_input("Exercise name", value=lift["name"], key=widget_key("lift_name_" + slot))
            column_max, column_single, column_sets = st.columns(3)
            edit["training_max"] = column_max.number_input(
                "Training max (" + units + ")", min_value=1.0, max_value=3000.0,
                value=float(round(lift["training_max"], 2)), step=0.5, key=widget_key("lift_tm_" + slot))
            edit["single_at_8_percent"] = column_single.number_input(
                "Single @8 percentage", min_value=50.0, max_value=100.0,
                value=float(lift["single_at_8_percent"]), step=0.5, key=widget_key("lift_single_" + slot))
            edit["sets"] = column_sets.number_input(
                "Sets", min_value=1, max_value=12, value=int(lift["sets"]), step=1, key=widget_key("lift_sets_" + slot))
            if variant == defaults.VARIANT_ORIGINAL:
                st.caption("Set range and how the training max moves outside it")
                column_a, column_b, column_c, column_d = st.columns(4)
                edit["lower_set_threshold"] = column_a.number_input(
                    "Lower threshold", min_value=1, max_value=20, value=int(lift["lower_set_threshold"]),
                    step=1, key=widget_key("lift_lower_" + slot))
                edit["upper_set_threshold"] = column_b.number_input(
                    "Upper threshold", min_value=1, max_value=30, value=int(lift["upper_set_threshold"]),
                    step=1, key=widget_key("lift_upper_" + slot))
                edit["increase_percent"] = column_c.number_input(
                    "Increase %", min_value=0.0, max_value=20.0, value=float(lift["increase_percent"]),
                    step=0.25, key=widget_key("lift_inc_" + slot))
                edit["decrease_percent"] = column_d.number_input(
                    "Decrease %", min_value=-20.0, max_value=0.0, value=float(lift["decrease_percent"]),
                    step=0.25, key=widget_key("lift_dec_" + slot))
            else:
                st.caption("Training max ladder: % change for each outcome")
                ladder = []
                ladder_columns = st.columns(4)
                for position in range(len(defaults.TM_LADDER_LABELS)):
                    column = ladder_columns[position % 4]
                    ladder.append(column.number_input(
                        defaults.TM_LADDER_LABELS[position], min_value=-25.0, max_value=25.0,
                        value=float(lift["ladder"][position]), step=0.25,
                        key=widget_key("lift_ladder_" + slot + "_" + str(position))))
                edit["ladder"] = ladder
            st.caption("Rank settings (just for fun)")
            column_factor, column_thresholds = st.columns([1, 2])
            edit["rank_factor"] = column_factor.number_input(
                "Rank factor", min_value=0.1, max_value=5.0, value=float(lift.get("rank_factor", 1.0)), step=0.05,
                help="This lift's max divided by the factor is the equivalent "
                     + defaults.RANK_TYPE_NAMES[defaults.RANK_TYPE_BY_SLOT[slot]] + " max.",
                key=widget_key("lift_rank_factor_" + slot))
            thresholds_text = ""
            if lift.get("rank_thresholds"):
                thresholds_text = ", ".join(str(value) for value in lift["rank_thresholds"])
            edit["rank_thresholds"] = column_thresholds.text_input(
                "Own thresholds (optional): beginner, novice, intermediate, advanced, elite in " + units,
                value=thresholds_text, placeholder="e.g. 135, 225, 270, 360, 450",
                key=widget_key("lift_rank_thresholds_" + slot))
            edits[slot] = edit

    if st.button("Save lift settings", type="primary"):
        for slot in defaults.ALL_SLOTS:
            lift = program["lifts"][slot]
            edit = edits[slot]
            if edit["name"].strip() != "":
                lift["name"] = edit["name"].strip()
            lift["training_max"] = float(edit["training_max"])
            lift["single_at_8_percent"] = float(edit["single_at_8_percent"])
            lift["sets"] = int(edit["sets"])
            if variant == defaults.VARIANT_ORIGINAL:
                lift["lower_set_threshold"] = int(edit["lower_set_threshold"])
                lift["upper_set_threshold"] = int(edit["upper_set_threshold"])
                lift["increase_percent"] = float(edit["increase_percent"])
                lift["decrease_percent"] = float(edit["decrease_percent"])
            else:
                lift["ladder"] = []
                for value in edit["ladder"]:
                    lift["ladder"].append(float(value))
            lift["rank_factor"] = float(edit["rank_factor"])
            numbers = []
            for part in edit["rank_thresholds"].split(","):
                try:
                    number = float(part)
                except ValueError:
                    continue
                if number > 0:
                    numbers.append(number)
            if len(numbers) == 5:
                lift["rank_thresholds"] = numbers
            else:
                lift["rank_thresholds"] = None
        save_program()
        st.success("Saved.")
        st.rerun()


TABLE_ROW_KEYS = ["reps_per_set", "rir_cutoff", "last_set_rir_target", "last_set_rep_target"]
TABLE_ROW_LABELS = ["Reps per set", "RIR cutoff (Original)", "Last-set RIR target (Last Set RIR)",
                    "Last-set rep target (RTF / Hypertrophy)"]


def percentage_column_labels():
    """Returns ["50%", "52.5%", ..., "100%"] for table headers."""
    labels = []
    for bucket in defaults.PERCENTAGE_BUCKETS:
        labels.append(logic.format_percent(bucket))
    return labels


def settings_tables(program):
    """Draws the rep/RIR table editor for one lift at a time. Returns nothing."""
    st.caption("Each column is a percentage of the training max. The app looks up today's reps and "
               "targets from the column nearest to today's intensity.")
    def label_for_slot(key):
        """Takes a slot key. Returns its label with the lift name (for the dropdown)."""
        return slot_label(program, key)

    slot = st.selectbox("Lift", defaults.ALL_SLOTS, format_func=label_for_slot, key=widget_key("table_slot"))
    lift = program["lifts"][slot]
    columns = percentage_column_labels()
    table = {}
    for position in range(len(TABLE_ROW_KEYS)):
        table[TABLE_ROW_LABELS[position]] = list(lift[TABLE_ROW_KEYS[position]])
    frame = pd.DataFrame(table, index=columns).T
    edited = st.data_editor(frame, key=widget_key("table_editor_" + slot))

    column_save, column_reset, column_copy = st.columns(3)
    if column_save.button("Save this lift's tables", type="primary"):
        for position in range(len(TABLE_ROW_KEYS)):
            values = []
            for value in edited.loc[TABLE_ROW_LABELS[position]]:
                values.append(int(value))
            lift[TABLE_ROW_KEYS[position]] = values
        save_program()
        st.success("Saved.")
        st.rerun()
    if column_reset.button("Reset this lift to defaults"):
        fresh = logic.build_lift_settings(program["variant"], slot, lift["name"], lift["training_max"])
        for key in TABLE_ROW_KEYS:
            lift[key] = fresh[key]
        save_program()
        st.rerun()
    if column_copy.button("Copy these tables to every lift"):
        for other_slot in defaults.ALL_SLOTS:
            for key in TABLE_ROW_KEYS:
                program["lifts"][other_slot][key] = list(lift[key])
        save_program()
        st.success("Copied.")
        st.rerun()


def settings_intensities(program):
    """Draws the per-lift, per-week intensity editor. Returns nothing."""
    st.caption("Percent of training max for each lift in each week. Weeks 7, 14 and 21 are deloads.")
    week_labels = []
    for week in range(1, defaults.TOTAL_WEEKS + 1):
        week_labels.append("W" + str(week))
    table = {}
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        table[lift["name"]] = list(lift["intensities"])
    # Weeks as rows and lifts as columns: 21 short rows read better than 21 wide columns.
    frame = pd.DataFrame(table, index=week_labels)
    edited = st.data_editor(frame, key=widget_key("intensity_editor"), height=780)

    column_save, column_reset = st.columns(2)
    if column_save.button("Save intensities", type="primary"):
        for slot in defaults.ALL_SLOTS:
            lift = program["lifts"][slot]
            values = []
            for value in edited[lift["name"]]:
                values.append(float(value))
            lift["intensities"] = values
        save_program()
        st.success("Saved.")
        st.rerun()
    if column_reset.button("Reset to the variant's defaults"):
        for slot in defaults.ALL_SLOTS:
            lift = program["lifts"][slot]
            fresh = logic.build_lift_settings(program["variant"], slot, lift["name"], lift["training_max"])
            lift["intensities"] = fresh["intensities"]
        save_program()
        st.rerun()


def settings_days(program):
    """Draws the training-day editor: order lifts, pick upper back and accessories. Returns nothing."""
    st.caption("Which day each lift lands on. Every lift keeps its own training max, intensity and reps "
               "wherever it goes, and the other days are not affected.")
    current_day = {}
    for day_index in range(len(program["days"])):
        for slot in program["days"][day_index]["slots"]:
            current_day[slot] = day_index + 1
    day_choices = ["Not scheduled"]
    for day_number in range(1, len(program["days"]) + 1):
        day_choices.append("Day " + str(day_number))
    assignment = {}
    assign_columns = st.columns(2)
    for position in range(len(defaults.ALL_SLOTS)):
        slot = defaults.ALL_SLOTS[position]
        current = "Not scheduled"
        if slot in current_day:
            current = "Day " + str(current_day[slot])
        assignment[slot] = assign_columns[position % 2].selectbox(
            slot_label(program, slot), day_choices, index=day_choices.index(current), key=widget_key("assign_" + slot))
    if st.button("Save day assignments", type="primary"):
        for day_index in range(len(program["days"])):
            day = program["days"][day_index]
            wanted = "Day " + str(day_index + 1)
            # Lifts that stay on this day keep their order; newly moved lifts go at the end.
            new_slots = []
            for slot in day["slots"]:
                if assignment[slot] == wanted:
                    new_slots.append(slot)
            for slot in defaults.ALL_SLOTS:
                if assignment[slot] == wanted and slot not in new_slots:
                    new_slots.append(slot)
            day["slots"] = new_slots
        save_program()
        st.success("Saved.")
        st.rerun()
    st.caption("Below: use the arrows to reorder lifts within a day, ✕ to remove one, and the dropdown to add "
               "a lift that is not scheduled yet. Accessory names save with the button at the bottom.")
    def label_for_slot(key):
        """Takes a slot key. Returns its label with the lift name (for the dropdown)."""
        return slot_label(program, key)

    scheduled = []
    for day in program["days"]:
        for slot in day["slots"]:
            scheduled.append(slot)

    day_edits = []
    for day_index in range(len(program["days"])):
        day = program["days"][day_index]
        st.markdown("### Day " + str(day_index + 1))
        for position in range(len(day["slots"])):
            slot = day["slots"][position]
            column_name, column_up, column_down, column_remove = st.columns([5, 1, 1, 1])
            column_name.write(str(position + 1) + ". " + slot_label(program, slot))
            key_suffix = str(day_index) + "_" + str(position)
            if column_up.button("▲", key=widget_key("up_" + key_suffix)) and position > 0:
                day["slots"][position], day["slots"][position - 1] = day["slots"][position - 1], day["slots"][position]
                save_program()
                st.rerun()
            if column_down.button("▼", key=widget_key("down_" + key_suffix)) and position < len(day["slots"]) - 1:
                day["slots"][position], day["slots"][position + 1] = day["slots"][position + 1], day["slots"][position]
                save_program()
                st.rerun()
            if column_remove.button("✕", key=widget_key("remove_" + key_suffix)):
                day["slots"].pop(position)
                save_program()
                st.rerun()

        unscheduled = []
        for slot in defaults.ALL_SLOTS:
            if slot not in scheduled:
                unscheduled.append(slot)
        if len(unscheduled) > 0:
            column_pick, column_add = st.columns([3, 1])
            choice = column_pick.selectbox("Add a lift to day " + str(day_index + 1), unscheduled,
                                           format_func=label_for_slot,
                                           key=widget_key("add_pick_" + str(day_index)))
            if column_add.button("Add", key=widget_key("add_button_" + str(day_index))):
                day["slots"].append(choice)
                save_program()
                st.rerun()

        edit = {}
        edit["accessories"] = st.text_area("Accessories (one per line)", value="\n".join(day["accessories"]),
                                           key=widget_key("accessories_" + str(day_index)))
        day_edits.append(edit)

    if st.button("Save accessory names", type="primary"):
        for day_index in range(len(program["days"])):
            day = program["days"][day_index]
            names = []
            for line in day_edits[day_index]["accessories"].split("\n"):
                if line.strip() != "":
                    names.append(line.strip())
            day["accessories"] = names
        save_program()
        st.success("Saved.")
        st.rerun()


def planned_accessory_names(program):
    """Takes program. Returns every accessory name on the training days, without repeats."""
    names = []
    for day in program["days"]:
        for name in day["accessories"]:
            if name.strip() != "" and name not in names:
                names.append(name)
    return names


def library_picture_picker(program, name, catalog, key_suffix):
    """
    A dropdown that points an exercise at any picture in the library.

    Takes: program, exercise name, catalog list, a widget key suffix.
    Saves the choice right away. Returns: nothing.
    """
    automatic = "Automatic match"
    options = [automatic] + exercise_library.catalog_names(catalog)
    by_id = exercise_library.catalog_by_id(catalog)
    current_id = program["image_choices"].get(name, "")
    current_label = automatic
    if current_id in by_id:
        current_label = by_id[current_id]["name"]
    choice = st.selectbox("Library picture", options, index=options.index(current_label),
                          key=widget_key("picture_" + key_suffix))
    if choice != current_label:
        if choice == automatic:
            program["image_choices"].pop(name, None)
        else:
            for entry in catalog:
                if entry["name"] == choice:
                    program["image_choices"][name] = entry["id"]
        save_program()
        st.rerun()


def settings_images(program):
    """Draws the image tab: pick a library picture or upload your own. Returns nothing."""
    catalog = load_catalog()
    if len(catalog) == 0:
        st.warning("The exercise library has not been downloaded. Run: python scripts/fetch_exercises.py")
    st.caption("Each picture shows the start and finish positions side by side, from the public-domain "
               "free-exercise-db. Pick any library picture for an exercise, or upload your own for a lift.")
    for slot in defaults.ALL_SLOTS:
        lift = program["lifts"][slot]
        column_image, column_text = st.columns([1, 1])
        with column_image:
            show_image(lift["name"], lift, width=360)
        with column_text:
            st.markdown("**" + logic.lift_display_name(program, slot) + "** · " + defaults.SLOT_LABELS[slot])
            st.caption(exercise_library.describe_match(lift["name"], catalog, lift.get("image_path", ""),
                                                       program["image_choices"].get(lift["name"], "")))
            library_picture_picker(program, lift["name"], catalog, "lift_" + slot)
            uploaded = st.file_uploader("Or upload my own image", type=["png", "jpg", "jpeg"],
                                        key=widget_key("upload_" + slot))
            if uploaded is not None:
                os.makedirs(USER_IMAGES_DIR, exist_ok=True)
                destination = os.path.join(USER_IMAGES_DIR, slot + "_" + uploaded.name)
                if lift.get("image_path", "") != destination:
                    with open(destination, "wb") as file:
                        file.write(uploaded.getbuffer())
                    lift["image_path"] = destination
                    save_program()
                    st.rerun()
            if lift.get("image_path", ""):
                if st.button("Back to the library picture", key=widget_key("clear_image_" + slot)):
                    lift["image_path"] = ""
                    save_program()
                    st.rerun()
        st.divider()

    st.markdown("### Accessories")
    names = planned_accessory_names(program)
    if len(names) == 0:
        st.caption("No accessories are planned yet.")
    for position in range(len(names)):
        name = names[position]
        column_image, column_text = st.columns([1, 1])
        with column_image:
            show_image(name, None, width=360)
        with column_text:
            st.markdown("**" + name + "**")
            st.caption(exercise_library.describe_match(name, catalog, "", program["image_choices"].get(name, "")))
            library_picture_picker(program, name, catalog, "acc_" + str(position))
        st.divider()


def settings_data(program):
    """Draws export/import controls. Returns nothing."""
    st.download_button("Download my program as JSON", data=storage.program_to_json_text(program),
                       file_name="sbs_program.json", mime="application/json")
    uploaded = st.file_uploader("Import a program JSON file (replaces the current program)", type=["json"],
                                key=widget_key("import_program"))
    if uploaded is not None:
        imported = storage.program_from_json_text(uploaded.getvalue().decode("utf-8"))
        if imported is None:
            st.error("That file does not look like an SBS Trainer program.")
        elif st.button("Replace my program with this file"):
            replace_program(imported)
            st.success("Imported.")
            st.rerun()
    st.caption("Your data lives in user_data/program.json. Backups are written there before any reset.")


def page_settings():
    """Draws the Settings page with its tabs. Returns nothing."""
    program = get_program()
    if program is None:
        st.warning("No program yet. Set one up first.")
        return
    st.title("Settings")
    st.caption("Sensible defaults everywhere: change only what you want to.")
    tab_general, tab_lifter, tab_lifts, tab_tables, tab_intensities, tab_days, tab_images, tab_data = st.tabs(
        ["General", "Lifter & ranks", "Lifts", "Rep & RIR tables", "Intensities", "Training days", "Images", "Data"])
    with tab_general:
        settings_general(program)
    with tab_lifter:
        st.caption("Used only for the ranks: sex, age and bodyweight pick the strength standards each lift is "
                   "measured against. Update the bodyweight as it changes.")
        draw_lifter_form(program, "settings")
    with tab_lifts:
        settings_lifts(program)
    with tab_tables:
        settings_tables(program)
    with tab_intensities:
        settings_intensities(program)
    with tab_days:
        settings_days(program)
    with tab_images:
        settings_images(program)
    with tab_data:
        settings_data(program)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Draws the sidebar, then the selected page. Returns nothing."""
    page = draw_sidebar()
    if page == PAGE_HOME:
        page_home()
    elif page == PAGE_SETUP:
        page_setup()
    elif page == PAGE_WORKOUT:
        page_workout()
    elif page == PAGE_RANKS:
        page_ranks()
    elif page == PAGE_PROGRESS:
        page_progress()
    else:
        page_settings()


main()
