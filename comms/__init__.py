"""Navitas transport-independent communications package."""

from .protocol import PROTOCOL_VERSION, ProtocolError

__all__ = ["PROTOCOL_VERSION", "ProtocolError"]
