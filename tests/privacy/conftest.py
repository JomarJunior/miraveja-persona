"""The no-network guard (FR-016). Imported by tests/conftest.py so it covers the whole suite."""

from __future__ import annotations

import socket
from collections.abc import Iterator
from typing import Any

import pytest


class NetworkUsed(AssertionError):
    pass


def _refuse(*_args: Any, **_kwargs: Any) -> Any:
    raise NetworkUsed("miraveja-persona must never open a network connection (FR-016)")


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(socket.socket, "connect", _refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)
    monkeypatch.setattr(socket, "getaddrinfo", _refuse)
    yield
