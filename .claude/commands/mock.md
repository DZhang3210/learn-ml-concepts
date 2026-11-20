---
description: Mock interview over topics already studied
argument-hint: "[unit id, section or topics, optional]"
---
Run a mock ML interview. Focus: $ARGUMENTS (if empty, mix across everything already seen).

1. Run `python tools/srs.py list` and pick only topics that have been seen (not "new").
   Lean toward `core` tier and topics with open weak points.
2. Act as an interviewer, not a tutor: one question at a time, no hints, realistic follow-ups
   ("why?", "what breaks if...", "how would you implement it?"). Mix definition, comparison,
   and "design/debug" questions (e.g. "your PPO run's KL explodes, what do you check?").
3. Run about 6-8 questions unless told otherwise. Don't give feedback until the end.
4. At the end: per-question verdict (one line each), the two biggest gaps, and record each
   topic touched with `python tools/srs.py record` (grade honestly, add --weak for gaps).
