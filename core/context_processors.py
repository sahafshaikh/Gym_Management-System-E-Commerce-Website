def cart_processor(request):
    """
    Context processor to add cart information to all templates
    """
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            cart_count = sum(item.quantity for item in cart.items.all())
        except:
            pass
    
    return {'cart_count': cart_count}

