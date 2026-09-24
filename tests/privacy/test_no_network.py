"""Every command runs with the network blocked (FR-016)."""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path

import pytest

from miraveja_persona.cli import main

from ..conftest import make_vault


def test_the_guard_is_active() -> None:
    with pytest.raises(AssertionError):
        socket.create_connection(("127.0.0.1", 9))


def test_every_command_runs_offline(tmp_path: Path, examples: Path) -> None:
    vault = make_vault(tmp_path / "vault", examples)
    pellam = vault / "personas/pellam/definition.persona.yaml"
    assert (
        main(
            [
                "new",
                "--name",
                "Test Persona Nine",
                "--synthetic",
                "-o",
                str(tmp_path / "nine.persona.yaml"),
            ]
        )
        == 0
    )
    assert main(["check", str(pellam)]) == 0
    assert main(["check", "--tree", str(vault), str(pellam)]) in (0, 3)
    assert main(["pasts", str(vault)]) == 0
    assert (
        main(["decide", "rule:/x:00000000", "--as", "accepted", "--by", "t", "--tree", str(vault)])
        == 1
    )
    assert main(["freeze", str(pellam), "--tree", str(vault)]) == 1  # synthetic: refused
    subprocess.run(["git", "init", "-q", str(tmp_path / "repo")], check=True)
    assert main(["guard", str(examples)]) == 0
