"""Bounded one-shot provider calls; uncertain results are never retried."""

import math
import threading

TIMEOUT_SECONDS = 30
# Native generation permits 300 seconds; observation includes bounded cleanup time.
MAX_TIMEOUT_SECONDS = 305
_MAX_CONCURRENT = 2

_slots = threading.BoundedSemaphore(_MAX_CONCURRENT)
_abandoned_lock = threading.Lock()
_abandoned = 0


class ProviderCapacityError(Exception):
    pass


def abandoned_calls() -> int:
    """Timed-out invocations whose worker thread may still be running."""
    with _abandoned_lock:
        return _abandoned


class _Invocation:
    """One detached daemon worker; a timeout abandons it without leaking a slot.

    The previous fixed pool kept a timed-out call's slot until its thread
    terminated, so two genuinely hung provider calls blocked all future calls
    until process restart. A fresh daemon thread per invocation costs far less
    than one provider round trip, and abandonment is only tracked as telemetry.
    """

    __slots__ = ("abandoned", "done", "error", "result")

    def __init__(self, function, request):
        self.done = threading.Event()
        self.abandoned = False
        self.result = None
        self.error: BaseException | None = None
        thread = threading.Thread(target=self._run, args=(function, request), name="studio-provider", daemon=True)
        thread.start()

    def _run(self, function, request):
        global _abandoned
        try:
            self.result = function(request)
            self.error = None
        except BaseException as exc:  # noqa: BLE001 The caller re-raises whatever arrived.
            self.error = exc
        finally:
            self.done.set()
            if self.abandoned:
                with _abandoned_lock:
                    _abandoned -= 1


def call(function, request, *, timeout_seconds=None):
    global _abandoned
    if timeout_seconds is None:
        timeout_seconds = TIMEOUT_SECONDS
    if (type(timeout_seconds) not in {int, float} or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= MAX_TIMEOUT_SECONDS):
        raise ValueError("provider_deadline_invalid")
    if not _slots.acquire(blocking=False):
        raise ProviderCapacityError
    try:
        invocation = _Invocation(function, request)
    except BaseException:
        _slots.release()
        raise
    if not invocation.done.wait(timeout_seconds):
        invocation.abandoned = True
        with _abandoned_lock:
            _abandoned += 1
        _slots.release()
        raise TimeoutError(f"provider_call_timeout_after_{timeout_seconds}s")
    _slots.release()
    if invocation.error is not None:
        raise invocation.error
    return invocation.result
