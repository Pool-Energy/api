import asyncio
import logging

from channels_redis.core import RedisChannelLayer
from redis import exceptions as redis_exceptions

logger = logging.getLogger(__name__)

# Transport errors that can escape redis-py's own native retry policy (see the
# CHANNEL_LAYERS hosts config) when chia-redis stays unresponsive for longer
# than the whole retry window.
_TRANSIENT_REDIS_ERRORS = (
    redis_exceptions.TimeoutError,
    redis_exceptions.ConnectionError,
    asyncio.TimeoutError,
)


class ResilientRedisChannelLayer(RedisChannelLayer):
    """Redis channel layer whose ``receive()`` never lets a transient Redis
    transport error kill the WebSocket consumer receive loop.

    redis-py already retries commands natively (with backoff) so short chia-redis
    hiccups are invisible. This is the last-resort guard: when a timeout still
    escapes, the receive is retried silently (no traceback, no log spam) instead
    of propagating through the ASGI app and tearing the consumer down. After a
    bounded number of consecutive failures the call finally raises so the
    framework still closes the socket cleanly and ``disconnect()`` purges the
    joined groups (instead of leaking the channel until ``group_expiry``).
    """

    # Consecutive receive failures tolerated before giving up with a single,
    # concise warning (no traceback). Bound so a fully unreachable chia-redis
    # eventually closes sockets instead of retrying forever.
    RECEIVE_RETRY_LIMIT = 15
    RECEIVE_RETRY_DELAY = 1.0

    async def receive(self, channel):
        consecutive_failures = 0
        while True:
            try:
                return await super().receive(channel)
            except _TRANSIENT_REDIS_ERRORS:
                consecutive_failures += 1
                if consecutive_failures >= self.RECEIVE_RETRY_LIMIT:
                    logger.warning(
                        'chia-redis unreachable: giving up on channel receive '
                        'after %d consecutive failures (channel=%s)',
                        consecutive_failures, channel,
                    )
                    raise
                # Retry silently: the consumer stays alive and keeps its groups.
                await asyncio.sleep(self.RECEIVE_RETRY_DELAY)
