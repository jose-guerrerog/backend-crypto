from django.db import models

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    portfolio = models.ForeignKey(Portfolio, related_name='transactions', on_delete=models.CASCADE)
    coin_id = models.CharField(max_length=50)
    coin_name = models.CharField(max_length=50)
    coin_symbol = models.CharField(max_length=10)
    amount = models.FloatField()
    price_usd = models.FloatField()
    transaction_type = models.CharField(max_length=4, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.amount} {self.coin_symbol}"
