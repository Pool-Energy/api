from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone


class Block(models.Model):

    class Meta:
        db_table = 'block'
        indexes = [
            models.Index(name='farmed_by_idx', fields=['farmed_by_id']),
        ]

    name = models.CharField(max_length=64)
    singleton = models.CharField(max_length=64)
    timestamp = models.BigIntegerField()
    farmed_height = models.BigIntegerField(unique=True)
    confirmed_block_index = models.BigIntegerField()
    puzzle_hash = models.CharField(max_length=64)
    amount = models.BigIntegerField()
    absorb_fee = models.IntegerField(default=0)
    farmed_by = models.ForeignKey(
        'api.Launcher', on_delete=models.SET_NULL, null=True
    )
    launcher_etw = models.BigIntegerField(default=-1)
    launcher_effort = models.IntegerField(default=-1)
    pool_space = models.BigIntegerField(default=0)
    estimate_to_win = models.BigIntegerField(default=-1)
    luck = models.IntegerField(default=-1)
    payout = models.ForeignKey(
        'Payout', related_name='blocks', on_delete=models.SET_NULL, null=True, default=None,
    )
    xch_price = models.JSONField(default=None, null=True)
    gigahorse_fee = models.BooleanField(default=False, null=True)


class Launcher(models.Model):

    class Meta:
        db_table = 'farmer'

    launcher_id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=200, null=True)
    picture_url = models.URLField(max_length=1024, default=None, null=True)
    delay_time = models.BigIntegerField()
    delay_puzzle_hash = models.TextField()
    authentication_public_key = models.TextField()
    singleton_tip = models.BinaryField()
    singleton_tip_state = models.BinaryField()
    p2_singleton_puzzle_hash = models.CharField(max_length=64)
    points = models.BigIntegerField()
    points_pplns = models.BigIntegerField()
    share_pplns = models.DecimalField(max_digits=21, decimal_places=20)
    difficulty = models.BigIntegerField()
    custom_difficulty = models.CharField(
        verbose_name='Custom Difficulty',
        help_text=(
            'Set a custom difficulty for the launcher to send less or more partials depending '
            'on preference'
        ),
        null=True,
        max_length=15,
        choices=(
            ('LOWEST', 'Lowest'),
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('HIGHEST', 'Highest'),
        ),
        default=None,
    )
    minimum_payout = models.BigIntegerField(
        verbose_name='Minimum Payout',
        help_text='Set a minimum value before sending out payout from rewards',
        null=True,
        default=None,
    )
    payout_instructions = models.TextField()
    is_pool_member = models.BooleanField()
    estimated_size = models.BigIntegerField(default=0)
    joined_at = models.DateTimeField(default=None, null=True)
    joined_last_at = models.DateTimeField(default=None, null=True)
    left_at = models.DateTimeField(default=None, null=True)
    left_last_at = models.DateTimeField(default=None, null=True)
    current_etw = models.BigIntegerField(default=None, null=True)
    last_block_timestamp = models.BigIntegerField(default=None, null=True)
    last_block_etw = models.BigIntegerField(default=None, null=True)
    email = models.EmailField(default=None, null=True)
    notify_missing_partials_hours = models.IntegerField(default=1, null=True)
    fcm_token = models.CharField(max_length=500, default=None, null=True)
    qrcode_token = models.CharField(max_length=64, default=None, null=True, db_index=True)
    push_missing_partials_hours = models.IntegerField(null=True, default=None)
    push_block_farmed = models.BooleanField(default=True)

    def is_authenticated(self):
        return False


class Notification(models.Model):

    class Meta:
        db_table = 'notification'

    launcher = models.OneToOneField(Launcher, on_delete=models.CASCADE, primary_key=True)
    size_drop = ArrayField(
        models.CharField(choices=(('PUSH', 'Push'), ('EMAIL', 'Email')), max_length=10),
        size=2,
        default=list,
    )
    size_drop_interval = models.IntegerField(null=True, default=None)
    size_drop_percent = models.IntegerField(null=True, default=None)
    size_drop_last_sent = models.DateTimeField(null=True, default=None)
    failed_partials = ArrayField(
        models.CharField(choices=(('PUSH', 'Push'), ('EMAIL', 'Email')), max_length=10),
        size=2,
        default=list,
    )
    failed_partials_percent = models.IntegerField(null=True, default=None)
    payment = ArrayField(
        models.CharField(choices=(('PUSH', 'Push'), ('EMAIL', 'Email')), max_length=10),
        size=2,
        default=list,
    )


