from django.urls import re_path

from . import consumers


websocket_urlpatterns = [
    re_path(r'ws/log/$', consumers.PoolLogConsumer.as_asgi()),
    re_path(r'ws/pool_status/$', consumers.PoolStatusConsumer.as_asgi()),
    re_path(r'ws/pool_stats/$', consumers.PoolStatsConsumer.as_asgi()),
    re_path(r'ws/blocks/$', consumers.BlocksConsumer.as_asgi()),
    re_path(r'ws/rewards/$', consumers.RewardsConsumer.as_asgi()),
    re_path(r'ws/farmers/$', consumers.FarmersConsumer.as_asgi()),
    re_path(r'ws/partials/$', consumers.PartialsConsumer.as_asgi()),
    re_path(r'ws/farmer/(?P<launcher_id>[0-9a-f]{64})/$', consumers.FarmerConsumer.as_asgi()),
]
