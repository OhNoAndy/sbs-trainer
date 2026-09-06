/*
exercise_library.js - exercise catalog lookup, ported from exercise_library.py.

Turns an exercise name into the picture strip to show, in this order:
  1. a library picture the user picked by hand (program.image_choices),
  2. the hand-written SBS name overrides (IMAGE_OVERRIDES, generated from Python),
  3. an exact match on the cleaned-up name,
  4. a fuzzy match (one name contains the other, or they share words),
  5. the placeholder image.
The catalog itself is ../data/exercises.json, shared with the Python app.
*/
"use strict";
(function () {

const IMAGE_OVERRIDES = (typeof window === "undefined")
  ? require("./defaults.js").IMAGE_OVERRIDES
  : window.SBS_IMAGE_OVERRIDES;

const IGNORED_WORDS = ["the", "a", "of", "with", "and", "to", "on", "in"];

function normalizeName(name) {
  let text = String(name).toLowerCase();
  for (const character of ["-", "_", "/", "(", ")", ",", ".", "'", "’"]) {
    text = text.split(character).join(" ");
  }
  return text.split(/\s+/).filter(function (word) { return word !== ""; }).join(" ");
}

function nameWords(name) {
  const words = [];
  for (let word of normalizeName(name).split(" ")) {
    if (word === "" || IGNORED_WORDS.includes(word)) continue;
    if (word.length > 3 && word.endsWith("s")) word = word.slice(0, -1);
    words.push(word);
  }
  return words;
}

function catalogById(catalog) {
  const lookup = {};
  for (const entry of catalog) lookup[entry.id] = entry;
  return lookup;
}

function catalogNames(catalog) {
  const names = [];
  for (const entry of catalog) names.push(entry.name);
  names.sort();
  return names;
}

function findExercise(name, catalog) {
  if (!catalog || catalog.length === 0 || !name || name.trim() === "") return { entry: null, how: "none" };
  const cleaned = normalizeName(name);
  const byId = catalogById(catalog);

  if (IMAGE_OVERRIDES[cleaned] && byId[IMAGE_OVERRIDES[cleaned]]) {
    return { entry: byId[IMAGE_OVERRIDES[cleaned]], how: "override" };
  }
  for (const entry of catalog) {
    if (normalizeName(entry.name) === cleaned) return { entry: entry, how: "exact" };
  }
  let bestEntry = null;
  for (const entry of catalog) {
    const entryName = normalizeName(entry.name);
    if (cleaned.length >= 4 && (entryName.includes(cleaned) || cleaned.includes(entryName))) {
      if (bestEntry === null || entryName.length < normalizeName(bestEntry.name).length) bestEntry = entry;
    }
  }
  if (bestEntry !== null) return { entry: bestEntry, how: "contains" };

  const queryWords = nameWords(name);
  if (queryWords.length === 0) return { entry: null, how: "none" };
  let bestScore = 0;
  for (const entry of catalog) {
    const entryWords = nameWords(entry.name);
    let shared = 0;
    for (const word of queryWords) if (entryWords.includes(word)) shared++;
    const score = shared / queryWords.length;
    const shorterName = bestEntry !== null && entry.name.length < bestEntry.name.length;
    if (score > bestScore || (score === bestScore && score > 0 && shorterName)) {
      bestScore = score;
      bestEntry = entry;
    }
  }
  if (bestScore >= 0.5) return { entry: bestEntry, how: "words" };
  return { entry: null, how: "none" };
}

function imageUrlForEntry(entry, base) {
  if (!entry || !entry.image) return "";
  return base + "images/" + entry.image;
}

function findImageUrl(name, catalog, chosenId, base) {
  if (chosenId) {
    const chosen = imageUrlForEntry(catalogById(catalog)[chosenId], base);
    if (chosen) return chosen;
  }
  const match = findExercise(name, catalog);
  const url = imageUrlForEntry(match.entry, base);
  if (url) return url;
  return base + "images/placeholder.png";
}

function describeMatch(name, catalog, chosenId) {
  const byId = catalogById(catalog);
  if (chosenId && byId[chosenId]) return "Using the library picture you picked: \"" + byId[chosenId].name + "\"";
  const match = findExercise(name, catalog);
  if (!match.entry || !match.entry.image) return "No match in the exercise library, showing the placeholder";
  if (match.how === "override") return "Matched to \"" + match.entry.name + "\" (built-in SBS name mapping)";
  if (match.how === "exact") return "Matched to \"" + match.entry.name + "\" (exact name)";
  return "Best guess: \"" + match.entry.name + "\" (fuzzy match)";
}

const SBS_LIBRARY = { normalizeName, nameWords, catalogById, catalogNames, findExercise, imageUrlForEntry, findImageUrl, describeMatch };

if (typeof module !== "undefined") {
  module.exports = SBS_LIBRARY;
} else {
  window.SBS_LIBRARY = SBS_LIBRARY;
}
})();
