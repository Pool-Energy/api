import asyncio
import json
import logging
import os
import subprocess

import redis.asyncio as aioredis

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.conf import settings


logger = logging.getLogger('api.consumers')
LOG_DIR = os.environ.get('POOL_LOG_DIR')
LOG_TASK = None
LOG_LINES = 15


class LogTask(object):

    def __init__(self):
        self._consumers = []
        self._last = []

    async def add_consumer(self, c):
        self._consumers.append(c)
        if self._last:
            await c.send(text_data=json.dumps({'data': self._last}))

    async def remove_consumer(self, i):
        try:
            self._consumers.remove(i)
        except Exception:
            pass

    async def send(self, data):
        for c in list(self._consumers):
            try:
                if len(c.subscribed_logs) != 2:
                    send_data = []
                    for j in data:
                        if 'partials' not in c.subscribed_logs and j['name'] == 'partials':
                            continue
                        send_data.append(j)
                else:
                    send_data = data
                if send_data:
                    asyncio.create_task(c.send(text_data=json.dumps({'data': send_data})))
            except Exception:
                pass

    async def run(self):
        global LOG_TASK

        proc = await asyncio.create_subprocess_exec(
            'tail',
            '-q',
            '-F',
            '-n', str(LOG_LINES),
            os.path.join(LOG_DIR, 'main.log.json'),
            os.path.join(LOG_DIR, 'partial.log.json'),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            limit=128 * 1024,
        )

        read_task = asyncio.create_task(self.read(proc))
        await proc.wait()
        read_task.cancel()

        LOG_TASK = None

    async def read(self, proc):
        try:
            data_send = []
            while self._consumers:
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), 1)
                except asyncio.TimeoutError:
                    if data_send:
                        send = list(data_send)
                        self._last += send
                        self._last = self._last[-LOG_LINES:]
                        data_send[:] = []
                        await self.send(send)
                    continue
                except ValueError as e:
                    if 'but chunk is longer than limit' in str(e):
                        continue
                    raise

                if not line:
                    break

                if not line.startswith(b'{'):
                    logger.info('Line is not a JSON %r', line)
                    continue

                try:
                    data_send.append(json.loads(line.decode(errors='ignore')))
                except ValueError:
                    pass

                if len(data_send) >= 10:
                    send = list(data_send)
                    self._last += send
                    self._last = self._last[-LOG_LINES:]
                    data_send[:] = []
                    await self.send(send)
        except Exception:
            logger.error('Failed to read from tail', exc_info=True)

        proc.kill()


class PoolLogConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        global LOG_TASK

        self.subscribed_logs = ['payments']

        await self.accept()

        if not os.path.exists(LOG_DIR):
            return

        if LOG_TASK is None:
            LOG_TASK = LogTask()
            asyncio.create_task(LOG_TASK.run())
        await LOG_TASK.add_consumer(self)

    async def disconnect(self, close_code):
        global LOG_TASK
        if LOG_TASK is not None:
            await LOG_TASK.remove_consumer(self)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        data = json.loads(text_data)

        for i in ('partials', 'payments'):
            if i in data:
                if i not in self.subscribed_logs:
                    self.subscribed_logs.append(i)
            else:
                if i in self.subscribed_logs:
                    self.subscribed_logs.remove(i)


# ================================================================================
# Live data (blocks, partials, payouts, pool status) via redis pub/sub
# ================================================================================
#
# `pool` (a separate asyncio process) publishes JSON events on redis pub/sub
# channels named `live:<kind>:<scope>` (see pool/pool/store/redis_store.py).
# `RedisRelay` below subscribes to `live:*` and re-broadcasts every message to
# the matching Django Channels group, which the WebSocket consumers below
# join depending on the page/launcher they represent.
#
# NOTE: this relay is started once per ASGI *process* (singleton, same pattern
# as `LOG_TASK` above). The current deployment runs a single gunicorn worker
# (see api/docker/entrypoint.sh, no `-w` flag), so this is safe. If the
# deployment ever moves to multiple workers/replicas, this relay MUST be
# extracted into its own dedicated process (e.g. a `manage.py` command),
# otherwise every worker would re-publish the same event and clients would
# receive duplicated messages.

