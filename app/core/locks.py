import threading
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager

import redis
from app.core.config import REDIS_URL

class Lock(ABC):
    """
    분산 락의 인터페이스. Redis 유무와 상관없이 동일하게 호출.
    """

    @abstractmethod
    def acquire(self, key: str) -> bool:
        """
        락을 잡는다. 성공하면 True, 이미 다른 곳이 잡고 있으면 False.
        """
        raise NotImplementedError

    @abstractmethod
    def release(self, key: str) -> None:
        """
        락을 푼다.
        """
        raise NotImplementedError

    @contextmanager
    def held(self, key: str) -> Iterator[bool]:
        """
        with 블록 동안 락을 잡고, 블록이 끝나면 자동으로 해제..
        """
        acquired = self.acquire(key)
        try:
            yield acquired
        finally:
            if acquired:
                self.release(key)


class InMemoryLock(Lock):
    """
    프로세스 하나 안에서만 유효한 락. Redis가 없을 때의 폴백.
    """

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._held_keys: set[str] = set()

    def acquire(self, key: str) -> bool:
        with self._guard:
            if key in self._held_keys:
                return False
            self._held_keys.add(key)
            return True

    def release(self, key: str) -> None:
        with self._guard:
            self._held_keys.discard(key)


class RedisLock(Lock):
    """
    Redis를 사용하는 분산 락
    """

    def __init__(self, redis_url: str) -> None:
        self._client = redis.from_url(redis_url)

    def acquire(self, key: str) -> bool:

        return bool(self._client.set(key, "1", nx=True, ex=5))

    def release(self, key: str) -> None:
        self._client.delete(key)


def _create_lock() -> Lock:

    if REDIS_URL:
        try:
            candidate = RedisLock(REDIS_URL)
            candidate._client.ping()
            return candidate
        except Exception:
            pass
    return InMemoryLock()


lock: Lock = _create_lock()