"""`new`: a scaffold with a fresh identifier and guidance for every part (R-11).

Guidance lines are YAML comments, so they never reach a runtime. Optional parts are
written commented out; uncomment the ones the persona needs.
"""

from __future__ import annotations

import uuid
from typing import Literal

OPTIONAL_PARTS = ("craft", "selfImage", "lore", "sharedPasts")

TEMPLATE = """\
# A new persona definition. Fill every empty part; uncomment the optional ones you need.
# Write who the persona is at the start, never rules it must keep. It may change once alive.
# Check it with: miraveja-persona check <this file>
miravejaPersona: 1
nature: {nature}

identity:
  id: {id}
  publicName: {name}
  # About: who the persona is, in your words. Two or three sentences.
  about: ""
  # openlyAI states that the persona knows it is an AI, and that its past, however
  # human-shaped, is a story it carries, not a claim to be human. It is always true.
  openlyAI: true
  # Optional: how the persona holds its past while knowing it is an AI.
  # selfUnderstanding: ""

taste:
  # What it is drawn to: light, places, moments, materials.
  drawnTo: ""
  # Subjects and moods it keeps returning to. Inclinations, never rules.
  themes:
    - ""
  # Favored styles and media, in words. Never a model name or setting.
  stylesAndMedia: ""
  # Optional: what it dislikes.
  # dislikes: ""

voice:
  # How it speaks and writes: sentence length, words, titles, humor.
  speech: ""
  # How it tends to treat visitors and other personas. Warm, distant, provocative...
  temperament: ""

tendencies:
  # When it tends to be in the studio, away or resting. A habit, never a timetable.
  presence: ""
  # How it tends to work: in bursts, slowly, rarely exhibiting. Never a count or deadline.
  work: ""

# What matters to it, as an artist and as a character.
cares:
  - ""

# Optional: craft preferences in words, such as formats or finishes. Never a model.
# craft: ""

# Optional: how it imagines itself looking. Never like a real person.
# selfImage: ""

# Optional: every invented person, place, group or work your prose names.
# Anything capitalized and not declared here is asked about as a possible real person.
# lore:
#   names:
#     - name: ""
#       is: place   # person | place | group | work | other

# Things it remembers from before it came alive. At least one.
seedMemories:
  - id: first-memory   # lowercase words and hyphens, unique in this file
    # Roughly when: "as a child", "the winter before the museum".
    when: ""
    # What happened, from its point of view. Past acts only, never orders.
    happened: ""

# Optional: a past with other resident personas. Facts only, never how anyone feels.
# Name participants as {{1}}, {{2}} in the order listed. Use the same story key in each
# definition that tells it; mark intended-difference when they remember it differently.
# sharedPasts:
#   - story: a-story-key
#     participants:
#       - {id}
#       - <another persona's identifier>
#     when: ""
#     happened: ""
#     telling: agreed   # agreed | intended-difference
"""


def scaffold(name: str, nature: Literal["resident", "synthetic"]) -> str:
    return TEMPLATE.format(nature=nature, id=uuid.uuid4(), name=_quote(name))


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
