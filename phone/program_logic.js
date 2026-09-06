/*
program_logic.js - the SBS training math, ported from program_logic.py.

The phone app runs entirely in the browser, so the math has to exist in
JavaScript too. Keep this file in step with program_logic.py:
  * same function names (camelCase here, snake_case there),
  * same data keys (snake_case in both, because both apps read and write the
    same JSON program file),
  * the tests in test_program_logic.js mirror test_program_logic.py.
All the numbers come from defaults.js, which is generated from defaults.py.
*/
"use strict";
(function () {

const DEFAULTS = (typeof window === "undefined")
  ? require("./defaults.js").DEFAULTS
  : window.SBS_DEFAULTS;

// ---------------------------------------------------------------------------
// 1. Rounding and percentage lookups
// ---------------------------------------------------------------------------
function roundToIncrement(value, increment) {
  // Nearest multiple of the increment; exact halves round up like MROUND.
  if (increment <= 0) return value;
  const numberOfIncrements = Math.floor(value / increment + 0.5 + 1e-9);
  return Math.round(numberOfIncrements * increment * 1000) / 1000;
}

function nearestPercentageBucket(percentage) {
  let closest = DEFAULTS.PERCENTAGE_BUCKETS[0];
  for (const bucket of DEFAULTS.PERCENTAGE_BUCKETS) {
    if (Math.abs(bucket - percentage) < Math.abs(closest - percentage)) closest = bucket;
  }
  return closest;
}

function bucketIndex(percentage) {
  return DEFAULTS.PERCENTAGE_BUCKETS.indexOf(nearestPercentageBucket(percentage));
}

function lookupByPercentage(table, percentage) {
  return table[bucketIndex(percentage)];
}

// ---------------------------------------------------------------------------
// 2. Weights and training maxes
// ---------------------------------------------------------------------------
function isDeloadWeek(week) {
  return DEFAULTS.DELOAD_WEEKS.includes(week);
}

function blockNumber(week) {
  return Math.floor((week - 1) / DEFAULTS.WEEKS_PER_BLOCK) + 1;
}

function calculateWorkingWeight(trainingMax, intensityPercent, roundingIncrement) {
  return roundToIncrement(trainingMax * intensityPercent / 100, roundingIncrement);
}

function calculateTrainingMaxFromSingle(singleWeight, singleAt8Percent) {
  return singleWeight / (singleAt8Percent / 100);
}

function applyTmChange(trainingMax, changePercent) {
  return trainingMax * (1 + changePercent / 100);
}

function estimateOneRepMax(weight, reps) {
  if (reps <= 1) return weight;
  return weight * (1 + reps / 30);
}

function valueOr(object, key, fallback) {
  // Same job as Python's dict.get(key, fallback), treating null like a missing key.
  if (object[key] === undefined || object[key] === null) return fallback;
  return object[key];
}

// ---------------------------------------------------------------------------
// 3. Per-lift settings and the daily prescription
// ---------------------------------------------------------------------------
function buildLiftSettings(variant, slot, name, startingMax) {
  const isMain = DEFAULTS.MAIN_SLOTS.includes(slot);
  let mainIntensities, auxiliaryOffset, repsPerSet, lastSetRepTarget;
  if (variant === DEFAULTS.VARIANT_HYPERTROPHY) {
    mainIntensities = DEFAULTS.HYPERTROPHY_MAIN_INTENSITIES;
    auxiliaryOffset = DEFAULTS.HYPERTROPHY_AUXILIARY_OFFSET;
    repsPerSet = DEFAULTS.HYPERTROPHY_REPS_PER_SET;
    lastSetRepTarget = DEFAULTS.HYPERTROPHY_LAST_SET_REP_TARGET;
  } else {
    mainIntensities = DEFAULTS.STRENGTH_MAIN_INTENSITIES;
    auxiliaryOffset = DEFAULTS.STRENGTH_AUXILIARY_OFFSET;
    repsPerSet = DEFAULTS.STRENGTH_REPS_PER_SET;
    lastSetRepTarget = DEFAULTS.RTF_LAST_SET_REP_TARGET;
  }
  const intensities = [];
  for (const mainValue of mainIntensities) {
    intensities.push(isMain ? mainValue : mainValue - auxiliaryOffset);
  }
  return {
    slot: slot,
    name: name,
    is_main: isMain,
    starting_max: Number(startingMax),
    training_max: Number(startingMax),
    intensities: intensities,
    reps_per_set: repsPerSet.slice(),
    rir_cutoff: DEFAULTS.ORIGINAL_RIR_CUTOFF.slice(),
    last_set_rir_target: DEFAULTS.LAST_SET_RIR_TARGET.slice(),
    last_set_rep_target: lastSetRepTarget.slice(),
    sets: DEFAULTS.DEFAULT_SETS[variant],
    lower_set_threshold: DEFAULTS.ORIGINAL_LOWER_SET_THRESHOLD,
    upper_set_threshold: DEFAULTS.ORIGINAL_UPPER_SET_THRESHOLD,
    increase_percent: DEFAULTS.ORIGINAL_INCREASE_PERCENT,
    decrease_percent: DEFAULTS.ORIGINAL_DECREASE_PERCENT,
    ladder: DEFAULTS.DEFAULT_TM_LADDER.slice(),
    single_at_8_percent: DEFAULTS.DEFAULT_SINGLE_AT_8_PERCENT,
    image_path: "",
    rank_factor: defaultRankFactor(name),
    rank_thresholds: null,
  };
}

function cleanExerciseName(name) {
  let text = String(name).toLowerCase();
  for (const character of ["-", "_", "/", "(", ")", ",", ".", "'"]) text = text.split(character).join(" ");
  return text.split(/\s+/).filter(function (word) { return word !== ""; }).join(" ");
}

function defaultRankFactor(name) {
  const factor = DEFAULTS.VARIATION_RANK_FACTORS[cleanExerciseName(name)];
  return factor === undefined ? 1.0 : factor;
}

function resetLiftTablesForVariant(lift, variant) {
  const fresh = buildLiftSettings(variant, lift.slot, lift.name, lift.training_max);
  for (const key of ["intensities", "reps_per_set", "rir_cutoff", "last_set_rir_target",
                     "last_set_rep_target", "sets", "ladder"]) {
    lift[key] = fresh[key];
  }
}

function getPrescription(variant, lift, week, roundingIncrement, deloadRepsPerSet) {
  if (deloadRepsPerSet === undefined) deloadRepsPerSet = DEFAULTS.DELOAD_REPS_PER_SET;
  const intensity = lift.intensities[week - 1];
  const trainingMax = lift.training_max;
  const prescription = {
    week: week,
    is_deload: isDeloadWeek(week),
    intensity: intensity,
    training_max: trainingMax,
    working_weight: calculateWorkingWeight(trainingMax, intensity, roundingIncrement),
    sets: lift.sets,
  };
  if (prescription.is_deload) {
    prescription.reps_per_set = deloadRepsPerSet;
    return prescription;
  }
  prescription.reps_per_set = lookupByPercentage(lift.reps_per_set, intensity);
  if (variant === DEFAULTS.VARIANT_ORIGINAL) {
    prescription.rir_cutoff = lookupByPercentage(lift.rir_cutoff, intensity);
    prescription.lower_set_threshold = lift.lower_set_threshold;
    prescription.upper_set_threshold = lift.upper_set_threshold;
  } else if (variant === DEFAULTS.VARIANT_LAST_SET_RIR) {
    prescription.last_set_rir_target = lookupByPercentage(lift.last_set_rir_target, intensity);
  } else {
    prescription.last_set_rep_target = lookupByPercentage(lift.last_set_rep_target, intensity);
  }
  return prescription;
}

function getPrescriptionForSlot(program, slot, week) {
  return getPrescription(program.variant, program.lifts[slot], week,
                         program.rounding_increment, program.deload_reps_per_set);
}

function describePrescription(variant, prescription) {
  const sets = prescription.sets;
  const reps = prescription.reps_per_set;
  if (prescription.is_deload) {
    return "Deload: " + sets + " easy sets of " + reps + ", no target";
  }
  if (variant === DEFAULTS.VARIANT_ORIGINAL) {
    return "Sets of " + reps + " until you reach " + prescription.rir_cutoff + " RIR (target "
      + prescription.lower_set_threshold + "-" + prescription.upper_set_threshold + " sets)";
  }
  if (variant === DEFAULTS.VARIANT_LAST_SET_RIR) {
    return sets + " sets of " + reps + ", aim for " + prescription.last_set_rir_target + " RIR on the last set";
  }
  return (sets - 1) + " sets of " + reps + ", then 1 set for as many reps as possible (target "
    + prescription.last_set_rep_target + ")";
}

// ---------------------------------------------------------------------------
// 4. The training-max engine (shared by every variant)
// ---------------------------------------------------------------------------
function ladderIndexForDifference(difference) {
  if (difference <= -2) return 0;
  if (difference >= 5) return 7;
  return difference + 2;
}

function calculateTmChangePercent(variant, lift, prescription, performance) {
  if (prescription.is_deload) return 0;
  if (variant === DEFAULTS.VARIANT_ORIGINAL) {
    const setsCompleted = valueOr(performance, "sets_completed", 0);
    if (setsCompleted < lift.lower_set_threshold) return lift.decrease_percent;
    if (setsCompleted > lift.upper_set_threshold) return lift.increase_percent;
    return 0;
  }
  const ladder = lift.ladder;
  if (variant === DEFAULTS.VARIANT_LAST_SET_RIR) {
    const setsMissed = prescription.sets - valueOr(performance, "sets_completed", 0);
    if (setsMissed >= 2) return ladder[0];
    if (setsMissed === 1) return ladder[1];
    const rirDifference = valueOr(performance, "last_set_rir", 0) - prescription.last_set_rir_target;
    if (rirDifference < 0) return ladder[1];
    return ladder[ladderIndexForDifference(rirDifference)];
  }
  const repDifference = valueOr(performance, "last_set_reps", 0) - prescription.last_set_rep_target;
  return ladder[ladderIndexForDifference(repDifference)];
}

function formatWeight(value, units) {
  return String(Math.round(value * 10) / 10) + " " + units;
}

function formatPercent(value) {
  return String(Math.round(value * 100) / 100) + "%";
}

function plural(count, word) {
  if (count === 1) return "1 " + word;
  return count + " " + word + "s";
}

function describeOutcome(variant, prescription, performance) {
  if (prescription.is_deload) return "Deload week, no target";
  if (variant === DEFAULTS.VARIANT_ORIGINAL) {
    const setsCompleted = valueOr(performance, "sets_completed", 0);
    return "You completed " + plural(setsCompleted, "set") + " (target "
      + prescription.lower_set_threshold + "-" + prescription.upper_set_threshold + ")";
  }
  if (variant === DEFAULTS.VARIANT_LAST_SET_RIR) {
    const setsCompleted = valueOr(performance, "sets_completed", 0);
    if (setsCompleted < prescription.sets) {
      return "You completed " + setsCompleted + " of " + prescription.sets + " sets";
    }
    const target = prescription.last_set_rir_target;
    const rir = valueOr(performance, "last_set_rir", 0);
    if (rir < target) return "Your last set had " + rir + " RIR, under the target of " + target;
    if (rir === target) return "Your last set hit the RIR target of " + target;
    return "Your last set had " + plural(rir - target, "more rep") + " in reserve than the target of " + target;
  }
  const target = prescription.last_set_rep_target;
  const reps = valueOr(performance, "last_set_reps", 0);
  if (reps > target) return "You beat the target by " + plural(reps - target, "rep");
  if (reps === target) return "You hit the target of " + plural(target, "rep") + " exactly";
  return "You fell " + plural(target - reps, "rep") + " short of the target of " + target;
}

function describeTmChange(variant, prescription, performance, changePercent, newTrainingMax, units) {
  const outcome = describeOutcome(variant, prescription, performance);
  const newMaxText = formatWeight(newTrainingMax, units);
  if (changePercent > 0) return outcome + " - training max going up " + formatPercent(changePercent) + " to " + newMaxText;
  if (changePercent < 0) return outcome + " - training max dropping " + formatPercent(Math.abs(changePercent)) + " to " + newMaxText;
  return outcome + " - training max stays at " + newMaxText;
}

function estimateSessionOneRepMax(variant, prescription, performance) {
  if (prescription.is_deload) return null;
  const weight = prescription.working_weight;
  let repsToFailure;
  if (variant === DEFAULTS.VARIANT_ORIGINAL) {
    repsToFailure = prescription.reps_per_set + prescription.rir_cutoff;
  } else if (variant === DEFAULTS.VARIANT_LAST_SET_RIR) {
    repsToFailure = prescription.reps_per_set + valueOr(performance, "last_set_rir", 0);
  } else {
    repsToFailure = valueOr(performance, "last_set_reps", 0);
  }
  return estimateOneRepMax(weight, repsToFailure);
}

function countTotalReps(variant, prescription, performance) {
  const reps = prescription.reps_per_set;
  if (prescription.is_deload) return prescription.sets * reps;
  if (variant === DEFAULTS.VARIANT_ORIGINAL || variant === DEFAULTS.VARIANT_LAST_SET_RIR) {
    return valueOr(performance, "sets_completed", 0) * reps;
  }
  return (prescription.sets - 1) * reps + valueOr(performance, "last_set_reps", 0);
}

// ---------------------------------------------------------------------------
// 5. Whole-program helpers: creating, logging, moving through the calendar
// ---------------------------------------------------------------------------
function todayString() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return now.getFullYear() + "-" + month + "-" + day;
}

function buildDefaultDays(frequency, skippedSlots, splitStyle) {
  if (!skippedSlots) skippedSlots = [];
  if (!splitStyle) splitStyle = DEFAULTS.SPLIT_FULL_BODY;
  const days = [];
  const split = DEFAULTS.SPLITS_BY_STYLE[splitStyle][frequency];
  for (let dayIndex = 0; dayIndex < split.length; dayIndex++) {
    const slots = [];
    for (const slot of split[dayIndex]) {
      if (!skippedSlots.includes(slot)) slots.push(slot);
    }
    // A row or pull-up is suggested on every day because the main lifts include no pulling.
    const rowExercise = DEFAULTS.UPPER_BACK_EXERCISES[dayIndex % DEFAULTS.UPPER_BACK_EXERCISES.length];
    days.push({ slots: slots, accessories: [rowExercise] });
  }
  return days;
}

function recordTrainingMax(program, slot, week, day, sessionNumber, trainingMax, reason) {
  program.tm_history.push({
    slot: slot, week: week, day: day, session: sessionNumber,
    training_max: trainingMax, reason: reason,
  });
}

function createProgram(variant, units, roundingIncrement, frequency, liftNames, startingMaxes, skippedSlots, splitStyle) {
  if (!splitStyle) splitStyle = DEFAULTS.SPLIT_FULL_BODY;
  const program = {
    version: 1,
    variant: variant,
    units: units,
    rounding_increment: Number(roundingIncrement),
    frequency: Number(frequency),
    split_style: splitStyle,
    current_week: 1,
    current_day: 1,
    created_on: todayString(),
    deload_reps_per_set: DEFAULTS.DELOAD_REPS_PER_SET,
    lifts: {},
    days: buildDefaultDays(Number(frequency), skippedSlots, splitStyle),
    history: [],
    tm_history: [],
    image_choices: {},
    lifter: { sex: "", age: 0, bodyweight: 0 },
  };
  for (const slot of DEFAULTS.ALL_SLOTS) {
    program.lifts[slot] = buildLiftSettings(variant, slot, liftNames[slot], startingMaxes[slot]);
    recordTrainingMax(program, slot, 0, 0, 0, Number(startingMaxes[slot]), "Starting max");
  }
  return program;
}

function ensureProgramDefaults(program) {
  if (!program.image_choices) program.image_choices = {};
  if (!DEFAULTS.SPLIT_STYLES.includes(program.split_style)) program.split_style = DEFAULTS.SPLIT_FULL_BODY;
  if (program.deload_reps_per_set === undefined) program.deload_reps_per_set = DEFAULTS.DELOAD_REPS_PER_SET;
  if (!program.lifter) program.lifter = { sex: "", age: 0, bodyweight: 0 };
  for (const slot of DEFAULTS.ALL_SLOTS) {
    const lift = program.lifts[slot];
    if (!lift) continue;
    if (lift.image_path === undefined) lift.image_path = "";
    if (lift.rank_factor === undefined) lift.rank_factor = defaultRankFactor(lift.name);
    if (lift.rank_thresholds === undefined) lift.rank_thresholds = null;
  }
  for (const day of program.days) {
    // Older files kept an upper-back exercise in a slot of its own; it is now
    // simply the first accessory of the day.
    if (day.upper_back !== undefined) {
      if (String(day.upper_back).trim() !== "") day.accessories.unshift(String(day.upper_back).trim());
      delete day.upper_back;
    }
  }
}

function liftDisplayName(program, slot) {
  const name = program.lifts[slot].name;
  let timesUsed = 0;
  for (const otherSlot of DEFAULTS.ALL_SLOTS) {
    if (program.lifts[otherSlot].name.trim().toLowerCase() === name.trim().toLowerCase()) timesUsed++;
  }
  if (timesUsed > 1) return name + " (" + DEFAULTS.SHORT_SLOT_LABELS[slot] + ")";
  return name;
}

function scheduledSlots(program) {
  const slots = [];
  for (const day of program.days) for (const slot of day.slots) slots.push(slot);
  return slots;
}

function buildWorkout(program, week, day) {
  const exercises = [];
  const dayPlan = program.days[day - 1];
  for (const slot of dayPlan.slots) {
    const prescription = getPrescriptionForSlot(program, slot, week);
    prescription.slot = slot;
    prescription.name = liftDisplayName(program, slot);
    exercises.push(prescription);
  }
  return exercises;
}

function logWorkout(program, week, day, liftResults, accessoryResults, sessionNotes, dateString) {
  const variant = program.variant;
  const units = program.units;
  const messages = [];
  const loggedLifts = [];
  const sessionNumber = program.history.length + 1;
  const rankChanges = [];

  for (const result of liftResults) {
    const slot = result.slot;
    const lift = program.lifts[slot];
    const trainingMaxBefore = lift.training_max;
    const rankBefore = rankForLift(program, slot);

    const single = valueOr(result, "single_at_8", null);
    if (single) {
      lift.training_max = calculateTrainingMaxFromSingle(single, lift.single_at_8_percent);
      recordTrainingMax(program, slot, week, day, sessionNumber, lift.training_max,
                        "Single @8 of " + formatWeight(single, units));
    }

    const prescription = getPrescriptionForSlot(program, slot, week);
    const changePercent = calculateTmChangePercent(variant, lift, prescription, result);
    const newTrainingMax = applyTmChange(lift.training_max, changePercent);
    const message = describeTmChange(variant, prescription, result, changePercent, newTrainingMax, units);

    lift.training_max = newTrainingMax;
    recordTrainingMax(program, slot, week, day, sessionNumber, newTrainingMax, message);

    // Ranks are just for fun: note when a lift crossed into another tier.
    const rankAfter = rankForLift(program, slot);
    let tierBefore = null;
    let tierAfter = null;
    if (rankBefore.available && rankAfter.available) {
      tierBefore = rankBefore.tier;
      tierAfter = rankAfter.tier;
      if (tierAfter !== tierBefore) {
        rankChanges.push({ slot: slot, name: liftDisplayName(program, slot), from_tier: tierBefore, to_tier: tierAfter,
                           from_name: rankBefore.tier_name, to_name: rankAfter.tier_name });
      }
    }

    loggedLifts.push({
      slot: slot,
      name: liftDisplayName(program, slot),
      intensity: prescription.intensity,
      working_weight: prescription.working_weight,
      sets: prescription.sets,
      reps_per_set: prescription.reps_per_set,
      is_deload: prescription.is_deload,
      rir_cutoff: valueOr(prescription, "rir_cutoff", null),
      last_set_rir_target: valueOr(prescription, "last_set_rir_target", null),
      last_set_rep_target: valueOr(prescription, "last_set_rep_target", null),
      sets_completed: valueOr(result, "sets_completed", null),
      last_set_rir: valueOr(result, "last_set_rir", null),
      last_set_reps: valueOr(result, "last_set_reps", null),
      single_at_8: single,
      total_reps: countTotalReps(variant, prescription, result),
      estimated_1rm: estimateSessionOneRepMax(variant, prescription, result),
      training_max_before: trainingMaxBefore,
      training_max_after: newTrainingMax,
      tm_change_percent: changePercent,
      message: message,
      notes: valueOr(result, "notes", ""),
      rank_before: tierBefore,
      rank_after: tierAfter,
    });
    messages.push(liftDisplayName(program, slot) + ": " + message);
  }

  for (const change of rankChanges) {
    if (change.to_tier > change.from_tier) messages.push("Rank up! " + change.name + ": " + change.from_name + " -> " + change.to_name);
    else messages.push("Rank down: " + change.name + " is now " + change.to_name);
  }

  program.history.push({
    date: dateString, week: week, day: day, variant: variant,
    lifts: loggedLifts, accessories: accessoryResults, notes: sessionNotes,
    rank_changes: rankChanges,
  });
  return messages;
}

function advanceToNextDay(program) {
  if (program.current_day < program.frequency) {
    program.current_day += 1;
  } else if (program.current_week < DEFAULTS.TOTAL_WEEKS) {
    program.current_day = 1;
    program.current_week += 1;
  }
}

function isCycleFinished(program) {
  const lastWeek = program.current_week === DEFAULTS.TOTAL_WEEKS;
  const lastDay = program.current_day === program.frequency;
  if (!(lastWeek && lastDay)) return false;
  for (const entry of program.history) {
    if (entry.week === DEFAULTS.TOTAL_WEEKS && entry.day === program.frequency) return true;
  }
  return false;
}

function startNewCycle(program) {
  program.current_week = 1;
  program.current_day = 1;
  for (const slot of DEFAULTS.ALL_SLOTS) {
    const lift = program.lifts[slot];
    lift.starting_max = lift.training_max;
    recordTrainingMax(program, slot, 0, 0, program.history.length, lift.training_max, "New cycle");
  }
}

function findLastAccessoryResult(program, name) {
  for (let position = program.history.length - 1; position >= 0; position--) {
    for (const accessory of program.history[position].accessories) {
      if (accessory.name.trim().toLowerCase() === name.trim().toLowerCase()) return accessory;
    }
  }
  return null;
}

function findHistoryEntry(program, week, day) {
  for (const entry of program.history) {
    if (entry.week === week && entry.day === day) return entry;
  }
  return null;
}

// ---------------------------------------------------------------------------
// 6. Ranks: each lift measured against strength standards (just for fun)
// ---------------------------------------------------------------------------
function ageCoefficient(age) {
  if (!age || age <= 0) return 1.0;
  age = Math.floor(age);
  if (age < 14) age = 14;
  if (age > 90) age = 90;
  const value = DEFAULTS.AGE_COEFFICIENTS[age];
  return value === undefined ? 1.0 : value;
}

function standardThresholds(rankType, sex, bodyweight, units) {
  const ratios = DEFAULTS.STANDARD_RATIOS[sex][rankType];
  const reference = DEFAULTS.STANDARDS_REFERENCE_BODYWEIGHT_LB[sex];
  let bodyweightLb = bodyweight;
  if (units === "kg") bodyweightLb = bodyweight / DEFAULTS.KG_PER_LB;
  const scale = Math.pow(bodyweightLb / reference, DEFAULTS.BODYWEIGHT_SCALING_EXPONENT);
  const thresholds = [];
  for (const ratio of ratios) {
    let value = ratio * reference * scale;
    if (units === "kg") value = value * DEFAULTS.KG_PER_LB;
    thresholds.push(value);
  }
  return thresholds;
}

function strengthPercentile(lift, thresholds) {
  const percentiles = DEFAULTS.STANDARD_PERCENTILES;
  if (lift <= 0) return 0;
  if (lift < thresholds[0]) return percentiles[0] * lift / thresholds[0];
  for (let position = 1; position < thresholds.length; position++) {
    if (lift < thresholds[position]) {
      const share = (lift - thresholds[position - 1]) / (thresholds[position] - thresholds[position - 1]);
      return percentiles[position - 1] + share * (percentiles[position] - percentiles[position - 1]);
    }
  }
  const step = thresholds[4] - thresholds[3];
  const stepsBeyondElite = (lift - thresholds[4]) / step;
  return 100 - 5 * Math.pow(0.5, stepsBeyondElite);
}

function liftForPercentile(percentile, thresholds) {
  const percentiles = DEFAULTS.STANDARD_PERCENTILES;
  if (percentile <= 0) return 0;
  if (percentile <= percentiles[0]) return thresholds[0] * percentile / percentiles[0];
  for (let position = 1; position < thresholds.length; position++) {
    if (percentile <= percentiles[position]) {
      const share = (percentile - percentiles[position - 1]) / (percentiles[position] - percentiles[position - 1]);
      return thresholds[position - 1] + share * (thresholds[position] - thresholds[position - 1]);
    }
  }
  if (percentile >= 99.99) percentile = 99.99;
  const step = thresholds[4] - thresholds[3];
  const stepsBeyondElite = Math.log2(5 / (100 - percentile));
  return thresholds[4] + stepsBeyondElite * step;
}

function tierIndexForPercentile(percentile) {
  let index = 0;
  for (let position = 0; position < DEFAULTS.RANK_TIERS.length; position++) {
    if (percentile >= DEFAULTS.RANK_TIERS[position].min_percentile) index = position;
  }
  return index;
}

function lifterDetailsComplete(program) {
  const lifter = program.lifter || {};
  return DEFAULTS.SEX_CHOICES.includes(lifter.sex) && lifter.age > 0 && lifter.bodyweight > 0;
}

function rankThresholdsForLift(program, slot) {
  const lift = program.lifts[slot];
  const custom = lift.rank_thresholds;
  if (custom && custom.length === 5 && Math.min.apply(null, custom) > 0) return { thresholds: custom.slice(), custom: true };
  const rankType = DEFAULTS.RANK_TYPE_BY_SLOT[slot];
  return { thresholds: standardThresholds(rankType, program.lifter.sex, program.lifter.bodyweight, program.units), custom: false };
}

function rankForLift(program, slot, trainingMax) {
  const lift = program.lifts[slot];
  const result = { slot: slot, name: liftDisplayName(program, slot), available: false };
  if (!lifterDetailsComplete(program)) return result;
  if (trainingMax === undefined || trainingMax === null) trainingMax = lift.training_max;
  const found = rankThresholdsForLift(program, slot);
  let factor = lift.rank_factor;
  if (!factor || factor <= 0) factor = 1.0;
  const coefficient = found.custom ? 1.0 : ageCoefficient(program.lifter.age);
  const adjusted = trainingMax / factor * coefficient;
  const percentile = strengthPercentile(adjusted, found.thresholds);
  const tier = tierIndexForPercentile(percentile);
  const lower = DEFAULTS.RANK_TIERS[tier].min_percentile;
  let upper = 100;
  let nextTierName = null;
  let trainingMaxForNext = null;
  if (tier + 1 < DEFAULTS.RANK_TIERS.length) {
    upper = DEFAULTS.RANK_TIERS[tier + 1].min_percentile;
    nextTierName = DEFAULTS.RANK_TIERS[tier + 1].name;
    trainingMaxForNext = liftForPercentile(upper, found.thresholds) / coefficient * factor;
  }
  let progress = (percentile - lower) / (upper - lower);
  if (progress < 0) progress = 0;
  if (progress > 1) progress = 1;
  result.available = true;
  result.training_max = trainingMax;
  result.percentile = percentile;
  result.tier = tier;
  result.tier_key = DEFAULTS.RANK_TIERS[tier].key;
  result.tier_name = DEFAULTS.RANK_TIERS[tier].name;
  result.effect = DEFAULTS.RANK_TIERS[tier].effect;
  result.progress = progress;
  result.next_tier_name = nextTierName;
  result.training_max_for_next = trainingMaxForNext;
  result.gap_to_next = trainingMaxForNext === null ? null : Math.max(0, trainingMaxForNext - trainingMax);
  result.thresholds = found.thresholds;
  result.custom_thresholds = found.custom;
  result.rank_factor = factor;
  return result;
}

function allRanks(program) {
  const scheduled = scheduledSlots(program);
  const ranks = [];
  for (const slot of DEFAULTS.ALL_SLOTS) if (scheduled.includes(slot)) ranks.push(rankForLift(program, slot));
  return ranks;
}

// ---------------------------------------------------------------------------
// 7. Progress numbers
// ---------------------------------------------------------------------------
function sessionLabels(program) {
  const labels = ["Start"];
  for (const entry of program.history) labels.push("W" + entry.week + " D" + entry.day);
  return labels;
}

function buildTrainingMaxTable(program) {
  const labels = sessionLabels(program);
  const columns = {};
  for (const slot of DEFAULTS.ALL_SLOTS) {
    const lift = program.lifts[slot];
    const values = [];
    let currentValue = lift.starting_max;
    for (let sessionNumber = 0; sessionNumber < labels.length; sessionNumber++) {
      for (const record of program.tm_history) {
        if (record.slot === slot && record.session === sessionNumber) currentValue = record.training_max;
      }
      values.push(Math.round(currentValue * 10) / 10);
    }
    columns[liftDisplayName(program, slot)] = values;
  }
  return { labels: labels, columns: columns };
}

function buildEstimatedMaxTable(program) {
  const labels = sessionLabels(program);
  const columns = {};
  for (const slot of DEFAULTS.ALL_SLOTS) {
    const lift = program.lifts[slot];
    const values = [null];
    for (const entry of program.history) {
      let estimate = null;
      for (const logged of entry.lifts) {
        if (logged.slot === slot && logged.estimated_1rm !== null && logged.estimated_1rm !== undefined) {
          estimate = Math.round(logged.estimated_1rm * 10) / 10;
        }
      }
      values.push(estimate);
    }
    columns[liftDisplayName(program, slot)] = values;
  }
  return { labels: labels, columns: columns };
}

function calculateSessionVolume(entry) {
  let volume = 0;
  for (const logged of entry.lifts) volume += logged.working_weight * logged.total_reps;
  for (const accessory of entry.accessories) volume += accessory.weight * accessory.sets * accessory.reps;
  return volume;
}

function summaryStats(program) {
  let totalVolume = 0;
  let totalSets = 0;
  for (const entry of program.history) {
    totalVolume += calculateSessionVolume(entry);
    for (const logged of entry.lifts) {
      totalSets += (logged.sets_completed !== null && logged.sets_completed !== undefined) ? logged.sets_completed : logged.sets;
    }
    for (const accessory of entry.accessories) totalSets += accessory.sets;
  }
  return {
    sessions: program.history.length,
    current_week: program.current_week,
    current_day: program.current_day,
    total_volume: totalVolume,
    total_sets: totalSets,
  };
}

const SBS = {
  DEFAULTS, roundToIncrement, nearestPercentageBucket, bucketIndex, lookupByPercentage,
  isDeloadWeek, blockNumber, calculateWorkingWeight, calculateTrainingMaxFromSingle, applyTmChange,
  estimateOneRepMax, buildLiftSettings, resetLiftTablesForVariant, getPrescription,
  getPrescriptionForSlot, describePrescription, ladderIndexForDifference, calculateTmChangePercent,
  formatWeight, formatPercent, plural, describeOutcome, describeTmChange, estimateSessionOneRepMax,
  countTotalReps, todayString, buildDefaultDays, recordTrainingMax, createProgram,
  ensureProgramDefaults, liftDisplayName, scheduledSlots, buildWorkout, logWorkout, advanceToNextDay,
  isCycleFinished, startNewCycle, findLastAccessoryResult, findHistoryEntry, sessionLabels,
  buildTrainingMaxTable, buildEstimatedMaxTable, calculateSessionVolume, summaryStats,
  cleanExerciseName, defaultRankFactor, ageCoefficient, standardThresholds, strengthPercentile,
  liftForPercentile, tierIndexForPercentile, lifterDetailsComplete, rankThresholdsForLift, rankForLift, allRanks,
};

if (typeof module !== "undefined") {
  module.exports = SBS;
} else {
  window.SBS = SBS;
}
})();
