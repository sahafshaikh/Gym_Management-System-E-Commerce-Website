from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Sum, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import json
from datetime import datetime, timedelta
from django.utils import timezone
import csv
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction  
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, fields, Q
from django.utils import timezone
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import letter  
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from accounts.models import UserProfile
from core.models import (
    Category, Product, ProductReview, Plan, PlanFeature, TeamMember,
    GymClass, ClassSchedule, ClassBooking, Workout, Cart, CartItem,
    Order, OrderItem, PlanSubscription, BlogPost, Newsletter, ContactMessage
)

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Authentication views
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid username or password, or you don't have admin privileges.")
    
    return render(request, 'admin_panel/login.html')

@user_passes_test(is_admin)
def admin_logout(request):
    logout(request)
    return redirect('admin_login')

# Dashboard view
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get counts for dashboard
    user_count = User.objects.count()
    product_count = Product.objects.count()
    order_count = Order.objects.count()
    subscription_count = PlanSubscription.objects.count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Recent users
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    # Sales data for chart
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)
    
    sales_data = Order.objects.filter(
        created_at__date__gte=last_30_days
    ).values('created_at__date').annotate(
        total_sales=Sum('total')
    ).order_by('created_at__date')
    
    sales_chart_data = {
        'labels': [str(item['created_at__date']) for item in sales_data],
        'data': [float(item['total_sales']) for item in sales_data]
    }
    
    context = {
        'user_count': user_count,
        'product_count': product_count,
        'order_count': order_count,
        'subscription_count': subscription_count,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'sales_chart_data': json.dumps(sales_chart_data)
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

# User views
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query) | users.filter(email__icontains=search_query)
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/users/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_staff = request.POST.get('is_staff') == 'on'
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff
            )
            
            # Update profile
            profile = user.profile
            profile.mobile = request.POST.get('mobile')
            profile.address = request.POST.get('address')
            profile.gender = request.POST.get('gender')
            profile.save()
            
            messages.success(request, f"User {username} created successfully!")
            return redirect('admin_user_list')
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
    
    return render(request, 'admin_panel/users/create.html')

@user_passes_test(is_admin)
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin_panel/users/detail.html', {'user': user})

@user_passes_test(is_admin)
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_staff = request.POST.get('is_staff') == 'on'
        
        # Update password if provided
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        
        # Update profile
        profile = user.profile
        profile.mobile = request.POST.get('mobile')
        profile.address = request.POST.get('address')
        profile.gender = request.POST.get('gender')
        profile.save()
        
        messages.success(request, f"User {user.username} updated successfully!")
        return redirect('admin_user_list')
    
    return render(request, 'admin_panel/users/edit.html', {'user': user})

@user_passes_test(is_admin)
@require_POST
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"User {username} deleted successfully!")
    return redirect('admin_user_list')

# Category views
@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/categories/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        
        try:
            Category.objects.create(name=name)
            messages.success(request, f"Category {name} created successfully!")
            return redirect('admin_category_list')
        except Exception as e:
            messages.error(request, f"Error creating category: {str(e)}")
    
    return render(request, 'admin_panel/categories/create.html')

@user_passes_test(is_admin)
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'admin_panel/categories/detail.html', {'category': category, 'products': products})

@user_passes_test(is_admin)
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.save()
        messages.success(request, f"Category {category.name} updated successfully!")
        return redirect('admin_category_list')
    
    return render(request, 'admin_panel/categories/edit.html', {'category': category})

@user_passes_test(is_admin)
@require_POST
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    name = category.name
    category.delete()
    messages.success(request, f"Category {name} deleted successfully!")
    return redirect('admin_category_list')

# Product views
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all().select_related('category')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    return render(request, 'admin_panel/products/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'categories': categories,
        'selected_category': category_id
    })

