"""Custom exceptions for Scholark-1 API clients."""


class SourceUnavailable(Exception):
    """Source returned no results or couldn't be reached."""

    def __init__(self, source: str, reason: str = ""):
        self.source = source
        self.reason = reason
        super().__init__(f"{source}: {reason}" if reason else source)


class RateLimited(SourceUnavailable):
    """Source rate-limited us."""

    def __init__(self, source: str):
        super().__init__(source, "rate limit exceeded")
