from rest_framework import serializers
from api.serializers import LauncherSerializer

from .models import Referral


class ReferralSerializer(serializers.HyperlinkedModelSerializer):
    launcher = LauncherSerializer()
    referrer = LauncherSerializer()

    class Meta:
        model = Referral
        fields = '__all__'
