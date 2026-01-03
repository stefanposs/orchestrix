"""Tests for retry policies."""

import pytest

from orchestrix.retry import (
    ExponentialBackoff,
    FixedDelay,
    LinearBackoff,
    NoRetry,
    RetryPolicy,
)


class TestNoRetry:
    """Test NoRetry policy - never retries."""

    def test_should_not_retry(self) -> None:
        """NoRetry should never retry."""
        policy = NoRetry()

        assert not policy.should_retry(1)
        assert not policy.should_retry(2)
        assert not policy.should_retry(100)

    def test_delay_is_zero(self) -> None:
        """NoRetry should have zero delay."""
        policy = NoRetry()

        assert policy.get_delay(1) == 0
        assert policy.get_delay(100) == 0


class TestFixedDelay:
    """Test FixedDelay policy - constant wait time."""

    def test_respects_max_retries(self) -> None:
        """FixedDelay should respect max_retries."""
        policy = FixedDelay(max_retries=3, delay=0.5)

        assert policy.should_retry(1)
        assert policy.should_retry(2)
        assert policy.should_retry(3)
        assert not policy.should_retry(4)

    def test_constant_delay(self) -> None:
        """FixedDelay should return constant delay."""
        policy = FixedDelay(max_retries=5, delay=2.0)

        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(5) == 2.0

    def test_zero_delay(self) -> None:
        """FixedDelay with zero delay should have no wait."""
        policy = FixedDelay(max_retries=3, delay=0.0)

        assert policy.get_delay(1) == 0.0
        assert policy.get_delay(2) == 0.0

    def test_invalid_max_retries(self) -> None:
        """FixedDelay should reject negative max_retries."""
        msg = "max_retries must be >= 0"
        with pytest.raises(ValueError, match=msg):
            FixedDelay(max_retries=-1)

    def test_invalid_delay(self) -> None:
        """FixedDelay should reject negative delay."""
        msg = "delay must be >= 0"
        with pytest.raises(ValueError, match=msg):
            FixedDelay(delay=-1.0)


class TestLinearBackoff:
    """Test LinearBackoff policy - incremental delays."""

    def test_linear_progression(self) -> None:
        """LinearBackoff should increase delay linearly."""
        policy = LinearBackoff(
            max_retries=5,
            initial_delay=1.0,
            increment=1.0,
        )

        assert policy.get_delay(1) == 1.0  # 1 + 0*1
        assert policy.get_delay(2) == 2.0  # 1 + 1*1
        assert policy.get_delay(3) == 3.0  # 1 + 2*1
        assert policy.get_delay(4) == 4.0  # 1 + 3*1

    def test_respects_max_delay(self) -> None:
        """LinearBackoff should not exceed max_delay."""
        policy = LinearBackoff(
            max_retries=10,
            initial_delay=1.0,
            increment=10.0,
            max_delay=5.0,
        )

        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 5.0  # capped at 5.0
        assert policy.get_delay(3) == 5.0  # capped at 5.0

    def test_respects_max_retries(self) -> None:
        """LinearBackoff should respect max_retries."""
        policy = LinearBackoff(max_retries=2, initial_delay=1.0)

        assert policy.should_retry(1)
        assert policy.should_retry(2)
        assert not policy.should_retry(3)

    def test_invalid_parameters(self) -> None:
        """LinearBackoff should validate parameters."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            LinearBackoff(max_retries=-1)

        with pytest.raises(ValueError, match="initial_delay must be > 0"):
            LinearBackoff(initial_delay=0)

        with pytest.raises(ValueError, match="increment must be >= 0"):
            LinearBackoff(increment=-1.0)


class TestExponentialBackoff:
    """Test ExponentialBackoff policy - exponential delays."""

    def test_exponential_progression(self) -> None:
        """ExponentialBackoff should increase delay exponentially."""
        policy = ExponentialBackoff(
            max_retries=5,
            initial_delay=1.0,
            multiplier=2.0,
            jitter=False,
        )

        assert policy.get_delay(1) == 1.0  # 1 * 2^0
        assert policy.get_delay(2) == 2.0  # 1 * 2^1
        assert policy.get_delay(3) == 4.0  # 1 * 2^2
        assert policy.get_delay(4) == 8.0  # 1 * 2^3

    def test_respects_max_delay(self) -> None:
        """ExponentialBackoff should not exceed max_delay."""
        policy = ExponentialBackoff(
            max_retries=10,
            initial_delay=1.0,
            multiplier=2.0,
            max_delay=5.0,
            jitter=False,
        )

        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 4.0
        assert policy.get_delay(4) == 5.0  # capped at max_delay
        assert policy.get_delay(5) == 5.0  # capped at max_delay

    def test_respects_max_retries(self) -> None:
        """ExponentialBackoff should respect max_retries."""
        policy = ExponentialBackoff(max_retries=3)

        assert policy.should_retry(1)
        assert policy.should_retry(2)
        assert policy.should_retry(3)
        assert not policy.should_retry(4)

    def test_with_jitter(self) -> None:
        """ExponentialBackoff with jitter should vary delays."""
        policy = ExponentialBackoff(
            max_retries=5,
            initial_delay=1.0,
            multiplier=2.0,
            jitter=True,
        )

        delay1 = policy.get_delay(2)
        delay2 = policy.get_delay(2)

        # With deterministic jitter, delays may differ slightly
        assert 0 < delay1 <= 5.0
        assert 0 < delay2 <= 5.0

    def test_zero_delay_for_zero_attempt(self) -> None:
        """Delay for attempt 0 should be 0."""
        policy = ExponentialBackoff()

        assert policy.get_delay(0) == 0

    def test_invalid_parameters(self) -> None:
        """ExponentialBackoff should validate parameters."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            ExponentialBackoff(max_retries=-1)

        with pytest.raises(ValueError, match="initial_delay must be > 0"):
            ExponentialBackoff(initial_delay=0)

        with pytest.raises(ValueError, match="max_delay must be >= initial_delay"):
            ExponentialBackoff(initial_delay=10, max_delay=5)

        with pytest.raises(ValueError, match="multiplier must be > 0"):
            ExponentialBackoff(multiplier=0)


class TestPolicyProtocol:
    """Test that custom policies can implement the protocol."""

    def test_custom_policy(self) -> None:
        """Custom policy should implement RetryPolicy protocol."""

        class CustomPolicy(RetryPolicy):
            def should_retry(self, attempt: int) -> bool:
                return attempt < 2

            def get_delay(self, attempt: int) -> float:  # noqa: ARG002
                return 0.1

        policy = CustomPolicy()

        assert policy.should_retry(1)
        assert not policy.should_retry(2)
        assert policy.get_delay(1) == 0.1
        assert policy.get_delay(100) == 0.1
