class WorkflowEngineError(Exception):
    """Base exception class for Enterprise Workflow Execution Engine."""

    def __init__(self, message: str, workflow_id: str = "Unknown", original_error: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.workflow_id = workflow_id
        self.original_error = original_error

    def __str__(self) -> str:
        return f"[WorkflowEngine:{self.workflow_id}] {self.message}"


class WorkflowCompilationError(WorkflowEngineError):
    """Raised when DAG graph compilation or validation fails."""
    pass


class WorkflowExecutionError(WorkflowEngineError):
    """Raised when workflow step execution fails."""
    pass


class WorkflowStateError(WorkflowEngineError):
    """Raised when state checkpoint or transition fails."""
    pass


class WorkflowTimeoutError(WorkflowEngineError):
    """Raised when workflow execution times out."""
    pass


class ApprovalPendingException(WorkflowEngineError):
    """Raised when execution pauses waiting for human approval."""
    pass
