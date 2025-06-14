from django.urls import path
from . import views

urlpatterns = [
    # Portfolio management
    path('portfolios/', views.portfolios, name='portfolios'),
    path('portfolios/<str:portfolio_id>/', views.portfolio_detail, name='portfolio_detail'),
    path('portfolios/<str:portfolio_id>/analytics/', views.portfolio_analytics_view, name='portfolio_analytics'),
    
    # Transaction management
    path('portfolios/<str:portfolio_id>/transactions/', views.add_transaction, name='add_transaction'),
    path('portfolios/<str:portfolio_id>/transactions/<str:transaction_id>/', views.remove_transaction, name='remove_transaction'),
    
    # Cryptocurrency data
    path('coins/search/', views.search_coins, name='search_coins'),
    path('coins/prices/', views.coin_prices, name='coin_prices'),
]