from django.urls import include, path, re_path
from rest_framework import routers
from referral.views import ReferralViewSet
from .views import (
    BlockViewSet,
    LauncherSizeView,
    LauncherViewSet,
    LoginView,
    LoginQRView,
    LoggedInView,
    MempoolView,
    NetspaceView,
    PartialView,
    PartialViewSet,
    HarvesterViewSet,
    PayoutAddressViewSet,
    PayoutTransactionViewSet,
    PayoutViewSet,
    PoolSizeView,
    QRCodeView,
    StatsView,
    TransactionViewSet,
    XCHPriceView,
    XCHScanStatsView,
    GlobalMessageView,
)

router = routers.DefaultRouter()
router.register('block', BlockViewSet)
router.register('launcher', LauncherViewSet)
router.register('partial', PartialViewSet)
router.register('harvester', HarvesterViewSet)
router.register('payout', PayoutViewSet)
router.register('payoutaddress', PayoutAddressViewSet)
router.register('transaction', TransactionViewSet)
router.register('referral', ReferralViewSet)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    re_path(r'launcher_size/?', LauncherSizeView.as_view()),
    re_path(r'pool_size/?', PoolSizeView.as_view()),
    re_path(r'stats/mempool/?', MempoolView.as_view()),
    re_path(r'stats/netspace/?', NetspaceView.as_view()),
    re_path(r'stats/partial/?', PartialView.as_view()),
    re_path(r'stats/xchprice/?', XCHPriceView.as_view()),
    path('login', LoginView.as_view()),
    path('login_qr', LoginQRView.as_view()),
    re_path(r'payouttransaction/?', PayoutTransactionViewSet.as_view()),
    path('qrcode', QRCodeView.as_view()),
    path('loggedin', LoggedInView.as_view()),
    path('stats', StatsView.as_view()),
    path('xchscan_stats', XCHScanStatsView.as_view()),
    path('message', GlobalMessageView.as_view()),
]
