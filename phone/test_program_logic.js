/*
test_program_logic.js - the same checks as test_program_logic.py, for the JavaScript port.

Run in a browser by opening phone/tests.html (no server needed beyond the one
serving the app), or with Node:  node phone/test_program_logic.js
*/
"use strict";
(function () {

const L = (typeof window === "undefined") ? require("./program_logic.js") : window.SBS;
const D = L.DEFAULTS;

const SPREADSHEET_MAXES = {
  squat: 490, bench: 325, deadlift: 525, ohp: 200,
  squat_aux_1: 420, squat_aux_2: 460, bench_aux_1: 310,
  bench_aux_2: 280, deadlift_aux: 500, ohp_aux: 245,
};

function assert(condition, message) {
  if (!condition) throw new Error("Assertion failed: " + (message || ""));
}

function closeTo(actual, expected, tolerance) {
  if (tolerance === undefined) tolerance = 0.01;
  return Math.abs(actual - expected) <= tolerance;
}

function makeProgram(variant, frequency) {
  if (frequency === undefined) frequency = 4;
  const names = variant === D.VARIANT_HYPERTROPHY ? D.HYPERTROPHY_DEFAULT_LIFT_NAMES : D.STRENGTH_DEFAULT_LIFT_NAMES;
  return L.createProgram(variant, "lb", 2.5, frequency, names, SPREADSHEET_MAXES);
}

function testRoundToIncrement() {
  assert(L.roundToIncrement(343, 2.5) === 342.5, "343 -> 342.5");
  assert(L.roundToIncrement(342.6, 5) === 345);
  assert(L.roundToIncrement(341.25, 2.5) === 342.5, "half rounds up");
  assert(L.roundToIncrement(343.75, 2.5) === 345);
  assert(L.roundToIncrement(100.04, 0.1) === 100);
  assert(L.roundToIncrement(100.06, 0.1) === 100.1);
  assert(L.roundToIncrement(123.4, 0) === 123.4);
}

function testPercentageBuckets() {
  assert(D.PERCENTAGE_BUCKETS.length === 21);
  assert(L.nearestPercentageBucket(71) === 70);
  assert(L.nearestPercentageBucket(71.3) === 72.5);
  assert(L.nearestPercentageBucket(49) === 50);
  assert(L.nearestPercentageBucket(120) === 100);
  assert(L.lookupByPercentage(D.STRENGTH_REPS_PER_SET, 70) === 5);
  assert(L.lookupByPercentage(D.ORIGINAL_RIR_CUTOFF, 60) === 4);
}

function testWeekOneSquatOriginal() {
  const program = makeProgram(D.VARIANT_ORIGINAL);
  const p = L.getPrescription(D.VARIANT_ORIGINAL, program.lifts.squat, 1, 2.5);
  assert(p.intensity === 70 && p.working_weight === 342.5 && p.reps_per_set === 5 && p.rir_cutoff === 3, JSON.stringify(p));
  assert(p.lower_set_threshold === 4 && p.upper_set_threshold === 6 && p.is_deload === false);
}

function testSumoAuxiliary() {
  const program = makeProgram(D.VARIANT_ORIGINAL);
  const p = L.getPrescription(D.VARIANT_ORIGINAL, program.lifts.deadlift_aux, 1, 2.5);
  assert(p.intensity === 60 && p.working_weight === 300 && p.reps_per_set === 7 && p.rir_cutoff === 4, JSON.stringify(p));
}

function testWeekTwoSquat() {
  const program = makeProgram(D.VARIANT_ORIGINAL);
  const p = L.getPrescription(D.VARIANT_ORIGINAL, program.lifts.squat, 2, 2.5);
  assert(p.intensity === 75 && p.working_weight === 367.5 && p.reps_per_set === 4);
}

function testVariantTargets() {
  const program = makeProgram(D.VARIANT_RTF);
  const rtf = L.getPrescription(D.VARIANT_RTF, program.lifts.squat, 1, 2.5);
  assert(rtf.sets === 5 && rtf.reps_per_set === 5 && rtf.last_set_rep_target === 10 && rtf.rir_cutoff === undefined);
  const incline = L.getPrescription(D.VARIANT_RTF, program.lifts.bench_aux_2, 1, 2.5);
  assert(incline.working_weight === 167.5 && incline.last_set_rep_target === 14);
  const lsr = L.getPrescription(D.VARIANT_LAST_SET_RIR, program.lifts.squat, 1, 2.5);
  assert(lsr.last_set_rir_target === 3 && lsr.sets === 5);
}

function testHypertrophy() {
  const program = makeProgram(D.VARIANT_HYPERTROPHY);
  const p = L.getPrescription(D.VARIANT_HYPERTROPHY, program.lifts.squat, 1, 2.5);
  assert(p.working_weight === 342.5 && p.sets === 4 && p.reps_per_set === 10 && p.last_set_rep_target === 12);
  const aux = L.getPrescription(D.VARIANT_HYPERTROPHY, program.lifts.squat_aux_1, 1, 2.5);
  assert(aux.intensity === 65 && aux.working_weight === 272.5 && aux.reps_per_set === 12 && aux.last_set_rep_target === 15);
}

function testSingleAt8() {
  const tm = L.calculateTrainingMaxFromSingle(460, 90);
  assert(Math.round(tm) === 511 && closeTo(tm, 511.11));
  assert(L.calculateWorkingWeight(tm, 70, 2.5) === 357.5);
}

function testLadderIndex() {
  const expected = { "-10": 0, "-2": 0, "-1": 1, "0": 2, "1": 3, "2": 4, "3": 5, "4": 6, "5": 7, "12": 7 };
  for (const key of Object.keys(expected)) assert(L.ladderIndexForDifference(Number(key)) === expected[key], key);
}

function testRtfLadder() {
  const program = makeProgram(D.VARIANT_RTF);
  const squat = program.lifts.squat;
  const p = L.getPrescription(D.VARIANT_RTF, squat, 1, 2.5);
  const expected = { 0: -5, 8: -5, 9: -2, 10: 0, 11: 0.5, 12: 1, 13: 1.5, 14: 2, 15: 3, 25: 3 };
  for (const reps of Object.keys(expected)) {
    const change = L.calculateTmChangePercent(D.VARIANT_RTF, squat, p, { last_set_reps: Number(reps) });
    assert(change === expected[reps], reps + " -> " + change);
  }
  const hyp = makeProgram(D.VARIANT_HYPERTROPHY);
  const hp = L.getPrescription(D.VARIANT_HYPERTROPHY, hyp.lifts.squat, 1, 2.5);
  assert(L.calculateTmChangePercent(D.VARIANT_HYPERTROPHY, hyp.lifts.squat, hp, { last_set_reps: 10 }) === -5);
  assert(L.calculateTmChangePercent(D.VARIANT_HYPERTROPHY, hyp.lifts.squat, hp, { last_set_reps: 17 }) === 3);
}

function testLastSetRirLadder() {
  const program = makeProgram(D.VARIANT_LAST_SET_RIR);
  const squat = program.lifts.squat;
  const p = L.getPrescription(D.VARIANT_LAST_SET_RIR, squat, 1, 2.5);
  const cases = [[3, 5, -5], [0, 5, -5], [4, 5, -2], [5, 2, -2], [5, 0, -2], [5, 3, 0], [5, 4, 0.5],
                 [5, 5, 1], [5, 6, 1.5], [5, 7, 2], [5, 8, 3], [5, 12, 3], [6, 3, 0]];
  for (const c of cases) {
    const change = L.calculateTmChangePercent(D.VARIANT_LAST_SET_RIR, squat, p, { sets_completed: c[0], last_set_rir: c[1] });
    assert(change === c[2], JSON.stringify(c) + " -> " + change);
  }
}

function testOriginalThresholds() {
  const program = makeProgram(D.VARIANT_ORIGINAL);
  const squat = program.lifts.squat;
  const p = L.getPrescription(D.VARIANT_ORIGINAL, squat, 1, 2.5);
  const expected = { 0: -5, 3: -5, 4: 0, 5: 0, 6: 0, 7: 2, 12: 2 };
  for (const sets of Object.keys(expected)) {
    assert(L.calculateTmChangePercent(D.VARIANT_ORIGINAL, squat, p, { sets_completed: Number(sets) }) === expected[sets], sets);
  }
  squat.lower_set_threshold = 6; squat.upper_set_threshold = 8; squat.increase_percent = 1; squat.decrease_percent = -3;
  assert(L.calculateTmChangePercent(D.VARIANT_ORIGINAL, squat, p, { sets_completed: 5 }) === -3);
  assert(L.calculateTmChangePercent(D.VARIANT_ORIGINAL, squat, p, { sets_completed: 9 }) === 1);
}

function testDeloads() {
  const terrible = { sets_completed: 0, last_set_rir: 0, last_set_reps: 0 };
  const amazing = { sets_completed: 12, last_set_rir: 12, last_set_reps: 40 };
  for (const variant of D.ALL_VARIANTS) {
    const program = makeProgram(variant);
    for (const slot of ["squat", "deadlift_aux"]) {
      for (const week of [7, 14, 21]) {
        const p = L.getPrescription(variant, program.lifts[slot], week, 2.5);
        assert(p.is_deload === true && p.reps_per_set === D.DELOAD_REPS_PER_SET);
        assert(p.rir_cutoff === undefined && p.last_set_rir_target === undefined && p.last_set_rep_target === undefined);
        assert(L.calculateTmChangePercent(variant, program.lifts[slot], p, terrible) === 0);
        assert(L.calculateTmChangePercent(variant, program.lifts[slot], p, amazing) === 0);
      }
    }
  }
}

function testIntensities() {
  const strength = makeProgram(D.VARIANT_RTF);
  const hyp = makeProgram(D.VARIANT_HYPERTROPHY);
  for (let week = 1; week <= 21; week++) {
    assert(closeTo(strength.lifts.squat.intensities[week - 1] - strength.lifts.squat_aux_1.intensities[week - 1], 10));
    assert(closeTo(hyp.lifts.squat.intensities[week - 1] - hyp.lifts.squat_aux_1.intensities[week - 1], 5));
    if (L.isDeloadWeek(week)) assert(strength.lifts.squat.intensities[week - 1] === 60);
  }
  assert(strength.lifts.squat.intensities[19] === 95 && hyp.lifts.squat.intensities[19] === 82.5);
  assert(L.blockNumber(7) === 1 && L.blockNumber(8) === 2 && L.blockNumber(21) === 3);
}

function testLogWorkoutAndCalendar() {
  const program = makeProgram(D.VARIANT_RTF, 4);
  const slots = L.buildWorkout(program, 1, 1).map(function (e) { return e.slot; });
  assert(JSON.stringify(slots) === JSON.stringify(["squat", "bench_aux_2", "deadlift_aux"]));
  const results = [
    { slot: "squat", last_set_reps: 13, single_at_8: null, notes: "" },
    { slot: "bench_aux_2", last_set_reps: 14, single_at_8: null, notes: "" },
    { slot: "deadlift_aux", last_set_reps: 12, single_at_8: null, notes: "" },
  ];
  const accessories = [{ name: "Barbell Row", kind: "accessory", weight: 135, sets: 3, reps: 10 }];
  const messages = L.logWorkout(program, 1, 1, results, accessories, "felt good", "2026-01-05");
  assert(messages.length === 3 && messages[0].includes("going up 1.5%") && messages[0].includes("beat the target by 3 reps"));
  assert(messages[1].includes("stays at") && messages[2].includes("dropping 5%"));
  assert(closeTo(program.lifts.squat.training_max, 490 * 1.015));
  assert(closeTo(program.lifts.deadlift_aux.training_max, 475));
  assert(program.history.length === 1 && program.history[0].lifts[0].estimated_1rm !== null);
  assert(L.findLastAccessoryResult(program, "barbell row").weight === 135);
  assert(L.findLastAccessoryResult(program, "Face Pull") === null);
  L.advanceToNextDay(program);
  assert(program.current_week === 1 && program.current_day === 2);
  L.advanceToNextDay(program); L.advanceToNextDay(program); L.advanceToNextDay(program);
  assert(program.current_week === 2 && program.current_day === 1);
  const weekTwo = L.getPrescriptionForSlot(program, "squat", 2);
  assert(weekTwo.working_weight === L.roundToIncrement(490 * 1.015 * 0.75, 2.5));
  L.logWorkout(program, 2, 1, [{ slot: "squat", last_set_reps: 8, single_at_8: 460, notes: "" }], [], "", "2026-01-12");
  assert(closeTo(program.lifts.squat.training_max, 511.11));
}

function testFullCycle() {
  for (const variant of D.ALL_VARIANTS) {
    const program = makeProgram(variant, 3);
    for (let week = 1; week <= 21; week++) {
      for (let day = 1; day <= 3; day++) {
        const results = [];
        for (const ex of L.buildWorkout(program, week, day)) {
          results.push({ slot: ex.slot, single_at_8: null, notes: "", sets_completed: ex.sets,
                         last_set_rir: ex.last_set_rir_target || 0, last_set_reps: ex.last_set_rep_target || 0 });
        }
        L.logWorkout(program, week, day, results, [], "", "2026-01-01");
        L.advanceToNextDay(program);
      }
    }
    assert(program.history.length === 63);
    for (const slot of D.ALL_SLOTS) assert(closeTo(program.lifts[slot].training_max, SPREADSHEET_MAXES[slot]), variant + " " + slot);
    assert(L.isCycleFinished(program));
    L.startNewCycle(program);
    assert(program.current_week === 1 && program.current_day === 1);
  }
  const program = makeProgram(D.VARIANT_RTF, 3);
  for (let week = 1; week <= 21; week++) {
    for (let day = 1; day <= 3; day++) {
      const results = [];
      for (const ex of L.buildWorkout(program, week, day)) {
        results.push({ slot: ex.slot, last_set_reps: (ex.last_set_rep_target || 0) + 5, single_at_8: null, notes: "" });
      }
      L.logWorkout(program, week, day, results, [], "", "2026-01-01");
      L.advanceToNextDay(program);
    }
  }
  assert(closeTo(program.lifts.squat.training_max, 490 * Math.pow(1.03, 18), 0.5));
  const table = L.buildTrainingMaxTable(program);
  assert(table.labels[0] === "Start" && table.labels[1] === "W1 D1" && table.labels.length === 64);
  assert(table.columns["Squat"][0] === 490);
  assert(L.summaryStats(program).sessions === 63);
}

function testSplits() {
  for (const style of D.SPLIT_STYLES) {
    for (const frequency of D.FREQUENCY_CHOICES) {
      const split = D.SPLITS_BY_STYLE[style][frequency];
      const scheduled = [];
      for (const day of split) for (const slot of day) scheduled.push(slot);
      assert(split.length === frequency);
      for (const slot of D.MAIN_SLOTS) assert(scheduled.filter(function (s) { return s === slot; }).length === 1);
      if (frequency === 2) assert(scheduled.length === 8);
      else assert(scheduled.slice().sort().join() === D.ALL_SLOTS.slice().sort().join());
    }
  }
  const lower = L.buildDefaultDays(4, [], D.SPLIT_UPPER_LOWER);
  assert(lower[0].slots.join() === "squat,deadlift_aux,squat_aux_2" && lower[2].slots.join() === "deadlift,squat_aux_1");
  const program = L.createProgram(D.VARIANT_RTF, "lb", 5, 5, D.STRENGTH_DEFAULT_LIFT_NAMES, SPREADSHEET_MAXES, [], D.SPLIT_UPPER_LOWER);
  assert(program.split_style === D.SPLIT_UPPER_LOWER && program.days[2].slots.join() === "deadlift");
  const old = JSON.parse(JSON.stringify(program));
  old.split_style = "something_removed";
  L.ensureProgramDefaults(old);
  assert(old.split_style === D.SPLIT_FULL_BODY);
  const preset = D.SETUP_PRESETS[D.PRESET_ANDY];
  assert(preset.accessories.length === preset.frequency);
  for (const slot of D.ALL_SLOTS) {
    if (preset.skipped_slots.includes(slot)) assert(preset.days[slot] === undefined);
    else assert(preset.days[slot] >= 1 && preset.days[slot] <= preset.frequency, slot);
  }
}

function testMessages() {
  assert(L.formatWeight(342.5, "lb") === "342.5 lb" && L.formatWeight(300, "kg") === "300 kg");
  assert(L.formatPercent(1.5) === "1.5%" && L.formatPercent(-5) === "-5%");
  const program = makeProgram(D.VARIANT_RTF);
  const p = L.getPrescription(D.VARIANT_RTF, program.lifts.squat, 1, 2.5);
  assert(L.describeTmChange(D.VARIANT_RTF, p, { last_set_reps: 9 }, -2, 480.2, "lb") ===
         "You fell 1 rep short of the target of 10 - training max dropping 2% to 480.2 lb");
  assert(L.describeTmChange(D.VARIANT_RTF, p, { last_set_reps: 10 }, 0, 490, "lb") ===
         "You hit the target of 10 reps exactly - training max stays at 490 lb");
  assert(L.describePrescription(D.VARIANT_RTF, p) === "4 sets of 5, then 1 set for as many reps as possible (target 10)");
  const original = L.getPrescription(D.VARIANT_ORIGINAL, program.lifts.squat, 1, 2.5);
  assert(L.describePrescription(D.VARIANT_ORIGINAL, original) === "Sets of 5 until you reach 3 RIR (target 4-6 sets)");
  assert(L.describePrescription(D.VARIANT_ORIGINAL, L.getPrescription(D.VARIANT_ORIGINAL, program.lifts.squat, 7, 2.5)) === "Deload: 5 easy sets of 5, no target");
}

function testSkippedSlotsAndDisplayNames() {
  const names = Object.assign({}, D.STRENGTH_DEFAULT_LIFT_NAMES);
  let program = L.createProgram(D.VARIANT_RTF, "lb", 5, 4, names, SPREADSHEET_MAXES, ["ohp", "squat_aux_2"]);
  for (const day of program.days) assert(!day.slots.includes("ohp") && !day.slots.includes("squat_aux_2"));
  assert(program.days[3].slots.length === 0 && program.lifts.ohp !== undefined);
  assert(L.buildWorkout(program, 1, 4).length === 0);
  names.squat_aux_1 = "Squat";
  names.squat_aux_2 = "squat";
  program = L.createProgram(D.VARIANT_RTF, "lb", 5, 4, names, SPREADSHEET_MAXES);
  assert(L.liftDisplayName(program, "squat") === "Squat (main)");
  assert(L.liftDisplayName(program, "squat_aux_1") === "Squat (aux 1)");
  assert(L.liftDisplayName(program, "bench") === "Bench Press");
  const table = L.buildTrainingMaxTable(program);
  assert(Object.keys(table.columns).length === 10 && table.columns["Squat (aux 1)"] !== undefined);
  const stripped = JSON.parse(JSON.stringify(program));
  delete stripped.image_choices;
  delete stripped.deload_reps_per_set;
  stripped.days[0].upper_back = "Pull-Up";
  L.ensureProgramDefaults(stripped);
  assert(JSON.stringify(stripped.image_choices) === "{}" && stripped.deload_reps_per_set === D.DELOAD_REPS_PER_SET);
  assert(stripped.days[0].accessories[0] === "Pull-Up" && stripped.days[0].upper_back === undefined);
  assert(L.buildDefaultDays(4)[0].accessories[0] === D.UPPER_BACK_EXERCISES[0]);
}


function testRankStandards() {
  const thresholds = L.standardThresholds("squat", "male", 180, "lb");
  assert(thresholds.map(Math.round).join() === "135,225,270,360,450", thresholds.join());
  for (let i = 0; i < 5; i++) assert(closeTo(L.strengthPercentile(thresholds[i], thresholds), D.STANDARD_PERCENTILES[i]));
  assert(closeTo(L.strengthPercentile(300, thresholds), 60));
  assert(closeTo(L.strengthPercentile(67.5, thresholds), 2.5));
  const step = thresholds[4] - thresholds[3];
  assert(closeTo(L.strengthPercentile(thresholds[4] + step, thresholds), 97.5));
  assert(closeTo(L.strengthPercentile(thresholds[4] + 3 * step, thresholds), 99.375));
  for (const percentile of [2.5, 5, 30, 60, 80, 95, 97.5, 99]) {
    assert(closeTo(L.strengthPercentile(L.liftForPercentile(percentile, thresholds), thresholds), percentile, 0.001), String(percentile));
  }
  const heavier = L.standardThresholds("squat", "male", 220, "lb");
  assert(heavier[4] > 450 && heavier[4] < 450 * 220 / 180);
  const kilograms = L.standardThresholds("squat", "male", 180 * D.KG_PER_LB, "kg");
  assert(closeTo(kilograms[4] / D.KG_PER_LB, 450, 0.01));
  const names = { 0: "Mortal", 4.9: "Mortal", 5: "Initiate", 12.5: "Vanguard", 20: "Warden", 35: "Colossus", 50: "Titan",
                  65: "Atlas", 80: "Demigod", 95: "Transcendent", 97.5: "Legend I", 98.75: "Legend II", 99.4: "Legend III", 100: "Legend III" };
  for (const key of Object.keys(names)) assert(D.RANK_TIERS[L.tierIndexForPercentile(Number(key))].name === names[key], key);
  assert(L.ageCoefficient(30) === 1 && L.ageCoefficient(60) === 1.34 && L.ageCoefficient(16) === 1.13 && L.ageCoefficient(0) === 1);
  assert(L.defaultRankFactor("Front Squat") === 0.85 && L.defaultRankFactor("Squat") === 1);
}

function testRankForLiftAndChanges() {
  const program = makeProgram(D.VARIANT_RTF);
  assert(L.rankForLift(program, "squat").available === false);
  program.lifter = { sex: "male", age: 30, bodyweight: 180 };
  const rank = L.rankForLift(program, "squat");
  assert(rank.available && rank.tier_name === "Transcendent" && rank.next_tier_name === "Legend I", JSON.stringify(rank));
  assert(closeTo(rank.training_max_for_next, 540, 0.01) && closeTo(rank.gap_to_next, 50, 0.01) && rank.effect === "electric");
  assert(L.rankForLift(program, "squat_aux_1").tier_name === "Transcendent");
  program.lifter.age = 60;
  assert(L.rankForLift(program, "squat").percentile > rank.percentile);
  program.lifts.squat.rank_thresholds = [200, 300, 400, 500, 600];
  const custom = L.rankForLift(program, "squat");
  assert(custom.custom_thresholds === true && custom.tier_name === "Atlas" && closeTo(custom.percentile, 77) && closeTo(custom.progress, 0.8));
  assert(L.allRanks(program).length === 10);

  const fresh = makeProgram(D.VARIANT_RTF);
  fresh.lifter = { sex: "male", age: 30, bodyweight: 180 };
  let messages = L.logWorkout(fresh, 1, 1, [{ slot: "squat", last_set_reps: 10, single_at_8: 500, notes: "" }], [], "", "2026-01-05");
  assert(messages[messages.length - 1] === "Rank up! Squat: Transcendent -> Legend I", messages.join(" | "));
  assert(fresh.history[0].rank_changes[0].to_name === "Legend I" && fresh.history[0].lifts[0].rank_before === 8 && fresh.history[0].lifts[0].rank_after === 9);
  messages = L.logWorkout(fresh, 2, 1, [{ slot: "squat", last_set_reps: 5, single_at_8: null, notes: "" }], [], "", "2026-01-12");
  assert(messages[messages.length - 1] === "Rank down: Squat is now Transcendent");
  const plain = makeProgram(D.VARIANT_RTF);
  messages = L.logWorkout(plain, 1, 1, [{ slot: "squat", last_set_reps: 15, single_at_8: null, notes: "" }], [], "", "2026-01-05");
  assert(messages.length === 1 && plain.history[0].rank_changes.length === 0);
}

function runAllTests(print) {
  const tests = [testRoundToIncrement, testPercentageBuckets, testWeekOneSquatOriginal, testSumoAuxiliary,
                 testWeekTwoSquat, testVariantTargets, testHypertrophy, testSingleAt8, testLadderIndex, testRtfLadder,
                 testLastSetRirLadder, testOriginalThresholds, testDeloads, testIntensities, testLogWorkoutAndCalendar,
                 testFullCycle, testSplits, testMessages, testSkippedSlotsAndDisplayNames,
                 testRankStandards, testRankForLiftAndChanges];
  let failed = 0;
  for (const test of tests) {
    try {
      test();
      print("PASS " + test.name);
    } catch (error) {
      failed++;
      print("FAIL " + test.name + ": " + error.message);
    }
  }
  print(failed === 0 ? "All " + tests.length + " tests passed." : failed + " test(s) failed.");
  return failed === 0;
}

if (typeof module !== "undefined") {
  runAllTests(console.log);
} else {
  window.runAllTests = runAllTests;
}
})();
