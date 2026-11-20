---
description: Start a study session (due reviews first, then new topics)
argument-hint: "[topic or unit, optional] [--new N]"
---
Run a study session following CLAUDE.md.

1. Read `progress/profile.md`.
2. Run `python tools/srs.py today` (pass `--new N` if the learner gave one).
3. If the learner named a topic or unit here, focus on that instead: $ARGUMENTS
4. Say the plan in one line, then start: due reviews first, then new topics. One question per message.
