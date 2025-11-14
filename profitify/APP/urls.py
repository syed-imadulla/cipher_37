from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing-page'),
    
    path('finance/', views.finance_tracker, name='finance-tracker'),
    
    path('advisor/', views.ai_advisor, name='ai-advisor'),

    path('login/', views.login_page, name='login-page'),
    
    path('dashboard/', views.dashboard, name='dashboard-page'),

    path('settings/', views.settings_page, name='settings-page'),

    # This is the API endpoint for your barcode scanner
    path('api/scan/<str:barcode>/', views.scan_product_api, name='api-scan-product'),
]