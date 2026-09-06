"""
scripts/build_phone_release.py - assemble a self-contained copy of the phone app.

The phone app normally borrows the exercise catalog and pictures from the main
project's data/ folder. This script copies the phone files AND that data into
one folder, so that folder alone can be published on GitHub Pages or any other
static host as its own repository. Run from the project folder:

    python scripts/build_phone_release.py                 # writes ../sbs-trainer-phone
    python scripts/build_phone_release.py /some/folder    # writes there instead

Re-running is safe: files are overwritten, and a .git folder in the output
(from an earlier "git init") is left alone.
"""
import os
import shutil
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHONE_DIR = os.path.join(PROJECT_DIR, "phone")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(PROJECT_DIR), "sbs-trainer-phone")

RELEASE_README = """# SBS Trainer

A phone app for running the Stronger By Science training programs. It lives on
your home screen, works with no internet connection, and keeps your training
log on your phone.

## Credit

The program design is by **Greg Nuckols / Stronger By Science**. The original
spreadsheets are free at the
[SBS program bundle](https://www.strongerbyscience.com/program-bundle/).
This app is an unofficial personal project, not affiliated with or endorsed by
Stronger By Science. Exercise photos come from
[free-exercise-db](https://github.com/yuhonas/free-exercise-db), public domain.

## Put it on your phone

Works on iPhone (Safari) and Android (Chrome), and in any desktop browser.

1. On the phone, open this repository's web address:
   <https://ohnoandy.github.io/sbs-trainer-phone/>
2. iPhone: tap Share, then **Add to Home Screen**. Android: tap the menu, then
   **Install app** or **Add to Home screen**.
3. Open it from the home screen and set up your program while you are still on
   wifi. The pictures for your exercises are saved at that moment. After that it
   works in airplane mode.

## Using it

**Setup.** Start from the SBS defaults or from the "Andy's Routine" preset,
which fills in a six-day squat/bench/deadlift week with its accessories. Then
pick a program variant, units and rounding, days per week, and a split style:
the full-body layout the standard templates use, or the upper/lower layout from
the SBS lower-frequency templates. Step 5 lets you choose which day each lift
lands on, and the same editor lives under Settings. Then your lifts and a real
or estimated one-rep max for each. Conservative maxes are fine: the
program raises a training max that is too low within a few weeks and lowers one
that is too high just as fast. Any lift slot can be skipped, and one checkbox
fills the auxiliary slots with your four main lifts if you do not want
variations. Add any accessories you want for each day; a row or pull-up is
suggested on each day because the main lifts include no pulling.

**Workout.** Each lift shows its picture, the weight to load, the sets and reps,
and the target for the day. If you work up to a heavy single at RPE 8 first,
type it in and the day's numbers recalculate. After the sets, enter your result:
sets completed, sets plus last-set RIR, or reps on the last set, depending on the
variant. The line under the input tells you what saving will do to the training
max. Fill in the accessory numbers, press **Save workout**, and the app moves to
the next day.

**Ranks.** Just for fun. Enter your sex, age and bodyweight and every main
lift gets a rank, from Mortal up through Titan and Demigod to Legend III, based
on its training max against strength standards, with a progress bar to the next
tier and the weight still needed. Ranks rise and fall with your training maxes,
and a rank-up gets its own little ceremony. The standards are approximate; any
lift can use five thresholds you type in from a standards calculator instead
(Settings, Lifts).

**Progress.** Training max and estimated one-rep max charts for every lift,
summary numbers, and the full history.

**Settings.** Every number the program uses can be changed per lift: training
maxes, set counts, thresholds, the training-max ladder, the rep and RIR tables,
the weekly intensities, the order of lifts on each day, and the picture used for
any exercise.

## The four variants

* **Reps to Failure.** Fixed sets, the last one for as many reps as possible.
  Beat the rep target and the training max goes up; fall short and it comes down.
* **Hypertrophy.** The same idea with four sets, higher reps and a lower
  intensity ceiling.
* **Last Set RIR.** Fixed sets; you rate how many reps you had left after the
  final set. More reps in reserve than the target raises the training max.
* **Original.** Open-ended sets until you reach the RIR cutoff. Too few sets
  lowers the training max; extra sets raise it.

Every variant runs 21 weeks in three 7-week blocks. Weeks 7, 14 and 21 are
deloads: lighter weights, easy sets, no target, no training-max change.

## Your data

Your program and log are stored in this phone's browser storage only; nothing
is uploaded anywhere. That storage survives closing the app, restarting the
phone, app updates and airplane mode. It is deleted if you remove the app icon
from the home screen or reset the phone.

On iPhone, an app on the Home Screen keeps its own storage, separate from
Safari's, so clearing Safari's history and website data should leave it alone.
Check it once after installing: log a workout, clear Safari's data, reopen the
app from the icon. On Android, Chrome's "clear site data" does clear installed
apps too.

Either way, keep a copy in real phone storage. A website cannot write files by
itself, so back up by hand now and then: the **Back up my data** button on the
workout page shares a dated backup file, and one tap on **Save to Files** or
iCloud Drive keeps it outside the browser. The line under the button shows when
the last backup was made.

If the phone ever loses the log, open the app, and on the setup screen tap
**Restore from a backup file** and pick the newest sbs_program file. Every
workout, training max and setting comes back exactly as it was. The same import
lives under **Settings, Data** while a program is loaded.
"""


def folder_size(path):
    """Takes a folder path. Returns its total size in bytes."""
    total = 0
    for root, folders, files in os.walk(path):
        if ".git" in folders:
            folders.remove(".git")   # git's own storage is not part of the app
        for name in files:
            total += os.path.getsize(os.path.join(root, name))
    return total


def main():
    """Copies the phone app and its data into the output folder. Returns nothing."""
    output = DEFAULT_OUTPUT
    if len(sys.argv) > 1:
        output = os.path.abspath(sys.argv[1])
    os.makedirs(output, exist_ok=True)

    shutil.copytree(PHONE_DIR, output, dirs_exist_ok=True)
    os.makedirs(os.path.join(output, "data"), exist_ok=True)
    for name in ["exercises.json", "demo_program.json"]:
        shutil.copy2(os.path.join(DATA_DIR, name), os.path.join(output, "data", name))
    shutil.copytree(os.path.join(DATA_DIR, "images"), os.path.join(output, "data", "images"), dirs_exist_ok=True)

    # GitHub Pages runs a site generator called Jekyll unless this file exists;
    # we do not want it touching anything.
    with open(os.path.join(output, ".nojekyll"), "w", encoding="utf-8") as file:
        file.write("")
    with open(os.path.join(output, "README.md"), "w", encoding="utf-8") as file:
        file.write(RELEASE_README)

    print("Wrote " + output)
    print("Size: " + str(round(folder_size(output) / (1024 * 1024), 1)) + " MB")
    print("Next: publish that folder as its own repository (see README.md, phone section).")


if __name__ == "__main__":
    main()
