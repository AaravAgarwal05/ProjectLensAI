"""Environment variable loader."""

import os
from pathlib import Path
from typing import Any


class EnvLoader:
    """Load and access environment variables filtered by a prefix."""

    def __init__(self) -> None:
        self._vars: dict[str, str] = {}

    def load(self, prefix: str) -> dict[str, str]:
        """Load all environment variables whose name starts with *prefix*.

        The prefix is stripped from the keys in the returned dict.
        """
        self._vars.clear()
        for key, value in os.environ.items():
            if key.startswith(prefix):
                stripped = key[len(prefix):]
                self._vars[stripped] = value
        return dict(self._vars)

    def get(self, key: str, default: Any = None) -> str | Any:
        """Return a specific environment variable (cached after :meth:`load`)."""
        return self._vars.get(key, os.environ.get(key, default))

    @classmethod
    def from_file(cls, path: str) -> "EnvLoader":
        """Create an EnvLoader by reading variables from a dotenv-style file.

        Only simple ``KEY=VALUE`` lines are parsed; no shell expansion.
        """
        loader = cls()
        p = Path(path)
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                loader._vars[key.strip()] = value.strip()
        return loader
