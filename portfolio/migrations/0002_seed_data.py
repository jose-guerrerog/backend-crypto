from django.db import migrations

def create_seed_data(apps, schema_editor):
    Portfolio = apps.get_model('portfolio', 'Portfolio')
    Transaction = apps.get_model('portfolio', 'Transaction')

    if not Portfolio.objects.exists():
        portfolio = Portfolio.objects.create(name="Default Portfolio")

        Transaction.objects.create(
            portfolio=portfolio,
            coin_id="bitcoin",
            coin_name="Bitcoin",
            coin_symbol="BTC",
            amount=0.01,
            price_usd=50000,
            transaction_type="buy"
        )

        Transaction.objects.create(
            portfolio=portfolio,
            coin_id="ethereum",
            coin_name="Ethereum",
            coin_symbol="ETH",
            amount=0.5,
            price_usd=2000,
            transaction_type="buy"
        )

def remove_seed_data(apps, schema_editor):
    Portfolio = apps.get_model('portfolio', 'Portfolio')
    Transaction = apps.get_model('portfolio', 'Transaction')

    Transaction.objects.all().delete()
    Portfolio.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_seed_data, remove_seed_data),
    ]
