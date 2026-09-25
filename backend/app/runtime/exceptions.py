class RuntimeException(Exception):
    """Base exception for Runtime Engine v2."""
    pass


class NodeExecutionException(RuntimeException):
    """Raised when a DAG node fails execution."""
    def __init__(self, message: str, node_id: str, retries: int = 0):
        super().__init__(message)
        self.node_id = node_id
        self.retries = retries


class WorkflowCancelledException(RuntimeException):
    """Raised when a workflow execution is cancelled by operator."""
    pass


class DependencyCycleException(RuntimeException):
    """Raised when a cycle is detected in the workflow DAG."""
    pass
