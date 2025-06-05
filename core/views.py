from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg
import json
from .models import (
    Product, Category, Plan, PlanFeature, TeamMember, GymClass, 
    ClassSchedule, ClassBooking, Workout, Cart, CartItem, Order, 
    OrderItem, PlanSubscription, BlogPost, Newsletter, ContactMessage
)
from .forms import WorkoutForm, ClassBookingForm, ContactForm, NewsletterForm

def home(request):
    featured_classes = GymClass.objects.all()[:3]
    featured_products = Product.objects.all().order_by('-rating')[:3]
    team_members = TeamMember.objects.all()
    plans = Plan.objects.all()
    blog_posts = BlogPost.objects.all().order_by('-created_at')[:3]
    
    context = {
        'featured_classes': featured_classes,
        'featured_products': featured_products,
        'team_members': team_members,
        'plans': plans,
        'blog_posts': blog_posts,
    }
    return render(request, 'core/index.html', context)

def about(request):
    team_members = TeamMember.objects.all()
    return render(request, 'core/about.html', {'team_members': team_members})

def classes(request):
    all_classes = GymClass.objects.all()
    return render(request, 'core/classes.html', {'classes': all_classes})

def plans_view(request):
    all_plans = Plan.objects.all()
    for plan in all_plans:
        plan.feature_list = plan.features.all()
    return render(request, 'core/plans.html', {'plans': all_plans})

def team(request):
    all_members = TeamMember.objects.all()
    return render(request, 'core/team.html', {'team_members': all_members})

def timetable(request):
    schedules = ClassSchedule.objects.all().select_related('gym_class')
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = ['06:00 AM', '09:00 AM', '06:00 PM']
    
    timetable_data = {}
    for day in days:
        timetable_data[day] = {}
        for time in times:
            # Use filter() instead of get() to avoid MultipleObjectsReturned
            schedule = schedules.filter(day=day, time=time).first()
            if schedule:
                timetable_data[day][time] = schedule.gym_class.name
            else:
                timetable_data[day][time] = "No Class"
    
    return render(request, 'core/timetable.html', {
        'timetable': timetable_data,
        'days': days,
        'times': times
    })

def blog(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'core/blog.html', {'posts': posts})

def blog_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    return render(request, 'core/blog_detail.html', {'post': post})

def store(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    selected_category = request.GET.get('category', 'All')
    
    if selected_category != 'All':
        products = products.filter(category__name=selected_category)
    
    return render(request, 'core/store.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:2]
    return render(request, 'core/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect('store')
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.error(request, "No more stock available for this product.")
            return redirect('store')
    
    product.stock -= 1
    product.save()
    
    messages.success(request, f"{product.name} added to cart!")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product = cart_item.product
    product.stock += cart_item.quantity
    product.save()
    cart_item.delete()
    
    messages.success(request, f"{product.name} removed from cart.")
    return redirect('cart')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product = cart_item.product
    
    try:
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity <= 0:
            return remove_from_cart(request, item_id)
        
        stock_change = cart_item.quantity - new_quantity
        if stock_change < 0 and abs(stock_change) > product.stock:
            messages.error(request, f"Only {product.stock} more units available for {product.name}.")
            new_quantity = cart_item.quantity + product.stock
        
        product.stock += stock_change
        product.save()
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        messages.success(request, f"{product.name} quantity updated.")
    except ValueError:
        messages.error(request, "Invalid quantity.")
    
    return redirect('cart')

@login_required
def cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
    except Cart.DoesNotExist:
        cart_items = []
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method not in ['card', 'upi']:
            messages.error(request, "Invalid payment method.")
            return redirect('checkout')
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total=total,
            payment_method=payment_method,
            status='completed'  # In a real app, this would be 'pending' until payment confirmation
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, "Order placed successfully!")
        return redirect('order_confirmation', order_id=order.id)
    
    return render(request, 'core/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_confirmation.html', {'order': order})

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': user_orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})

@login_required
def subscribe_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method not in ['card', 'upi']:
            messages.error(request, "Invalid payment method.")
            return redirect('plans')
        
        # Create subscription (1 month)
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30)
        
        subscription = PlanSubscription.objects.create(
            user=request.user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            active=True
        )
        
        # Create order for the plan
        order = Order.objects.create(
            user=request.user,
            total=plan.price,
            payment_method=payment_method,
            status='completed'  # In a real app, this would be 'pending' until payment confirmation
        )
        
        messages.success(request, f"You have successfully subscribed to the {plan.name} plan!")
        return redirect('subscription_confirmation', subscription_id=subscription.id)
    
    return render(request, 'core/subscribe_plan.html', {'plan': plan})

@login_required
def subscription_confirmation(request, subscription_id):
    subscription = get_object_or_404(PlanSubscription, id=subscription_id, user=request.user)
    return render(request, 'core/subscription_confirmation.html', {'subscription': subscription})

@login_required
def subscriptions(request):
    user_subscriptions = PlanSubscription.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'core/subscriptions.html', {'subscriptions': user_subscriptions})

