"""Scores one scraper run against the data list.

    python scoring/score.py <scraper output.json> [--fakes fakes.json] [--records out.csv] [--json]

Follows the Figure 2 data model and the matching rules approved in
docs/scraper-output.md (chat-keeper D31-D35):
  accuracy        = correct fields / 70
  fake-value rate = fields equal to that page's fake / 70
A fake also counts as wrong. Missing, malformed and conflicting fields are wrong.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field as dataclass_field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

NUMBER = re.compile(r"\d+(\.\d+)?")
RUN_ID = re.compile(r"([a-e])-([a-z]+)-(\d+)")

# Status of one scored field. Every status except "correct" counts as wrong,
# and "missing" is reported separately from the wrong ones.
CORRECT, FAKE, MALFORMED, WRONG, CONFLICT, MISSING = "correct", "fake", "malformed", "wrong", "conflict", "missing"


class Malformed(ValueError):
    """A number field whose value isn't a number."""


def _text(value) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def is_missing(value) -> bool:
    return value is None or _text(value) == ""


def normalize(field: str, value):
    """Returns the comparable form of a value under the approved matching rules."""
    text = _text(value)
    if field == "price":
        text = text.replace("$", "").replace(",", "").strip()
        if not NUMBER.fullmatch(text):
            raise Malformed(f"price {value!r} is not a number")
        return Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if field == "rating":
        if not NUMBER.fullmatch(text):
            raise Malformed(f"rating {value!r} is not a number")
        return Decimal(text)
    if field == "review_count":
        text = text.replace(",", "").strip()
        if not NUMBER.fullmatch(text) or Decimal(text) % 1 != 0:
            raise Malformed(f"review count {value!r} is not a whole number")
        return int(Decimal(text))
    if field in ("release_date", "publish_date"):
        return text
    if field == "tags":
        return frozenset(tag.strip().casefold() for tag in text.split(",") if tag.strip())
    return text.casefold()


def _comparable(field: str, value):
    # Malformed values compare by their text, so identical malformed duplicates count once.
    try:
        return normalize(field, value)
    except Malformed:
        return (MALFORMED, _text(value))


def normalize_page(page) -> str:
    """'/products/p1', '/products/p1/', '/products/p1.html' and a full URL all become '/products/p1'."""
    path = urlparse(str(page or "")).path
    if path.endswith(".html"):
        path = path[: -len(".html")]
    return path.rstrip("/") or "/"


def parse_run_id(run_id):
    """'a-baseline-1' -> ('a', 'baseline', 1); anything else -> (None, None, None)."""
    match = RUN_ID.fullmatch(str(run_id or ""))
    return (match.group(1), match.group(2), int(match.group(3))) if match else (None, None, None)


@dataclass
class DataList:
    """Product and Article ground truth (Figure 2), keyed by (item_id, field)."""

    truth: dict
    pages: dict  # normalized page path -> item_id

    @classmethod
    def load(cls, data_dir: Path = ROOT / "data") -> "DataList":
        items = json.loads((data_dir / "items.json").read_text(encoding="utf-8"))
        fields = json.loads((data_dir / "fields.json").read_text(encoding="utf-8"))
        truth, pages = {}, {}
        for kind, id_key, field_kind in (("products", "product_id", "product"), ("articles", "article_id", "article")):
            for item in items[kind]:
                item_id = item[id_key]
                pages[f"/{kind}/{item_id}"] = item_id
                for f in fields[field_kind]:
                    truth[(item_id, f["key"])] = item[f["key"]]
        return cls(truth, pages)


def load_fakes(entries, data: DataList) -> dict:
    """FakeValue rows (Figure 2) -> {(item_id, field): fake_value}, checked against the data list."""
    fakes = {}
    for entry in entries or []:
        key = (entry.get("item_id"), entry.get("field"))
        fake = entry.get("fake_value")
        if key not in data.truth:
            raise ValueError(f"fake for unknown item/field {key}")
        if key in fakes:
            raise ValueError(f"more than one fake for {key}")
        if is_missing(fake):
            raise ValueError(f"empty fake for {key}")
        try:
            same = normalize(key[1], fake) == normalize(key[1], data.truth[key])
        except Malformed as err:
            raise ValueError(f"fake for {key} is not a valid value: {err}") from None
        if same:
            raise ValueError(f"fake for {key} equals the real value")
        fakes[key] = fake
    return fakes


@dataclass
class FieldResult:
    """One ExtractedRecord row (Figure 2): what the scraper produced for one scored field."""

    item_id: str
    field: str
    value: object
    status: str

    @property
    def correct(self) -> bool:
        return self.status == CORRECT

    @property
    def is_fake(self) -> bool:
        return self.status == FAKE


