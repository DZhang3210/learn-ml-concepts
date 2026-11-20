---
description: Build a new deck from a pasted topic list
argument-hint: "<deck-name>"
---
Build a new deck named `$ARGUMENTS` from the topic list the learner pastes (ask for it if
they haven't). Follow `decks/README.md` for the format.

1. Ask at most two short questions first if needed: the goal (exam, interview, curiosity) and
   how deep (breadth vs depth). Skip if obvious.
2. Group topics into units and order them so prerequisites come first.
3. For each topic write: a stable kebab-case id, title, unit, tier, 1-3 checkpoint questions
   that define "knows it", and a real reference (only cite papers/books you're sure exist;
   say "-" otherwise). Set "read": true only for the few sources truly worth reading.
4. Write `decks/<name>/deck.json`, then run `python tools/srs.py list --deck <name>` to check it loads.
5. Ask whether to make it the default deck (`progress/config.json`).