@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        rating = request.POST.get('rating', 0)
        
        try:
            product = Product.objects.create(
                name=name,
                category_id=category_id,
                price=price,
                stock=stock,
                description=description,
                rating=rating
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
            
            messages.success(request, f"Product {name} created successfully!")
            return redirect('admin_product_list')
        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")
    
    categories = Category.objects.all()
    return render(request, 'admin_panel/products/create.html', {'categories': categories})

@user_passes_test(is_admin)
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = ProductReview.objects.filter(product=product).select_related('user')
    return render(request, 'admin_panel/products/detail.html', {'product': product, 'reviews': reviews})

@user_passes_test(is_admin)
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')
        product.rating = request.POST.get('rating', 0)
        
        # Handle image upload
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        
        product.save()
        messages.success(request, f"Product {product.name} updated successfully!")
        return redirect('admin_product_list')
    
    categories = Category.objects.all()
    return render(request, 'admin_panel/products/edit.html', {'product': product, 'categories': categories})

@user_passes_test(is_admin)
@require_POST
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    product.delete()
    messages.success(request, f"Product {name} deleted successfully!")
    return redirect('admin_product_list')

# Plan views
@user_passes_test(is_admin)
def plan_list(request):
    plans = Plan.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        plans = plans.filter(name__icontains=search_query) | plans.filter(description__icontains=search_query)
    
    # Pagination
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/plans/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def plan_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        
        try:
            plan = Plan.objects.create(
                name=name,
                price=price,
                description=description
            )
            
            # Add features
            features = request.POST.getlist('features[]')
            for feature in features:
                if feature.strip():
                    PlanFeature.objects.create(plan=plan, feature=feature.strip())
            
            messages.success(request, f"Plan {name} created successfully!")
            return redirect('admin_plan_list')
        except Exception as e:
            messages.error(request, f"Error creating plan: {str(e)}")
    
    return render(request, 'admin_panel/plans/create.html')

@user_passes_test(is_admin)
def plan_detail(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    features = PlanFeature.objects.filter(plan=plan)
    subscriptions = PlanSubscription.objects.filter(plan=plan).select_related('user')
    return render(request, 'admin_panel/plans/detail.html', {
        'plan': plan,
        'features': features,
        'subscriptions': subscriptions
    })

@user_passes_test(is_admin)
def plan_edit(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    features = PlanFeature.objects.filter(plan=plan)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name')
        plan.price = request.POST.get('price')
        plan.description = request.POST.get('description')
        plan.save()
        
        # Update features
        features.delete()  # Remove existing features
        new_features = request.POST.getlist('features[]')
        for feature in new_features:
            if feature.strip():
                PlanFeature.objects.create(plan=plan, feature=feature.strip())
        
        messages.success(request, f"Plan {plan.name} updated successfully!")
        return redirect('admin_plan_list')
    
    return render(request, 'admin_panel/plans/edit.html', {'plan': plan, 'features': features})

@user_passes_test(is_admin)
@require_POST
def plan_delete(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    name = plan.name
    plan.delete()
    messages.success(request, f"Plan {name} deleted successfully!")
    return redirect('admin_plan_list')

# Plan Feature views
@user_passes_test(is_admin)
def plan_feature_list(request):
    features = PlanFeature.objects.all().select_related('plan')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        features = features.filter(feature__icontains=search_query) | features.filter(plan__name__icontains=search_query)
    
    # Filter by plan
    plan_id = request.GET.get('plan')
    if plan_id:
        features = features.filter(plan_id=plan_id)
    
    # Pagination
    paginator = Paginator(features, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    plans = Plan.objects.all()
    
    return render(request, 'admin_panel/plan_features/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'plans': plans,
        'selected_plan': plan_id
    })

@user_passes_test(is_admin)
def plan_feature_create(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan')
        feature = request.POST.get('feature')
        
        try:
            PlanFeature.objects.create(
                plan_id=plan_id,
                feature=feature
            )
            messages.success(request, "Plan feature created successfully!")
            return redirect('admin_plan_feature_list')
        except Exception as e:
            messages.error(request, f"Error creating plan feature: {str(e)}")
    
    plans = Plan.objects.all()
    return render(request, 'admin_panel/plan_features/create.html', {'plans': plans})

@user_passes_test(is_admin)
def plan_feature_detail(request, feature_id):
    feature = get_object_or_404(PlanFeature, id=feature_id)
    return render(request, 'admin_panel/plan_features/detail.html', {'feature': feature})

@user_passes_test(is_admin)
def plan_feature_edit(request, feature_id):
    feature = get_object_or_404(PlanFeature, id=feature_id)
    
    if request.method == 'POST':
        feature.plan_id = request.POST.get('plan')
        feature.feature = request.POST.get('feature')
        feature.save()
        messages.success(request, "Plan feature updated successfully!")
        return redirect('admin_plan_feature_list')
    
    plans = Plan.objects.all()
    return render(request, 'admin_panel/plan_features/edit.html', {'feature': feature, 'plans': plans})

@user_passes_test(is_admin)
@require_POST
def plan_feature_delete(request, feature_id):
    feature = get_object_or_404(PlanFeature, id=feature_id)
    feature.delete()
    messages.success(request, "Plan feature deleted successfully!")
    return redirect('admin_plan_feature_list')

# Team Member views
@user_passes_test(is_admin)
def team_member_list(request):
    members = TeamMember.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(name__icontains=search_query) | members.filter(position__icontains=search_query)
    
    # Pagination
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/team_members/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def team_member_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        position = request.POST.get('position')
        bio = request.POST.get('bio')
        
        try:
            member = TeamMember.objects.create(
                name=name,
                position=position,
                bio=bio
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                member.image = request.FILES['image']
                member.save()
            
            messages.success(request, f"Team member {name} created successfully!")
            return redirect('admin_team_member_list')
        except Exception as e:
            messages.error(request, f"Error creating team member: {str(e)}")
    
    return render(request, 'admin_panel/team_members/create.html')

@user_passes_test(is_admin)
def team_member_detail(request, member_id):
    member = get_object_or_404(TeamMember, id=member_id)
    return render(request, 'admin_panel/team_members/detail.html', {'member': member})

@user_passes_test(is_admin)
def team_member_edit(request, member_id):
    member = get_object_or_404(TeamMember, id=member_id)
    
    if request.method == 'POST':
        member.name = request.POST.get('name')
        member.position = request.POST.get('position')
        member.bio = request.POST.get('bio')
        
        # Handle image upload
        if 'image' in request.FILES:
            member.image = request.FILES['image']
        
        member.save()
        messages.success(request, f"Team member {member.name} updated successfully!")
        return redirect('admin_team_member_list')
    
    return render(request, 'admin_panel/team_members/edit.html', {'member': member})

@user_passes_test(is_admin)
@require_POST
def team_member_delete(request, member_id):
    member = get_object_or_404(TeamMember, id=member_id)
    name = member.name
    member.delete()
    messages.success(request, f"Team member {name} deleted successfully!")
    return redirect('admin_team_member_list')

# Gym Class views
@user_passes_test(is_admin)
def gym_class_list(request):
    classes = GymClass.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        classes = classes.filter(name__icontains=search_query) | classes.filter(description__icontains=search_query)
    
    # Pagination
    paginator = Paginator(classes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/gym_classes/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def gym_class_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        try:
            gym_class = GymClass.objects.create(
                name=name,
                description=description
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                gym_class.image = request.FILES['image']
                gym_class.save()
            
            messages.success(request, f"Gym class {name} created successfully!")
            return redirect('admin_gym_class_list')
        except Exception as e:
            messages.error(request, f"Error creating gym class: {str(e)}")
    
    return render(request, 'admin_panel/gym_classes/create.html')

@user_passes_test(is_admin)
def gym_class_detail(request, class_id):
    gym_class = get_object_or_404(GymClass, id=class_id)
    schedules = ClassSchedule.objects.filter(gym_class=gym_class)
    return render(request, 'admin_panel/gym_classes/detail.html', {'gym_class': gym_class, 'schedules': schedules})

@user_passes_test(is_admin)
def gym_class_edit(request, class_id):
    gym_class = get_object_or_404(GymClass, id=class_id)
    
    if request.method == 'POST':
        gym_class.name = request.POST.get('name')
        gym_class.description = request.POST.get('description')
        
        # Handle image upload
        if 'image' in request.FILES:
            gym_class.image = request.FILES['image']
        
        gym_class.save()
        messages.success(request, f"Gym class {gym_class.name} updated successfully!")
        return redirect('admin_gym_class_list')
    
    return render(request, 'admin_panel/gym_classes/edit.html', {'gym_class': gym_class})

@user_passes_test(is_admin)
@require_POST
def gym_class_delete(request, class_id):
    gym_class = get_object_or_404(GymClass, id=class_id)
    name = gym_class.name
    gym_class.delete()
    messages.success(request, f"Gym class {name} deleted successfully!")
    return redirect('admin_gym_class_list')

# Class Schedule views
@user_passes_test(is_admin)
def class_schedule_list(request):
    schedules = ClassSchedule.objects.all().select_related('gym_class')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        schedules = schedules.filter(gym_class__name__icontains=search_query)
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        schedules = schedules.filter(gym_class_id=class_id)
    
    # Pagination
    paginator = Paginator(schedules, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    classes = GymClass.objects.all()
    
    return render(request, 'admin_panel/class_schedules/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'classes': classes,
        'selected_class': class_id
    })

@user_passes_test(is_admin)
def class_schedule_create(request):
    if request.method == 'POST':
        gym_class_id = request.POST.get('gym_class')
        day = request.POST.get('day')
        time = request.POST.get('time')
        
        try:
            ClassSchedule.objects.create(
                gym_class_id=gym_class_id,
                day=day,
                time=time
            )
            messages.success(request, "Class schedule created successfully!")
            return redirect('admin_class_schedule_list')
        except Exception as e:
            messages.error(request, f"Error creating class schedule: {str(e)}")
    
    classes = GymClass.objects.all()
    return render(request, 'admin_panel/class_schedules/create.html', {'classes': classes})

@user_passes_test(is_admin)
def class_schedule_detail(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    bookings = ClassBooking.objects.filter(class_schedule=schedule).select_related('user')
    return render(request, 'admin_panel/class_schedules/detail.html', {'schedule': schedule, 'bookings': bookings})

@user_passes_test(is_admin)
def class_schedule_edit(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    
    if request.method == 'POST':
        schedule.gym_class_id = request.POST.get('gym_class')
        schedule.day = request.POST.get('day')
        schedule.time = request.POST.get('time')
        schedule.save()
        messages.success(request, "Class schedule updated successfully!")
        return redirect('admin_class_schedule_list')
    
    classes = GymClass.objects.all()
    return render(request, 'admin_panel/class_schedules/edit.html', {'schedule': schedule, 'classes': classes})

@user_passes_test(is_admin)
@require_POST
def class_schedule_delete(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    schedule.delete()
    messages.success(request, "Class schedule deleted successfully!")
    return redirect('admin_class_schedule_list')

# Class Booking views
@user_passes_test(is_admin)
def class_booking_list(request):
    bookings = ClassBooking.objects.all().select_related('user', 'class_schedule', 'class_schedule__gym_class')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        bookings = bookings.filter(user__username__icontains=search_query) | bookings.filter(class_schedule__gym_class__name__icontains=search_query)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        bookings = bookings.filter(status=status)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/class_bookings/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status
    })

@user_passes_test(is_admin)
def class_booking_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        class_schedule_id = request.POST.get('class_schedule')
        booking_date = request.POST.get('booking_date')
        status = request.POST.get('status')
        
        try:
            ClassBooking.objects.create(
                user_id=user_id,
                class_schedule_id=class_schedule_id,
                booking_date=booking_date,
                status=status
            )
            messages.success(request, "Class booking created successfully!")
            return redirect('admin_class_booking_list')
        except Exception as e:
            messages.error(request, f"Error creating class booking: {str(e)}")
    
    users = User.objects.all()
    schedules = ClassSchedule.objects.all().select_related('gym_class')
    return render(request, 'admin_panel/class_bookings/create.html', {'users': users, 'schedules': schedules})

@user_passes_test(is_admin)
def class_booking_detail(request, booking_id):
    booking = get_object_or_404(ClassBooking, id=booking_id)
    return render(request, 'admin_panel/class_bookings/detail.html', {'booking': booking})

@user_passes_test(is_admin)
def class_booking_edit(request, booking_id):
    booking = get_object_or_404(ClassBooking, id=booking_id)
    
    if request.method == 'POST':
        booking.user_id = request.POST.get('user')
        booking.class_schedule_id = request.POST.get('class_schedule')
        booking.booking_date = request.POST.get('booking_date')
        booking.status = request.POST.get('status')
        booking.save()
        messages.success(request, "Class booking updated successfully!")
        return redirect('admin_class_booking_list')
    
    users = User.objects.all()
    schedules = ClassSchedule.objects.all().select_related('gym_class')
    return render(request, 'admin_panel/class_bookings/edit.html', {
        'booking': booking,
        'users': users,
        'schedules': schedules
    })

@user_passes_test(is_admin)
@require_POST
def class_booking_delete(request, booking_id):
    booking = get_object_or_404(ClassBooking, id=booking_id)
    booking.delete()
    messages.success(request, "Class booking deleted successfully!")
    return redirect('admin_class_booking_list')

# Workout views
@user_passes_test(is_admin)
def workout_list(request):
    workouts = Workout.objects.all().select_related('user')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        workouts = workouts.filter(name__icontains=search_query) | workouts.filter(user__username__icontains=search_query)
    
    # Filter by user
    user_id = request.GET.get('user')
    if user_id:
        workouts = workouts.filter(user_id=user_id)
    
    # Pagination
    paginator = Paginator(workouts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    users = User.objects.all()
    
    return render(request, 'admin_panel/workouts/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'users': users,
        'selected_user': user_id
    })

@user_passes_test(is_admin)
def workout_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        name = request.POST.get('name')
        duration = request.POST.get('duration')
        calories = request.POST.get('calories')
        date = request.POST.get('date')
        
        try:
            Workout.objects.create(
                user_id=user_id,
                name=name,
                duration=duration,
                calories=calories,
                date=date
            )
            messages.success(request, "Workout created successfully!")
            return redirect('admin_workout_list')
        except Exception as e:
            messages.error(request, f"Error creating workout: {str(e)}")
    
    users = User.objects.all()
    return render(request, 'admin_panel/workouts/create.html', {'users': users})

@user_passes_test(is_admin)
def workout_detail(request, workout_id):
    workout = get_object_or_404(Workout, id=workout_id)
    return render(request, 'admin_panel/workouts/detail.html', {'workout': workout})

@user_passes_test(is_admin)
def workout_edit(request, workout_id):
    workout = get_object_or_404(Workout, id=workout_id)
    
    if request.method == 'POST':
        workout.user_id = request.POST.get('user')
        workout.name = request.POST.get('name')
        workout.duration = request.POST.get('duration')
        workout.calories = request.POST.get('calories')
        workout.date = request.POST.get('date')
        workout.save()
        messages.success(request, "Workout updated successfully!")
        return redirect('admin_workout_list')
    
    users = User.objects.all()
    return render(request, 'admin_panel/workouts/edit.html', {'workout': workout, 'users': users})

@user_passes_test(is_admin)
@require_POST
def workout_delete(request, workout_id):
    workout = get_object_or_404(Workout, id=workout_id)
    workout.delete()
    messages.success(request, "Workout deleted successfully!")
    return redirect('admin_workout_list')

# Order views
@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all().select_related('user')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(user__username__icontains=search_query)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/orders/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status
    })

@user_passes_test(is_admin)
def order_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        total = request.POST.get('total')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')
        
        try:
            order = Order.objects.create(
                user_id=user_id,
                total=total,
                payment_method=payment_method,
                status=status
            )
            
            # Add order items
            product_ids = request.POST.getlist('product_ids[]')
            quantities = request.POST.getlist('quantities[]')
            prices = request.POST.getlist('prices[]')
            
            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and prices[i]:
                    OrderItem.objects.create(
                        order=order,
                        product_id=product_ids[i],
                        quantity=quantities[i],
                        price=prices[i]
                    )
            
            messages.success(request, f"Order #{order.id} created successfully!")
            return redirect('admin_order_list')
        except Exception as e:
            messages.error(request, f"Error creating order: {str(e)}")
    
    users = User.objects.all()
    products = Product.objects.all()
    return render(request, 'admin_panel/orders/create.html', {'users': users, 'products': products})

@user_passes_test(is_admin)
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order).select_related('product')
    return render(request, 'admin_panel/orders/detail.html', {'order': order, 'items': items})

@user_passes_test(is_admin)
def order_edit(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order).select_related('product')
    
    if request.method == 'POST':
        order.user_id = request.POST.get('user')
        order.total = request.POST.get('total')
        order.payment_method = request.POST.get('payment_method')
        order.status = request.POST.get('status')
        order.save()
        
        # Update order items
        items.delete()  # Remove existing items
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        prices = request.POST.getlist('prices[]')
        
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and prices[i]:
                OrderItem.objects.create(
                    order=order,
                    product_id=product_ids[i],
                    quantity=quantities[i],
                    price=prices[i]
                )
        
        messages.success(request, f"Order #{order.id} updated successfully!")
        return redirect('admin_order_list')
    
    users = User.objects.all()
    products = Product.objects.all()
    return render(request, 'admin_panel/orders/edit.html', {
        'order': order,
        'items': items,
        'users': users,
        'products': products
    })

@user_passes_test(is_admin)
@require_POST
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, f"Order #{order_id} deleted successfully!")
    return redirect('admin_order_list')

# Plan Subscription views
@user_passes_test(is_admin)
def subscription_list(request):
    subscriptions = PlanSubscription.objects.all().select_related('user', 'plan')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        subscriptions = subscriptions.filter(user__username__icontains=search_query) | subscriptions.filter(plan__name__icontains=search_query)
    
    # Filter by active status
    active = request.GET.get('active')
    if active is not None:
        subscriptions = subscriptions.filter(active=(active == 'true'))
    
    # Pagination
    paginator = Paginator(subscriptions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/subscriptions/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_active': active
    })

@user_passes_test(is_admin)
def subscription_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        plan_id = request.POST.get('plan')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        active = request.POST.get('active') == 'on'
        
        try:
            subscription = PlanSubscription.objects.create(
                user_id=user_id,
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date,
                active=active
            )
            messages.success(request, "Subscription created successfully!")
            return redirect('admin_subscription_list')
        except Exception as e:
            messages.error(request, f"Error creating subscription: {str(e)}")
    
    users = User.objects.all()
    plans = Plan.objects.all()
    return render(request, 'admin_panel/subscriptions/create.html', {'users': users, 'plans': plans})

@user_passes_test(is_admin)
def subscription_detail(request, subscription_id):
    subscription = get_object_or_404(PlanSubscription, id=subscription_id)
    return render(request, 'admin_panel/subscriptions/detail.html', {'subscription': subscription})

@user_passes_test(is_admin)
def subscription_edit(request, subscription_id):
    subscription = get_object_or_404(PlanSubscription, id=subscription_id)
    
    if request.method == 'POST':
        subscription.user_id = request.POST.get('user')
        subscription.plan_id = request.POST.get('plan')
        subscription.start_date = request.POST.get('start_date')
        subscription.end_date = request.POST.get('end_date')
        subscription.active = request.POST.get('active') == 'on'
        subscription.save()
        messages.success(request, "Subscription updated successfully!")
        return redirect('admin_subscription_list')
    
    users = User.objects.all()
    plans = Plan.objects.all()
    return render(request, 'admin_panel/subscriptions/edit.html', {
        'subscription': subscription,
        'users': users,
        'plans': plans
    })

@user_passes_test(is_admin)
@require_POST
def subscription_delete(request, subscription_id):
    subscription = get_object_or_404(PlanSubscription, id=subscription_id)
    subscription.delete()
    messages.success(request, "Subscription deleted successfully!")
    return redirect('admin_subscription_list')

# Blog Post views
@user_passes_test(is_admin)
def blog_post_list(request):
    posts = BlogPost.objects.all().select_related('author')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(title__icontains=search_query) | posts.filter(content__icontains=search_query)
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/blog_posts/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def blog_post_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author_id = request.POST.get('author')
        content = request.POST.get('content')
        
        try:
            post = BlogPost.objects.create(
                title=title,
                author_id=author_id,
                content=content
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                post.image = request.FILES['image']
                post.save()
            
            messages.success(request, f"Blog post '{title}' created successfully!")
            return redirect('admin_blog_post_list')
        except Exception as e:
            messages.error(request, f"Error creating blog post: {str(e)}")
    
    users = User.objects.all()
    return render(request, 'admin_panel/blog_posts/create.html', {'users': users})

@user_passes_test(is_admin)
def blog_post_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    return render(request, 'admin_panel/blog_posts/detail.html', {'post': post})

@user_passes_test(is_admin)
def blog_post_edit(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    
    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.author_id = request.POST.get('author')
        post.content = request.POST.get('content')
        
        # Handle image upload
        if 'image' in request.FILES:
            post.image = request.FILES['image']
        
        post.save()
        messages.success(request, f"Blog post '{post.title}' updated successfully!")
        return redirect('admin_blog_post_list')
    
    users = User.objects.all()
    return render(request, 'admin_panel/blog_posts/edit.html', {'post': post, 'users': users})

@user_passes_test(is_admin)
@require_POST
def blog_post_delete(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    title = post.title
    post.delete()
    messages.success(request, f"Blog post '{title}' deleted successfully!")
    return redirect('admin_blog_post_list')

# Newsletter views
@user_passes_test(is_admin)
def newsletter_list(request):
    newsletters = Newsletter.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        newsletters = newsletters.filter(email__icontains=search_query)
    
    # Pagination
    paginator = Paginator(newsletters, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/newsletters/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def newsletter_create(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            Newsletter.objects.create(email=email)
            messages.success(request, f"Newsletter subscriber '{email}' created successfully!")
            return redirect('admin_newsletter_list')
        except Exception as e:
            messages.error(request, f"Error creating newsletter subscriber: {str(e)}")
    
    return render(request, 'admin_panel/newsletters/create.html')

@user_passes_test(is_admin)
def newsletter_detail(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    return render(request, 'admin_panel/newsletters/detail.html', {'newsletter': newsletter})

@user_passes_test(is_admin)
def newsletter_edit(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if request.method == 'POST':
        newsletter.email = request.POST.get('email')
        newsletter.save()
        messages.success(request, f"Newsletter subscriber '{newsletter.email}' updated successfully!")
        return redirect('admin_newsletter_list')
    
    return render(request, 'admin_panel/newsletters/edit.html', {'newsletter': newsletter})

@user_passes_test(is_admin)
@require_POST
def newsletter_delete(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    email = newsletter.email
    newsletter.delete()
    messages.success(request, f"Newsletter subscriber '{email}' deleted successfully!")
    return redirect('admin_newsletter_list')

# Contact Message views
@user_passes_test(is_admin)
def contact_message_list(request):
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        messages_list = messages_list.filter(name__icontains=search_query) | messages_list.filter(email__icontains=search_query) | messages_list.filter(message__icontains=search_query)
    
    # Pagination
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_panel/contact_messages/list.html', {'page_obj': page_obj, 'search_query': search_query})

@user_passes_test(is_admin)
def contact_message_detail(request, message_id):
    contact_message = get_object_or_404(ContactMessage, id=message_id)
    return render(request, 'admin_panel/contact_messages/detail.html', {'message': contact_message})

@user_passes_test(is_admin)
@require_POST
def contact_message_delete(request, message_id):
    contact_message = get_object_or_404(ContactMessage, id=message_id)
    contact_message.delete()
    messages.success(request, "Contact message deleted successfully!")
    return redirect('admin_contact_message_list')

# API endpoints for AJAX operations
@user_passes_test(is_admin)
def api_user_list(request):
    users = User.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query) | users.filter(email__icontains=search_query)
    
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.get_full_name(),
        'is_staff': user.is_staff
    } for user in users[:20]]  # Limit to 20 results
    
    return JsonResponse({'users': users_data})

@user_passes_test(is_admin)
def api_category_list(request):
    categories = Category.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    categories_data = [{
        'id': category.id,
        'name': category.name
    } for category in categories]
    
    return JsonResponse({'categories': categories_data})

@user_passes_test(is_admin)
def api_product_list(request):
    products = Product.objects.all().select_related('category')
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    products_data = [{
        'id': product.id,
        'name': product.name,
        'category': product.category.name,
        'price': float(product.price),
        'stock': product.stock
    } for product in products[:20]]  # Limit to 20 results
    
    return JsonResponse({'products': products_data})

@user_passes_test(is_admin)
def api_plan_list(request):
    plans = Plan.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        plans = plans.filter(name__icontains=search_query)
    
    plans_data = [{
        'id': plan.id,
        'name': plan.name,
        'price': float(plan.price)
    } for plan in plans]
    
    return JsonResponse({'plans': plans_data})

@user_passes_test(is_admin)
def api_team_member_list(request):
    members = TeamMember.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(name__icontains=search_query)
    
    members_data = [{
        'id': member.id,
        'name': member.name,
        'position': member.position
    } for member in members]
    
    return JsonResponse({'members': members_data})

@user_passes_test(is_admin)
def api_gym_class_list(request):
    classes = GymClass.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        classes = classes.filter(name__icontains=search_query)
    
    classes_data = [{
        'id': gym_class.id,
        'name': gym_class.name
    } for gym_class in classes]
    
    return JsonResponse({'classes': classes_data})

@user_passes_test(is_admin)
def api_order_list(request):
    orders = Order.objects.all().select_related('user')
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(user__username__icontains=search_query)
    
    orders_data = [{
        'id': order.id,
        'user': order.user.username,
        'total': float(order.total),
        'status': order.status,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for order in orders[:20]]  # Limit to 20 results
    
    return JsonResponse({'orders': orders_data})

@user_passes_test(is_admin)
def api_subscription_list(request):
    subscriptions = PlanSubscription.objects.all().select_related('user', 'plan')
    search_query = request.GET.get('search', '')
    if search_query:
        subscriptions = subscriptions.filter(user__username__icontains=search_query)
    
    subscriptions_data = [{
        'id': subscription.id,
        'user': subscription.user.username,
        'plan': subscription.plan.name,
        'start_date': subscription.start_date.strftime('%Y-%m-%d'),
        'end_date': subscription.end_date.strftime('%Y-%m-%d'),
        'active': subscription.active
    } for subscription in subscriptions[:20]]  # Limit to 20 results
    
    return JsonResponse({'subscriptions': subscriptions_data})

@user_passes_test(is_admin)
def api_blog_post_list(request):
    posts = BlogPost.objects.all().select_related('author')
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(title__icontains=search_query)
    
    posts_data = [{
        'id': post.id,
        'title': post.title,
        'author': post.author.username,
        'created_at': post.created_at.strftime('%Y-%m-%d')
    } for post in posts[:20]]  # Limit to 20 results
    
    return JsonResponse({'posts': posts_data})

# Report-related functions
@user_passes_test(is_admin)
def reports_dashboard(request):
    # Get counts for dashboard
    user_count = User.objects.count()
    product_count = Product.objects.count()
    order_count = Order.objects.count()
    subscription_count = PlanSubscription.objects.count()
    
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Default to last 30 days
    
    # Get filter parameters
    date_range = request.GET.get('date_range', '30')
    if date_range == '7':
        start_date = end_date - timedelta(days=7)
    elif date_range == '90':
        start_date = end_date - timedelta(days=90)
    elif date_range == '365':
        start_date = end_date - timedelta(days=365)
    
    # Sales data for chart
    sales_data = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values('created_at__date').annotate(
        total_sales=Sum('total')
    ).order_by('created_at__date')
    
    # Format data for charts
    dates = [item['created_at__date'].strftime('%Y-%m-%d') for item in sales_data]
    sales = [float(item['total_sales']) for item in sales_data]
    
    # Get top selling products
    top_products = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__created_at__date__lte=end_date
    ).values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(F('price') * F('quantity'))
    ).order_by('-total_quantity')[:5]
    
    # Get top subscribed plans
    top_plans = PlanSubscription.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values('plan__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'user_count': user_count,
        'product_count': product_count,
        'order_count': order_count,
        'subscription_count': subscription_count,
        'dates': json.dumps(dates),
        'sales': json.dumps(sales),
        'top_products': top_products,
        'top_plans': top_plans,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': date_range
    }
    
    return render(request, 'admin_panel/reports/dashboard.html', context)

@user_passes_test(is_admin)
def user_report(request):
    # Get all users
    users = User.objects.all().order_by('-date_joined')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        users = users.filter(date_joined__date__gte=start_date)
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        users = users.filter(date_joined__date__lte=end_date)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # User registration over time
    user_registrations = User.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date
    ).values('date_joined__date').annotate(
        count=Count('id')
    ).order_by('date_joined__date')
    
    # Format data for charts
    dates = [item['date_joined__date'].strftime('%Y-%m-%d') for item in user_registrations]
    counts = [item['count'] for item in user_registrations]
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'dates': json.dumps(dates),
        'counts': json.dumps(counts)
    }
    
    return render(request, 'admin_panel/reports/users.html', context)

@user_passes_test(is_admin)
def sales_report(request):
    # Get all orders
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        orders = orders.filter(created_at__date__gte=start_date)
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        orders = orders.filter(created_at__date__lte=end_date)
    
    # Calculate total revenue
    total_revenue = orders.aggregate(total=Sum('total'))['total'] or 0
    
    # Sales data for chart
    sales_data = orders.values('created_at__date').annotate(
        total_sales=Sum('total')
    ).order_by('created_at__date')
    
    # Format data for charts
    dates = [item['created_at__date'].strftime('%Y-%m-%d') for item in sales_data]
    sales = [float(item['total_sales']) for item in sales_data]
    
    # Get payment method distribution
    payment_methods = orders.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('-count')
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'dates': json.dumps(dates),
        'sales': json.dumps(sales),
        'payment_methods': payment_methods
    }
    
    return render(request, 'admin_panel/reports/sales.html', context)

@user_passes_test(is_admin)
def subscription_report(request):
    # Get all subscriptions
    subscriptions = PlanSubscription.objects.all().select_related('user', 'plan').order_by('-created_at')
    
    # Get filter parameters
    active_filter = request.GET.get('active', 'all')
    if active_filter == 'active':
        subscriptions = subscriptions.filter(active=True)
    elif active_filter == 'inactive':
        subscriptions = subscriptions.filter(active=False)
    
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        subscriptions = subscriptions.filter(created_at__date__gte=start_date)
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        subscriptions = subscriptions.filter(created_at__date__lte=end_date)
    
    # Calculate total revenue
    total_revenue = subscriptions.aggregate(total=Sum('plan__price'))['total'] or 0
    
    # Subscriptions by plan
    subscriptions_by_plan = subscriptions.values('plan__name').annotate(
        count=Count('id'),
        revenue=Sum('plan__price')
    ).order_by('-count')
    
    # Subscriptions over time
    subscriptions_over_time = subscriptions.values('created_at__date').annotate(
        count=Count('id')
    ).order_by('created_at__date')
    
    # Format data for charts
    dates = [item['created_at__date'].strftime('%Y-%m-%d') for item in subscriptions_over_time]
    counts = [item['count'] for item in subscriptions_over_time]
    
    # Pagination
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'active_filter': active_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'subscriptions_by_plan': subscriptions_by_plan,
        'dates': json.dumps(dates),
        'counts': json.dumps(counts)
    }
    
    return render(request, 'admin_panel/reports/subscriptions.html', context)

@user_passes_test(is_admin)
def booking_report(request):
    # Get all bookings
    bookings = ClassBooking.objects.all().select_related('user', 'class_schedule', 'class_schedule__gym_class').order_by('-booking_date')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        bookings = bookings.filter(booking_date__gte=start_date)
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        bookings = bookings.filter(booking_date__lte=end_date)
    
    # Bookings by class
    bookings_by_class = bookings.values('class_schedule__gym_class__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Bookings by day of week
    bookings_by_day = bookings.values('booking_date__week_day').annotate(
        count=Count('id')
    ).order_by('booking_date__week_day')
    
    # Map day numbers to day names
    day_map = {
        1: 'Sunday',
        2: 'Monday',
        3: 'Tuesday',
        4: 'Wednesday',
        5: 'Thursday',
        6: 'Friday',
        7: 'Saturday'
    }
    
    for item in bookings_by_day:
        item['day_name'] = day_map.get(item['booking_date__week_day'], 'Unknown')
    
    # Bookings over time
    bookings_over_time = bookings.values('booking_date').annotate(
        count=Count('id')
    ).order_by('booking_date')
    
    # Format data for charts
    dates = [item['booking_date'].strftime('%Y-%m-%d') for item in bookings_over_time]
    counts = [item['count'] for item in bookings_over_time]
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'bookings_by_class': bookings_by_class,
        'bookings_by_day': bookings_by_day,
        'dates': json.dumps(dates),
        'counts': json.dumps(counts)
    }
    
    return render(request, 'admin_panel/reports/bookings.html', context)

@user_passes_test(is_admin)
def export_report(request, report_type):
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    
    # Create response with appropriate headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'users':
        # Export user report
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Active'])
        
        users = User.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).order_by('-date_joined')
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.get_full_name(),
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                'Yes' if user.is_active else 'No'
            ])
    
    elif report_type == 'sales':
        # Export sales report
        writer.writerow(['Order ID', 'User', 'Total', 'Payment Method', 'Status', 'Date'])
        
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user').order_by('-created_at')
        
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username,
                order.total,
                order.payment_method,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif report_type == 'subscriptions':
        # Export subscriptions report
        writer.writerow(['ID', 'User', 'Plan', 'Price', 'Start Date', 'End Date', 'Active'])
        
        subscriptions = PlanSubscription.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user', 'plan').order_by('-created_at')
        
        for subscription in subscriptions:
            writer.writerow([
                subscription.id,
                subscription.user.username,
                subscription.plan.name,
                subscription.plan.price,
                subscription.start_date.strftime('%Y-%m-%d'),
                subscription.end_date.strftime('%Y-%m-%d'),
                'Yes' if subscription.active else 'No'
            ])
    
    elif report_type == 'bookings':
        # Export bookings report
        writer.writerow(['ID', 'User', 'Class', 'Date', 'Time', 'Status'])
        
        bookings = ClassBooking.objects.filter(
            booking_date__gte=start_date,
            booking_date__lte=end_date
        ).select_related('user', 'class_schedule', 'class_schedule__gym_class').order_by('-booking_date')
        
        for booking in bookings:
            writer.writerow([
                booking.id,
                booking.user.username,
                booking.class_schedule.gym_class.name,
                booking.booking_date.strftime('%Y-%m-%d'),
                booking.class_schedule.time,
                booking.status
            ])
    
    return response

@user_passes_test(is_admin)
def contact_message_reply(request, message_id):
    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        reply_text = request.POST.get('reply')
        
        if reply_text:
            # Send email reply
            try:
                send_mail(
                    f'Re: {message.subject}',
                    reply_text,
                    settings.DEFAULT_FROM_EMAIL,
                    [message.email],
                    fail_silently=False,
                )
                
                # Mark message as read
                message.is_read = True
                message.save()
                
                messages.success(request, f"Reply sent to {message.name} successfully!")
            except Exception as e:
                messages.error(request, f"Error sending reply: {str(e)}")
        else:
            messages.error(request, "Reply text cannot be empty.")
    
    return redirect('admin_contact_message_detail', message_id=message.id)

@user_passes_test(is_admin)
def subscription_add(request):
    if request.method == "POST":
        user_id = request.POST.get("user")
        plan_id = request.POST.get("plan")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        active = request.POST.get("active") == "on"

        try:
            PlanSubscription.objects.create(
                user_id=user_id,
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date,
                active=active,
            )
            messages.success(request, "Subscription added successfully!")
            return redirect("admin_subscription_list")
        except Exception as e:
            messages.error(request, f"Error adding subscription: {str(e)}")

    users = User.objects.all()
    plans = Plan.objects.all()
    return render(request, "admin_panel/subscriptions/add.html", {"users": users, "plans": plans})

@user_passes_test(is_admin)
def create_booking(request):
    users = User.objects.all()
    class_schedules = ClassSchedule.objects.select_related('gym_class').all()
    gym_classes = GymClass.objects.all()  # Fetch all gym classes

    if request.method == "POST":
        user_id = request.POST.get("user")
        schedule_id = request.POST.get("class_schedule")
        booking_date = request.POST.get("booking_date")
        status = request.POST.get("status")

        try:
            ClassBooking.objects.create(
                user_id=user_id,
                class_schedule_id=schedule_id,
                booking_date=booking_date,
                status=status,
            )
            messages.success(request, "Class booked successfully!")
            return redirect("admin_class_booking_list")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(
        request,
        "admin_panel/class_bookings/create.html",
        {
            "users": users,
            "class_schedules": class_schedules,
            "gym_classes": gym_classes,  # Pass gym classes to the template
        },
    )
'''
@user_passes_test(is_admin)
def export_user_report(request, report_type):
    # Get query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', 'all')
    export_format = request.GET.get('format', 'csv')  # Default to CSV, can be 'pdf'

    # Ensure fresh data by wrapping in a transaction block
    with transaction.atomic():
        if report_type == 'sales':
            # Sales report logic
            queryset = Order.objects.all().select_related('user')  # Optimize with select_related
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)

            if export_format == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []
                styles = getSampleStyleSheet()

                elements.append(Paragraph("Sales Report", styles['Title']))
                data = [['Order ID', 'Customer', 'Total', 'Payment Method', 'Status', 'Date']]
                for order in queryset:
                    data.append([
                        f"#{order.id}",
                        order.user.username if order.user else 'N/A',
                        f"₹{order.total:.2f}",
                        order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else order.payment_method,
                        order.get_status_display() if hasattr(order, 'get_status_display') else order.status,
                        order.created_at.strftime('%b %d, %Y %H:%M') if order.created_at else 'N/A'
                    ])

                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)

                doc.build(elements)
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
                return response

            else:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
                writer = csv.writer(response)
                writer.writerow(['Order ID', 'Customer', 'Total', 'Payment Method', 'Status', 'Date'])
                for order in queryset:
                    writer.writerow([
                        f"#{order.id}",
                        order.user.username if order.user else 'N/A',
                        f"₹{order.total:.2f}",
                        order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else order.payment_method,
                        order.get_status_display() if hasattr(order, 'get_status_display') else order.status,
                        order.created_at.strftime('%b %d, %Y %H:%M') if order.created_at else 'N/A'
                    ])
                return response

        elif report_type == 'users':
            # User report logic
            queryset = User.objects.all()
            if start_date:
                queryset = queryset.filter(date_joined__gte=start_date)
            if end_date:
                queryset = queryset.filter(date_joined__lte=end_date)
            if status_filter != 'all':
                queryset = queryset.filter(is_active=(status_filter == 'active'))

            if export_format == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []
                styles = getSampleStyleSheet()

                elements.append(Paragraph("User Report", styles['Title']))
                data = [['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Status']]
                for user in queryset:
                    data.append([
                        str(user.id),
                        user.username,
                        user.email,
                        user.get_full_name(),
                        user.date_joined.strftime('%b %d, %Y') if user.date_joined else 'N/A',
                        user.last_login.strftime('%b %d, %Y %H:%M') if user.last_login else 'Never',
                        'Active' if user.is_active else 'Inactive'
                    ])

                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)

                doc.build(elements)
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="user_report.pdf"'
                return response

            else:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="user_report.csv"'
                writer = csv.writer(response)
                writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Status'])
                for user in queryset:
                    writer.writerow([
                        user.id,
                        user.username,
                        user.email,
                        user.get_full_name(),
                        user.date_joined.strftime('%b %d, %Y') if user.date_joined else 'N/A',
                        user.last_login.strftime('%b %d, %Y %H:%M') if user.last_login else 'Never',
                        'Active' if user.is_active else 'Inactive'
                    ])
                return response

        else:
            return HttpResponse("Invalid report type", status=400)'''

@user_passes_test(is_admin)
def export_report(request, report_type):
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        # Default to 30 days ago if no start date provided
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    
    # Create response with appropriate headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'users':
        # Export user report
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Active'])
        
        # Use date_joined instead of date_joined__date to capture all users
        users = User.objects.all().order_by('-date_joined')
        if start_date:
            users = users.filter(date_joined__date__gte=start_date)
        if end_date:
            users = users.filter(date_joined__date__lte=end_date)
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.get_full_name(),
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                'Yes' if user.is_active else 'No'
            ])
    
    elif report_type == 'sales':
        # Export sales report
        writer.writerow(['Order ID', 'User', 'Total', 'Payment Method', 'Status', 'Date'])
        
        # Get all orders first, then apply date filtering
        orders = Order.objects.all().select_related('user').order_by('-created_at')
        if start_date:
            orders = orders.filter(created_at__date__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__date__lte=end_date)
        
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username if order.user else 'N/A',
                order.total,
                order.payment_method,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif report_type == 'subscriptions':
        # Export subscriptions report
        writer.writerow(['ID', 'User', 'Plan', 'Price', 'Start Date', 'End Date', 'Active'])
        
        # Get all subscriptions first, then apply date filtering
        subscriptions = PlanSubscription.objects.all().select_related('user', 'plan').order_by('-created_at')
        if start_date:
            subscriptions = subscriptions.filter(created_at__date__gte=start_date)
        if end_date:
            subscriptions = subscriptions.filter(created_at__date__lte=end_date)
        
        for subscription in subscriptions:
            writer.writerow([
                subscription.id,
                subscription.user.username,
                subscription.plan.name,
                subscription.plan.price,
                subscription.start_date.strftime('%Y-%m-%d'),
                subscription.end_date.strftime('%Y-%m-%d'),
                'Yes' if subscription.active else 'No'
            ])
    
    elif report_type == 'bookings':
        # Export bookings report
        writer.writerow(['ID', 'User', 'Class', 'Date', 'Time', 'Status'])
        
        # Get all bookings first, then apply date filtering
        bookings = ClassBooking.objects.all().select_related('user', 'class_schedule', 'class_schedule__gym_class').order_by('-booking_date')
        if start_date:
            bookings = bookings.filter(booking_date__gte=start_date)
        if end_date:
            bookings = bookings.filter(booking_date__lte=end_date)
        
        for booking in bookings:
            writer.writerow([
                booking.id,
                booking.user.username,
                booking.class_schedule.gym_class.name,
                booking.booking_date.strftime('%Y-%m-%d'),
                booking.class_schedule.time,
                booking.status
            ])
    
    return response

