"""Immutable models of a persona definition and an author's note.

They mirror the hub schemas. A definition is read once, at birth (FR-018), so these
models expose no way to reload, merge or update one.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SLUG_PATTERN = r"^[a-z0-9-]{1,64}$"

PersonaId = Annotated[str, StringConstraints(pattern=UUID_PATTERN)]
Slug = Annotated[str, StringConstraints(pattern=SLUG_PATTERN)]
Prose = Annotated[str, StringConstraints(min_length=1, max_length=4000)]
When = Annotated[str, StringConstraints(min_length=1, max_length=200)]
Name = Annotated[str, StringConstraints(min_length=1, max_length=80)]


class Part(BaseModel):
    model_config = ConfigDict(
        frozen=True, extra="forbid", alias_generator=to_camel, populate_by_name=True
    )


class Identity(Part):
    id: PersonaId
    public_name: Name
    about: Prose
    openly_ai: Literal[True] = Field(alias="openlyAI")
    self_understanding: Prose | None = None


class Taste(Part):
    drawn_to: Prose
    themes: Annotated[tuple[Prose, ...], Field(min_length=1)]
    styles_and_media: Prose
    dislikes: Prose | None = None


class Voice(Part):
    speech: Prose
    temperament: Prose


class Tendencies(Part):
    presence: Prose
    work: Prose


class LoreName(Part):
    name: Name
    is_: Literal["person", "place", "group", "work", "other"] = Field(alias="is")


class Lore(Part):
    names: tuple[LoreName, ...] = ()


class SeedMemory(Part):
    id: Slug
    when: When
    happened: Prose


class SharedPast(Part):
    story: Slug
    participants: Annotated[tuple[PersonaId, ...], Field(min_length=2)]
    when: When
    happened: Prose
    telling: Literal["agreed", "intended-difference"]


class Definition(Part):
    """One persona's starting point. Frozen: read once, never re-applied."""

    miraveja_persona: Literal[1]
    nature: Literal["resident", "synthetic"]
    identity: Identity
    taste: Taste
    voice: Voice
    tendencies: Tendencies
    cares: Annotated[tuple[Prose, ...], Field(min_length=1)]
    craft: Prose | None = None
    self_image: Prose | None = None
    lore: Lore | None = None
    seed_memories: Annotated[tuple[SeedMemory, ...], Field(min_length=1)]
    shared_pasts: tuple[SharedPast, ...] = ()


class NoteAbout(Part):
    persona: PersonaId | None = None
    story: Slug | None = None
    seed_memory: Slug | None = None


class AuthorNote(Part):
    """Team-only lore. No runtime ever loads one (FR-032)."""

    miraveja_author_note: Literal[1]
    nature: Literal["resident", "synthetic"]
    about: NoteAbout
    truth: Annotated[str, StringConstraints(min_length=1, max_length=8000)]
    written_by: Name
    written_on: str
