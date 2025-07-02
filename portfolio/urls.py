from django.urls import path
from . import views

urlpatterns = [
    path('portfolios/', views.portfolios, name='portfolios'),
    path('portfolios/<int:portfolio_id>/', views.portfolio_detail, name='portfolio-detail'),
    path('portfolios/<int:portfolio_id>/transactions/', views.portfolio_transactions, name='portfolio-transactions'),
    path('portfolios/<int:portfolio_id>/transactions/<int:transaction_id>/', views.remove_transaction, name='remove-transaction'),
    path('portfolios/<int:portfolio_id>/analytics/', views.portfolio_analytics_view, name='portfolio-analytics'),
    path('coins/search/', views.search_coins, name='search-coins'),
    path('coins/prices/', views.coin_prices, name='coin-prices'),
]