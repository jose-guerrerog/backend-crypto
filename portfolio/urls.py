from django.urls import path
from . import views

urlpatterns = [
    # Portfolio endpoints - flexible pattern to handle any ID format
    path('portfolios/', views.portfolios, name='portfolios'),
    path('portfolios/<path:portfolio_id>/', views.portfolio_detail, name='portfolio-detail'),
    
    # Transaction endpoints - flexible pattern to handle any ID format
    path('portfolios/<path:portfolio_id>/transactions/', views.portfolio_transactions, name='portfolio-transactions'),
    path('portfolios/<path:portfolio_id>/transactions/<str:transaction_id>/', views.remove_transaction, name='remove-transaction'),
    
    # Analytics endpoint - flexible pattern to handle any ID format  
    path('portfolios/<path:portfolio_id>/analytics/', views.portfolio_analytics_view, name='portfolio-analytics'),
    
    # Coin endpoints
    path('coins/search/', views.search_coins, name='search-coins'),
    path('coins/prices/', views.coin_prices, name='coin-prices'),
]