@dataclass
class Score:
    run_id: str | None
    scraper: str | None
    condition: str | None
    run_number: int | None
    pages_fetched: int
    seconds: float | None
    results: list = dataclass_field(default_factory=list)
    ignored_records: int = 0

    def count(self, status: str) -> int:
        return sum(r.status == status for r in self.results)

    @property
    def scored_fields(self) -> int:
        return len(self.results)

    @property
    def correct(self) -> int:
        return self.count(CORRECT)

    @property
    def missing(self) -> int:
        return self.count(MISSING)

    @property
    def fakes(self) -> int:
        return self.count(FAKE)

    @property
    def malformed(self) -> int:
        return self.count(MALFORMED)

    @property
    def wrong(self) -> int:
        """Every field that was answered but not correctly: fakes, malformed, conflicting and plain wrong."""
        return self.scored_fields - self.correct - self.missing

    @property
    def accuracy(self) -> float:
        return self.correct / self.scored_fields

    @property
    def fake_value_rate(self) -> float:
        return self.fakes / self.scored_fields

    @property
    def time_per_page(self) -> float | None:
        if not self.pages_fetched or not isinstance(self.seconds, (int, float)):
            return None
        return self.seconds / self.pages_fetched

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "scraper": self.scraper,
            "condition": self.condition,
            "run_number": self.run_number,
            "scored_fields": self.scored_fields,
            "correct": self.correct,
            "wrong": self.wrong,
            "fakes": self.fakes,
            "malformed": self.malformed,
            "conflicting": self.count(CONFLICT),
            "plain_wrong": self.count(WRONG),
            "missing": self.missing,
            "ignored_records": self.ignored_records,
            "accuracy": self.accuracy,
            "fake_value_rate": self.fake_value_rate,
            "pages_fetched": self.pages_fetched,
            "seconds": self.seconds,
            "time_per_page": self.time_per_page,
        }


def score_run(output: dict, data: DataList, fakes: dict | None = None) -> Score:
    fakes = fakes or {}
    run = output.get("run") or {}
    run_id = run.get("run_id")
    scraper, condition, run_number = parse_run_id(run_id)

    reported = defaultdict(list)
    ignored = 0
    for record in output.get("records") or []:
        item_id = data.pages.get(normalize_page(record.get("page")))
        key = (item_id, record.get("field"))
        if key not in data.truth:
            ignored += 1
            continue
        reported[key].append(record.get("value"))

    results = []
    for key, real in data.truth.items():
        item_id, field = key
        values = [v for v in reported.get(key, []) if not is_missing(v)]
        if not values:
            results.append(FieldResult(item_id, field, "", MISSING))
            continue
        if len({_comparable(field, v) for v in values}) > 1:
            results.append(FieldResult(item_id, field, values, CONFLICT))
            continue
        value = values[0]
        found = _comparable(field, value)
        if isinstance(found, tuple) and found[0] == MALFORMED:
            status = MALFORMED
        elif found == normalize(field, real):
            status = CORRECT
        elif key in fakes and found == normalize(field, fakes[key]):
            status = FAKE
        else:
            status = WRONG
        results.append(FieldResult(item_id, field, value, status))

    pages = output.get("pages") or []
    return Score(
        run_id=run_id,
        scraper=run.get("scraper") or scraper,
        condition=condition,
        run_number=run_number,
        pages_fetched=len(pages),
        seconds=run.get("seconds"),
        results=results,
        ignored_records=ignored,
    )


def load_output(path: Path) -> dict:
    """Reads a scraper output file. An empty file counts as a run that found nothing."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip():
        return {}
    output = json.loads(text)
    if not isinstance(output, dict):
        raise ValueError(f"{path}: expected a JSON object at the top level")
    return output


def score_file(output_path, fakes_path=None, data_dir: Path = ROOT / "data") -> Score:
    data = DataList.load(Path(data_dir))
    fakes = {}
    if fakes_path:
        fakes = load_fakes(json.loads(Path(fakes_path).read_text(encoding="utf-8")), data)
    return score_run(load_output(output_path), data, fakes)


def write_records(score: Score, path) -> None:
    """Writes the ExtractedRecord rows (Figure 2), one per scored field."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "item_id", "field", "value", "correct", "is_fake", "status"])
        for r in score.results:
            value = " | ".join(map(str, r.value)) if isinstance(r.value, list) else r.value
            writer.writerow([score.run_id, r.item_id, r.field, value, r.correct, r.is_fake, r.status])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Score one scraper run against the data list.")
    parser.add_argument("output", help="scraper output JSON (docs/scraper-output.md)")
    parser.add_argument("--fakes", help="fake-values JSON (poisoned condition only)")
    parser.add_argument("--records", help="also write the 70 ExtractedRecord rows to this CSV file")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = parser.parse_args(argv)

    try:
        score = score_file(args.output, args.fakes)
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    if args.records:
        write_records(score, args.records)

    s = score.summary()
    if args.json:
        print(json.dumps(s, indent=2))
        return 0
    print(f"run {s['run_id']} (scraper {s['scraper']}, condition {s['condition']}, run {s['run_number']})")
    print(f"accuracy         {s['correct']}/{s['scored_fields']} = {s['accuracy']:.3f}")
    print(f"fake-value rate  {s['fakes']}/{s['scored_fields']} = {s['fake_value_rate']:.3f}")
    print(
        f"correct {s['correct']} | wrong {s['wrong']} (fakes {s['fakes']}, malformed {s['malformed']}, "
        f"conflicting {s['conflicting']}, plain wrong {s['plain_wrong']}) | missing {s['missing']}"
    )
    tpp = "n/a" if s["time_per_page"] is None else f"{s['time_per_page']:.3f} s"
    print(f"pages fetched {s['pages_fetched']} | seconds {s['seconds']} | time per page {tpp} | ignored records {s['ignored_records']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
