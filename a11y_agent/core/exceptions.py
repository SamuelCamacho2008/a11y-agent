"""Domain exceptions for A11y Agent."""

class A11yError(Exception):
    """Base exception for all A11y Agent errors."""
    pass

class SSRFSecurityError(A11yError):
    """Raised when a URL attempts to access private/internal network addresses or forbidden schemes."""
    pass

class CrawlError(A11yError):
    """Raised when fetching or rendering a target page fails."""
    pass

class AnalysisError(A11yError):
    """Raised when axe-core or heuristic analysis fails."""
    pass

class LLMAnalysisError(A11yError):
    """Raised when LLM parsing or structured output generation fails."""
    pass

class ReportGenerationError(A11yError):
    """Raised when generating HTML/JSON/PDF reports fails."""
    pass
