from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Referral
from .serializers import ReferralSerializer


@extend_schema_view(
    list=extend_schema(
        auth=[],
        description='List all referrals.',
        methods=['GET'],
        responses={200: ReferralSerializer(many=True)},
    ),
    retrieve=extend_schema(
        auth=[],
        description='Retrieve a specific referral.',
        methods=['GET'],
        responses={200: ReferralSerializer(many=False)},
    ),
)
class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Referral.objects.filter(active=True)
    serializer_class = ReferralSerializer
    filterset_fields = ['launcher', 'referrer']
    search_fields = ['launcher', 'referrer']
    ordering_fields = ['total_income']
    ordering = ['-total_income']