@user_passes_test(is_admin)
def export_user_report(request, report_type):
    # Get query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', 'all')
    export_format = request.GET.get('format', 'csv')  # Default to CSV, can be 'pdf'

    # Get current date for default end date
    current_date = timezone.now().date()
    
    # Ensure fresh data by wrapping in a transaction block
    with transaction.atomic():
        if report_type == 'sales':
            # Sales report logic - get all orders first
            queryset = Order.objects.all().select_related('user').order_by('-created_at')
            
            # Apply date filtering if provided
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(created_at__date__gte=start_date_obj)
                except ValueError:
                    # Handle invalid date format
                    pass
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(created_at__date__lte=end_date_obj)
                except ValueError:
                    # Handle invalid date format
                    pass
            
            # Apply status filtering if provided
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)

            if export_format == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []
                styles = getSampleStyleSheet()

                elements.append(Paragraph("Sales Report", styles['Title']))
                elements.append(Paragraph(f"Generated on: {current_date.strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Paragraph(f"Date Range: {start_date or 'All'} to {end_date or 'Present'}", styles['Normal']))
                
                data = [['Order ID', 'Customer', 'Total', 'Payment Method', 'Status', 'Date']]
                for order in queryset:
                    data.append([
                        f"#{order.id}",
                        order.user.username if order.user else 'N/A',
                        f"₹{float(order.total):.2f}",
                        order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else order.payment_method,
                        order.get_status_display() if hasattr(order, 'get_status_display') else order.status,
                        order.created_at.strftime('%b %d, %Y %H:%M') if order.created_at else 'N/A'
                    ])

                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)

                doc.build(elements)
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="sales_report_{current_date.strftime("%Y%m%d")}.pdf"'
                return response

            else:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="sales_report_{current_date.strftime("%Y%m%d")}.csv"'
                writer = csv.writer(response)
                writer.writerow(['Order ID', 'Customer', 'Total', 'Payment Method', 'Status', 'Date'])
                for order in queryset:
                    writer.writerow([
                        f"#{order.id}",
                        order.user.username if order.user else 'N/A',
                        f"₹{float(order.total):.2f}",
                        order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else order.payment_method,
                        order.get_status_display() if hasattr(order, 'get_status_display') else order.status,
                        order.created_at.strftime('%b %d, %Y %H:%M') if order.created_at else 'N/A'
                    ])
                return response

        elif report_type == 'users':
            # User report logic - get all users first
            queryset = User.objects.all().order_by('-date_joined')
            
            # Apply date filtering if provided
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(date_joined__date__gte=start_date_obj)
                except ValueError:
                    # Handle invalid date format
                    pass
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(date_joined__date__lte=end_date_obj)
                except ValueError:
                    # Handle invalid date format
                    pass
            
            # Apply status filtering if provided
            if status_filter != 'all':
                queryset = queryset.filter(is_active=(status_filter == 'active'))

            if export_format == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []
                styles = getSampleStyleSheet()

                elements.append(Paragraph("User Report", styles['Title']))
                elements.append(Paragraph(f"Generated on: {current_date.strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Paragraph(f"Date Range: {start_date or 'All'} to {end_date or 'Present'}", styles['Normal']))
                
                data = [['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Status']]
                for user in queryset:
                    data.append([
                        str(user.id),
                        user.username,
                        user.email,
                        user.get_full_name(),
                        user.date_joined.strftime('%b %d, %Y') if user.date_joined else 'N/A',
                        user.last_login.strftime('%b %d, %Y %H:%M') if user.last_login else 'Never',
                        'Active' if user.is_active else 'Inactive'
                    ])

                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)

                doc.build(elements)
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="user_report_{current_date.strftime("%Y%m%d")}.pdf"'
                return response

            else:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="user_report_{current_date.strftime("%Y%m%d")}.csv"'
                writer = csv.writer(response)
                writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Status'])
                for user in queryset:
                    writer.writerow([
                        user.id,
                        user.username,
                        user.email,
                        user.get_full_name(),
                        user.date_joined.strftime('%b %d, %Y') if user.date_joined else 'N/A',
                        user.last_login.strftime('%b %d, %Y %H:%M') if user.last_login else 'Never',
                        'Active' if user.is_active else 'Inactive'
                    ])
                return response

        else:
            return HttpResponse("Invalid report type", status=400)

 
def export_subscriptions_to_csv(subscriptions, filename="subscriptions_report.csv"):
    """Export subscriptions to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Email', 'Plan', 'Price', 'Start Date', 'End Date', 'Status', 'Created At'])
    
    for subscription in subscriptions:
        writer.writerow([
            subscription.id,
            subscription.user.username,
            subscription.user.email,
            subscription.plan.name,
            subscription.plan.price,
            subscription.start_date.strftime('%Y-%m-%d'),
            subscription.end_date.strftime('%Y-%m-%d'),
            'Active' if subscription.active else 'Inactive',
            subscription.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

def export_subscriptions_to_pdf(subscriptions, title="Subscriptions Report"):
    """Export subscriptions to PDF format"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title
    elements.append(Paragraph(title, styles['Title']))
    
    # Add report date
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))  # Add some space
    
    # Table data
    data = [['ID', 'User', 'Plan', 'Start Date', 'End Date', 'Status', 'Price']]
    
    for subscription in subscriptions:
        status = 'Active' if subscription.active else 'Inactive'
        data.append([
            str(subscription.id),
            subscription.user.username,
            subscription.plan.name,
            subscription.start_date.strftime('%Y-%m-%d'),
            subscription.end_date.strftime('%Y-%m-%d'),
            status,
            f"₹{subscription.plan.price}"
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="subscriptions_report_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response

def export_subscription_report(request):
    """Export subscription report in CSV or PDF format"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status', 'all')
    plan_id = request.GET.get('plan', 'all')
    export_format = request.GET.get('format', 'csv')
    
    # Base queryset
    subscriptions = PlanSubscription.objects.all().select_related('user', 'plan')
    
    # Apply filters
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        subscriptions = subscriptions.filter(start_date__gte=start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        subscriptions = subscriptions.filter(start_date__lte=end_date)
    
    if status == 'active':
        subscriptions = subscriptions.filter(active=True)
    elif status == 'expired':
        subscriptions = subscriptions.filter(active=False, end_date__lt=timezone.now().date())
    elif status == 'cancelled':
        subscriptions = subscriptions.filter(active=False, end_date__gt=timezone.now().date())
    
    if plan_id != 'all':
        subscriptions = subscriptions.filter(plan_id=plan_id)
    
    # Generate report based on format
    if export_format == 'pdf':
        return export_subscriptions_to_pdf(subscriptions)
    else:
        return export_subscriptions_to_csv(subscriptions)

@user_passes_test(is_admin)
def export_report(request, report_type):
    """Generic export function for different report types"""
    if report_type == 'subscriptions':
        return export_subscription_report(request)
    elif report_type == 'users':
        return export_user_report(request)
    elif report_type == 'sales':
        return export_sales_report(request)
    elif report_type == 'bookings':
        return export_bookings_report(request)
    else:
        return HttpResponse("Invalid report type", status=400)



# Update the admin_dashboard view to properly fetch subscription data
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get counts for dashboard
    user_count = User.objects.count()
    product_count = Product.objects.count()
    order_count = Order.objects.count()
    subscription_count = PlanSubscription.objects.count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Recent users
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    # Sales data for chart
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    sales_data = Order.objects.filter(
        created_at__date__gte=last_30_days
    ).values('created_at__date').annotate(
        total_sales=Sum('total')
    ).order_by('created_at__date')
    
    sales_chart_data = {
        'labels': [item['created_at__date'].strftime('%Y-%m-%d') for item in sales_data],
        'data': [float(item['total_sales']) for item in sales_data]
    }
    
    # Add subscription data for dashboard
    active_subscriptions = PlanSubscription.objects.filter(active=True).count()
    recent_subscriptions = PlanSubscription.objects.select_related('user', 'plan').order_by('-created_at')[:5]
    
    # Subscription revenue data
    subscription_revenue = PlanSubscription.objects.filter(
        created_at__date__gte=last_30_days
    ).aggregate(total=Sum('plan__price'))['total'] or 0
    
    context = {
        'user_count': user_count,
        'product_count': product_count,
        'order_count': order_count,
        'subscription_count': subscription_count,
        'active_subscriptions': active_subscriptions,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'recent_subscriptions': recent_subscriptions,
        'subscription_revenue': subscription_revenue,
        'sales_chart_data': json.dumps(sales_chart_data)
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

# Update the subscription_list view to properly fetch and filter subscription data
@user_passes_test(is_admin)
def subscription_list(request):
    # Get all subscriptions with related user and plan data
    subscriptions = PlanSubscription.objects.all().select_related('user', 'plan')
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', 'all')
    
    # Apply date filters if provided
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(start_date__gte=start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(end_date__lte=end_date)
        except ValueError:
            pass
    
    # Apply status filter if provided
    if status_filter == 'active':
        subscriptions = subscriptions.filter(active=True)
    elif status_filter == 'inactive':
        subscriptions = subscriptions.filter(active=False)
    elif status_filter == 'trialing':
        subscriptions = subscriptions.filter(status='trialing')
    elif status_filter == 'canceled':
        subscriptions = subscriptions.filter(status='canceled')
    
    # Calculate plan statistics
    plan_stats = PlanSubscription.objects.values('plan__name').annotate(
        total=Count('id'),
        active=Count('id', filter=Q(active=True)),
        revenue=Sum('plan__price'),
        avg_duration=Avg(ExpressionWrapper(
            F('end_date') - F('start_date'),
            output_field=fields.DurationField()
        ))
    ).order_by('plan__name')
    
    # Convert timedelta to days for avg_duration
    for stat in plan_stats:
        if stat['avg_duration']:
            stat['avg_duration'] = stat['avg_duration'].days
    
    context = {
        'subscriptions': subscriptions,
        'status_filter': status_filter,
        'plan_stats': plan_stats,
        'start_date': start_date if isinstance(start_date, datetime) else None,
        'end_date': end_date if isinstance(end_date, datetime) else None,
    }
    
    return render(request, 'admin_panel/subscriptions/list.html', context)

# Update the subscription_detail view to include more comprehensive data
@user_passes_test(is_admin)
def subscription_detail(request, subscription_id):
    subscription = get_object_or_404(PlanSubscription, id=subscription_id)
    
    # Get plan features
    plan_features = PlanFeature.objects.filter(plan=subscription.plan)
    
    # Get user's subscription history
    user_subscriptions = PlanSubscription.objects.filter(
        user=subscription.user
    ).select_related('plan').order_by('-start_date')
    
    # Calculate subscription duration in days
    if subscription.start_date and subscription.end_date:
        duration_days = (subscription.end_date - subscription.start_date).days
    else:
        duration_days = 0
    
    # Add duration_days to subscription object
    subscription.duration_days = duration_days
    
    # Get user activity (placeholder - implement based on your model)
    user_activities = []  # Replace with actual user activity data if available
    
    context = {
        'subscription': subscription,
        'plan_features': plan_features,
        'user_subscriptions': user_subscriptions,
        'user_activities': user_activities,
    }
    
    return render(request, 'admin_panel/subscriptions/detail.html', context)

# Update the export_report function to properly handle subscription data
@user_passes_test(is_admin)
def export_report(request, report_type):
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    export_format = request.GET.get('format', 'csv')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        try:
            end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if report_type == 'subscriptions':
        # Get status filter
        status_filter = request.GET.get('status', 'all')
        
        # Get all subscriptions with related user and plan data
        subscriptions = PlanSubscription.objects.all().select_related('user', 'plan')
        
        # Apply date filters
        subscriptions = subscriptions.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Apply status filter if provided
        if status_filter == 'active':
            subscriptions = subscriptions.filter(active=True)
        elif status_filter == 'inactive':
            subscriptions = subscriptions.filter(active=False)
        elif status_filter == 'trialing':
            subscriptions = subscriptions.filter(status='trialing')
        elif status_filter == 'canceled':
            subscriptions = subscriptions.filter(status='canceled')
        
        if export_format == 'pdf':
            return export_subscriptions_to_pdf(subscriptions)
        else:
            return export_subscriptions_to_csv(subscriptions)
    
    # Handle other report types...
    # (Keep your existing code for other report types)
    
    # Create response with appropriate headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'users':
        # Export user report
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Active'])
        
        users = User.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).order_by('-date_joined')
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.get_full_name(),
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                'Yes' if user.is_active else 'No'
            ])
    
    elif report_type == 'sales':
        # Export sales report
        writer.writerow(['Order ID', 'User', 'Total', 'Payment Method', 'Status', 'Date'])
        
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user').order_by('-created_at')
        
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username,
                order.total,
                order.payment_method,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif report_type == 'subscriptions':
        # Export subscriptions report
        writer.writerow(['ID', 'User', 'Email', 'Plan', 'Price', 'Start Date', 'End Date', 'Status', 'Created At'])
        
        subscriptions = PlanSubscription.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user', 'plan').order_by('-created_at')
        
        for subscription in subscriptions:
            writer.writerow([
                subscription.id,
                subscription.user.username,
                subscription.user.email,
                subscription.plan.name,
                subscription.plan.price,
                subscription.start_date.strftime('%Y-%m-%d'),
                subscription.end_date.strftime('%Y-%m-%d'),
                'Active' if subscription.active else 'Inactive',
                subscription.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif report_type == 'bookings':
        # Export bookings report
        writer.writerow(['ID', 'User', 'Class', 'Date', 'Time', 'Status'])
        
        bookings = ClassBooking.objects.filter(
            booking_date__gte=start_date,
            booking_date__lte=end_date
        ).select_related('user', 'class_schedule', 'class_schedule__gym_class').order_by('-booking_date')
        
        for booking in bookings:
            writer.writerow([
                booking.id,
                booking.user.username,
                booking.class_schedule.gym_class.name,
                booking.booking_date.strftime('%Y-%m-%d'),
                booking.class_schedule.time,
                booking.status
            ])
    
    return response

#hyy

def export_subscriptions_to_csv(subscriptions, filename="subscriptions_report.csv"):
    """Export subscriptions to CSV format with comprehensive data"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'User', 'Email', 'Plan', 'Price', 'Start Date', 'End Date', 
        'Status', 'Created At', 'Duration (Days)', 'Payment Method'
    ])
    
    for subscription in subscriptions:
        # Calculate duration in days
        if subscription.start_date and subscription.end_date:
            duration = (subscription.end_date - subscription.start_date).days
        else:
            duration = 0
            
        # Determine status text
        if subscription.active:
            status = 'Active'
        elif subscription.end_date < timezone.now().date():
            status = 'Expired'
        else:
            status = 'Inactive'
            
        writer.writerow([
            subscription.id,
            subscription.user.username,
            subscription.user.email,
            subscription.plan.name,
            float(subscription.plan.price),
            subscription.start_date.strftime('%Y-%m-%d'),
            subscription.end_date.strftime('%Y-%m-%d'),
            status,
            subscription.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            duration,
            getattr(subscription, 'payment_method', 'N/A')
        ])
    
    return response

