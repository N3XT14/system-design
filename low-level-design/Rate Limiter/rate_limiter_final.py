from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from threading import Lock
import time


# =========================
# Enums
# =========================

class RateLimiterType(Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"


# =========================
# Base Rate Limiter
# =========================

class RateLimiter(ABC):

    @abstractmethod
    def is_allowed(self, user_id: str) -> bool:
        pass


# =========================
# Token Bucket
# =========================

class TokenBucket:
    def __init__(self, capacity):
        self.tokens = capacity
        self.last_refill = time.time()

        # Protects THIS user's bucket.
        self.lock = Lock()


class TokenBucketRateLimiter(RateLimiter):

    def __init__(
        self,
        capacity=3,
        refill_interval=20.0
    ):
        self.capacity = capacity
        self.refill_interval = refill_interval

        # user_id -> TokenBucket
        self.buckets = {}

        # Protects bucket creation only.
        self._buckets_lock = Lock()

    def _get_bucket(self, user_id):
        with self._buckets_lock:

            if user_id not in self.buckets:
                self.buckets[user_id] = TokenBucket(
                    self.capacity
                )

            return self.buckets[user_id]

    def is_allowed(self, user_id: str) -> bool:

        bucket = self._get_bucket(user_id)

        # Only requests for the SAME user
        # compete for this lock.
        with bucket.lock:

            now = time.time()

            elapsed = (
                now - bucket.last_refill
            )

            tokens_to_add = int(
                elapsed // self.refill_interval
            )

            if tokens_to_add > 0:

                bucket.tokens = min(
                    self.capacity,
                    bucket.tokens + tokens_to_add
                )

                # Preserve partial refill time.
                bucket.last_refill += (
                    tokens_to_add
                    * self.refill_interval
                )

            if bucket.tokens <= 0:
                return False

            bucket.tokens -= 1

            return True


# =========================
# Sliding Window
# =========================

class SlidingWindow:
    def __init__(self):
        self.timestamps = deque()

        # Protects THIS user's window.
        self.lock = Lock()


class SlidingWindowRateLimiter(RateLimiter):

    def __init__(
        self,
        max_requests=3,
        window=60.0
    ):
        self.max_requests = max_requests
        self.window = window

        # user_id -> SlidingWindow
        self.windows = {}

        # Protects window creation only.
        self._windows_lock = Lock()

    def _get_window(self, user_id):

        with self._windows_lock:

            if user_id not in self.windows:
                self.windows[user_id] = (
                    SlidingWindow()
                )

            return self.windows[user_id]

    def is_allowed(self, user_id: str) -> bool:

        window = self._get_window(user_id)

        with window.lock:

            now = time.time()

            # Remove expired requests.
            while (
                window.timestamps
                and
                now - window.timestamps[0]
                >= self.window
            ):
                window.timestamps.popleft()

            if (
                len(window.timestamps)
                >= self.max_requests
            ):
                return False

            window.timestamps.append(now)

            return True


# =========================
# Factory
# =========================

class RateLimiterFactory:

    @staticmethod
    def create(
        limiter_type: RateLimiterType,
        **kwargs
    ) -> RateLimiter:

        if (
            limiter_type
            == RateLimiterType.TOKEN_BUCKET
        ):
            return TokenBucketRateLimiter(
                **kwargs
            )

        if (
            limiter_type
            == RateLimiterType.SLIDING_WINDOW
        ):
            return SlidingWindowRateLimiter(
                **kwargs
            )

        raise ValueError(
            "Unsupported rate limiter type."
        )


# =========================
# Example
# =========================

if __name__ == "__main__":

    limiter = RateLimiterFactory.create(
        RateLimiterType.SLIDING_WINDOW,
        max_requests=5,
        window=60
    )

    user = "user_1"

    for i in range(6):

        allowed = limiter.is_allowed(user)

        print(
            f"Request {i + 1}: "
            f"{'Allowed' if allowed else 'Rejected'}"
        )
