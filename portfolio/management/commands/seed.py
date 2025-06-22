from django.core.management.base import BaseCommand
from portfolio.models import Portfolio, Transaction

class Command(BaseCommand):
    help = 'Wipes and seeds the database with sample portfolios and transactions.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing old data...")
        Transaction.objects.all().delete()
        Portfolio.objects.all().delete()

        self.stdout.write("Seeding new data...")

        p1 = Portfolio.objects.create(name="Jose's Portfolio")
        p2 = Portfolio.objects.create(name="Sample Portfolio")

        Transaction.objects.bulk_create([
            Transaction(portfolio=p1, coin_id="bitcoin", coin_name="Bitcoin", coin_symbol="BTC", amount=0.01, price_usd=50000, transaction_type="buy"),
            Transaction(portfolio=p1, coin_id="ethereum", coin_name="Ethereum", coin_symbol="ETH", amount=0.5, price_usd=2000, transaction_type="buy"),
            Transaction(portfolio=p1, coin_id="cardano", coin_name="Cardano", coin_symbol="ADA", amount=100, price_usd=1.5, transaction_type="buy"),
            Transaction(portfolio=p1, coin_id="bitcoin", coin_name="Bitcoin", coin_symbol="BTC", amount=0.005, price_usd=52000, transaction_type="sell"),

            Transaction(portfolio=p2, coin_id="solana", coin_name="Solana", coin_symbol="SOL", amount=2, price_usd=100, transaction_type="buy"),
            Transaction(portfolio=p2, coin_id="ethereum", coin_name="Ethereum", coin_symbol="ETH", amount=0.2, price_usd=2100, transaction_type="buy"),
            Transaction(portfolio=p2, coin_id="dogecoin", coin_name="Dogecoin", coin_symbol="DOGE", amount=500, price_usd=0.08, transaction_type="buy"),
        ])

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))