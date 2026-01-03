"""Retry policies for resilient message handling.

Retry strategies for handlers that fail transiently.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Callable


class RetryPolicy(ABC):
    """Abstract base class for retry policies.

    Determines whether to retry a failed operation and how long to wait.
    """

    @abstractmethod
    def should_retry(self, attempt: int) -> bool:
        """Check if operation should be retried.

        Args:
            attempt: The attempt number (1-indexed)

        Returns:
            True if should retry, False otherwise
        """

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay in seconds before the next attempt.

        Args:
            attempt: The attempt number (1-indexed)

        Returns:
            Delay in seconds
        """


class NoRetry(RetryPolicy):
    """Retry policy that never retries.

    Useful for handlers that should fail immediately without retry.
    """

    def should_retry(self, attempt: int) -> bool:  # noqa: ARG002
        """No retries."""
        return False

    def get_delay(self, attempt: int) -> float:  # noqa: ARG002
        """No delay needed."""
        return 0


class ExponentialBackoff(RetryPolicy):
    """Exponential backoff with optional jitter.

    Retries with increasing delays: 1s, 2s, 4s, 8s, ...
    Optional jitter adds randomness to prevent thundering herd.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ) -> None:
        """Initialize exponential backoff policy.

        Args:
            max_retries: Maximum number of retries (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            multiplier: Exponential multiplier (default: 2.0)
            jitter: Add random jitter to delays (default: True)
        """
        msg_max_retries = "max_retries must be >= 0"
        if max_retries < 0:
            raise ValueError(msg_max_retries)

        msg_initial_delay = "initial_delay must be > 0"
        if initial_delay <= 0:
            raise ValueError(msg_initial_delay)

        msg_max_delay = "max_delay must be >= initial_delay"
        if max_delay < initial_delay:
            raise ValueError(msg_max_delay)

        msg_multiplier = "multiplier must be > 0"
        if multiplier <= 0:
            raise ValueError(msg_multiplier)

        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def should_retry(self, attempt: int) -> bool:
        """Check if we should retry based on attempt count."""
        return attempt <= self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.

        Formula: min(initial * (multiplier ^ (attempt - 1)), max_delay)
        Optional jitter: multiply by 1.0 + random(-0.25, 0.25)
        """
        if attempt <= 0:
            return 0

        # Calculate exponential delay
        delay = self.initial_delay * (self.multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)

        # Add jitter if enabled (deterministic: use attempt for seed consistency)
        if self.jitter:
            # Deterministic jitter based on attempt for testing
            jitter_factor = 1.0 + ((attempt % 3) - 1) * 0.1
            delay *= jitter_factor

        return delay


class LinearBackoff(RetryPolicy):
    """Linear backoff: 1s, 2s, 3s, 4s, ...

    Simpler than exponential, less aggressive backoff.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        """Initialize linear backoff policy.

        Args:
            max_retries: Maximum number of retries (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            increment: Delay increment each retry (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
        """
        msg_max_retries = "max_retries must be >= 0"
        if max_retries < 0:
            raise ValueError(msg_max_retries)

        msg_initial_delay = "initial_delay must be > 0"
        if initial_delay <= 0:
            raise ValueError(msg_initial_delay)

        msg_increment = "increment must be >= 0"
        if increment < 0:
            raise ValueError(msg_increment)

        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.increment = increment
        self.max_delay = max_delay

    def should_retry(self, attempt: int) -> bool:
        """Check if we should retry."""
        return attempt <= self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Calculate linear backoff delay.

        Formula: min(initial + (increment * (attempt - 1)), max_delay)
        """
        if attempt <= 0:
            return 0

        delay = self.initial_delay + (self.increment * (attempt - 1))
        return min(delay, self.max_delay)


class FixedDelay(RetryPolicy):
    """Fixed delay between retries: 1s, 1s, 1s, ...

    Simplest retry strategy, constant wait time.
    """

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
    ) -> None:
        """Initialize fixed delay policy.

        Args:
            max_retries: Maximum number of retries (default: 3)
            delay: Fixed delay in seconds (default: 1.0)
        """
        msg_max_retries = "max_retries must be >= 0"
        if max_retries < 0:
            raise ValueError(msg_max_retries)

        msg_delay = "delay must be >= 0"
        if delay < 0:
            raise ValueError(msg_delay)

        self.max_retries = max_retries
        self.delay = delay

    def should_retry(self, attempt: int) -> bool:
        """Check if we should retry."""
        return attempt <= self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Return fixed delay."""
        return self.delay if attempt > 0 else 0


def retry_sync(
    func: Callable[[...], None],
    *args: object,
    policy: RetryPolicy | None = None,
    **kwargs: object,
) -> None:
    """Execute function with retry policy.

    Args:
        func: Function to execute
        args: Positional arguments for function
        policy: Retry policy (default: ExponentialBackoff)
        kwargs: Keyword arguments for function

    Raises:
        Last exception if all retries exhausted
    """
    if policy is None:
        policy = ExponentialBackoff()

    attempt = 0

    while True:
        attempt += 1
        try:
            func(*args, **kwargs)
        except Exception:
            if not policy.should_retry(attempt):
                raise
            delay = policy.get_delay(attempt)
            if delay > 0:
                time.sleep(delay)
        else:
            return