def export_subscriptions_to_pdf(subscriptions, title="Subscriptions Report"):
    """Export subscriptions to PDF format with improved formatting"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title
    elements.append(Paragraph(title, styles['Title']))
    
    # Add report date
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))  # Add some space
    
    # Add summary statistics
    active_count = sum(1 for s in subscriptions if s.active)
    inactive_count = len(subscriptions) - active_count
    
    elements.append(Paragraph(f"Total Subscriptions: {len(subscriptions)}", styles['Normal']))
    elements.append(Paragraph(f"Active Subscriptions: {active_count}", styles['Normal']))
    elements.append(Paragraph(f"Inactive Subscriptions: {inactive_count}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))  # Add some space
    
    # Table data
    data = [['ID', 'User', 'Plan', 'Start Date', 'End Date', 'Status', 'Price']]
    
    for subscription in subscriptions:
        # Determine status text
        if subscription.active:
            status = 'Active'
        elif subscription.end_date < timezone.now().date():
            status = 'Expired'
        else:
            status = 'Inactive'
            
        data.append([
            str(subscription.id),
            subscription.user.username,
            subscription.plan.name,
            subscription.start_date.strftime('%Y-%m-%d'),
            subscription.end_date.strftime('%Y-%m-%d'),
            status,
            f"₹{float(subscription.plan.price)}"
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="subscriptions_report_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response

@user_passes_test(is_admin)
def export_report(request, report_type):
    """Improved export function that properly handles all report types"""
    # Get date range for filtering
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    export_format = request.GET.get('format', 'csv')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    if end_date_param:
        try:
            end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if report_type == 'subscriptions' or report_type == 'membership':
        # Get status filter
        status_filter = request.GET.get('status', 'all')
        plan_filter = request.GET.get('plan', 'all')
        
        # Get all subscriptions with related user and plan data
        subscriptions = PlanSubscription.objects.all().select_related('user', 'plan')
        
        # Apply date filters
        subscriptions = subscriptions.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Apply status filter if provided
        if status_filter == 'active':
            subscriptions = subscriptions.filter(active=True)
        elif status_filter == 'inactive':
            subscriptions = subscriptions.filter(active=False)
        
        # Apply plan filter if provided
        if plan_filter != 'all' and plan_filter.isdigit():
            subscriptions = subscriptions.filter(plan_id=int(plan_filter))
        
        if export_format == 'pdf':
            return export_subscriptions_to_pdf(subscriptions)
        else:
            return export_subscriptions_to_csv(subscriptions)
    
    elif report_type == 'users':
        # Export user report
        users = User.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).order_by('-date_joined')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_report_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Date Joined', 'Last Login', 'Active'])
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.get_full_name(),
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                'Yes' if user.is_active else 'No'
            ])
        
        return response
    
    elif report_type == 'sales':
        # Export sales report
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user').order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'User', 'Total', 'Payment Method', 'Status', 'Date'])
        
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username if order.user else 'N/A',
                float(order.total),
                order.payment_method,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    elif report_type == 'bookings':
        # Export bookings report
        bookings = ClassBooking.objects.filter(
            booking_date__gte=start_date,
            booking_date__lte=end_date
        ).select_related('user', 'class_schedule', 'class_schedule__gym_class').order_by('-booking_date')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bookings_report_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Class', 'Date', 'Time', 'Status'])
        
        for booking in bookings:
            writer.writerow([
                booking.id,
                booking.user.username,
                booking.class_schedule.gym_class.name,
                booking.booking_date.strftime('%Y-%m-%d'),
                booking.class_schedule.time,
                booking.status
            ])
        
        return response
    
    # Default case - return empty response
    return HttpResponse("Invalid report type", status=400)
@user_passes_test(is_admin)
def subscription_report(request):
    """
    View for displaying subscription reports with comprehensive data and filtering options
    """
    # Get all subscriptions with related user and plan data
    subscriptions = PlanSubscription.objects.all().select_related('user', 'plan').order_by('-created_at')
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', 'all')
    plan_filter = request.GET.get('plan', 'all')
    
    # Apply date filters if provided
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(created_at__date__gte=start_date_obj)
        except ValueError:
            start_date_obj = timezone.now().date() - timedelta(days=30)
    else:
        start_date_obj = timezone.now().date() - timedelta(days=30)
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(created_at__date__lte=end_date_obj)
        except ValueError:
            end_date_obj = timezone.now().date()
    else:
        end_date_obj = timezone.now().date()
    
    # Apply status filter if provided
    if status_filter == 'active':
        subscriptions = subscriptions.filter(active=True)
    elif status_filter == 'inactive':
        subscriptions = subscriptions.filter(active=False)
    
    # Apply plan filter if provided
    if plan_filter != 'all' and plan_filter.isdigit():
        subscriptions = subscriptions.filter(plan_id=int(plan_filter))
    
    # Calculate subscription statistics
    total_subscriptions = subscriptions.count()
    active_subscriptions = subscriptions.filter(active=True).count()
    expired_subscriptions = subscriptions.filter(
        active=False, 
        end_date__lt=timezone.now().date()
    ).count()
    expiring_soon = subscriptions.filter(
        active=True,
        end_date__lte=timezone.now().date() + timedelta(days=30),
        end_date__gte=timezone.now().date()
    ).count()
    
    # Get subscription trend data (subscriptions over time)
    subscription_trend = subscriptions.values('created_at__date').annotate(
        count=Count('id')
    ).order_by('created_at__date')
    
    # Format data for charts
    dates = [item['created_at__date'].strftime('%Y-%m-%d') for item in subscription_trend]
    subscription_counts = [item['count'] for item in subscription_trend]
    
    # Get plan distribution data
    plan_distribution = subscriptions.values('plan__name', 'plan_id').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Prepare data for plan distribution chart
    plan_names = [item['plan__name'] for item in plan_distribution]
    plan_counts = [item['count'] for item in plan_distribution]
    
    # Generate colors for plan chart
    plan_colors = [
        'rgba(78, 115, 223, 0.8)',
        'rgba(28, 200, 138, 0.8)',
        'rgba(54, 185, 204, 0.8)',
        'rgba(246, 194, 62, 0.8)',
        'rgba(231, 74, 59, 0.8)',
        'rgba(133, 135, 150, 0.8)',
    ]
    
    # Ensure we have enough colors for all plans
    while len(plan_colors) < len(plan_names):
        plan_colors.extend(plan_colors)
    
    # Trim to match the number of plans
    plan_colors = plan_colors[:len(plan_names)]
    
    # Create hover colors (slightly darker)
    plan_hover_colors = [color.replace('0.8', '1.0') for color in plan_colors]
    
    # Get all plans for filter dropdown
    all_plans = Plan.objects.all()
    
    # Create plan objects for legend
    plans = []
    for i, plan in enumerate(plan_distribution):
        if i < len(plan_colors):
            plans.append({
                'name': plan['plan__name'],
                'color': plan_colors[i].replace('rgba', 'rgb').replace(', 0.8)', ')')
            })
    
    # Pagination
    paginator = Paginator(subscriptions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'subscriptions': page_obj,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'expiring_soon': expiring_soon,
        'start_date': start_date_obj,
        'end_date': end_date_obj,
        'status_filter': status_filter,
        'plan_filter': plan_filter,
        'all_plans': all_plans,
        'dates': json.dumps(dates),
        'subscription_counts': json.dumps(subscription_counts),
        'plan_names': json.dumps(plan_names),
        'plan_counts': json.dumps(plan_counts),
        'plan_colors': json.dumps(plan_colors),
        'plan_hover_colors': json.dumps(plan_hover_colors),
        'plans': plans
    }
    
    return render(request, 'admin_panel/reports/subscriptions.html', context)
