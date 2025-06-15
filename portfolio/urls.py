from django.urls import path
from . import views

urlpatterns = [
    # Portfolio endpoints - use str instead of path to avoid greedy matching
    path('portfolios/', views.portfolios, name='portfolios'),
    path('portfolios/<int:portfolio_id>/', views.portfolio_detail, name='portfolio-detail'),
    
    # Transaction endpoints - use str to match UUID format exactly
    path('portfolios/<int:portfolio_id>/transactions/', views.portfolio_transactions, name='portfolio-transactions'),
    path('portfolios/<int:portfolio_id>/transactions/<int:transaction_id>/', views.remove_transaction, name='remove-transaction'),
    
    # Analytics endpoint - use str to match UUID format exactly
    path('portfolios/<int:portfolio_id>/analytics/', views.portfolio_analytics_view, name='portfolio-analytics'),
    
    # Coin endpoints
    path('coins/search/', views.search_coins, name='search-coins'),
    path('coins/prices/', views.coin_prices, name='coin-prices'),
]