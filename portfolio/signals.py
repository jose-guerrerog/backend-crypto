# from django.db.models.signals import post_migrate
# from django.db import transaction
# from django.dispatch import receiver
# from .models import Portfolio, Transaction
# from django.utils.timezone import now

# @receiver(post_migrate)
# def create_default_data(sender, **kwargs):
#     with transaction.atomic():
#         # Create default portfolio if it doesn't exist
#         portfolio, created = Portfolio.objects.get_or_create(name="Default Portfolio")

#         # Create some example transactions only if there are none
#         if not portfolio.transactions.exists():
#             Transaction.objects.bulk_create([
#                 Transaction(
#                     portfolio=portfolio,
#                     coin_id="bitcoin",
#                     coin_name="Bitcoin",
#                     coin_symbol="BTC",
#                     amount=0.01,
#                     price_usd=100000.0,
#                     transaction_type="buy",
#                     timestamp=now()
#                 ),
#                 Transaction(
#                     portfolio=portfolio,
#                     coin_id="ethereum",
#                     coin_name="Ethereum",
#                     coin_symbol="ETH",
#                     amount=0.5,
#                     price_usd=3500.0,
#                     transaction_type="buy",
#                     timestamp=now()
#                 ),
#             ])