from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('classes/', views.classes, name='classes'),
    path('plans/', views.plans_view, name='plans'),
    path('team/', views.team, name='team'),
    path('timetable/', views.timetable, name='timetable'),
    path('blog/', views.blog, name='blog'),
    path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
    path('store/', views.store, name='store'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    
    # Cart and checkout
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.orders, name='orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Plan subscriptions
    path('subscribe/<int:plan_id>/', views.subscribe_plan, name='subscribe_plan'),
    path('subscription-confirmation/<int:subscription_id>/', views.subscription_confirmation, name='subscription_confirmation'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    
    # Tracker and booking
    path('tracker/', views.tracker, name='tracker'),
    path('delete-workout/<int:workout_id>/', views.delete_workout, name='delete_workout'),
    path('bookclass/', views.bookclass, name='bookclass'),
    path('booking/', views.booking, name='booking'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('booking-history/', views.booking_history, name='booking_history'),
    
    # Other pages
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    
    # API endpoints
    path('api/newsletter-subscribe/', views.newsletter_subscribe, name='api_newsletter_subscribe'),
    path('api/get-cart/', views.api_get_cart, name='api_get_cart'),
    path('api/add-to-cart/', views.api_add_to_cart, name='api_add_to_cart'),

    
]

