# portfolio/migrations/0002_seed_data.py

from django.db import migrations

def create_seed_data(apps, schema_editor):
    Portfolio = apps.get_model('portfolio', 'Portfolio')
    Transaction = apps.get_model('portfolio', 'Transaction')

    # Wipe all previous data
    Transaction.objects.all().delete()
    Portfolio.objects.all().delete()

    # First Portfolio with 4 transactions
    portfolio1 = Portfolio.objects.create(name="Long-Term Holdings")
    Transaction.objects.bulk_create([
        Transaction(
            portfolio=portfolio1,
            coin_id="bitcoin",
            coin_name="Bitcoin",
            coin_symbol="BTC",
            amount=0.01,
            price_usd=50000,
            transaction_type="buy"
        ),
        Transaction(
            portfolio=portfolio1,
            coin_id="ethereum",
            coin_name="Ethereum",
            coin_symbol="ETH",
            amount=0.5,
            price_usd=2000,
            transaction_type="buy"
        ),
        Transaction(
            portfolio=portfolio1,
            coin_id="cardano",
            coin_name="Cardano",
            coin_symbol="ADA",
            amount=100,
            price_usd=1.2,
            transaction_type="buy"
        ),
        Transaction(
            portfolio=portfolio1,
            coin_id="bitcoin",
            coin_name="Bitcoin",
            coin_symbol="BTC",
            amount=0.005,
            price_usd=55000,
            transaction_type="buy"
        ),
    ])

    # Second Portfolio with 3 transactions
    portfolio2 = Portfolio.objects.create(name="High-Risk Trades")
    Transaction.objects.bulk_create([
        Transaction(
            portfolio=portfolio2,
            coin_id="dogecoin",
            coin_name="Dogecoin",
            coin_symbol="DOGE",
            amount=1000,
            price_usd=0.05,
            transaction_type="buy"
        ),
        Transaction(
            portfolio=portfolio2,
            coin_id="solana",
            coin_name="Solana",
            coin_symbol="SOL",
            amount=20,
            price_usd=35,
            transaction_type="buy"
        ),
        Transaction(
            portfolio=portfolio2,
            coin_id="shiba-inu",
            coin_name="Shiba Inu",
            coin_symbol="SHIB",
            amount=1000000,
            price_usd=0.00001,
            transaction_type="buy"
        ),
    ])

class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_seed_data),
    ]
