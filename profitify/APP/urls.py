from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing-page'),
    
    path('finance/', views.finance_tracker, name='finance-tracker'),
    
    path('advisor/', views.ai_advisor, name='ai-advisor'),

    path('login/', views.login_page, name='login-page'),
    
    path('dashboard/', views.dashboard, name='dashboard-page'),

    path('settings/', views.settings_page, name='settings-page'),

    path('api/scan-check/', views.scan_barcode_api, name='scan-barcode-api'),

    # In APP/urls.py replace the sell_product-related lines with:
    path('sell_product/', views.sell_product_list, name='sell-product-list'),
    
    path('sell_product/<int:product_>/', views.sell_product, name='sell-product-page'),


    path('add_product/', views.add_product, name='add_product-page'),   

    

    # This is the API endpoint for your barcode scanner
    path('api/scan/<str:barcode>/', views.scan_product_api, name='api-scan-product'),

    path('api/generate-summary/', views.generate_ai_summary, name='generate-ai-summary'),
]