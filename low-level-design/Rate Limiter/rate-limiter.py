import threading
import time
from typing import Optional


class RateLimiter:
    def is_allowed(self, user_id: str) -> bool:
        raise NotImplementedError


class TokenBucketRateLimiter(RateLimiter):
    def __init__(self, capacity=3, refill_interval=20.0):
        self.capacity = capacity
        self.refill_interval = refill_interval
        self.buckets = {}
        self.lock = threading.Lock()

    def is_allowed(self, user_id: str) -> bool:
        with self.lock:
            if user_id not in self.buckets:
                self.buckets[user_id] = {
                    "tokens": self.capacity,
                    "last_refill": time.time()
                }

            bucket = self.buckets[user_id]
            now = time.time()
            elapsed = now - bucket["last_refill"]
            tokens_to_add = int(elapsed // self.refill_interval)
            if tokens_to_add > 0:
                new_tokens = min(self.capacity, bucket["tokens"] + tokens_to_add)
                self.buckets[user_id]["tokens"] = new_tokens
                self.buckets[user_id]["last_refill"] = now

            if self.buckets[user_id]["tokens"] > 0:
                self.buckets[user_id]["tokens"] -= 1
                return True
            return False


class SlidingWindowRateLimiter(RateLimiter):
    def __init__(self, max_requests=3, window=60.0):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}  # Stores per-user timestamp list
        self.lock = threading.Lock()

    def is_allowed(self, user_id: str) -> bool:
        with self.lock:
            now = time.time()
            if user_id not in self.requests:
                self.requests[user_id] = []

            # Remove requests outside the window
            self.requests[user_id] = [ts for ts in self.requests[user_id] if now - ts < self.window]

            if len(self.requests[user_id]) < self.max_requests:
                self.requests[user_id].append(now)
                return True
            return False


class RateLimiterFactory:
    @staticmethod
    def create(limiter_type: str = "token_bucket", **kwargs) -> RateLimiter:
        if limiter_type == "token_bucket":
            return TokenBucketRateLimiter(**kwargs)
        elif limiter_type == "sliding_window":
            return SlidingWindowRateLimiter(**kwargs)
        else:
            raise ValueError("Unknown rate limiter algorithm.")
    

# Example usage
if __name__ == "__main__":
    limiter = RateLimiterFactory.create("sliding_window", max_requests=5, window=60.0)
    user = "user_1"

    for i in range(5):
        allowed = limiter.is_allowed(user)
        print(f"Request {i+1} for {user} - allowed: {allowed}")

        if not allowed:
            print("Rate limit exceeded.")
        time.sleep(5)
