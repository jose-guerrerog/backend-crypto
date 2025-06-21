from django.core.management.base import BaseCommand
from portfolio.models import Portfolio, Transaction
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed the database with initial portfolio and transaction data'

    def handle(self, *args, **kwargs):
        portfolio, created = Portfolio.objects.get_or_create(
            name='Sample Portfolio',
            defaults={'description': 'This is a test portfolio'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created portfolio: {portfolio.name}"))
        else:
            self.stdout.write(self.style.WARNING("Portfolio already exists"))

        # Add transactions
        Transaction.objects.get_or_create(
            portfolio=portfolio,
            coin_id='bitcoin',
            coin_symbol='BTC',
            coin_name='Bitcoin',
            amount=0.01,
            price_at_purchase=30000,
            transaction_type='buy',
            timestamp=timezone.now()
        )

        self.stdout.write(self.style.SUCCESS("Seed data inserted."))