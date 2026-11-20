# Study Coach

A spaced-repetition tutor that runs inside [Claude Code](https://claude.com/claude-code).
Claude walks you through a deck of topics in order: it asks what you already know, teaches
the gaps (overview first, then why it matters, then the one equation worth knowing), checks
you with questions, and schedules each topic for review before you forget it.

The first deck, `ml-interview`, covers ~150 ML interview concepts (RL, LLMs, generative
models, distributed training, classical ML, linear algebra), ordered as a learning path.

## Use

Open this folder in Claude Code, then:

| Command | What it does |
| --- | --- |
| `/study` | Due reviews first, then 3 new topics. `/study ppo` jumps to a topic. |
| `/review` | Only what's due. |
| `/mock [unit]` | Mock interview over topics you've already seen. |
| `/status` | Progress by unit, weak points, what's due. |
| `/new-deck <name>` | Turn a pasted topic list into a new deck. |

Or just say "let's study".

## How it works

- `CLAUDE.md` is the tutor's teaching protocol (probe → overview → deepen → check → record).
- `decks/<name>/deck.json` holds topics in order, each with checkpoint questions, a tier
  (`core` / `solid` / `aware`) and a reference. Format: [decks/README.md](decks/README.md).
- `tools/srs.py` is the scheduler (standard-library Python 3.10+). Grades 0–3 move a topic
  between Leitner boxes with review gaps of 0, 1, 3, 7, 16, 35, 75 days. It also keeps notes
  and specific weak points, which the tutor targets on review.
- `progress/` is your state: per-deck progress and `profile.md` (how you learn). It's committed
  so it syncs between machines; make the repo private if you'd rather keep it to yourself.

```bash
python tools/srs.py today      # what's due + next new topics
python tools/srs.py status     # progress summary
python tools/srs.py show ppo   # a topic's checkpoints and history
python tools/srs.py --help
```

## Another subject

Run `/new-deck <name>` and paste a topic list, or write `decks/<name>/deck.json` by hand.
Switch the default in `progress/config.json`, or pass `--deck <name>`.
