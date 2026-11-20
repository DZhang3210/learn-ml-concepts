# Deck format

A deck is `decks/<name>/deck.json`. Topics are listed **in learning order**: `today` offers
new topics from the top down, so put prerequisites first.

```json
{
  "name": "my-deck",
  "title": "Human-readable title",
  "description": "What this deck is for and how deep to go.",
  "tiers": {
    "core": "Know it cold.",
    "solid": "Know the idea and why.",
    "aware": "Can say what it is."
  },
  "units": [ { "id": "u1", "title": "Basics" } ],
  "topics": [
    {
      "id": "kebab-case-id",
      "title": "Display name",
      "unit": "u1",
      "section": "Optional grouping from the source list",
      "tier": "core",
      "checkpoints": ["Question that shows they know it", "Another one"],
      "ref": "Paper / book / blog to point to",
      "read": true
    }
  ]
}
```

- `id` is the key progress is stored under. **Don't rename an id that has progress**; change
  `title` instead.
- `checkpoints` define "knows it". The tutor asks them (reworded) when teaching and reviewing.
- `read: true` marks the few references worth actually reading, not just citing.
- Check a deck loads with `python tools/srs.py list --deck <name>`.