@login_required
def tracker(request):
    user_workouts = Workout.objects.filter(user=request.user).order_by('-date')
    
    if request.method == 'POST':
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()
            messages.success(request, "Workout added successfully!")
            return redirect('tracker')
    else:
        form = WorkoutForm()
    
    return render(request, 'core/tracker.html', {
        'workouts': user_workouts,
        'form': form
    })

@login_required
def delete_workout(request, workout_id):
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    workout.delete()
    messages.success(request, "Workout deleted successfully!")
    return redirect('tracker')

@login_required
def booking(request):
    user_bookings = ClassBooking.objects.filter(user=request.user, status='Booked').order_by('booking_date')
    
    if request.method == 'POST':
        form = ClassBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            messages.success(request, "Class booked successfully!")
            return redirect('booking')
    else:
        form = ClassBookingForm()
    
    return render(request, 'core/booking.html', {
        'bookings': user_bookings,
        'form': form
    })

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(ClassBooking, id=booking_id, user=request.user)
    booking.status = 'Cancelled'
    booking.save()
    messages.success(request, "Booking cancelled successfully!")
    return redirect('booking')

@login_required
def booking_history(request):
    all_bookings = ClassBooking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'core/booking_history.html', {'bookings': all_bookings})

def faq(request):
    return render(request, 'core/faq.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent!")
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})

@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'Subscribed successfully!'})
    return JsonResponse({'success': False, 'errors': form.errors})

# API endpoints for AJAX requests
@login_required
def api_get_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
        items = []
        for item in cart_items:
            items.append({
                'id': item.id,
                'name': item.product.name,
                'price': float(item.product.price),
                'quantity': item.quantity,
                'total': float(item.product.price * item.quantity)
            })
        return JsonResponse({
            'success': True,
            'items': items,
            'total': float(sum(item.product.price * item.quantity for item in cart_items))
        })
    except Cart.DoesNotExist:
        return JsonResponse({'success': True, 'items': [], 'total': 0})

@login_required
def api_add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock <= 0:
                return JsonResponse({'success': False, 'message': 'Out of stock'})
            
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
            
            if not item_created:
                if cart_item.quantity < product.stock:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    return JsonResponse({'success': False, 'message': 'No more stock available'})
            
            product.stock -= 1
            product.save()
            
            return JsonResponse({'success': True, 'message': f"{product.name} added to cart!"})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def bookclass(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        booking_date = request.POST.get('booking_date')
        payment_method = request.POST.get('payment_method')
        special_requests = request.POST.get('special_requests')
        
        fitness_class = get_object_or_404(FitnessClass, id=class_id)
        
        # Check if user already has a booking for this class on this date
        existing_booking = ClassBooking.objects.filter(
            user=request.user,
            fitness_class=fitness_class,
            booking_date=booking_date
        ).exists()
        
        if existing_booking:
            messages.warning(request, 'You already have a booking for this class on this date!')
            return redirect('booking')
        
        # Create booking
        booking = ClassBooking.objects.create(
            user=request.user,
            fitness_class=fitness_class,
            booking_date=booking_date,
            payment_method=payment_method,
            special_requests=special_requests,
            status='confirmed'
        )
        
        messages.success(request, f'Your booking for {fitness_class.name} has been confirmed!')
        return redirect('booking')
    
    return redirect('booking')

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(ClassBooking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Your booking has been cancelled successfully!')
    
    return redirect('booking')
