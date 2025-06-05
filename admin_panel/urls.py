from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Users and Profiles
    path('users/', views.user_list, name='admin_user_list'),
    path('users/create/', views.user_create, name='admin_user_create'),
    path('users/<int:user_id>/', views.user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='admin_user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='admin_user_delete'),
    
    # Categories
    path('categories/', views.category_list, name='admin_category_list'),
    path('categories/create/', views.category_create, name='admin_category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='admin_category_detail'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='admin_category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='admin_category_delete'),
    
    # Products
    path('products/', views.product_list, name='admin_product_list'),
    path('products/create/', views.product_create, name='admin_product_create'),
    path('products/<int:product_id>/', views.product_detail, name='admin_product_detail'),
    path('products/<int:product_id>/edit/', views.product_edit, name='admin_product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='admin_product_delete'),
    
    # Plans
    path('plans/', views.plan_list, name='admin_plan_list'),
    path('plans/create/', views.plan_create, name='admin_plan_create'),
    path('plans/<int:plan_id>/', views.plan_detail, name='admin_plan_detail'),
    path('plans/<int:plan_id>/edit/', views.plan_edit, name='admin_plan_edit'),
    path('plans/<int:plan_id>/delete/', views.plan_delete, name='admin_plan_delete'),
    
    # Plan Features
    path('plan-features/', views.plan_feature_list, name='admin_plan_feature_list'),
    path('plan-features/create/', views.plan_feature_create, name='admin_plan_feature_create'),
    path('plan-features/<int:feature_id>/', views.plan_feature_detail, name='admin_plan_feature_detail'),
    path('plan-features/<int:feature_id>/edit/', views.plan_feature_edit, name='admin_plan_feature_edit'),
    path('plan-features/<int:feature_id>/delete/', views.plan_feature_delete, name='admin_plan_feature_delete'),
    
    # Team Members
    path('team-members/', views.team_member_list, name='admin_team_member_list'),
    path('team-members/create/', views.team_member_create, name='admin_team_member_create'),
    path('team-members/<int:member_id>/', views.team_member_detail, name='admin_team_member_detail'),
    path('team-members/<int:member_id>/edit/', views.team_member_edit, name='admin_team_member_edit'),
    path('team-members/<int:member_id>/delete/', views.team_member_delete, name='admin_team_member_delete'),
    
    # Gym Classes
    path('gym-classes/', views.gym_class_list, name='admin_gym_class_list'),
    path('gym-classes/create/', views.gym_class_create, name='admin_gym_class_create'),
    path('gym-classes/<int:class_id>/', views.gym_class_detail, name='admin_gym_class_detail'),
    path('gym-classes/<int:class_id>/edit/', views.gym_class_edit, name='admin_gym_class_edit'),
    path('gym-classes/<int:class_id>/delete/', views.gym_class_delete, name='admin_gym_class_delete'),
    
    # Class Schedules
    path('class-schedules/', views.class_schedule_list, name='admin_class_schedule_list'),
    path('class-schedules/create/', views.class_schedule_create, name='admin_class_schedule_create'),
    path('class-schedules/<int:schedule_id>/', views.class_schedule_detail, name='admin_class_schedule_detail'),
    path('class-schedules/<int:schedule_id>/edit/', views.class_schedule_edit, name='admin_class_schedule_edit'),
    path('class-schedules/<int:schedule_id>/delete/', views.class_schedule_delete, name='admin_class_schedule_delete'),
    
    # Class Bookings
    path('class-bookings/', views.class_booking_list, name='admin_class_booking_list'),
    path('class-bookings/create/', views.class_booking_create, name='admin_class_booking_create'),
    path('class-bookings/<int:booking_id>/', views.class_booking_detail, name='admin_class_booking_detail'),
    path('class-bookings/<int:booking_id>/edit/', views.class_booking_edit, name='admin_class_booking_edit'),
    path('class-bookings/<int:booking_id>/delete/', views.class_booking_delete, name='admin_class_booking_delete'),
    
    # Workouts
    path('workouts/', views.workout_list, name='admin_workout_list'),
    path('workouts/create/', views.workout_create, name='admin_workout_create'),
    path('workouts/<int:workout_id>/', views.workout_detail, name='admin_workout_detail'),
    path('workouts/<int:workout_id>/edit/', views.workout_edit, name='admin_workout_edit'),
    path('workouts/<int:workout_id>/delete/', views.workout_delete, name='admin_workout_delete'),
    
    # Orders
    path('orders/', views.order_list, name='admin_order_list'),
    path('orders/create/', views.order_create, name='admin_order_create'),
    path('orders/<int:order_id>/', views.order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/edit/', views.order_edit, name='admin_order_edit'),
    path('orders/<int:order_id>/delete/', views.order_delete, name='admin_order_delete'),
    
    # Plan Subscriptions
    path('subscriptions/', views.subscription_list, name='admin_subscription_list'),
    path('subscriptions/', views.subscription_list, name='admin_subscriptions'),
    path('subscriptions/create/', views.subscription_create, name='admin_subscription_create'),
    path('subscriptions/add/', views.subscription_add, name='admin_subscription_add'),
    path('subscriptions/<int:subscription_id>/', views.subscription_detail, name='admin_subscription_detail'),
    path('subscriptions/<int:subscription_id>/edit/', views.subscription_edit, name='admin_subscription_edit'),
    path('subscriptions/<int:subscription_id>/delete/', views.subscription_delete, name='admin_subscription_delete'),
    
    # Blog Posts
    path('blog-posts/', views.blog_post_list, name='admin_blog_post_list'),
    path('blog-posts/create/', views.blog_post_create, name='admin_blog_post_create'),
    path('blog-posts/<int:post_id>/', views.blog_post_detail, name='admin_blog_post_detail'),
    path('blog-posts/<int:post_id>/edit/', views.blog_post_edit, name='admin_blog_post_edit'),
    path('blog-posts/<int:post_id>/delete/', views.blog_post_delete, name='admin_blog_post_delete'),
    
    # Newsletter Subscribers
    path('newsletters/', views.newsletter_list, name='admin_newsletter_list'),
    path('newsletters/create/', views.newsletter_create, name='admin_newsletter_create'),
    path('newsletters/<int:newsletter_id>/', views.newsletter_detail, name='admin_newsletter_detail'),
    path('newsletters/<int:newsletter_id>/edit/', views.newsletter_edit, name='admin_newsletter_edit'),
    path('newsletters/<int:newsletter_id>/delete/', views.newsletter_delete, name='admin_newsletter_delete'),
    
    # Contact Messages
    path('contact-messages/', views.contact_message_list, name='admin_contact_message_list'),
    path('contact-messages/<int:message_id>/', views.contact_message_detail, name='admin_contact_message_detail'),
    path('contact-messages/<int:message_id>/delete/', views.contact_message_delete, name='admin_contact_message_delete'),
    path('contact-messages/<int:message_id>/reply/', views.contact_message_reply, name='admin_contact_message_reply'),
    
    # Reports
    path('reports/', views.reports_dashboard, name='admin_reports_dashboard'),
    path('reports/users/', views.user_report, name='admin_user_report'),
    path('reports/sales/', views.sales_report, name='admin_sales_report'),
    path('reports/subscriptions/', views.subscription_report, name='admin_subscription_report'),
    path('reports/bookings/', views.booking_report, name='admin_booking_report'),
    path('reports/export/<str:report_type>/', views.export_report, name='admin_export_report'),
    path('admin/reports/export/<str:report_type>/', views.export_user_report, name='admin_export_report'),

    # API endpoints for AJAX operations
    path('api/users/', views.api_user_list, name='api_user_list'),
    path('api/categories/', views.api_category_list, name='api_category_list'),
    path('api/products/', views.api_product_list, name='api_product_list'),
    path('api/plans/', views.api_plan_list, name='api_plan_list'),
    path('api/team-members/', views.api_team_member_list, name='api_team_member_list'),
    path('api/gym-classes/', views.api_gym_class_list, name='api_gym_class_list'),
    path('api/orders/', views.api_order_list, name='api_order_list'),
    path('api/subscriptions/', views.api_subscription_list, name='api_subscription_list'),
    path('api/blog-posts/', views.api_blog_post_list, name='api_blog_post_list'),
]

