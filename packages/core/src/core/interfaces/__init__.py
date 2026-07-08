"""Core interfaces package."""

from core.interfaces.provider import BaseProvider
from core.interfaces.repository import BaseRepository
from core.interfaces.service import BaseService
from core.interfaces.plugin import IPlugin
from core.interfaces.workflow import IWorkflow

__all__ = [
    "BaseProvider",
    "BaseRepository",
    "BaseService",
    "IPlugin",
    "IWorkflow",
]
