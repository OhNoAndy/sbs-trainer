# SBS Trainer

A pure-Python web app that runs the **Stronger By Science (SBS) 2.0 training
programs** in your browser: setup, today's workout with exercise photos, logging,
and automatic training-max adjustment. It replaces the spreadsheet workflow with
a Streamlit app and a JSON file.

Built as a personal project for *CSC 1301K – Principles of Computer Science I*.

## Credit

The program design is by **Greg Nuckols / Stronger By Science**. The original
templates are distributed free as Google Sheets from the
[SBS program bundle](https://www.strongerbyscience.com/program-bundle/).

This app is an **unofficial personal project**, not affiliated with or endorsed by
Stronger By Science. It does not include the original spreadsheets or the official
instruction document; all in-app explanations are written in our own words. If you
want the real thing, use the link above.

Exercise photos and the exercise catalog come from
[yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db),
released into the public domain (Unlicense). Each picture in the app shows the
start and finish positions side by side. If the automatic match is wrong for an
exercise, pick any of the 876 library pictures for it on the Settings › Images
tab, or upload your own.

## Quick start (under two minutes)

You need Python 3.9 or newer.

```bash
git clone <this repository>
cd sbs-trainer
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens the app at <http://localhost:8501>. Everything runs locally and
offline; nothing is fetched at runtime. To edit the code, open the `sbs-trainer`
folder in VS Code (File › Open Folder) or any editor; there is no build step.

Want to look around before entering your own numbers? Click **Load demo data** in
the sidebar: a fictional lifter part-way through week 9 with every earlier session
logged. **Reset to empty** clears it again (a backup is written first).

## Using the app

1. **Setup** – start from the SBS defaults or a preset routine, then pick a
   program variant, units and rounding increment, training days per week, the
   split style (the full-body layout of the standard templates, or the upper/lower
   layout of the SBS lower-frequency templates if you do not want the same movement
   on back-to-back days), your lifts and starting maxes, which day each lift lands
   on, and the accessories for each day. A row
   or pull-up is suggested on every day because the main lifts include no pulling. Any lift slot can be set to *Skip this slot* if you do not want
   it, and one checkbox fills the auxiliary slots with your four main lifts if you
   would rather not do variations. Conservative maxes are fine; the program
   corrects itself within a few weeks.
2. **Today's Workout** – each lift shows its photo, working weight, sets and reps,
   and the RIR cutoff or last-set target. Optionally log a heavy single at RPE 8 to
   recalculate the day's training max. Log your result, and the app tells you
   immediately how the training max changed, e.g. *"You beat the target by 3 reps -
   training max going up 1.5% to 497.4 lb"*. Accessories are logged as weight, sets
   and reps, with last time's numbers shown as the target to beat.
3. **Ranks** – just for fun: enter your sex, age and bodyweight and every main and
   auxiliary lift gets a rank from Mortal to Legend III, based on its training max
   against strength standards, with a progress bar to the next tier. Ranks go up
   and down with your training maxes. The standards are approximate (bodyweight
   multiples calibrated to commonly cited numbers, scaled to bodyweight with the
   two-thirds rule and adjusted with the powerlifting age coefficients); any lift
   can use five thresholds you type in from a standards calculator instead.
4. **Progress** – training max and estimated-1RM charts for every lift, a full
   workout history, and summary stats.
5. **Settings** – everything the spreadsheet lets you change: rep, RIR and last-set
   tables for each lift across all 21 percentage buckets, set thresholds and
   training-max percentages, per-lift per-week intensities, the single-@8
   percentage, rounding, which lifts fill which slots and their order within a
   day, the accessories on each day, and custom images.

Your data lives in `user_data/program.json` (git-ignored). You can export and
import it as JSON from the Progress and Settings pages, which is handy for moving
between a laptop and a phone.

## The phone app (works offline, no computer needed)

The `phone/` folder is a second front end for the same program: a small web app
in plain HTML, CSS and JavaScript that runs entirely on the phone. It stores your
program and log on the phone, works with no internet connection after the first
visit, and reads and writes the **same JSON file** as the Python app, so you can
move your data between the two.

### Publishing it (once, from the computer)

The phone app needs the exercise catalog and pictures next to it, so publish the
**standalone folder** the build script makes rather than `phone/` on its own:

```bash
python scripts/build_phone_release.py
```

That writes `../sbs-trainer-phone` (next to this project, about 28 MB): the app
files plus `data/` with the catalog, the 873 pictures and the demo file, ready to
be a repository of its own. Your training data is never in it.

Do not use GitHub's "Upload files" web page for this: it stops at 100 files per
upload, and the pictures alone are 873. Use one of these instead:

* **GitHub Desktop** (free, no command line). Install it and sign in. Then
  *File › Add Local Repository*, choose the `sbs-trainer-phone` folder, and press
  *Publish repository*. Untick "Keep this code private", because GitHub Pages on a
  free account needs a public repository.
* **Terminal.** Create an empty public repository on github.com called
  `sbs-trainer-phone` (no README), then, in the folder, which already has a first
  commit:

  ```bash
  cd ~/Documents/sbs-trainer-phone && git remote add origin https://github.com/OhNoAndy/sbs-trainer-phone.git && git push -u origin main
  ```

  Git asks for your GitHub username and a personal access token, not your
  password; GitHub Desktop handles that part for you.

Then turn on the website: in the repository on github.com open *Settings ›
Pages*, under "Build and deployment" choose *Deploy from a branch*, pick branch
`main` and folder `/ (root)`, and save. After a minute the same page says
"Your site is live at ..." with the address.

### The address

It is built from your GitHub username and the repository name:

```
https://ohnoandy.github.io/sbs-trainer-phone/
```

GitHub writes the username in lower case in that address.
There is no `/phone/` on the end when you publish the standalone folder; that
suffix only applies if you publish the whole `sbs-trainer` project instead, in
which case the app is at `https://ohnoandy.github.io/sbs-trainer/phone/`.

### On the phone

1. Open the address in Safari (iPhone) or Chrome (Android) while on wifi.
2. Tap Share, then *Add to Home Screen* (Chrome: *Install app*). It gets an icon
   and opens full screen.
3. Set up your program. Its pictures are saved for offline use at that moment,
   so give it a few seconds on wifi, then it keeps working in airplane mode.
4. Back up now and then with *Settings › Data › Share / download my program*; it
   sends the JSON to Files, AirDrop or mail, and *Import a program file* on
   either app reads it back.

To try the standalone folder on the computer first, run a tiny web server inside
it and open <http://localhost:8000/> in a browser:

```bash
cd ~/Documents/sbs-trainer-phone && python3 -m http.server 8000
```

The numbers in the phone app are generated from `defaults.py` by
`scripts/make_phone_defaults.py`, and `phone/test_program_logic.js` mirrors the
Python tests: open `phone/tests.html` through the same web server to run them.
Re-run `scripts/build_phone_release.py` after any change to `phone/` or the
pictures, then commit and push the standalone folder again.

## The training math in one screen

* **Training max (TM)** – every lift has one. It starts at the max you enter and
  moves up or down after each session. It is *not* your true 1RM; it is the number
  that generates your weights, and it is kept unrounded internally.
* **Working weight** = `round_to_increment(TM × intensity, rounding_increment)`.
* **Intensity** comes from a 21-week table (three 7-week blocks that get heavier;
  weeks 7, 14 and 21 are 60% deloads). Auxiliary lifts use the same shape minus
  10 points (strength variants) or 5 points (hypertrophy).
* **Reps and targets** are looked up from the intensity percentage, snapped to the
  nearest of 21 buckets (50%, 52.5%, ..., 100%), not from the week number.
* **Deloads** are a hard-coded special case: easy sets at the listed weight, no
  target, no TM change.
* **Single @8** – log a heavy single at RPE 8 and today's TM becomes
  `single ÷ single_at_8_percentage` (90% by default).
* **TM adjustment** – one engine with the variant as a parameter:
  * *Original*: below the lower set threshold → −5%, above the upper → +2%.
  * *Last Set RIR*, *Reps to Failure*, *Hypertrophy*: an 8-step ladder from −5%
    (2+ below target) through 0% (hit target) to +3% (beat by 5+).

All of those numbers are defaults in `defaults.py` and editable per lift in the app.

## Project structure

```
sbs-trainer/
├── app.py                  # Streamlit UI and page routing (the only file that imports streamlit)
├── program_logic.py        # all training math, pure functions, no UI
├── storage.py              # JSON save/load
├── exercise_library.py     # exercise catalog + image lookup with an SBS-name override map
├── defaults.py             # every default table as a named constant
├── test_program_logic.py   # plain assert tests, run with python
├── scripts/
│   ├── fetch_exercises.py  # downloads and trims free-exercise-db into data/
│   ├── make_demo_data.py   # regenerates data/demo_program.json
│   ├── make_phone_defaults.py # writes phone/defaults.js from defaults.py
│   ├── make_icons.py       # draws the phone app icons with Pillow
│   ├── make_rank_badges.py # draws the rank badges as PNGs with Pillow
│   └── build_phone_release.py # assembles ../sbs-trainer-phone, the standalone folder to publish
├── .streamlit/config.toml  # Streamlit's built-in dark theme (config, not CSS)
├── phone/                  # the offline phone app (HTML/CSS/JavaScript)
│   ├── index.html, styles.css, app.js   # screens
│   ├── program_logic.js    # port of program_logic.py, same function names
│   ├── exercise_library.js # port of exercise_library.py
│   ├── defaults.js         # generated from defaults.py
│   ├── sw.js, manifest.webmanifest, icons/   # offline support and home-screen icon
│   └── test_program_logic.js, tests.html     # the mirrored tests
├── data/
│   ├── badges/             # rank badge pictures, drawn by scripts/make_rank_badges.py
│   ├── exercises.json      # trimmed catalog (876 exercises)
│   ├── images/             # one start/finish photo strip per exercise + placeholder.png
│   └── demo_program.json   # the presentation dataset
├── user_data/              # created at runtime, git-ignored
├── requirements.txt
└── README.md
```

## Running the tests

```bash
python test_program_logic.py
```

No pytest needed. The expected weights (squat 490 → 342.5 at 70%, sumo deadlift
500 → 300 at 60%, single of 460 → TM 511, and so on) are taken from the original
spreadsheet, so a green run means the app reproduces the real program.

## Refreshing the exercise images

The images and catalog are committed, so you never need to do this. If you want to
re-download or update them:

```bash
python scripts/fetch_exercises.py            # everything, a few minutes
python scripts/fetch_exercises.py --limit 20 # quick test
```

Already-downloaded images are skipped. The script only uses the standard library
and Pillow.

## Regenerating the demo data

```bash
python scripts/make_demo_data.py
```

## Design notes

* **Streamlit, JSON, and nothing else.** Standard library plus `streamlit`,
  `pandas` and `pillow`. No database, no HTML/CSS/JS, no web framework.
* **`program_logic.py` never imports Streamlit.** Values in, values out, which is
  why the tests are plain `assert` statements and why the demo generator can reuse
  the exact logging code the app uses.
* **One dictionary is the whole app state.** It lives in `st.session_state` while
  the app runs and is written to disk after every change.
* **Percentages are stored as percentages** (70 means 70%), so the code reads the
  way the program is written.
* **The setup is a single page rather than a multi-step wizard.** It is simpler than
  juggling wizard steps in session state, and you can scroll back to fix a value.
* **Intro-course vocabulary on purpose:** functions, `if`/`else`, `for` loops,
  lists, dicts, string formatting and file I/O. No classes, no decorators beyond
  `@st.cache_data`, no nested comprehensions.
* **The phone app is a port, not a rewrite.** `program_logic.js` follows
  `program_logic.py` function for function, its numbers are generated from
  `defaults.py`, and its tests mirror the Python tests, so the Python file stays
  the reference implementation the class project is graded on.

## Licenses

* The application code in this repository is yours to use under the MIT license.
* The SBS program design belongs to Greg Nuckols / Stronger By Science; this app
  only reproduces the arithmetic so you can run the program you downloaded from
  them.
* Exercise data and photos: public domain via free-exercise-db.
