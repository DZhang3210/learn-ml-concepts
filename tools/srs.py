"""Study Coach scheduler: decks, progress and spaced review.

Leitner-style boxes: each topic sits in box 0-6. A good answer moves it up, a bad one
sends it back to box 1. Higher box = longer gap before the next review.
No dependencies beyond the standard library.

    python tools/srs.py today                 what to review and learn now
    python tools/srs.py show <id>             a topic's card and history
    python tools/srs.py record <id> <0-3> [--note TEXT] [--weak TEXT]... [--resolve TEXT]... [--placement]
    python tools/srs.py status                progress by unit, weak spots, upcoming reviews
    python tools/srs.py list [--unit u4]      every topic with its state
    python tools/srs.py search <text>         find topic ids
    python tools/srs.py reset <id>            forget a topic's progress

All commands take --deck NAME (default from progress/config.json) and --date YYYY-MM-DD
(pretend today is that date; for testing).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECKS = ROOT / "decks"
PROGRESS = ROOT / "progress"
SCHEMA_VERSION = 1

# Days until the next review for each box. Box 0 means "seen, failed, due again today".
INTERVALS = [0, 1, 3, 7, 16, 35, 75]
MAX_BOX = len(INTERVALS) - 1
GRADES = {0: "blank", 1: "shaky", 2: "good", 3: "solid"}


# ---------- storage ----------

def default_deck() -> str:
    cfg = PROGRESS / "config.json"
    if cfg.exists():
        return json.loads(cfg.read_text(encoding="utf-8")).get("deck", "ml-interview")
    return "ml-interview"


def load_deck(name: str) -> dict:
    path = DECKS / name / "deck.json"
    if not path.exists():
        sys.exit(f"No deck '{name}' at {path.relative_to(ROOT)}. Decks: {', '.join(list_decks()) or 'none'}")
    deck = json.loads(path.read_text(encoding="utf-8"))
    ids = [t["id"] for t in deck["topics"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"Deck '{name}' has duplicate topic ids: {', '.join(sorted(dupes))}")
    units = {u["id"] for u in deck.get("units", [])}
    for t in deck["topics"]:
        if units and t.get("unit") not in units:
            sys.exit(f"Topic '{t['id']}' has unknown unit '{t.get('unit')}'")
    return deck


def list_decks() -> list[str]:
    return sorted(p.parent.name for p in DECKS.glob("*/deck.json"))


def progress_path(name: str) -> Path:
    return PROGRESS / f"{name}.json"


def load_progress(name: str) -> dict:
    path = progress_path(name)
    if not path.exists():
        return {"schemaVersion": SCHEMA_VERSION, "deck": name, "topics": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_progress(name: str, prog: dict) -> None:
    PROGRESS.mkdir(exist_ok=True)
    tmp = progress_path(name).with_suffix(".tmp")
    tmp.write_text(json.dumps(prog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(progress_path(name))


# ---------- scheduling ----------

def next_box(box: int | None, grade: int, placement: bool) -> int:
    if placement:
        return 3  # already knew it: first check in a week
    if box is None:
        box = 0
    if grade == 0:
        return 0
    if grade == 1:
        return 1
    if grade == 2:
        return min(max(box, 1) + 1, MAX_BOX)
    return min(max(box, 1) + 2, MAX_BOX)


def state_of(entry: dict | None) -> str:
    if not entry:
        return "new"
    box = entry["box"]
    if box >= 5:
        return "mastered"
    if box >= 3:
        return "known"
    return "learning"


def is_due(entry: dict | None, today: date) -> bool:
    return bool(entry) and date.fromisoformat(entry["due"]) <= today


# ---------- helpers ----------

def find_topic(deck: dict, query: str) -> dict:
    q = query.lower()
    by_id = {t["id"]: t for t in deck["topics"]}
    if q in by_id:
        return by_id[q]
    prefix = [t for t in deck["topics"] if t["id"].startswith(q)]
    if len(prefix) == 1:
        return prefix[0]
    hits = [t for t in deck["topics"] if q in t["id"] or q in t["title"].lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"No topic matches '{query}'. Try: python tools/srs.py search {query}")
    sys.exit("Ambiguous, did you mean: " + ", ".join(f"{t['id']}" for t in hits))


def unit_title(deck: dict, unit_id: str) -> str:
    for u in deck.get("units", []):
        if u["id"] == unit_id:
            return u["title"]
    return unit_id


def line(t: dict, entry: dict | None, today: date) -> str:
    st = state_of(entry)
    extra = ""
    if entry:
        days = (date.fromisoformat(entry["due"]) - today).days
        when = "due now" if days <= 0 else f"due in {days}d"
        extra = f"  box {entry['box']}, {when}"
        if entry.get("weak"):
            extra += f", {len(entry['weak'])} weak"
    star = " [read]" if t.get("read") else ""
    return f"  {t['id']:<26} {t['title']}  ({t.get('tier', '-')}, {st}){extra}{star}"


# ---------- commands ----------

def cmd_today(deck: dict, prog: dict, today: date, args) -> None:
    topics = prog["topics"]
    due = [t for t in deck["topics"] if is_due(topics.get(t["id"]), today)]
    due.sort(key=lambda t: (topics[t["id"]]["due"], topics[t["id"]]["box"]))
    fresh = [t for t in deck["topics"] if t["id"] not in topics][: args.new]

    print(f"Deck: {deck['title']}  ({today.isoformat()})")
    print(f"\nDue reviews ({len(due)}):" if due else "\nDue reviews: none")
    for t in due:
        print(line(t, topics[t["id"]], today))
    if fresh:
        print(f"\nNext new topics (in deck order, {args.new} per session):")
        for t in fresh:
            print(line(t, None, today) + f"  - {unit_title(deck, t['unit'])}")
    else:
        print("\nNo new topics left. Every topic has been seen.")
    seen = len(topics)
    print(f"\nSeen {seen}/{len(deck['topics'])} topics.")


def cmd_show(deck: dict, prog: dict, today: date, args) -> None:
    t = find_topic(deck, args.topic)
    e = prog["topics"].get(t["id"])
    print(f"{t['title']}  [{t['id']}]")
    print(f"Unit: {unit_title(deck, t['unit'])}   Section: {t.get('section', '-')}   Tier: {t.get('tier', '-')}")
    if t.get("tier") and deck.get("tiers", {}).get(t["tier"]):
        print(f"Tier means: {deck['tiers'][t['tier']]}")
    print(f"Reference: {t.get('ref', '-')}" + ("   (worth actually reading)" if t.get("read") else ""))
    print("\nCheckpoints:")
    for i, c in enumerate(t.get("checkpoints", []), 1):
        print(f"  {i}. {c}")
    if not e:
        print("\nProgress: new (never studied)")
        return
    days = (date.fromisoformat(e["due"]) - today).days
    print(f"\nProgress: {state_of(e)}, box {e['box']}, due {e['due']} ({'now' if days <= 0 else f'in {days}d'})")
    if e.get("weak"):
        print("Weak points (open):")
        for w in e["weak"]:
            print(f"  - {w}")
    if e.get("resolved"):
        print("Weak points (fixed):")
        for w in e["resolved"][-5:]:
            print(f"  - {w}")
    print("History:")
    for h in e.get("history", [])[-8:]:
        note = f" - {h['note']}" if h.get("note") else ""
        tag = " (placement)" if h.get("placement") else ""
        print(f"  {h['date']}  grade {h['grade']} ({GRADES[h['grade']]}){tag}{note}")


def cmd_record(deck: dict, prog: dict, today: date, args) -> None:
    t = find_topic(deck, args.topic)
    if args.grade not in GRADES:
        sys.exit("Grade must be 0 (blank), 1 (shaky), 2 (good) or 3 (solid).")
    if args.placement and args.grade != 3:
        sys.exit("--placement means they already knew it: use it only with grade 3.")
    e = prog["topics"].get(t["id"]) or {"box": None, "weak": [], "resolved": [], "history": []}
    box = next_box(e["box"], args.grade, args.placement)
    e["box"] = box
    e["due"] = (today + timedelta(days=INTERVALS[box])).isoformat()
    e["last"] = today.isoformat()
    for r in args.resolve or []:
        match = [w for w in e["weak"] if r.lower() in w.lower()]
        if not match:
            print(f"(no open weak point matches '{r}', skipped)")
        for w in match:
            e["weak"].remove(w)
            e["resolved"].append(w)
    for w in args.weak or []:
        if w not in e["weak"]:
            e["weak"].append(w)
    h = {"date": today.isoformat(), "grade": args.grade}
    if args.note:
        h["note"] = args.note
    if args.placement:
        h["placement"] = True
    e["history"].append(h)
    prog["topics"][t["id"]] = e
    save_progress(deck["name"], prog)
    print(f"Recorded {t['id']}: grade {args.grade} ({GRADES[args.grade]}) -> box {box}, next review {e['due']}.")


def cmd_status(deck: dict, prog: dict, today: date, args) -> None:
    topics = prog["topics"]
    print(f"Deck: {deck['title']}  ({today.isoformat()})\n")
    print(f"  {'unit':<48} {'new':>4} {'lrn':>4} {'known':>5} {'mast':>4}")
    for u in deck.get("units", []):
        ts = [t for t in deck["topics"] if t["unit"] == u["id"]]
        c = {"new": 0, "learning": 0, "known": 0, "mastered": 0}
        for t in ts:
            c[state_of(topics.get(t["id"]))] += 1
        print(f"  {u['title'][:48]:<48} {c['new']:>4} {c['learning']:>4} {c['known']:>5} {c['mastered']:>4}")
    due_now = sum(is_due(topics.get(t["id"]), today) for t in deck["topics"])
    week = sum(
        1 for t in deck["topics"]
        if topics.get(t["id"]) and today < date.fromisoformat(topics[t["id"]]["due"]) <= today + timedelta(days=7)
    )
    print(f"\nSeen {len(topics)}/{len(deck['topics'])}. Due now: {due_now}. Due in the next 7 days: {week}.")
    weak = [(t, topics[t["id"]]) for t in deck["topics"] if topics.get(t["id"], {}).get("weak")]
    if weak:
        print("\nOpen weak points:")
        for t, e in weak:
            for w in e["weak"]:
                print(f"  {t['id']}: {w}")
    struggling = [t["id"] for t in deck["topics"]
                  if topics.get(t["id"]) and sum(h["grade"] <= 1 for h in topics[t["id"]]["history"]) >= 2]
    if struggling:
        print("\nRepeatedly struggled with: " + ", ".join(struggling))


def cmd_list(deck: dict, prog: dict, today: date, args) -> None:
    for u in deck.get("units", []):
        if args.unit and u["id"] != args.unit:
            continue
        print(f"\n{u['id']}  {u['title']}")
        for t in deck["topics"]:
            if t["unit"] == u["id"]:
                print(line(t, prog["topics"].get(t["id"]), today))
    print(f"\n{len(deck['topics'])} topics.")


def cmd_search(deck: dict, prog: dict, today: date, args) -> None:
    q = args.text.lower()
    hits = [t for t in deck["topics"]
            if q in t["id"] or q in t["title"].lower() or q in t.get("section", "").lower()]
    for t in hits:
        print(line(t, prog["topics"].get(t["id"]), today))
    if not hits:
        print(f"No topic matches '{args.text}'.")


def cmd_reset(deck: dict, prog: dict, today: date, args) -> None:
    t = find_topic(deck, args.topic)
    if prog["topics"].pop(t["id"], None) is None:
        print(f"{t['id']} has no progress.")
        return
    save_progress(deck["name"], prog)
    print(f"Reset {t['id']} to new.")


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--deck", default=None)
    common.add_argument("--date", default=None, help="pretend today is YYYY-MM-DD")

    p = argparse.ArgumentParser(description="Study Coach scheduler", parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("today", parents=[common]); s.add_argument("--new", type=int, default=3)
    s = sub.add_parser("show", parents=[common]); s.add_argument("topic")
    s = sub.add_parser("record", parents=[common]); s.add_argument("topic"); s.add_argument("grade", type=int)
    s.add_argument("--note"); s.add_argument("--weak", action="append"); s.add_argument("--resolve", action="append")
    s.add_argument("--placement", action="store_true")
    sub.add_parser("status", parents=[common])
    s = sub.add_parser("list", parents=[common]); s.add_argument("--unit")
    s = sub.add_parser("search", parents=[common]); s.add_argument("text")
    s = sub.add_parser("reset", parents=[common]); s.add_argument("topic")
    sub.add_parser("decks", parents=[common])

    args = p.parse_args(argv)
    if args.cmd == "decks":
        print("\n".join(list_decks()))
        return
    name = args.deck or default_deck()
    deck = load_deck(name)
    deck["name"] = name
    prog = load_progress(name)
    today = date.fromisoformat(args.date) if args.date else date.today()
    {
        "today": cmd_today, "show": cmd_show, "record": cmd_record, "status": cmd_status,
        "list": cmd_list, "search": cmd_search, "reset": cmd_reset,
    }[args.cmd](deck, prog, today, args)


if __name__ == "__main__":
    main()
