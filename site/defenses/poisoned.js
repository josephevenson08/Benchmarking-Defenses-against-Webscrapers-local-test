//poisoned fills in fake values for scrapers to see, then the page swaps the real values back in after 2 s
// Written by Claude at Joseph's request (Nov 23, chat-keeper D110); the price case is Joseph's own lines.

const config = require("../../config.json"); // for the swap delay (poison_swap_delay_seconds)

// ---------- helpers ----------

// a random item from the list that is not the real value
function pick(list, real, rng) {
  const choices = list.filter((item) => item !== real);
  return choices[Math.floor(rng() * choices.length)];
}

// a random whole number from lo to hi
function between(lo, hi, rng) {
  return lo + Math.floor(rng() * (hi - lo + 1));
}

// made-up words only: none of these are a real brand, category, name or tag on the site
const BRANDS = ["Brookline", "Ostrava", "Pemberly", "Quillon", "Rosmere", "Thistle", "Varden", "Wexley"];
const ADJECTIVES = ["Compact", "Classic", "Deluxe", "Everyday", "Folding", "Premium", "Rustic", "Slim"];
const NOUNS = ["Table", "Lamp", "Rug", "Clock", "Chair", "Mirror", "Bench", "Basket"];
const CATEGORIES = ["Furniture", "Home Decor", "Garden", "Office", "Toys", "Bath", "Storage", "Pets"];
const AVAILABILITY = ["In stock", "Low stock", "Out of stock", "Pre-order"];
const TITLES = [
  "Five Ways to Brighten a Small Room",
  "A Beginner's Guide to Houseplants",
  "How to Pick a Desk Chair",
  "Keeping Your Garden Tools Sharp",
  "Planning a Weekend Bike Ride",
];
const FIRST_NAMES = ["Avery", "Jordan", "Priya", "Marcus", "Elena", "Tomas"];
const LAST_NAMES = ["Lindqvist", "Abara", "Moreau", "Castillo", "Brennan", "Hartley"];
const SENTENCES = [
  "A sturdy everyday pick with a simple design and a two-year warranty.",
  "Light, easy to wipe down and made to last through years of daily use.",
  "A quick guide to the basics, with tips you can use this weekend.",
  "Compact and practical, with a matte finish that suits any room.",
  "Step-by-step advice for getting started without spending much.",
];
const TAGS = ["home", "tips", "garden", "storage", "budget", "diy", "weekend", "decor"];

// ---------- one fake per field (the generator calls this 70 times) ----------

function fakeValue(row, rng) {
  switch (row.key) {
    case "price": { // Joseph's lines
      const real = Number(row.value.replace("$", ""));
      let amount = 10 + rng() * 140;
      amount = Number(amount.toFixed(2));
      if (amount === real) amount = amount + 1;
      return "$" + amount.toFixed(2);
    }
    case "rating": { // 1.0 to 5.0, one decimal
      const real = Number(row.value);
      let amount = Number((1 + rng() * 4).toFixed(1));
      if (amount === real) amount = amount > 3 ? amount - 1 : amount + 1;
      return amount.toFixed(1);
    }
    case "review_count": { // a whole number, with a comma for thousands
      const real = Number(row.value.replace(",", ""));
      let amount = between(50, 9999, rng);
      if (amount === real) amount = amount + 1;
      return amount.toLocaleString("en-US");
    }
    case "sku": { // keep the letters (e.g. "LF-HP-"), new 4 digits
      const letters = row.value.slice(0, 6);
      let digits = between(0, 9999, rng);
      if (letters + String(digits).padStart(4, "0") === row.value) digits = (digits + 1) % 10000;
      return letters + String(digits).padStart(4, "0");
    }
    case "availability":
      return pick(AVAILABILITY, row.value, rng);
    case "release_date":
    case "publish_date": { // YYYY-MM-DD; day 28 or lower so every date exists
      const year = between(2022, 2026, rng);
      const month = String(between(1, 12, rng)).padStart(2, "0");
      let day = between(1, 28, rng);
      if (`${year}-${month}-${String(day).padStart(2, "0")}` === row.value) day = day === 28 ? 27 : day + 1;
      return `${year}-${month}-${String(day).padStart(2, "0")}`;
    }
    case "category":
      return pick(CATEGORIES, row.value, rng);
    case "brand":
      return pick(BRANDS, row.value, rng);
    case "name":
      return pick(BRANDS, null, rng) + " " + pick(ADJECTIVES, null, rng) + " " + pick(NOUNS, null, rng);
    case "title":
      return pick(TITLES, row.value, rng);
    case "author":
      return pick(FIRST_NAMES, null, rng) + " " + pick(LAST_NAMES, null, rng);
    case "description":
    case "summary":
      return pick(SENTENCES, row.value, rng);
    case "tags": { // 3 different tags
      const first = pick(TAGS, null, rng);
      const second = pick(TAGS, first, rng);
      const third = pick(TAGS.filter((tag) => tag !== second), first, rng);
      return first + ", " + second + ", " + third;
    }
    default:
      return "Fake " + row.value; // anything not listed above
  }
}

// ---------- the swap: the text this returns runs in the browser ----------

function script(page) {
  if (!page.valuesPath) return ""; // only item pages have real values to swap in
  const delay = config.poison_swap_delay_seconds * 1000;
  // ${...} is filled in here, when the page is built; everything else runs in the browser
  return `
    setTimeout(async function () {
      const response = await fetch("${page.valuesPath}");
      const data = await response.json();
      document.querySelectorAll(".field").forEach(function (row) {
        const label = row.querySelector(".label").textContent;
        const real = data.fields.find(function (field) { return field.label === label; });
        if (real) row.querySelector(".value").textContent = real.value;
      });
    }, ${delay});`;
}

module.exports = { fakeValue, script };