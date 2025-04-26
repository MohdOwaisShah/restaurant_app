from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import menu

urlpatterns = [
    path('generate-qr/<int:table_number>/', views.generate_qr, name='generate_qr'),
    path('login/<int:table_number>/', views.login_view, name='table_login'),
    path('login/', views.login_view, name='login'),
    path('', views.menu, name='menu'),
    path('menu/', menu, name='menu'),
    path('qr-codes/', views.qr_codes_view, name='qr_codes'),
    path('logout/', views.logout_view, name='logout'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('update-instructions/', views.update_instructions, name='update_instructions'),
    path('get-cart-count/', views.get_cart_count, name='get_cart_count'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('history/', views.re_order, name='re_order'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('transactions/', views.view_transactions, name='view_transactions'),
    path('reorder/<int:transaction_id>/', views.reorder, name='reorder'),
    path('restaurant-admin/', views.admin_login, name='restaurant_admin'),
    path('get-addons/<int:item_id>/', views.get_addons, name='get_addons'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # ✅ Serve images