class Singleton(models.Model):

    class Meta:
        db_table = 'singleton'

    launcher = models.ForeignKey(Launcher, on_delete=models.CASCADE)
    singleton_name = models.CharField(max_length=64)
    singleton_tip = models.BinaryField()
    singleton_tip_state = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)


class Partial(models.Model):

    class Meta:
        db_table = 'partial'

    launcher = models.ForeignKey(Launcher, on_delete=models.CASCADE)
    timestamp = models.IntegerField()
    difficulty = models.IntegerField()
    error = models.CharField(max_length=25, null=True, default=None)
    harvester_id = models.CharField(max_length=64, null=True, default=None)
    plot_id = models.CharField(max_length=128, null=True, default=None)
    chia_version = models.CharField(max_length=20, null=True, default=None)
    remote = models.CharField(max_length=45, null=True, default=None)
    pool_host = models.CharField(max_length=35, null=True, default=None)
    time_taken = models.FloatField(default=None, null=True)
    plot_size = models.IntegerField(default=None, null=True)


class Harvester(models.Model):

    class Meta:
        db_table = 'harvester'
        constraints = [
            models.UniqueConstraint(fields=['harvester', 'launcher'], name='unique_launcher_harvester'),
        ]

    launcher = models.CharField(max_length=64)
    harvester = models.CharField(max_length=64)
    version = models.CharField(max_length=20, null=True, default=None)
    name = models.CharField(max_length=200, null=True, default=None)


class PendingPartial(models.Model):

    class Meta:
        db_table = 'pending_partial'

    partial = models.JSONField(default=dict)
    req_metadata = models.JSONField(default=dict, null=True)
    time_received = models.BigIntegerField()
    points_received = models.IntegerField()


class Payout(models.Model):

    class Meta:
        db_table = 'payout'

    datetime = models.DateTimeField(default=timezone.now)
    amount = models.BigIntegerField()
    fee = models.BigIntegerField(default=0)
    referral = models.BigIntegerField(default=0)


class CoinReward(models.Model):

    class Meta:
        db_table = 'coin_reward'

    name = models.CharField(max_length=64, primary_key=True)
    payout = models.ForeignKey(Payout, on_delete=models.CASCADE)


class Transaction(models.Model):

    class Meta:
        db_table = 'transaction'

    transaction = models.CharField(max_length=64, unique=True)
    created_at_time = models.DateTimeField(null=True)
    xch_price = models.JSONField(default=None, null=True)
    confirmed_block_index = models.IntegerField(null=True, default=None)


class PayoutAddress(models.Model):

    class Meta:
        db_table = 'payout_address'

    payout = models.ForeignKey(Payout, on_delete=models.CASCADE)
    fee = models.BooleanField(default=False)
    tx_fee = models.BigIntegerField(default=0)
    puzzle_hash = models.CharField(max_length=64)
    pool_puzzle_hash = models.CharField(max_length=64, default='')
    launcher = models.ForeignKey(Launcher, on_delete=models.SET_NULL, null=True, default=None)
    amount = models.BigIntegerField()
    fee_amount = models.BigIntegerField(null=True, default=None)
    referral = models.ForeignKey('referral.Referral', null=True, default=None, on_delete=models.SET_NULL)
    referral_amount = models.BigIntegerField(default=0)
    transaction = models.ForeignKey(Transaction, null=True, on_delete=models.SET_NULL)


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class GlobalInfo(SingletonModel):

    class Meta:
        db_table = 'globalinfo'

    blockchain_height = models.BigIntegerField(default=0)
    blockchain_space = models.CharField(default='0', max_length=128)
    blockchain_avg_block_time = models.BigIntegerField(default=0, null=True)
    xch_current_price = models.JSONField(default=dict)
    wallets = models.JSONField(default=dict)
    nodes = models.JSONField(default=dict)


class GlobalMessage(models.Model):

    class Meta:
        db_table = 'globalmessage'

    name = models.CharField(max_length=200, null=False)
    message = models.CharField(null=False)
    datetime = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=50, default='info', null=False)
    enabled = models.BooleanField(default=False)
