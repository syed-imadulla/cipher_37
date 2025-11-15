from django.urls import path
from . import views

urlpatterns = [
    # ---------------------
    # PAGE ROUTES (HTML pages)
    # ---------------------
    path('', views.landing_page, name='landing-page'),
    path('login/', views.login_page, name='login-page'),
    path('dashboard/', views.dashboard, name='dashboard-page'),
    path('finance/', views.finance_tracker, name='finance-tracker'),
    path('advisor/', views.ai_advisor, name='ai-advisor'),
    path('settings/', views.settings_page, name='settings-page'),
    path('add-product/', views.add_product, name='add-product-page'),
    path('sell-product/<int:product_id>/', views.sell_product, name='sell-product-page'),

    # ---------------------
    # API ROUTES (AJAX / JSON endpoints)
    # ---------------------

    # BARCODE / SCANNER APIs
    path('api/scan-check/', views.scan_barcode_api, name='scan-barcode-api'),
    path('api/scan/<str:barcode>/', views.scan_product_api, name='api-scan-product'),

    # GENERAL TEST / UPDATE API (if you still need it)
    path('api/update-item/', views.update_item, name='update-item'),

    # FINAL: SELL PRODUCT API (THIS IS WHAT FRONTEND NEEDS)
    path('api/sell-product/', views.sell_product_api, name='sell-product-api'),
]
