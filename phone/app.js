/*
app.js - the phone app's screens: setup, workout, progress, settings.

Everything runs in the browser. The program dictionary is the same JSON the
Python app uses; it is kept in localStorage and can be shared as a file.
The math lives in program_logic.js (a port of program_logic.py); this file
only draws screens and reads inputs, like app.py does for Streamlit.
*/
"use strict";
(function () {
  const L = window.SBS;
  const D = L.DEFAULTS;
  const LIB = window.SBS_LIBRARY;
  const STORAGE_KEY = "sbs_trainer_program";
  const BACKUP_KEY = "sbs_trainer_last_backup";
  // Where the catalog and pictures live: "./data/" when the phone app is
  // published on its own, "../data/" when it sits inside the full project.
  // start() checks which one exists.
  let DATA_BASE = "./data/";
  const OTHER_OPTION = "Other (type a name)";
  const SKIP_OPTION = "Skip this slot";
  const CHART_COLORS = ["#ff5a4e", "#4e9dff", "#46c57f", "#f2c14e", "#c17bff", "#ff9c4e", "#4ee1d9", "#ff6fb1", "#9ad34e", "#8f9bb3"];

  const state = {
    program: null,
    page: "workout",
    catalog: [],
    saveMessages: [],
    draft: null,
    setup: null,
    rankQueue: [],
    ui: { settingsLift: "squat", tablesLift: "squat", pictureName: "", chart: "Main lifts", open: { general: true } },
  };

  // -------------------------------------------------------------------------
  // Small helpers
  // -------------------------------------------------------------------------
  function esc(text) {
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function $(selector) { return document.querySelector(selector); }
  function $all(selector) { return Array.prototype.slice.call(document.querySelectorAll(selector)); }
  function toast(text) {
    const box = $("#toast");
    box.textContent = text;
    box.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { box.hidden = true; }, 2600);
  }
  function numberValue(element, fallback) {
    const value = parseFloat(element.value);
    return isNaN(value) ? fallback : value;
  }
  function ordinal(number) {
    number = Math.round(number);
    const remainder = number % 100;
    let suffix = "th";
    if (remainder < 10 || remainder > 20) suffix = { 1: "st", 2: "nd", 3: "rd" }[number % 10] || "th";
    return number + suffix;
  }
  function numberOr(value, fallback) {
    const parsed = parseFloat(value);
    return isNaN(parsed) ? fallback : parsed;
  }

  // ---- Rank badges (just for fun) ----
  const TIER_COLORS = { mortal: "#8a8f9c", initiate: "#9fb3cc", vanguard: "#4e9dff", warden: "#2dd4bf", colossus: "#46c57f",
                        titan: "#b07cff", atlas: "#f5d90a", demigod: "#ff9c3f", transcendent: "#ff4d5a",
                        legend_1: "#c084fc", legend_2: "#c084fc", legend_3: "#c084fc" };
  const RAINBOW = "linear-gradient(90deg, #7dd3fc, #c084fc, #f472b6, #fde68a, #86efac)";
  const RAINBOW_STOPS = ["#7dd3fc", "#c084fc", "#f472b6", "#fde68a", "#86efac"];
  function isLegend(tierKey) { return String(tierKey).indexOf("legend") === 0; }
  function tierNameHtml(tierKey, tierName) {
    // Legend names shimmer through the rainbow; every other tier uses its colour.
    if (isLegend(tierKey)) return '<span class="rainbow">' + esc(tierName) + "</span>";
    return '<span style="color:' + tierColor(tierKey) + '">' + esc(tierName) + "</span>";
  }
  function starPoints(centerX, centerY, outerRadius, innerRadius, spikes) {
    const points = [];
    for (let i = 0; i < spikes * 2; i++) {
      const radius = i % 2 === 0 ? outerRadius : innerRadius;
      const angle = -Math.PI / 2 + i * Math.PI / spikes;
      points.push((centerX + radius * Math.cos(angle)).toFixed(1) + "," + (centerY + radius * Math.sin(angle)).toFixed(1));
    }
    return points.join(" ");
  }
  function rainbowGradientDefs() {
    let stops = "";
    for (let i = 0; i < RAINBOW_STOPS.length; i++) {
      stops += '<stop offset="' + Math.round(i * 100 / (RAINBOW_STOPS.length - 1)) + '%" stop-color="' + RAINBOW_STOPS[i] + '"/>';
    }
    return '<defs><linearGradient id="legend-rainbow" x1="0" y1="0" x2="1" y2="1">' + stops + "</linearGradient></defs>";
  }
  const TIER_GLYPHS = { mortal: "M", initiate: "I", vanguard: "V", warden: "W", colossus: "C", titan: "T", atlas: "A",
                        demigod: "D", transcendent: "\u2726", legend_1: "L", legend_2: "L", legend_3: "L" };
  function tierColor(tierKey) { return TIER_COLORS[tierKey] || "#8a8f9c"; }
  function badgeShape(tierKey) {
    if (tierKey === "transcendent") return "star";
    if (isLegend(tierKey)) return "gem";
    return "hex";
  }
  function badgeSvg(tierKey, color) {
    if (tierKey === "transcendent") {
      // An eight-pointed starburst with a glowing core.
      return '<svg viewBox="0 0 100 100" aria-hidden="true">' +
        '<polygon points="' + starPoints(50, 50, 47, 31, 8) + '" fill="rgba(0,0,0,0.45)" stroke="' + color + '" stroke-width="4" stroke-linejoin="round"/>' +
        '<polygon points="' + starPoints(50, 50, 30, 20, 8) + '" fill="' + color + '" fill-opacity="0.18"/>' +
        '<circle cx="50" cy="50" r="13" fill="rgba(0,0,0,0.55)" stroke="' + color + '" stroke-width="3"/>' +
        '<circle cx="50" cy="50" r="5" fill="' + color + '"/></svg>';
    }
    if (isLegend(tierKey)) {
      // A faceted gem in rainbow colours with the Legend step inside.
      const numeral = { legend_1: "I", legend_2: "II", legend_3: "III" }[tierKey];
      return '<svg viewBox="0 0 100 100" aria-hidden="true">' + rainbowGradientDefs() +
        '<polygon points="26,10 74,10 94,38 50,95 6,38" fill="rgba(0,0,0,0.5)" stroke="url(#legend-rainbow)" stroke-width="4" stroke-linejoin="round"/>' +
        '<polygon points="26,10 74,10 94,38 50,95 6,38" fill="url(#legend-rainbow)" fill-opacity="0.3"/>' +
        '<polyline points="6,38 94,38" stroke="url(#legend-rainbow)" stroke-width="2" fill="none" opacity="0.9"/>' +
        '<polyline points="26,10 38,38 50,95" stroke="url(#legend-rainbow)" stroke-width="2" fill="none" opacity="0.7"/>' +
        '<polyline points="74,10 62,38 50,95" stroke="url(#legend-rainbow)" stroke-width="2" fill="none" opacity="0.7"/>' +
        '<text x="50" y="57" text-anchor="middle" font-size="26" font-weight="800" fill="#ffffff" stroke="rgba(0,0,0,0.6)" stroke-width="1">' + numeral + "</text></svg>";
    }
    const glyph = TIER_GLYPHS[tierKey] || "?";
    return '<svg viewBox="0 0 100 100" aria-hidden="true">' +
      '<polygon points="50,4 92,27 92,73 50,96 8,73 8,27" fill="rgba(0,0,0,0.45)" stroke="' + color + '" stroke-width="5" stroke-linejoin="round"/>' +
      '<polygon points="50,16 82,33 82,67 50,84 18,67 18,33" fill="' + color + '" fill-opacity="0.16"/>' +
      '<text x="50" y="63" text-anchor="middle" font-size="40" font-weight="800" fill="' + color + '">' + glyph + "</text></svg>";
  }
  function rankBadgeHtml(rank, size) {
    if (!rank || !rank.available) {
      return '<span class="badge badge-locked" style="--size:' + size + 'px;--tier:#6b7280" title="Enter your details under Ranks">' + badgeSvg("", "#6b7280") + "</span>";
    }
    const color = tierColor(rank.tier_key);
    return '<span class="badge shape-' + badgeShape(rank.tier_key) + ' effect-' + rank.effect + '" style="--size:' + size + 'px;--tier:' + color + '" title="' + esc(rank.tier_name) + '">' + badgeSvg(rank.tier_key, color) + "</span>";
  }
  function rankInlineHtml(slot) {
    if (!state.program || !L.lifterDetailsComplete(state.program)) return "";
    const rank = L.rankForLift(state.program, slot);
    return '<div class="rank-inline">' + rankBadgeHtml(rank, 30).replace('class="badge ', 'class="badge quiet ') + tierNameHtml(rank.tier_key, rank.tier_name) + "</div>";
  }
  function options(list, selected) {
    let html = "";
    for (const item of list) {
      html += '<option value="' + esc(item) + '"' + (item === selected ? " selected" : "") + ">" + esc(item) + "</option>";
    }
    return html;
  }
  function variantOptions(selected) {
    let html = "";
    for (const variant of D.ALL_VARIANTS) {
      html += '<option value="' + variant + '"' + (variant === selected ? " selected" : "") + ">" + esc(D.VARIANT_NAMES[variant]) + "</option>";
    }
    return html;
  }
  function imageUrl(name) {
    const chosen = state.program ? (state.program.image_choices[name] || "") : "";
    return LIB.findImageUrl(name, state.catalog, chosen, DATA_BASE);
  }
  function imageTag(name, className) {
    return '<img class="' + className + '" src="' + esc(imageUrl(name)) + '" alt="" loading="lazy" data-zoom="1" data-name="' + esc(name) + '" ' +
      "onerror=\"this.onerror=null;this.src='" + DATA_BASE + "images/placeholder.png'\">";
  }
  function openImageViewer(source, name) {
    // The library pictures are two frames side by side (start and finish);
    // show each frame at full width, stacked, so details are twice as big.
    closeImageViewer();
    const overlay = document.createElement("div");
    overlay.id = "image-overlay";
    overlay.className = "image-overlay";
    overlay.setAttribute("data-action", "close-image");
    const isPlaceholder = source.indexOf("placeholder.png") !== -1;
    let frames;
    if (isPlaceholder) {
      frames = '<img class="frame-single" src="' + esc(source) + '" alt="">';
    } else {
      frames = '<div class="frame" style="background-image:url(\'' + esc(source) + '\')"></div><p class="frame-label">Start</p>' +
        '<div class="frame second" style="background-image:url(\'' + esc(source) + '\')"></div><p class="frame-label">Finish</p>';
    }
    overlay.innerHTML = '<div class="image-sheet"><div class="image-title">' + esc(name) + '</div>' + frames +
      '<p class="muted small" style="text-align:center">Pinch to zoom further · tap to close</p></div>';
    document.body.appendChild(overlay);
  }
  function closeImageViewer() {
    const existing = $("#image-overlay");
    if (existing) existing.remove();
  }
  function slotLabel(slot) {
    return L.liftDisplayName(state.program, slot) + " · " + D.SLOT_LABELS[slot];
  }
  function programExerciseNames() {
    const names = [];
    for (const slot of D.ALL_SLOTS) names.push(state.program.lifts[slot].name);
    for (const day of state.program.days) {
      for (const name of day.accessories) if (!names.includes(name)) names.push(name);
    }
    return names;
  }

  // -------------------------------------------------------------------------
  // Storage
  // -------------------------------------------------------------------------
  function loadProgram() {
    try {
      const text = localStorage.getItem(STORAGE_KEY);
      if (!text) return null;
      const program = JSON.parse(text);
      L.ensureProgramDefaults(program);
      return program;
    } catch (error) {
      return null;
    }
  }
  function saveProgram() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.program));
  }
  function replaceProgram(program) {
    state.program = program;
    state.draft = null;
    state.saveMessages = [];
    localStorage.removeItem(BACKUP_KEY);   // the backup record belonged to the previous program
    if (program) {
      L.ensureProgramDefaults(program);
      saveProgram();
      precacheProgramImages();
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }
  function backupStatus() {
    // How long it has been since the log was last exported.
    let record = null;
    try { record = JSON.parse(localStorage.getItem(BACKUP_KEY)); } catch (error) { record = null; }
    const sessions = state.program ? state.program.history.length : 0;
    let sessionsSince = sessions;
    let daysSince = null;
    if (record) {
      sessionsSince = Math.max(0, sessions - record.sessions);
      daysSince = Math.floor((Date.now() - new Date(record.date).getTime()) / 86400000);
    }
    return { sessionsSince: sessionsSince, daysSince: daysSince };
  }
  function recordBackup() {
    localStorage.setItem(BACKUP_KEY, JSON.stringify({ date: new Date().toISOString(), sessions: state.program.history.length }));
  }
  function importFileHtml(label) {
    // A file picker that reads a backup JSON back in (handled in bindEvents).
    return '<label class="secondary" style="margin:0">' + esc(label) + '<input type="file" accept="application/json,.json" id="import-file"></label>';
  }
  function lastBackupText() {
    const status = backupStatus();
    if (status.daysSince === null) return "No backup file has been made from this phone yet.";
    if (status.daysSince === 0) return "Last backup today, " + status.sessionsSince + " workout(s) logged since.";
    return "Last backup " + status.daysSince + " day(s) ago, " + status.sessionsSince + " workout(s) logged since.";
  }
  function precacheProgramImages() {
    // Ask for every picture the program uses once, so the service worker
    // stores them and they show up later with no connection.
    if (!state.program || !("serviceWorker" in navigator)) return;
    fetch(DATA_BASE + "images/placeholder.png").catch(function () {});
    for (const name of programExerciseNames()) {
      fetch(imageUrl(name)).catch(function () {});
    }
  }

  // -------------------------------------------------------------------------
  // Setup page
  // -------------------------------------------------------------------------
  function newSetupDraft() {
    return { preset: D.PRESET_SBS, variant: D.VARIANT_RTF, units: "lb", rounding: 5, frequency: 4, splitStyle: D.SPLIT_FULL_BODY, sameLifts: false, picks: {}, days: {}, assignments: null,
             lifter: { sex: "", age: "", bodyweight: "" } };
  }
  function applyPreset(key) {
    // Fill the whole setup form from a preset; every field stays editable afterwards.
    const fresh = newSetupDraft();
    fresh.preset = key;
    const preset = D.SETUP_PRESETS[key];
    if (preset) {
      fresh.variant = preset.variant;
      fresh.units = preset.units;
      fresh.rounding = preset.rounding_increment;
      fresh.frequency = preset.frequency;
      fresh.splitStyle = preset.split_style;
      fresh.sameLifts = preset.same_lifts;
      for (const slot of Object.keys(preset.lift_names)) {
        fresh.picks[slot] = { choice: preset.lift_names[slot], typed: "", max: D.DEFAULT_STARTING_MAXES[preset.units][slot] };
      }
      for (const slot of preset.skipped_slots) {
        fresh.picks[slot] = { choice: SKIP_OPTION, typed: "", max: D.DEFAULT_STARTING_MAXES[preset.units][slot] };
      }
      fresh.assignments = Object.assign({}, preset.days);
      for (let dayIndex = 0; dayIndex < preset.accessories.length; dayIndex++) {
        fresh.days[preset.frequency + "-" + dayIndex] = { accessories: preset.accessories[dayIndex].join(", ") };
      }
    }
    state.setup = fresh;
  }
  function setupDefaultNames() {
    return state.setup.variant === D.VARIANT_HYPERTROPHY ? D.HYPERTROPHY_DEFAULT_LIFT_NAMES : D.STRENGTH_DEFAULT_LIFT_NAMES;
  }
  function setupPick(slot) {
    const setup = state.setup;
    if (!setup.picks[slot]) {
      setup.picks[slot] = { choice: setupDefaultNames()[slot], typed: "", max: D.DEFAULT_STARTING_MAXES[setup.units][slot] };
    }
    return setup.picks[slot];
  }
  function setupDay(dayIndex) {
    const setup = state.setup;
    const key = setup.frequency + "-" + dayIndex;
    if (!setup.days[key]) {
      // A row or pull-up is suggested first because the main lifts include no pulling.
      setup.days[key] = { accessories: D.UPPER_BACK_EXERCISES[dayIndex % D.UPPER_BACK_EXERCISES.length] };
    }
    return setup.days[key];
  }
  function slotsUsedBySplit(frequency, splitStyle) {
    const used = [];
    for (const day of D.SPLITS_BY_STYLE[splitStyle][frequency]) for (const slot of day) used.push(slot);
    return used;
  }
  function splitStyleRadiosHtml(selected, dataAttribute) {
    let html = "";
    for (const style of D.SPLIT_STYLES) {
      html += '<label class="variant-option"><input type="radio" name="split-style" ' + dataAttribute + ' value="' + style + '"' +
        (style === selected ? " checked" : "") + ">" + esc(D.SPLIT_STYLE_NAMES[style]) +
        '<span class="desc">' + esc(D.SPLIT_STYLE_DESCRIPTIONS[style]) + "</span></label>";
    }
    return html;
  }
  function resolveSetup() {
    // Turn the setup draft into lift names, maxes and skipped slots.
    const setup = state.setup;
    const names = {};
    const maxes = {};
    const skipped = [];
    const used = slotsUsedBySplit(setup.frequency, setup.splitStyle);
    const defaults = setupDefaultNames();
    for (const slot of D.ALL_SLOTS) {
      names[slot] = defaults[slot];
      maxes[slot] = D.DEFAULT_STARTING_MAXES[setup.units][slot];
      if (!used.includes(slot)) continue;
      if (setup.sameLifts && D.PARENT_SLOT[slot]) {
        const parent = D.PARENT_SLOT[slot];
        names[slot] = names[parent];
        maxes[slot] = maxes[parent];
        if (skipped.includes(parent)) skipped.push(slot);
        continue;
      }
      const pick = setupPick(slot);
      if (pick.choice === SKIP_OPTION) { skipped.push(slot); continue; }
      if (pick.choice === OTHER_OPTION) names[slot] = pick.typed.trim() || defaults[slot];
      else names[slot] = pick.choice;
      maxes[slot] = pick.max;
    }
    return { names: names, maxes: maxes, skipped: skipped };
  }
  function trainedSlotsInOrder(resolved) {
    // The slots that will actually be trained, in the standard slot order.
    const setup = state.setup;
    const used = slotsUsedBySplit(setup.frequency, setup.splitStyle);
    return D.ALL_SLOTS.filter(function (slot) { return used.includes(slot) && !resolved.skipped.includes(slot); });
  }
  function currentAssignments(resolved) {
    // Which day (1-based) each trained slot lands on: the split style's layout,
    // overridden by anything the user changed in the day editor.
    const setup = state.setup;
    const assignments = {};
    const plans = L.buildDefaultDays(setup.frequency, resolved.skipped, setup.splitStyle);
    for (let dayIndex = 0; dayIndex < plans.length; dayIndex++) {
      for (const slot of plans[dayIndex].slots) assignments[slot] = dayIndex + 1;
    }
    if (setup.assignments) {
      for (const slot of Object.keys(setup.assignments)) {
        if (setup.assignments[slot] >= 1 && setup.assignments[slot] <= setup.frequency) assignments[slot] = setup.assignments[slot];
      }
    }
    return assignments;
  }
  function plansFromAssignments(assignments, resolved) {
    // Turn the slot -> day choices into day plans (accessory defaults come from the style's layout).
    const setup = state.setup;
    const plans = L.buildDefaultDays(setup.frequency, resolved.skipped, setup.splitStyle);
    const trained = trainedSlotsInOrder(resolved);
    for (let dayIndex = 0; dayIndex < plans.length; dayIndex++) {
      plans[dayIndex].slots = trained.filter(function (slot) { return assignments[slot] === dayIndex + 1; });
    }
    return plans;
  }
  function setupSlotName(slot, resolved) {
    // The lift's name, marked "(lighter)" when an auxiliary slot repeats its main lift.
    const parent = D.PARENT_SLOT[slot];
    if (parent && resolved.names[slot] === resolved.names[parent]) return resolved.names[slot] + " (lighter)";
    return resolved.names[slot];
  }
  function dayPlanLinesHtml(plans, resolved) {
    let html = "";
    for (let dayIndex = 0; dayIndex < plans.length; dayIndex++) {
      const names = plans[dayIndex].slots.map(function (slot) { return setupSlotName(slot, resolved); });
      html += '<p class="muted"><strong>Day ' + (dayIndex + 1) + ":</strong> " + (names.length ? esc(names.join(", ")) : "no main lifts, only accessories") + "</p>";
    }
    return html;
  }
  function renderSetup() {
    if (!state.setup) state.setup = newSetupDraft();
    const setup = state.setup;
    const resolved = resolveSetup();
    const used = slotsUsedBySplit(setup.frequency, setup.splitStyle);
    let html = "<h1>Set up a program</h1>";
    if (state.program) html += '<div class="banner warn">You already have a program. Creating a new one replaces it.</div>';
    else html += '<div class="card"><strong>Already have a backup file?</strong><p class="muted">Restore it instead of starting over. Pick the newest sbs_program file from Files or iCloud Drive.</p><div class="actions" style="margin:8px 0 0">' + importFileHtml("Restore from a backup file") + "</div></div>";

    html += "<h3>Start from</h3>";
    for (const key of D.PRESET_KEYS) {
      html += '<label class="variant-option"><input type="radio" name="preset" data-setup="preset" value="' + key + '"' +
        (key === setup.preset ? " checked" : "") + ">" + esc(D.PRESET_NAMES[key]) +
        '<span class="desc">' + esc(D.PRESET_DESCRIPTIONS[key]) + "</span></label>";
    }
    html += '<p class="muted">A preset only fills in the form below. The main lifts always follow the program\'s intensities, reps, targets and training-max rules.</p>';

    html += "<h3>1. Program variant</h3>";
    for (const variant of D.ALL_VARIANTS) {
      html += '<label class="variant-option"><input type="radio" name="variant" data-setup="variant" value="' + variant + '"' +
        (variant === setup.variant ? " checked" : "") + ">" + esc(D.VARIANT_NAMES[variant]) +
        '<span class="desc">' + esc(D.VARIANT_DESCRIPTIONS[variant]) + "</span></label>";
    }

    html += '<h3>2. Units and rounding</h3><div class="row"><label>Units<select data-setup="units">' + options(D.UNIT_CHOICES, setup.units) +
      '</select></label><label>Rounding increment<select data-setup="rounding">' + options(D.ROUNDING_CHOICES.map(String), String(setup.rounding)) +
      '</select></label></div><p class="muted">5 for pound plates, 2.5 for kilo plates, 0.1 to round in your head.</p>';

    html += '<h3>3. About you (for ranks, optional)</h3><p class="muted">Ranks compare each lift with strength standards for lifters of your sex, age and bodyweight. Just for fun; it changes nothing in the program. Leave it blank to skip, or fill it in later under Ranks.</p>';
    html += '<div class="row"><label>Sex<select data-setup="sex"><option value=""' + (setup.lifter.sex === "" ? " selected" : "") + ">Not set</option>";
    for (const sex of D.SEX_CHOICES) html += '<option value="' + sex + '"' + (setup.lifter.sex === sex ? " selected" : "") + ">" + esc(D.SEX_NAMES[sex]) + "</option>";
    html += '</select></label><label>Age<input type="number" inputmode="numeric" min="10" max="100" data-setup="age" value="' + esc(setup.lifter.age) + '"></label>' +
      '<label>Bodyweight (' + setup.units + ')<input type="number" inputmode="decimal" step="0.5" data-setup="bodyweight" value="' + esc(setup.lifter.bodyweight) + '"></label></div>';

    html += '<h3>4. Training days and split</h3><label>Days per week<select data-setup="frequency">' + options(D.FREQUENCY_CHOICES.map(String), String(setup.frequency)) + "</select></label>";
    html += '<p class="muted" style="margin-top:12px">Split style</p>' + splitStyleRadiosHtml(setup.splitStyle, 'data-setup="splitStyle"');
    html += '<p class="muted">Every lift is trained once a week, so more days means fewer lifts per day. The split style only decides which day each lift lands on; you can change any of that in step 6.</p>';

    html += "<h3>5. Lifts and starting maxes</h3><p class=\"muted\">Real or estimated one-rep maxes. Conservative numbers are fine: the program corrects a low guess within a few weeks.</p>";
    html += '<label class="check"><input type="checkbox" data-setup="sameLifts"' + (setup.sameLifts ? " checked" : "") + "> Keep it simple: use my four main lifts for the auxiliary slots too</label>";
    html += '<p class="muted">Choose "' + SKIP_OPTION + '" to leave a lift out; you can add it back in Settings.</p>';
    for (const slot of D.ALL_SLOTS) {
      if (!used.includes(slot)) continue;
      if (setup.sameLifts && D.PARENT_SLOT[slot]) {
        const skippedText = resolved.skipped.includes(slot) ? "skipped" : esc(resolved.names[slot]) + ", same max, trained a little lighter";
        html += '<p class="muted"><strong>' + esc(D.SLOT_LABELS[slot]) + ":</strong> " + skippedText + "</p>";
        continue;
      }
      const pick = setupPick(slot);
      const choices = D.SLOT_VARIATIONS[slot].slice();
      const defaultName = setupDefaultNames()[slot];
      if (!choices.includes(defaultName)) choices.unshift(defaultName);
      if (!choices.includes(pick.choice) && pick.choice !== OTHER_OPTION && pick.choice !== SKIP_OPTION) choices.unshift(pick.choice);
      choices.push(OTHER_OPTION, SKIP_OPTION);
      html += '<div class="card"><label>' + esc(D.SLOT_LABELS[slot]) + '<select data-setup="pick" data-slot="' + slot + '">' + options(choices, pick.choice) + "</select></label>";
      if (pick.choice === OTHER_OPTION) {
        html += '<label>Exercise name<input type="text" data-setup="typed" data-slot="' + slot + '" value="' + esc(pick.typed) + '"></label>';
      }
      if (pick.choice !== SKIP_OPTION) {
        html += '<label>1RM (' + setup.units + ')<input type="number" inputmode="decimal" step="' + setup.rounding + '" data-setup="max" data-slot="' + slot + '" value="' + pick.max + '"></label>';
      }
      html += "</div>";
    }

    const assignments = currentAssignments(resolved);
    const plans = plansFromAssignments(assignments, resolved);
    html += "<h3>6. Which day each lift lands on</h3><p class=\"muted\">Prefilled from the split style. Change any lift's day here. Every lift keeps its own training max, intensity and reps wherever it goes, and the other days stay exactly as they are.</p>";
    for (const slot of trainedSlotsInOrder(resolved)) {
      html += "<label>" + esc(setupSlotName(slot, resolved)) + ' <span class="small">· ' + esc(D.SLOT_LABELS[slot]) + '</span><select data-setup="day" data-slot="' + slot + '">';
      for (let day = 1; day <= setup.frequency; day++) {
        html += '<option value="' + day + '"' + (assignments[slot] === day ? " selected" : "") + ">Day " + day + "</option>";
      }
      html += "</select></label>";
    }
    html += '<div style="margin-top:10px">' + dayPlanLinesHtml(plans, resolved) + "</div>";

    html += "<h3>7. Accessories</h3><p class=\"muted\">Anything after the main lifts, comma separated: rows, pull-ups, arm and core work. The main lifts include no pulling, so a row or pull-up is suggested on each day. No prescribed progression: you log what you did and try to beat it.</p>";
    for (let dayIndex = 0; dayIndex < plans.length; dayIndex++) {
      const day = setupDay(dayIndex);
      const liftNames = plans[dayIndex].slots.map(function (slot) { return setupSlotName(slot, resolved); });
      html += '<div class="card"><strong>Day ' + (dayIndex + 1) + ":</strong> " + (liftNames.length ? esc(liftNames.join(", ")) : "no main lifts on this day");
      html += '<label>Accessories (comma separated)<input type="text" list="accessory-list" data-setup="accessories" data-day="' + dayIndex + '" value="' + esc(day.accessories) + '" placeholder="Barbell Row, Face Pull, Leg Curl"></label></div>';
    }
    html += '<datalist id="accessory-list">' + options(D.UPPER_BACK_EXERCISES.concat(D.ACCESSORY_SUGGESTIONS), "") + "</datalist>";

    html += '<h3>8. Create</h3><p class="muted">Rep tables, intensities, thresholds and exercise order start at the program defaults and can be changed in Settings.</p>';
    html += '<div class="actions"><button class="primary" data-action="create-program">Create program</button>';
    if (state.program) html += '<button class="secondary" data-action="nav" data-page="workout">Cancel</button>';
    html += "</div>" + creditHtml();
    return html;
  }
  function createProgramFromSetup() {
    if (state.program && !window.confirm("Replace your current program? Export it first if you want to keep the log.")) return;
    const setup = state.setup;
    const resolved = resolveSetup();
    const program = L.createProgram(setup.variant, setup.units, setup.rounding, setup.frequency, resolved.names, resolved.maxes, resolved.skipped, setup.splitStyle);
    const plans = plansFromAssignments(currentAssignments(resolved), resolved);
    for (let dayIndex = 0; dayIndex < plans.length; dayIndex++) {
      const day = setupDay(dayIndex);
      plans[dayIndex].accessories = day.accessories.split(",").map(function (n) { return n.trim(); }).filter(function (n) { return n !== ""; });
    }
    program.days = plans;
    program.lifter = { sex: setup.lifter.sex, age: Math.round(numberOr(setup.lifter.age, 0)), bodyweight: numberOr(setup.lifter.bodyweight, 0) };
    replaceProgram(program);
    state.setup = null;
    state.page = "workout";
    render();
    toast("Program created. Pictures are being saved for offline use.");
  }
  function handleSetupChange(target) {
    const setup = state.setup;
    const field = target.dataset.setup;
    if (field === "preset") { applyPreset(target.value); render(); return; }
    if (field === "variant") { setup.variant = target.value; setup.picks = {}; }
    else if (field === "units") { setup.units = target.value; setup.rounding = setup.units === "lb" ? 5 : 2.5; setup.picks = {}; }
    else if (field === "rounding") setup.rounding = Number(target.value);
    else if (field === "frequency") { setup.frequency = Number(target.value); setup.assignments = null; }
    else if (field === "splitStyle") { setup.splitStyle = target.value; setup.assignments = null; }
    else if (field === "sameLifts") setup.sameLifts = target.checked;
    else if (field === "pick") setupPick(target.dataset.slot).choice = target.value;
    else if (field === "typed") setupPick(target.dataset.slot).typed = target.value;
    else if (field === "max") setupPick(target.dataset.slot).max = numberValue(target, 100);
    else if (field === "day") {
      if (!setup.assignments) setup.assignments = {};
      setup.assignments[target.dataset.slot] = Number(target.value);
    }
    else if (field === "accessories") setupDay(Number(target.dataset.day)).accessories = target.value;
    else if (field === "sex") setup.lifter.sex = target.value;
    else if (field === "age") setup.lifter.age = target.value;
    else if (field === "bodyweight") setup.lifter.bodyweight = target.value;
    if (!["typed", "max", "accessories", "age", "bodyweight"].includes(field)) render();
  }

  // -------------------------------------------------------------------------
  // Workout page
  // -------------------------------------------------------------------------
  function defaultResult(exercise) {
    const variant = state.program.variant;
    return {
      single_at_8: 0,
      sets_completed: variant === D.VARIANT_ORIGINAL ? (exercise.lower_set_threshold || 0) : exercise.sets,
      last_set_rir: exercise.last_set_rir_target || 0,
      last_set_reps: exercise.last_set_rep_target || 0,
      notes: "",
    };
  }
  function ensureDraft() {
    const program = state.program;
    const week = program.current_week;
    const day = program.current_day;
    if (state.draft && state.draft.week === week && state.draft.day === day) return state.draft;
    const draft = { week: week, day: day, lifts: {}, accessories: [], notes: "" };
    for (const exercise of L.buildWorkout(program, week, day)) draft.lifts[exercise.slot] = defaultResult(exercise);
    const plan = program.days[day - 1];
    const planned = [];
    for (const name of plan.accessories) planned.push({ name: name, kind: "accessory" });
    for (const item of planned) {
      const last = L.findLastAccessoryResult(program, item.name);
      draft.accessories.push({ name: item.name, kind: item.kind, weight: last ? last.weight : 0, sets: last ? last.sets : 3, reps: last ? last.reps : 10, last: last });
    }
    state.draft = draft;
    return draft;
  }
  function exerciseWithDraft(slot) {
    // Today's prescription, recomputed from the single @8 if one was typed in.
    const program = state.program;
    const draft = ensureDraft();
    const lift = program.lifts[slot];
    const single = draft.lifts[slot].single_at_8;
    let prescription;
    if (single > 0) {
      const previewLift = Object.assign({}, lift, { training_max: L.calculateTrainingMaxFromSingle(single, lift.single_at_8_percent) });
      prescription = L.getPrescription(program.variant, previewLift, draft.week, program.rounding_increment, program.deload_reps_per_set);
    } else {
      prescription = L.getPrescriptionForSlot(program, slot, draft.week);
    }
    prescription.slot = slot;
    prescription.name = L.liftDisplayName(program, slot);
    return prescription;
  }
  function previewText(slot) {
    const program = state.program;
    const exercise = exerciseWithDraft(slot);
    if (exercise.is_deload) return "Deload: nothing to rate, the training max does not change.";
    const result = ensureDraft().lifts[slot];
    const change = L.calculateTmChangePercent(program.variant, program.lifts[slot], exercise, result);
    const newMax = L.applyTmChange(exercise.training_max, change);
    return "If you save this: " + L.describeTmChange(program.variant, exercise, result, change, newMax, program.units);
  }
  function exerciseCardInner(slot) {
    const program = state.program;
    const variant = program.variant;
    const units = program.units;
    const lift = program.lifts[slot];
    const exercise = exerciseWithDraft(slot);
    const result = ensureDraft().lifts[slot];
    let html = "<h2>" + esc(exercise.name) + "</h2>" + rankInlineHtml(slot) + imageTag(lift.name, "exercise-image");
    html += '<details class="single"' + (result.single_at_8 > 0 ? " open" : "") + "><summary>Heavy single @8 first? (optional)</summary>" +
      '<label>Weight of today\'s single at RPE 8 (0 = skipped)<input type="number" inputmode="decimal" step="' + program.rounding_increment +
      '" data-lift-field="single_at_8" data-slot="' + slot + '" value="' + result.single_at_8 + '"></label>';
    if (result.single_at_8 > 0) {
      html += '<p class="muted">A single of ' + L.formatWeight(result.single_at_8, units) + " at " + L.formatPercent(lift.single_at_8_percent) +
        " gives a training max of " + L.formatWeight(exercise.training_max, units) + " for today.</p>";
    }
    html += "</details>";
    html += '<div class="numbers"><div class="weight"><span class="label">Working weight</span><span class="big">' + esc(L.formatWeight(exercise.working_weight, units)) + "</span></div>" +
      "<div class=\"plan\"><strong>" + esc(L.describePrescription(variant, exercise)) + '</strong><span class="muted">' + esc(L.formatPercent(exercise.intensity)) + " of training max " + esc(L.formatWeight(exercise.training_max, units)) + "</span></div></div>";
    if (exercise.is_deload) {
      html += '<p class="muted">Deload: do the sets and move on.</p>';
    } else if (variant === D.VARIANT_ORIGINAL) {
      html += "<label>Sets completed before reaching " + exercise.rir_cutoff + ' RIR<input type="number" inputmode="numeric" min="0" max="30" step="1" data-lift-field="sets_completed" data-slot="' + slot + '" value="' + result.sets_completed + '"></label>';
    } else if (variant === D.VARIANT_LAST_SET_RIR) {
      html += '<div class="row"><label>Sets completed<input type="number" inputmode="numeric" min="0" max="30" step="1" data-lift-field="sets_completed" data-slot="' + slot + '" value="' + result.sets_completed + '"></label>' +
        '<label>RIR on the last set<input type="number" inputmode="numeric" min="0" max="20" step="1" data-lift-field="last_set_rir" data-slot="' + slot + '" value="' + result.last_set_rir + '"></label></div>';
    } else {
      html += '<label>Reps on your last set (to failure)<input type="number" inputmode="numeric" min="0" max="100" step="1" data-lift-field="last_set_reps" data-slot="' + slot + '" value="' + result.last_set_reps + '"></label>';
    }
    html += '<p class="preview" data-preview="' + slot + '">' + esc(previewText(slot)) + "</p>";
    html += '<input type="text" placeholder="Notes (optional)" data-lift-field="notes" data-slot="' + slot + '" value="' + esc(result.notes) + '">';
    return html;
  }
  function accessoryCardHtml(item, index) {
    const units = state.program.units;
    let html = '<section class="card accessory"><div class="row"><div>' + imageTag(item.name, "accessory-image") + '</div><div style="flex:2"><strong>' + esc(item.name) + "</strong>";
    if (item.last) html += '<p class="muted small">Last time: ' + esc(L.formatWeight(item.last.weight, units)) + " × " + item.last.sets + " sets × " + item.last.reps + " reps</p>";
    else html += '<p class="muted small">First time logging this exercise.</p>';
    html += "</div></div>";
    html += '<div class="row row-3"><label>Weight<input type="number" inputmode="decimal" step="' + state.program.rounding_increment + '" data-acc-field="weight" data-index="' + index + '" value="' + item.weight + '"></label>' +
      '<label>Sets<input type="number" inputmode="numeric" step="1" min="0" data-acc-field="sets" data-index="' + index + '" value="' + item.sets + '"></label>' +
      '<label>Reps<input type="number" inputmode="numeric" step="1" min="0" data-acc-field="reps" data-index="' + index + '" value="' + item.reps + '"></label></div></section>';
    return html;
  }
  function renderWorkout() {
    const program = state.program;
    const draft = ensureDraft();
    const week = draft.week;
    const day = draft.day;
    let html = "";
    if (state.saveMessages.length > 0) {
      html += '<div class="banner"><strong>Workout saved. Training max changes:</strong><ul>';
      for (const message of state.saveMessages) html += "<li>" + esc(message) + "</li>";
      html += '</ul><button class="small" data-action="dismiss-messages" style="margin-top:8px">OK</button></div>';
    }
    if (L.isCycleFinished(program)) {
      html += '<div class="banner">You finished all 21 weeks. Test your maxes, then start the next cycle; your training maxes carry over.' +
        '<div class="actions"><button class="primary" data-action="start-cycle">Start a new 21-week cycle</button></div></div>';
    }
    html += "<h1>Week " + week + " · Day " + day + "</h1>";
    html += '<p class="muted">Block ' + L.blockNumber(week) + " of 3 · " + esc(D.VARIANT_NAMES[program.variant]) + "</p>";
    if (L.isDeloadWeek(week)) html += '<div class="banner warn">Deload week: lighter weights, easy sets, no target, training maxes do not change.</div>';
    const previous = L.findHistoryEntry(program, week, day);
    if (previous) html += '<div class="banner warn">This session was already logged on ' + esc(previous.date) + ". Saving again adds a second entry.</div>";

    const exercises = L.buildWorkout(program, week, day);
    if (exercises.length === 0) html += '<p class="muted">No main lifts on this day, only upper back and accessories.</p>';
    for (const exercise of exercises) {
      html += '<section class="card" id="card-' + exercise.slot + '">' + exerciseCardInner(exercise.slot) + "</section>";
    }

    html += "<h3>Accessories</h3><p class=\"muted\">Last time's numbers are filled in as the target to beat. Leave sets at 0 to skip one today.</p>";
    for (let index = 0; index < draft.accessories.length; index++) html += accessoryCardHtml(draft.accessories[index], index);
    html += '<div class="row"><input type="text" id="new-accessory" list="accessory-list" placeholder="Add an accessory to this day"><button class="small" data-action="add-accessory">Add</button></div>';
    html += '<datalist id="accessory-list">' + options(D.UPPER_BACK_EXERCISES.concat(D.ACCESSORY_SUGGESTIONS), "") + "</datalist>";
    html += '<label>Session notes (optional)<textarea data-field="session-notes">' + esc(draft.notes) + "</textarea></label>";
    html += '<div class="actions"><button class="primary" data-action="save-workout">Save workout</button>' +
      '<button class="secondary" data-action="skip-day">Skip this day without logging</button>' +
      '<button class="secondary" data-action="export">Back up my data (share a file)</button></div>' +
      '<p class="muted small">' + esc(lastBackupText()) + "</p>";
    html += '<details><summary>Jump to a different week or day</summary><div class="row"><label>Week<input type="number" id="jump-week" inputmode="numeric" min="1" max="' + D.TOTAL_WEEKS + '" value="' + week + '"></label>' +
      '<label>Day<input type="number" id="jump-day" inputmode="numeric" min="1" max="' + program.frequency + '" value="' + day + '"></label></div>' +
      '<div class="actions"><button class="secondary" data-action="jump">Go there</button></div></details>';
    html += creditHtml();
    return html;
  }
  function saveWorkout() {
    const program = state.program;
    const draft = ensureDraft();
    const liftResults = [];
    for (const exercise of L.buildWorkout(program, draft.week, draft.day)) {
      const result = draft.lifts[exercise.slot];
      liftResults.push({
        slot: exercise.slot,
        single_at_8: result.single_at_8 > 0 ? result.single_at_8 : null,
        sets_completed: exercise.is_deload ? exercise.sets : result.sets_completed,
        last_set_rir: result.last_set_rir,
        last_set_reps: result.last_set_reps,
        notes: result.notes,
      });
    }
    const accessoryResults = [];
    for (const item of draft.accessories) {
      if (item.sets > 0) accessoryResults.push({ name: item.name, kind: item.kind, weight: item.weight, sets: item.sets, reps: item.reps });
    }
    const messages = L.logWorkout(program, draft.week, draft.day, liftResults, accessoryResults, draft.notes, L.todayString());
    L.advanceToNextDay(program);
    saveProgram();
    state.saveMessages = messages;
    state.draft = null;
    render();
    window.scrollTo(0, 0);
    queueRankChanges(program.history[program.history.length - 1].rank_changes || []);
  }
  function queueRankChanges(changes) {
    state.rankQueue = changes.slice();
    showNextRankChange();
  }
  function showNextRankChange() {
    const existing = $("#rank-overlay");
    if (existing) existing.remove();
    if (!state.rankQueue || state.rankQueue.length === 0) return;
    const change = state.rankQueue.shift();
    const up = change.to_tier > change.from_tier;
    const tierKey = D.RANK_TIERS[change.to_tier].key;
    const color = tierColor(tierKey);
    const effect = D.RANK_TIERS[change.to_tier].effect;
    const overlay = document.createElement("div");
    overlay.id = "rank-overlay";
    overlay.className = "rank-overlay" + (up ? " up" : " down");
    overlay.setAttribute("data-action", "dismiss-rank");
    overlay.innerHTML = '<div class="rank-pop" style="--tier:' + color + '">' +
      '<div class="rank-title">' + (up ? "RANK UP" : "RANK DOWN") + "</div>" +
      '<div class="rank-stage">' + (up ? '<span class="rank-ring"></span><span class="rank-ring second"></span>' : "") +
      '<span class="badge big shape-' + badgeShape(tierKey) + ' effect-' + (up ? effect : "none") + '" style="--size:150px;--tier:' + color + '">' + badgeSvg(tierKey, color) + "</span></div>" +
      '<div class="rank-lift">' + esc(change.name) + "</div>" +
      '<div class="rank-path"><span>' + esc(change.from_name) + '</span> <span class="arrow">\u2192</span> ' + tierNameHtml(tierKey, change.to_name) + "</div>" +
      '<p class="muted small">Tap to continue</p></div>';
    document.body.appendChild(overlay);
  }
  function handleLiftInput(target, eventType) {
    const draft = ensureDraft();
    const slot = target.dataset.slot;
    const field = target.dataset.liftField;
    if (field === "notes") draft.lifts[slot].notes = target.value;
    else draft.lifts[slot][field] = numberValue(target, 0);
    if (field === "single_at_8") {
      if (eventType === "change") $("#card-" + slot).innerHTML = exerciseCardInner(slot);
      return;
    }
    const preview = $('[data-preview="' + slot + '"]');
    if (preview) preview.textContent = previewText(slot);
  }
  function handleAccessoryInput(target) {
    const item = ensureDraft().accessories[Number(target.dataset.index)];
    item[target.dataset.accField] = numberValue(target, 0);
  }

  // -------------------------------------------------------------------------
  // Ranks page (just for fun)
  // -------------------------------------------------------------------------
  function lifterFormHtml(prefix) {
    const lifter = state.program.lifter || {};
    let html = '<div class="row"><label>Sex<select id="' + prefix + '-sex"><option value=""' + (lifter.sex ? "" : " selected") + ">Choose</option>";
    for (const sex of D.SEX_CHOICES) html += '<option value="' + sex + '"' + (lifter.sex === sex ? " selected" : "") + ">" + esc(D.SEX_NAMES[sex]) + "</option>";
    html += '</select></label><label>Age<input type="number" id="' + prefix + '-age" inputmode="numeric" min="10" max="100" value="' + (lifter.age || "") + '"></label>' +
      '<label>Bodyweight (' + state.program.units + ')<input type="number" id="' + prefix + '-weight" inputmode="decimal" step="0.5" value="' + (lifter.bodyweight || "") + '"></label></div>';
    return html;
  }
  function saveLifterFrom(prefix) {
    const sex = $("#" + prefix + "-sex").value;
    const age = Math.round(numberValue($("#" + prefix + "-age"), 0));
    const bodyweight = numberValue($("#" + prefix + "-weight"), 0);
    if (!sex || age <= 0 || bodyweight <= 0) { toast("Please fill in sex, age and bodyweight."); return; }
    state.program.lifter = { sex: sex, age: age, bodyweight: bodyweight };
    saveProgram();
    render();
    toast("Saved.");
  }
  function tierLadderHtml() {
    let html = '<details><summary>The ladder</summary><p class="muted small">Five common levels sit at the 5th, 20th, 50th, 80th and 95th percentiles of trained lifters (beginner, novice, intermediate, advanced, elite). This app splits them into ten tiers, with three Legend steps inside the top 2.5%. Standards are approximate and can be replaced per lift under Settings.</p><ul class="ladder">';
    for (let position = D.RANK_TIERS.length - 1; position >= 0; position--) {
      const tier = D.RANK_TIERS[position];
      const fake = { available: true, tier_key: tier.key, tier_name: tier.name, effect: tier.effect };
      html += "<li>" + rankBadgeHtml(fake, 40) + '<span class="tier-label">' + tierNameHtml(tier.key, tier.name) + '</span><span class="muted small">top ' + (Math.round((100 - tier.min_percentile) * 100) / 100) + "%</span></li>";
    }
    return html + "</ul></details>";
  }
  function rankCardHtml(rank) {
    const units = state.program.units;
    const color = tierColor(rank.tier_key);
    let html = '<section class="card rank-row"><div class="rank-head">' + rankBadgeHtml(rank, 66) +
      "<div><h2>" + esc(rank.name) + '</h2><div class="tier-name">' + tierNameHtml(rank.tier_key, rank.tier_name) + "</div>" +
      '<div class="muted small">Training max ' + esc(L.formatWeight(rank.training_max, units)) + " · about the " + ordinal(rank.percentile) + " percentile</div></div></div>";
    html += '<div class="rank-bar"><div class="rank-fill" style="width:' + Math.round(rank.progress * 100) + "%;background:" + (isLegend(rank.tier_key) ? RAINBOW : color) + '"></div></div>';
    if (rank.next_tier_name) {
      html += '<p class="muted small">' + esc(L.formatWeight(rank.gap_to_next, units)) + " more on the training max to reach " + esc(rank.next_tier_name) + "</p>";
    } else {
      html += '<p class="muted small">Top of the ladder.</p>';
    }
    if (rank.custom_thresholds) html += '<p class="muted small">Using your own thresholds for this lift.</p>';
    else if (rank.rank_factor !== 1) html += '<p class="muted small">Counted as ' + esc(L.formatWeight(rank.training_max / rank.rank_factor, units)) + " on the main lift (factor " + rank.rank_factor + ").</p>";
    return html + "</section>";
  }
  function renderRanks() {
    const program = state.program;
    let html = "<h1>Ranks</h1>";
    if (!L.lifterDetailsComplete(program)) {
      html += '<div class="card"><strong>Unlock your ranks</strong><p class="muted">Each lift gets a rank from its training max, compared with strength standards for lifters of your sex, age and bodyweight. Just for fun; nothing here changes the program.</p>' +
        lifterFormHtml("ranks") + '<div class="actions"><button class="primary" data-action="save-lifter" data-prefix="ranks">Show my ranks</button></div></div>';
      return html + tierLadderHtml() + creditHtml();
    }
    const lifter = program.lifter;
    html += '<p class="muted">Standards for a ' + lifter.age + "-year-old " + esc(D.SEX_NAMES[lifter.sex].toLowerCase()) + " at " + esc(L.formatWeight(lifter.bodyweight, program.units)) +
      ", adjusted for bodyweight and age. Each lift is ranked by its training max, so ranks move with your training. Update your details under Settings.</p>";
    for (const rank of L.allRanks(program)) html += rankCardHtml(rank);
    return html + tierLadderHtml() + creditHtml();
  }

  // -------------------------------------------------------------------------
  // Progress page
  // -------------------------------------------------------------------------
  function lineChartSvg(labels, series) {
    const width = 640, height = 300, left = 52, right = 14, top = 14, bottom = 40;
    let min = Infinity, max = -Infinity;
    for (const item of series) for (const value of item.values) {
      if (value === null || value === undefined) continue;
      if (value < min) min = value;
      if (value > max) max = value;
    }
    if (min === Infinity) return '<p class="muted">Nothing to plot yet.</p>';
    if (max === min) { max += 5; min -= 5; }
    const pad = (max - min) * 0.08;
    min -= pad; max += pad;
    const count = labels.length;
    function x(i) { return count === 1 ? left : left + i / (count - 1) * (width - left - right); }
    function y(v) { return top + (max - v) / (max - min) * (height - top - bottom); }
    let svg = '<svg class="chart" viewBox="0 0 ' + width + " " + height + '" xmlns="http://www.w3.org/2000/svg">';
    for (let tick = 0; tick <= 4; tick++) {
      const value = min + (max - min) * tick / 4;
      svg += '<line x1="' + left + '" y1="' + y(value) + '" x2="' + (width - right) + '" y2="' + y(value) + '" stroke="#353a4d" stroke-width="1"/>';
      svg += '<text x="' + (left - 6) + '" y="' + (y(value) + 4) + '" fill="#a3a8b8" font-size="12" text-anchor="end">' + Math.round(value) + "</text>";
    }
    const labelPositions = count <= 3 ? [0, count - 1] : [0, Math.floor(count / 2), count - 1];
    for (const i of labelPositions) {
      if (i < 0) continue;
      svg += '<text x="' + x(i) + '" y="' + (height - 12) + '" fill="#a3a8b8" font-size="12" text-anchor="middle">' + esc(labels[i]) + "</text>";
    }
    series.forEach(function (item, seriesIndex) {
      // Each lift is trained about once a week, so its points sit several
      // sessions apart: join the points that exist and skip the gaps.
      const color = CHART_COLORS[seriesIndex % CHART_COLORS.length];
      let path = "";
      let dots = "";
      let pointCount = 0;
      for (let i = 0; i < item.values.length; i++) {
        const value = item.values[i];
        if (value === null || value === undefined) continue;
        path += (pointCount === 0 ? " M " : " L ") + x(i).toFixed(1) + " " + y(value).toFixed(1);
        pointCount++;
        if (series.length <= 4 || pointCount === 1) {
          dots += '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(value).toFixed(1) + '" r="3" fill="' + color + '"/>';
        }
      }
      svg += '<path d="' + path + '" fill="none" stroke="' + color + '" stroke-width="2.5" stroke-linejoin="round"/>' + dots;
    });
    svg += "</svg>";
    let legend = '<div class="legend">';
    series.forEach(function (item, seriesIndex) {
      legend += '<span style="--swatch:' + CHART_COLORS[seriesIndex % CHART_COLORS.length] + '">' + esc(item.name) + "</span>";
    });
    return svg + legend + "</div>";
  }
  function chartSeries(table, choice) {
    const program = state.program;
    let names;
    if (choice === "Main lifts") names = D.MAIN_SLOTS.map(function (slot) { return L.liftDisplayName(program, slot); });
    else if (choice === "All lifts") names = Object.keys(table.columns);
    else names = [choice];
    return names.filter(function (name) { return table.columns[name] !== undefined; })
      .map(function (name) { return { name: name, values: table.columns[name] }; });
  }
  function resultText(logged) {
    const variant = state.program.variant;
    if (logged.is_deload) return "deload";
    if (variant === D.VARIANT_ORIGINAL) return logged.sets_completed + " sets";
    if (variant === D.VARIANT_LAST_SET_RIR) return logged.sets_completed + " sets, " + logged.last_set_rir + " RIR";
    return logged.last_set_reps + " reps on the last set";
  }
  function renderProgress() {
    const program = state.program;
    const units = program.units;
    const stats = L.summaryStats(program);
    let html = "<h1>Progress</h1>";
    html += '<div class="stats"><div class="stat"><div class="label">Sessions logged</div><div class="value">' + stats.sessions + "</div></div>" +
      '<div class="stat"><div class="label">Current week</div><div class="value">' + stats.current_week + " / " + D.TOTAL_WEEKS + "</div></div>" +
      '<div class="stat"><div class="label">Total volume</div><div class="value">' + Math.round(stats.total_volume).toLocaleString() + " " + units + "</div></div>" +
      '<div class="stat"><div class="label">Total sets</div><div class="value">' + stats.total_sets + "</div></div></div>";
    if (program.history.length === 0) return html + '<p class="muted">Log a workout and the charts will appear here.</p>' + creditHtml();

    const tmTable = L.buildTrainingMaxTable(program);
    const choices = ["Main lifts", "All lifts"].concat(Object.keys(tmTable.columns));
    html += '<h3>Training max over time</h3><label>Show<select data-field="chart">' + options(choices, state.ui.chart) + "</select></label>";
    html += lineChartSvg(tmTable.labels, chartSeries(tmTable, state.ui.chart));
    const e1rmTable = L.buildEstimatedMaxTable(program);
    html += "<h3>Estimated 1RM trend</h3>" + lineChartSvg(e1rmTable.labels, chartSeries(e1rmTable, state.ui.chart));
    html += '<p class="muted small">Epley estimate from the hardest set of each session. Gaps are deload weeks.</p>';

    html += "<h3>Workout history</h3>";
    for (let position = program.history.length - 1; position >= 0; position--) {
      const entry = program.history[position];
      html += '<div class="history-entry"><strong>Week ' + entry.week + " · Day " + entry.day + '</strong> <span class="muted">' + esc(entry.date) + "</span><ul>";
      for (const logged of entry.lifts) {
        html += "<li>" + esc(logged.name) + ": " + esc(L.formatWeight(logged.working_weight, units)) + " · " + esc(resultText(logged)) +
          " · TM " + esc(L.formatPercent(logged.tm_change_percent)) + " → " + esc(L.formatWeight(logged.training_max_after, units)) +
          (logged.notes ? ' <span class="muted">' + esc(logged.notes) + "</span>" : "") + "</li>";
      }
      for (const accessory of entry.accessories) {
        html += '<li class="muted">' + esc(accessory.name) + ": " + esc(L.formatWeight(accessory.weight, units)) + " × " + accessory.sets + " × " + accessory.reps + "</li>";
      }
      if (entry.notes) html += '<li class="muted">Notes: ' + esc(entry.notes) + "</li>";
      html += "</ul></div>";
    }
    return html + creditHtml();
  }

  // -------------------------------------------------------------------------
  // Settings page
  // -------------------------------------------------------------------------
  function section(key, title, inner) {
    return '<details data-section="' + key + '"' + (state.ui.open[key] ? " open" : "") + "><summary>" + esc(title) + "</summary>" + inner + "</details>";
  }
  function settingsGeneralHtml() {
    const program = state.program;
    return '<label>Program variant<select id="set-variant">' + variantOptions(program.variant) + "</select></label>" +
      '<label class="check"><input type="checkbox" id="set-reset-tables" checked> When changing variant, also reset rep tables, intensities, sets and ladder to that variant\'s defaults (training maxes are kept)</label>' +
      '<div class="row"><label>Units<select id="set-units">' + options(D.UNIT_CHOICES, program.units) + "</select></label>" +
      '<label>Rounding increment<input type="number" id="set-rounding" inputmode="decimal" step="0.1" min="0.1" value="' + program.rounding_increment + '"></label></div>' +
      '<label>Training days per week<select id="set-frequency">' + options(D.FREQUENCY_CHOICES.map(String), String(program.frequency)) + "</select></label>" +
      '<p class="muted" style="margin-top:12px">Split style (changing days or style rebuilds the training days from that layout)</p>' +
      splitStyleRadiosHtml(program.split_style, 'id="set-split-style"') +
      '<div class="row"><label>Current week<input type="number" id="set-week" inputmode="numeric" min="1" max="' + D.TOTAL_WEEKS + '" value="' + program.current_week + '"></label>' +
      '<label>Current day<input type="number" id="set-day" inputmode="numeric" min="1" max="6" value="' + program.current_day + '"></label>' +
      '<label>Deload reps per set<input type="number" id="set-deload-reps" inputmode="numeric" min="1" max="20" value="' + program.deload_reps_per_set + '"></label></div>' +
      '<div class="actions"><button class="primary" data-action="save-general">Save general settings</button></div>';
  }
  function saveGeneral() {
    const program = state.program;
    const variant = $("#set-variant").value;
    if (variant !== program.variant) {
      program.variant = variant;
      if ($("#set-reset-tables").checked) for (const slot of D.ALL_SLOTS) L.resetLiftTablesForVariant(program.lifts[slot], variant);
    }
    program.units = $("#set-units").value;
    program.rounding_increment = numberValue($("#set-rounding"), program.rounding_increment);
    const frequency = Number($("#set-frequency").value);
    const checkedStyle = document.querySelector('input[name="split-style"]:checked');
    const splitStyle = checkedStyle ? checkedStyle.value : program.split_style;
    if (frequency !== program.frequency || splitStyle !== program.split_style) {
      program.frequency = frequency;
      program.split_style = splitStyle;
      program.days = L.buildDefaultDays(frequency, [], splitStyle);
    }
    program.current_week = Math.min(D.TOTAL_WEEKS, Math.max(1, Math.round(numberValue($("#set-week"), program.current_week))));
    program.current_day = Math.min(program.frequency, Math.max(1, Math.round(numberValue($("#set-day"), program.current_day))));
    program.deload_reps_per_set = Math.max(1, Math.round(numberValue($("#set-deload-reps"), 5)));
    state.draft = null;
    saveProgram();
    render();
    toast("Saved.");
  }
  function settingsLiftsHtml() {
    const program = state.program;
    const slot = state.ui.settingsLift;
    const lift = program.lifts[slot];
    const scheduled = L.scheduledSlots(program);
    let html = '<label>Lift<select data-field="settingsLift">';
    for (const s of D.ALL_SLOTS) html += '<option value="' + s + '"' + (s === slot ? " selected" : "") + ">" + esc(slotLabel(s)) + (scheduled.includes(s) ? "" : " (not scheduled)") + "</option>";
    html += "</select></label>";
    html += '<label>Exercise name<input type="text" id="lift-name" value="' + esc(lift.name) + '"></label>';
    html += '<div class="row"><label>Training max<input type="number" id="lift-tm" inputmode="decimal" step="0.5" value="' + (Math.round(lift.training_max * 100) / 100) + '"></label>' +
      '<label>Single @8 %<input type="number" id="lift-single" inputmode="decimal" step="0.5" min="50" max="100" value="' + lift.single_at_8_percent + '"></label>' +
      '<label>Sets<input type="number" id="lift-sets" inputmode="numeric" step="1" min="1" max="12" value="' + lift.sets + '"></label></div>';
    if (program.variant === D.VARIANT_ORIGINAL) {
      html += '<p class="muted">Set range and how the training max moves outside it</p><div class="row">' +
        '<label>Lower threshold<input type="number" id="lift-lower" inputmode="numeric" step="1" value="' + lift.lower_set_threshold + '"></label>' +
        '<label>Upper threshold<input type="number" id="lift-upper" inputmode="numeric" step="1" value="' + lift.upper_set_threshold + '"></label></div><div class="row">' +
        '<label>Increase %<input type="number" id="lift-increase" inputmode="decimal" step="0.25" value="' + lift.increase_percent + '"></label>' +
        '<label>Decrease %<input type="number" id="lift-decrease" inputmode="decimal" step="0.25" value="' + lift.decrease_percent + '"></label></div>';
    } else {
      html += '<p class="muted">Training max ladder: % change for each outcome</p>';
      for (let position = 0; position < D.TM_LADDER_LABELS.length; position += 2) {
        html += '<div class="row">';
        for (let offset = 0; offset < 2; offset++) {
          const index = position + offset;
          html += "<label>" + esc(D.TM_LADDER_LABELS[index]) + '<input type="number" class="ladder" data-index="' + index + '" inputmode="decimal" step="0.25" value="' + lift.ladder[index] + '"></label>';
        }
        html += "</div>";
      }
    }
    let thresholdsText = "";
    if (lift.rank_thresholds && lift.rank_thresholds.length === 5) thresholdsText = lift.rank_thresholds.join(", ");
    html += '<p class="muted" style="margin-top:14px">Rank settings (just for fun)</p>' +
      '<label>Rank factor: this lift\'s max divided by the factor is the equivalent ' + esc(D.RANK_TYPE_NAMES[D.RANK_TYPE_BY_SLOT[slot]]) + ' max<input type="number" id="lift-rank-factor" inputmode="decimal" step="0.05" min="0.1" max="5" value="' + (lift.rank_factor || 1) + '"></label>' +
      '<label>Own thresholds, optional: five numbers in ' + program.units + ' for beginner, novice, intermediate, advanced, elite (from a standards calculator for your bodyweight and age)<input type="text" id="lift-rank-thresholds" inputmode="decimal" placeholder="e.g. 135, 225, 270, 360, 450" value="' + esc(thresholdsText) + '"></label>';
    html += '<div class="actions"><button class="primary" data-action="save-lift">Save this lift</button></div>';
    return html;
  }
  function saveLift() {
    const program = state.program;
    const lift = program.lifts[state.ui.settingsLift];
    const name = $("#lift-name").value.trim();
    if (name !== "") lift.name = name;
    lift.training_max = numberValue($("#lift-tm"), lift.training_max);
    lift.single_at_8_percent = numberValue($("#lift-single"), lift.single_at_8_percent);
    lift.sets = Math.max(1, Math.round(numberValue($("#lift-sets"), lift.sets)));
    if (program.variant === D.VARIANT_ORIGINAL) {
      lift.lower_set_threshold = Math.round(numberValue($("#lift-lower"), lift.lower_set_threshold));
      lift.upper_set_threshold = Math.round(numberValue($("#lift-upper"), lift.upper_set_threshold));
      lift.increase_percent = numberValue($("#lift-increase"), lift.increase_percent);
      lift.decrease_percent = numberValue($("#lift-decrease"), lift.decrease_percent);
    } else {
      for (const input of $all("input.ladder")) lift.ladder[Number(input.dataset.index)] = numberValue(input, 0);
    }
    lift.rank_factor = numberValue($("#lift-rank-factor"), 1) || 1;
    const thresholdNumbers = $("#lift-rank-thresholds").value.split(",").map(function (part) { return parseFloat(part); }).filter(function (n) { return !isNaN(n) && n > 0; });
    lift.rank_thresholds = thresholdNumbers.length === 5 ? thresholdNumbers : null;
    state.draft = null;
    saveProgram();
    precacheProgramImages();
    render();
    toast("Saved.");
  }
  const TABLE_ROWS = [["reps_per_set", "Reps per set"], ["rir_cutoff", "RIR cutoff (Original)"],
                      ["last_set_rir_target", "Last-set RIR target"], ["last_set_rep_target", "Last-set rep target"]];
  function settingsTablesHtml() {
    const program = state.program;
    const slot = state.ui.tablesLift;
    const lift = program.lifts[slot];
    let html = '<p class="muted">Columns are percentages of the training max; the app reads the column nearest to the day\'s intensity.</p><label>Lift<select data-field="tablesLift">';
    for (const s of D.ALL_SLOTS) html += '<option value="' + s + '"' + (s === slot ? " selected" : "") + ">" + esc(slotLabel(s)) + "</option>";
    html += '</select></label><div class="table-wrap"><table><tr><th class="sticky">Table</th>';
    for (const bucket of D.PERCENTAGE_BUCKETS) html += "<th>" + L.formatPercent(bucket) + "</th>";
    html += "</tr>";
    for (const row of TABLE_ROWS) {
      html += '<tr><td class="sticky">' + esc(row[1]) + "</td>";
      for (let column = 0; column < D.PERCENTAGE_BUCKETS.length; column++) {
        html += '<td><input type="number" inputmode="numeric" step="1" min="0" data-table-row="' + row[0] + '" data-table-col="' + column + '" value="' + lift[row[0]][column] + '"></td>';
      }
      html += "</tr>";
    }
    html += "</table></div>";
    html += '<div class="actions"><button class="primary" data-action="save-tables">Save this lift\'s tables</button>' +
      '<button class="secondary" data-action="reset-tables">Reset this lift to defaults</button>' +
      '<button class="secondary" data-action="copy-tables">Copy these tables to every lift</button></div>';
    return html;
  }
  function readTablesFromInputs(lift) {
    for (const row of TABLE_ROWS) {
      const values = lift[row[0]].slice();
      for (const input of $all('[data-table-row="' + row[0] + '"]')) values[Number(input.dataset.tableCol)] = Math.round(numberValue(input, 0));
      lift[row[0]] = values;
    }
  }
  function settingsIntensitiesHtml() {
    const program = state.program;
    let html = '<p class="muted">Percent of training max per lift per week. Weeks 7, 14 and 21 are deloads.</p><div class="table-wrap"><table><tr><th class="sticky">Week</th>';
    for (const slot of D.ALL_SLOTS) html += "<th>" + esc(L.liftDisplayName(program, slot)) + "</th>";
    html += "</tr>";
    for (let week = 1; week <= D.TOTAL_WEEKS; week++) {
      html += '<tr><td class="sticky">W' + week + (L.isDeloadWeek(week) ? " deload" : "") + "</td>";
      for (const slot of D.ALL_SLOTS) {
        html += '<td><input type="number" inputmode="decimal" step="2.5" data-int-slot="' + slot + '" data-int-week="' + week + '" value="' + program.lifts[slot].intensities[week - 1] + '"></td>';
      }
      html += "</tr>";
    }
    html += "</table></div>";
    html += '<div class="actions"><button class="primary" data-action="save-intensities">Save intensities</button><button class="secondary" data-action="reset-intensities">Reset to the variant\'s defaults</button></div>';
    return html;
  }
  function settingsDaysHtml() {
    const program = state.program;
    const scheduled = L.scheduledSlots(program);
    let html = '<p class="muted">Which day each lift lands on. Every lift keeps its own training max, intensity and reps wherever it goes, and the other days are not affected.</p>';
    const currentDay = {};
    for (let dayIndex = 0; dayIndex < program.days.length; dayIndex++) {
      for (const slot of program.days[dayIndex].slots) currentDay[slot] = dayIndex + 1;
    }
    for (const slot of D.ALL_SLOTS) {
      html += "<label>" + esc(slotLabel(slot)) + '<select data-assign-slot="' + slot + '"><option value="0"' + (currentDay[slot] ? "" : " selected") + ">Not scheduled</option>";
      for (let day = 1; day <= program.days.length; day++) {
        html += '<option value="' + day + '"' + (currentDay[slot] === day ? " selected" : "") + ">Day " + day + "</option>";
      }
      html += "</select></label>";
    }
    html += '<div class="actions"><button class="primary" data-action="save-day-assignments">Save day assignments</button></div>';
    html += '<p class="muted">Below: arrows reorder lifts within a day, ✕ removes one, the dropdown adds an unscheduled lift. Accessory names save with the button at the bottom.</p>';
    for (let dayIndex = 0; dayIndex < program.days.length; dayIndex++) {
      const day = program.days[dayIndex];
      html += "<h3>Day " + (dayIndex + 1) + '</h3><ul class="day-list">';
      for (let position = 0; position < day.slots.length; position++) {
        html += "<li><span>" + (position + 1) + ". " + esc(slotLabel(day.slots[position])) + "</span>" +
          '<button class="small icon" data-action="move-up" data-day="' + dayIndex + '" data-pos="' + position + '">▲</button>' +
          '<button class="small icon" data-action="move-down" data-day="' + dayIndex + '" data-pos="' + position + '">▼</button>' +
          '<button class="small icon" data-action="remove-slot" data-day="' + dayIndex + '" data-pos="' + position + '">✕</button></li>';
      }
      html += "</ul>";
      const unscheduled = D.ALL_SLOTS.filter(function (s) { return !scheduled.includes(s); });
      if (unscheduled.length > 0) {
        html += '<div class="row"><select id="add-slot-' + dayIndex + '">';
        for (const s of unscheduled) html += '<option value="' + s + '">' + esc(slotLabel(s)) + "</option>";
        html += '</select><button class="small" data-action="add-slot" data-day="' + dayIndex + '">Add</button></div>';
      }
      html += '<label>Accessories (one per line)<textarea data-day-accessories="' + dayIndex + '">' + esc(day.accessories.join("\n")) + "</textarea></label>";
    }
    html += '<div class="actions"><button class="primary" data-action="save-days">Save accessory names</button></div>';
    return html;
  }
  function settingsPicturesHtml() {
    const program = state.program;
    const names = programExerciseNames();
    if (!state.ui.pictureName || !names.includes(state.ui.pictureName)) state.ui.pictureName = names[0] || "";
    const name = state.ui.pictureName;
    const chosen = program.image_choices[name] || "";
    const byId = LIB.catalogById(state.catalog);
    const currentLabel = byId[chosen] ? byId[chosen].name : "Automatic match";
    let html = '<p class="muted">Every picture shows the start and finish positions. Pick any library picture for an exercise if the automatic match is wrong.</p>';
    html += '<label>Exercise<select data-field="pictureName">' + options(names, name) + "</select></label>";
    html += imageTag(name, "exercise-image") + '<p class="muted small">' + esc(LIB.describeMatch(name, state.catalog, chosen)) + "</p>";
    html += '<label>Library picture<select id="picture-choice">' + options(["Automatic match"].concat(LIB.catalogNames(state.catalog)), currentLabel) + "</select></label>";
    html += '<div class="actions"><button class="primary" data-action="save-picture">Use this picture</button></div>';
    return html;
  }
  function settingsDataHtml() {
    const backupText = lastBackupText();
    return '<p class="muted">Your log lives in this phone\'s browser storage only. It survives closing the app, restarting ' +
      "the phone and app updates, but it is deleted if you remove the app icon, clear the browser's website data, or " +
      "reset the phone. A copy in Files or iCloud Drive is outside all of that: the Back up button here or on the " +
      "workout page shares a dated backup file, and one tap on Save to Files keeps it. The same file opens in the " +
      'computer app.</p><p class="muted"><strong>' + esc(backupText) + "</strong></p>" +
      '<div class="actions"><button class="secondary" data-action="export">Share / download my program (JSON)</button>' +
      importFileHtml("Import a program file (restore a backup)") +
      '<button class="secondary" data-action="load-demo">Load demo data</button>' +
      '<button class="secondary" data-action="new-program">Set up a new program</button>' +
      '<button class="secondary" data-action="reset-program">Delete my program from this phone</button></div>';
  }
  function renderSettings() {
    let html = "<h1>Settings</h1><p class=\"muted\">Sensible defaults everywhere: change only what you want to.</p>";
    html += section("general", "General", settingsGeneralHtml());
    html += section("lifter", "Lifter & ranks", '<p class="muted">Used only for the ranks: sex, age and bodyweight pick the strength standards each lift is measured against. Update the bodyweight as it changes.</p>' +
      lifterFormHtml("settings") + '<div class="actions"><button class="primary" data-action="save-lifter" data-prefix="settings">Save</button></div>');
    html += section("lifts", "Lifts", settingsLiftsHtml());
    html += section("tables", "Rep & RIR tables", settingsTablesHtml());
    html += section("intensities", "Intensities", settingsIntensitiesHtml());
    html += section("days", "Training days", settingsDaysHtml());
    html += section("pictures", "Pictures", settingsPicturesHtml());
    html += section("data", "Data", settingsDataHtml());
    return html + creditHtml();
  }

  // -------------------------------------------------------------------------
  // Import / export
  // -------------------------------------------------------------------------
  function exportProgram() {
    const text = JSON.stringify(state.program, null, 2);
    const fileName = "sbs_program_" + L.todayString() + ".json";   // dated, so old backups are not overwritten
    try {
      const file = new File([text], fileName, { type: "application/json" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file], title: "SBS Trainer program" })
          .then(function () { recordBackup(); render(); toast("Backup shared."); })
          .catch(function () {});
        return;
      }
    } catch (error) { /* fall through to a download */ }
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([text], { type: "application/json" }));
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    recordBackup();
    render();
    toast("Backup downloaded.");
  }
  function importProgramText(text) {
    let program;
    try { program = JSON.parse(text); } catch (error) { toast("That file is not valid JSON."); return; }
    if (!program || typeof program !== "object" || !program.lifts || !program.variant) { toast("That file does not look like an SBS Trainer program."); return; }
    if (state.program && !window.confirm("Replace the program on this phone with the imported one?")) return;
    replaceProgram(program);
    state.page = "workout";
    render();
    toast("Imported.");
  }

  // -------------------------------------------------------------------------
  // Actions and rendering
  // -------------------------------------------------------------------------
  function creditHtml() {
    return '<p class="credit">Program design by Greg Nuckols / Stronger By Science (<a href="https://www.strongerbyscience.com/program-bundle/">SBS program bundle</a>). ' +
      "Unofficial personal project, not affiliated with or endorsed by SBS. Exercise photos: free-exercise-db (public domain).</p>";
  }
  function renderNav() {
    const nav = $("#nav");
    let html = "";
    for (const page of ["workout", "ranks", "progress", "settings"]) {
      const label = page === "workout" ? "Workout" : page === "ranks" ? "Ranks" : page === "progress" ? "Progress" : "Settings";
      html += '<button data-action="nav" data-page="' + page + '"' + (state.page === page ? ' class="active"' : "") + ">" + label + "</button>";
    }
    nav.innerHTML = html;
    nav.hidden = !state.program;
  }
  function render() {
    const main = $("#app");
    if (!state.program) state.page = "setup";
    if (state.page === "setup") main.innerHTML = renderSetup();
    else if (state.page === "ranks") main.innerHTML = renderRanks();
    else if (state.page === "progress") main.innerHTML = renderProgress();
    else if (state.page === "settings") main.innerHTML = renderSettings();
    else main.innerHTML = renderWorkout();
    renderNav();
  }
  function handleAction(button) {
    const program = state.program;
    const action = button.dataset.action;
    if (action === "dismiss-rank") { showNextRankChange(); return; }
    if (action === "close-image") { closeImageViewer(); return; }
    if (action === "save-lifter") { saveLifterFrom(button.dataset.prefix); return; }
    if (action === "nav") { state.page = button.dataset.page; if (state.page === "setup") state.setup = null; render(); window.scrollTo(0, 0); return; }
    if (action === "create-program") { createProgramFromSetup(); return; }
    if (action === "dismiss-messages") { state.saveMessages = []; render(); return; }
    if (action === "save-workout") { saveWorkout(); return; }
    if (action === "skip-day") { L.advanceToNextDay(program); state.draft = null; saveProgram(); render(); window.scrollTo(0, 0); return; }
    if (action === "start-cycle") { L.startNewCycle(program); state.draft = null; saveProgram(); render(); return; }
    if (action === "jump") {
      program.current_week = Math.min(D.TOTAL_WEEKS, Math.max(1, Math.round(numberValue($("#jump-week"), 1))));
      program.current_day = Math.min(program.frequency, Math.max(1, Math.round(numberValue($("#jump-day"), 1))));
      state.draft = null; saveProgram(); render(); window.scrollTo(0, 0); return;
    }
    if (action === "add-accessory") {
      const name = $("#new-accessory").value.trim();
      if (name === "") return;
      program.days[program.current_day - 1].accessories.push(name);
      saveProgram(); state.draft = null; render(); precacheProgramImages(); return;
    }
    if (action === "save-general") { saveGeneral(); return; }
    if (action === "save-lift") { saveLift(); return; }
    if (action === "save-tables") { readTablesFromInputs(program.lifts[state.ui.tablesLift]); saveProgram(); state.draft = null; render(); toast("Saved."); return; }
    if (action === "reset-tables") {
      const lift = program.lifts[state.ui.tablesLift];
      const fresh = L.buildLiftSettings(program.variant, lift.slot, lift.name, lift.training_max);
      for (const row of TABLE_ROWS) lift[row[0]] = fresh[row[0]];
      saveProgram(); state.draft = null; render(); return;
    }
    if (action === "copy-tables") {
      const lift = program.lifts[state.ui.tablesLift];
      readTablesFromInputs(lift);
      for (const slot of D.ALL_SLOTS) for (const row of TABLE_ROWS) program.lifts[slot][row[0]] = lift[row[0]].slice();
      saveProgram(); state.draft = null; render(); toast("Copied to every lift."); return;
    }
    if (action === "save-intensities") {
      for (const input of $all("[data-int-slot]")) program.lifts[input.dataset.intSlot].intensities[Number(input.dataset.intWeek) - 1] = numberValue(input, 0);
      saveProgram(); state.draft = null; render(); toast("Saved."); return;
    }
    if (action === "reset-intensities") {
      for (const slot of D.ALL_SLOTS) {
        const lift = program.lifts[slot];
        lift.intensities = L.buildLiftSettings(program.variant, slot, lift.name, lift.training_max).intensities;
      }
      saveProgram(); state.draft = null; render(); return;
    }
    if (action === "move-up" || action === "move-down" || action === "remove-slot") {
      const slots = program.days[Number(button.dataset.day)].slots;
      const position = Number(button.dataset.pos);
      if (action === "remove-slot") slots.splice(position, 1);
      else {
        const other = action === "move-up" ? position - 1 : position + 1;
        if (other >= 0 && other < slots.length) { const kept = slots[position]; slots[position] = slots[other]; slots[other] = kept; }
      }
      saveProgram(); state.draft = null; render(); return;
    }
    if (action === "add-slot") {
      const select = $("#add-slot-" + button.dataset.day);
      if (select) { program.days[Number(button.dataset.day)].slots.push(select.value); saveProgram(); state.draft = null; render(); }
      return;
    }
    if (action === "save-day-assignments") {
      const chosen = {};
      for (const select of $all("[data-assign-slot]")) chosen[select.dataset.assignSlot] = Number(select.value);
      for (let dayIndex = 0; dayIndex < program.days.length; dayIndex++) {
        const day = program.days[dayIndex];
        // Lifts that stay on this day keep their order; newly moved lifts go at the end.
        const staying = day.slots.filter(function (slot) { return chosen[slot] === dayIndex + 1; });
        const arriving = D.ALL_SLOTS.filter(function (slot) { return chosen[slot] === dayIndex + 1 && !staying.includes(slot); });
        day.slots = staying.concat(arriving);
      }
      saveProgram(); state.draft = null; render(); toast("Saved."); return;
    }
    if (action === "save-days") {
      for (const area of $all("[data-day-accessories]")) {
        program.days[Number(area.dataset.dayAccessories)].accessories = area.value.split("\n").map(function (n) { return n.trim(); }).filter(function (n) { return n !== ""; });
      }
      saveProgram(); state.draft = null; precacheProgramImages(); render(); toast("Saved."); return;
    }
    if (action === "save-picture") {
      const label = $("#picture-choice").value;
      const name = state.ui.pictureName;
      if (label === "Automatic match") delete program.image_choices[name];
      else for (const entry of state.catalog) if (entry.name === label) program.image_choices[name] = entry.id;
      saveProgram(); precacheProgramImages(); render(); toast("Picture saved."); return;
    }
    if (action === "export") { exportProgram(); return; }
    if (action === "load-demo") {
      fetch(DATA_BASE + "demo_program.json").then(function (response) { return response.text(); })
        .then(importProgramText).catch(function () { toast("The demo file is not available offline yet."); });
      return;
    }
    if (action === "new-program") { state.setup = null; state.page = "setup"; render(); window.scrollTo(0, 0); return; }
    if (action === "reset-program") {
      if (window.confirm("Delete the program and every logged workout from this phone? Export first if you want a copy.")) { replaceProgram(null); render(); }
      return;
    }
  }
  function bindEvents() {
    document.body.addEventListener("click", function (event) {
      const picture = event.target.closest("img[data-zoom]");
      if (picture) { openImageViewer(picture.getAttribute("src"), picture.getAttribute("data-name") || ""); return; }
      const button = event.target.closest("[data-action]");
      if (button) handleAction(button);
    });
    document.body.addEventListener("input", function (event) {
      const target = event.target;
      if (target.dataset.liftField) handleLiftInput(target, "input");
      else if (target.dataset.accField) handleAccessoryInput(target);
      else if (target.dataset.field === "session-notes") ensureDraft().notes = target.value;
      else if (target.dataset.setup && ["typed", "max", "accessories", "age", "bodyweight"].includes(target.dataset.setup)) handleSetupChange(target);
    });
    document.body.addEventListener("change", function (event) {
      const target = event.target;
      if (target.dataset.liftField === "single_at_8") handleLiftInput(target, "change");
      else if (target.dataset.setup && !["typed", "max", "accessories", "age", "bodyweight"].includes(target.dataset.setup)) handleSetupChange(target);
      else if (target.dataset.field === "chart") { state.ui.chart = target.value; render(); }
      else if (target.dataset.field === "settingsLift") { state.ui.settingsLift = target.value; render(); }
      else if (target.dataset.field === "tablesLift") { state.ui.tablesLift = target.value; render(); }
      else if (target.dataset.field === "pictureName") { state.ui.pictureName = target.value; render(); }
      else if (target.id === "import-file" && target.files && target.files[0]) {
        const reader = new FileReader();
        reader.onload = function () { importProgramText(String(reader.result)); };
        reader.readAsText(target.files[0]);
      }
    });
    document.body.addEventListener("toggle", function (event) {
      const details = event.target;
      if (details.dataset && details.dataset.section) state.ui.open[details.dataset.section] = details.open;
    }, true);
  }

  function findDataBase() {
    // Try the standalone layout first, then the full-project layout.
    return fetch("./data/exercises.json").then(function (response) {
      if (response.ok) return "./data/";
      throw new Error("not here");
    }).catch(function () {
      return fetch("../data/exercises.json").then(function (response) {
        if (response.ok) return "../data/";
        return "./data/";
      }).catch(function () { return "./data/"; });
    });
  }

  function start() {
    bindEvents();
    state.program = loadProgram();
    render();
    // Ask the browser not to evict this site's storage when space runs low.
    if (navigator.storage && navigator.storage.persist) {
      navigator.storage.persist().catch(function () {});
    }
    findDataBase().then(function (base) {
      DATA_BASE = base;
      return fetch(DATA_BASE + "exercises.json");
    }).then(function (response) { return response.json(); })
      .then(function (catalog) { state.catalog = catalog; render(); precacheProgramImages(); })
      .catch(function () { state.catalog = []; });
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("./sw.js").catch(function () {});
    }
  }
  start();
})();