REDIS_RELAY = None


def _group_name_for_channel(channel: str) -> str:
    # e.g. "live:partial:all" -> "live_partial_all"
    #      "live:partial:<launcher_id>" -> "live_partial_<launcher_id>"
    return channel.replace(':', '_')


class RedisRelay(object):

    def __init__(self):
        self._task: asyncio.Task | None = None

    async def start(self):
        self._task = asyncio.create_task(self.run())

    async def run(self):
        global REDIS_RELAY

        channel_layer = get_channel_layer()
        client = aioredis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

        try:
            pubsub = client.pubsub()
            await pubsub.psubscribe('live:*')

            async for message in pubsub.listen():
                if message is None:
                    continue
                if message.get('type') != 'pmessage':
                    continue

                channel = message['channel']
                if isinstance(channel, bytes):
                    channel = channel.decode()

                data = message['data']
                if isinstance(data, bytes):
                    data = data.decode()

                try:
                    payload = json.loads(data)
                except ValueError:
                    logger.warning('Failed to decode live event on channel %r', channel)
                    continue

                group = _group_name_for_channel(channel)
                # channel is "live:<kind>:<scope>" or "live:<kind>" (pool_status)
                kind = channel.split(':')[1] if ':' in channel else channel
                try:
                    await channel_layer.group_send(group, {
                        'type': 'live.message',
                        'kind': kind,
                        'payload': payload,
                    })
                except Exception:
                    logger.error('Failed to relay live event to group %r', group, exc_info=True)
        except Exception:
            logger.error('Redis relay stopped unexpectedly', exc_info=True)
        finally:
            REDIS_RELAY = None


class LiveGroupConsumer(AsyncWebsocketConsumer):
    """
    Base class for WebSocket consumers that just join one or more Channels
    groups fed by `RedisRelay` and forward every message to the client as-is.
    Subclasses must implement `get_groups()`.
    """

    def get_groups(self) -> list:
        raise NotImplementedError

    async def connect(self):
        global REDIS_RELAY

        await self.accept()

        if REDIS_RELAY is None:
            REDIS_RELAY = RedisRelay()
            await REDIS_RELAY.start()

        self.groups_joined = self.get_groups()
        for group in self.groups_joined:
            await self.channel_layer.group_add(group, self.channel_name)

    async def disconnect(self, close_code):
        for group in getattr(self, 'groups_joined', []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def live_message(self, event):
        await self.send(text_data=json.dumps({
            'kind': event['kind'],
            'payload': event['payload'],
        }))


class PoolStatusConsumer(LiveGroupConsumer):
    def get_groups(self):
        return ['live_pool_status']


class PoolStatsConsumer(LiveGroupConsumer):
    def get_groups(self):
        # Aggregated influx-backed metrics (netspace/mempool/xchprice) are not
        # event-driven; only pool status + partial throughput are live for now.
        return ['live_pool_status', 'live_partial_all']


class BlocksConsumer(LiveGroupConsumer):
    def get_groups(self):
        return ['live_block_all']


class RewardsConsumer(LiveGroupConsumer):
    def get_groups(self):
        return ['live_payout_all']


class FarmersConsumer(LiveGroupConsumer):
    def get_groups(self):
        return ['live_partial_all', 'live_block_all']


class PartialsConsumer(LiveGroupConsumer):
    """Global, all-farmers live partial feed (`/partials` page), grouped by
    signage point. Also joins the blocks group so found blocks can be
    correlated (best-effort, by timestamp proximity) to a signage point
    row client-side."""

    def get_groups(self):
        return ['live_partial_all', 'live_block_all']


class FarmerConsumer(LiveGroupConsumer):
    """Live feed scoped to a single farmer (`/farmer/{id}` page: overview,
    partials, blocks, rewards, payouts tabs)."""

    def get_groups(self):
        launcher_id = self.scope['url_route']['kwargs']['launcher_id']
        return [
            f'live_partial_{launcher_id}',
            f'live_block_{launcher_id}',
            f'live_payout_{launcher_id}',
        ]

