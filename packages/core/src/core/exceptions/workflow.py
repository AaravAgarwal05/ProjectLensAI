"""Workflow-specific exceptions."""

from core.exceptions.base import ProjectLensError


class WorkflowError(ProjectLensError):
    """Raised when a workflow execution fails."""

    def __init__(self, message: str = "", code: str = "WORKFLOW_ERROR") -> None:
        super().__init__(message, code)


class WorkflowTimeoutError(WorkflowError):
    """Raised when a workflow times out."""

    def __init__(self, message: str = "", code: str = "WORKFLOW_TIMEOUT") -> None:
        super().__init__(message, code)


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow fails validation."""

    def __init__(self, message: str = "", code: str = "WORKFLOW_VALIDATION_ERROR") -> None:
        super().__init__(message, code)
