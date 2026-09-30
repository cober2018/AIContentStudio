"""Bounded one-shot provider calls; uncertain results are never retried."""

import threading
from concurrent.futures import ThreadPoolExecutor

TIMEOUT_SECONDS = 30
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="studio-provider")
_slots = threading.BoundedSemaphore(2)


class ProviderCapacityError(Exception):
    pass


def call(function, request):
    if not _slots.acquire(blocking=False):
        raise ProviderCapacityError
    try:
        future = _pool.submit(function, request)
    except Exception:
        _slots.release()
        raise
    # A timed-out operation can still be live; retain its slot until terminal.
    future.add_done_callback(lambda _result: _slots.release())
    return future.result(timeout=TIMEOUT_SECONDS)
