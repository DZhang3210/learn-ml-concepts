---
description: Review only topics that are due, no new material
---
Run a review-only session following the "Reviewing a due topic" section of CLAUDE.md.

1. Run `python tools/srs.py today --new 0`.
2. For each due topic: `show` it, ask a checkpoint question cold (target open weak points
   first, vary the wording), give feedback, `record` the grade.
3. If nothing is due, say so and when the next review is (`python tools/srs.py status`), and
   offer a new topic instead.
