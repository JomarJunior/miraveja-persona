"""`decide` records a team member's call on an uncertain finding (T044; FR-017, R-6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona.cli import main
from miraveja_persona.vault import check_tree
from miraveja_persona.yamlio import read_document

from ..conftest import make_vault


@pytest.fixture
def vault(tmp_path: Path, examples: Path) -> Path:
    root = make_vault(tmp_path / "vault", examples, resident=True)
    pellam = root / "personas/pellam/definition.persona.yaml"
    text = pellam.read_text(encoding="utf-8")
    pellam.write_text(
        text.replace("crewed opposing boats", "crewed opposing boats in a bitter race").replace(
            "telling: agreed", "telling: intended-difference", 1
        ),
        encoding="utf-8",
    )
    ivo = root / "personas/ivo/definition.persona.yaml"
    ivo.write_text(
        ivo.read_text(encoding="utf-8").replace(
            "telling: agreed", "telling: intended-difference", 1
        ),
        encoding="utf-8",
    )
    return root


def uncertain(vault: Path) -> list[str]:
    return [
        f.fingerprint
        for f in check_tree(vault).findings
        if f.certainty == "uncertain" and not f.decided
    ]


def test_undecided_uncertain_findings_exit_3(vault: Path) -> None:
    assert uncertain(vault)
    assert (
        main(
            ["check", "--tree", str(vault), str(vault / "personas/pellam/definition.persona.yaml")]
        )
        == 3
    )


def test_decide_records_and_check_passes(vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for fingerprint in uncertain(vault):
        assert (
            main(
                ["decide", fingerprint, "--as", "accepted", "--by", "tester", "--tree", str(vault)]
            )
            == 0
        )
    entries = read_document(vault / "personas/pellam/decisions.yaml").data
    assert {"finding", "decision", "by", "on"} <= set(entries[0])
    assert entries[0]["decision"] == "accepted" and entries[0]["by"] == "tester"
    capsys.readouterr()
    assert (
        main(
            ["check", "--tree", str(vault), str(vault / "personas/pellam/definition.persona.yaml")]
        )
        == 0
    )
    assert "decided accepted" in capsys.readouterr().out


def test_certain_findings_cannot_be_decided(vault: Path) -> None:
    pellam = vault / "personas/pellam/definition.persona.yaml"
    pellam.write_text(
        pellam.read_text().replace("Works slowly", "Posts three pieces every day. Works slowly")
    )
    certain = [f.fingerprint for f in check_tree(vault).findings if f.certainty == "certain"]
    assert certain
    assert main(["decide", certain[0], "--as", "accepted", "--by", "t", "--tree", str(vault)]) == 1


def test_unknown_fingerprint_is_refused(vault: Path) -> None:
    assert (
        main(
            ["decide", "past.x:/y:00000000", "--as", "accepted", "--by", "t", "--tree", str(vault)]
        )
        == 1
    )


def test_stale_decisions_are_reported(vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for fingerprint in uncertain(vault):
        main(["decide", fingerprint, "--as", "not-an-issue", "--by", "t", "--tree", str(vault)])
    pellam = vault / "personas/pellam/definition.persona.yaml"
    pellam.write_text(pellam.read_text().replace(" in a bitter race", ""))
    capsys.readouterr()
    main(["check", "--tree", str(vault), str(pellam)])
    assert "stale decision" in capsys.readouterr().err


def test_reordering_keeps_decisions(vault: Path) -> None:
    for fingerprint in uncertain(vault):
        main(["decide", fingerprint, "--as", "accepted", "--by", "t", "--tree", str(vault)])
    pellam = vault / "personas/pellam/definition.persona.yaml"
    data = read_document(pellam).data
    text = pellam.read_text()
    first = text.index("  - story: junior-regatta")
    second = text.index("  - story: lighthouse-mural")
    swapped = text[:first] + text[second:] + text[first:second]
    pellam.write_text(swapped if swapped.endswith("\n") else swapped + "\n")
    assert read_document(pellam).data["sharedPasts"][0]["story"] == data["sharedPasts"][1]["story"]
    assert uncertain(vault) == []
