from django.shortcuts import render, redirect, get_object_or_404
from .models import FoodItem, Cart, UserProfile, Order, Category,Transaction, TransactionItem, AddOn
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
import json
import os
from django.http import JsonResponse, HttpResponse
from django import template
import uuid
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.urls import reverse
import logging
import razorpay
import qrcode
import io
import socket



from io import BytesIO
register = template.Library()

logger = logging.getLogger(__name__)

@register.filter
def multiply(value, arg):
    return value * arg

# Saving the data from excel into the json file
def save_menu_to_json():
    try:
        food_items = FoodItem.objects.all()
        
        # Get or create categories first
        categories = {}
        for item in food_items:
            category_name = item.category
            if category_name not in categories:
                category, created = Category.objects.get_or_create(name=category_name)
                categories[category_name] = category
        
        menu_data = []
        for item in food_items:
            # Get the Category instance
            category = categories.get(item.category)
            if not category:
                continue
                
            menu_data.append({
                'name': item.name,
                'description': item.description,
                'price': float(item.price),
                'category_id': category.id,  # Store category ID instead of name
                'is_vegetarian': item.is_vegetarian,
                'stock_quantity': item.stock_quantity
            })
        
        json_file_path = os.path.join(settings.BASE_DIR, 'menu_data.json')
        
        os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
        
        with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(menu_data, jsonfile, indent=4, ensure_ascii=False)
        
        return {'success': True, 'data': menu_data}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Add this function to handle importing from JSON
def import_menu_from_json():
    try:
        json_file_path = os.path.join(settings.BASE_DIR, 'menu_data.json')
        with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
            menu_data = json.load(jsonfile)
        
        for item_data in menu_data:
            # Get or create the category
            category_name = item_data['category']
            category, _ = Category.objects.get_or_create(name=category_name)
            
            # Create or update the food item
            FoodItem.objects.update_or_create(
                name=item_data['name'],
                defaults={
                    'description': item_data.get('description', ''),
                    'price': item_data['price'],
                    'category': category,
                    'is_vegetarian': item_data.get('is_vegetarian', False),
                    'stock_quantity': item_data.get('stock_quantity', 0)
                }
            )
        
        return {'success': True, 'message': 'Menu imported successfully'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Displaying menu items from the above stored data in json file
def menuitems(request):
    # Get all food items from the database
    menu_items = FoodItem.objects.all().order_by('category')
    
    # Get cart count for the current session
    cart_id = get_or_create_cart_id(request)
    cart_count = Cart.objects.filter(cart_id=cart_id).count()
    
    # For debugging
    print(f"Number of menu items found: {menu_items.count()}")
    for item in menu_items:
        print(f"Item: {item.name}, Price: {item.price}, Category: {item.category}")
    
    context = {
        'menu_items': menu_items,
        'cart_count': cart_count
    }
    return render(request, 'menu.html', context)


def is_restaurant_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_restaurant_admin, login_url='/admin/login/')
def admin_login(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login as administrator first.')
        return redirect('/admin/login/')
    return render(request, 'admin.html')

def get_or_create_cart_id(request):
    if 'cart_id' not in request.session:
        request.session['cart_id'] = str(uuid.uuid4())
    return request.session['cart_id']

@login_required
def add_to_cart(request, item_id):
    if request.method == 'POST':
        try:
            # Get the food item
            food_item = get_object_or_404(FoodItem, id=item_id)
            
            # Parse the request data with error handling
            try:
                data = json.loads(request.body.decode('utf-8'))  # Ensure proper decoding
                quantity = int(data.get('quantity', 1))  # Convert to int for safety
                selected_addons = data.get('addons', [])  # Expect list of addon objects or IDs
                logger.debug(f"Received data for item {item_id}: quantity={quantity}, addons={selected_addons}, raw body={request.body}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in add_to_cart for item {item_id}: {str(e)} - Raw body: {request.body}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                }, status=400)
            except ValueError as e:
                logger.error(f"Invalid quantity value for item {item_id}: {str(e)} - Data: {data}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid quantity value'
                }, status=400)

            # Get or initialize cart
            cart = request.session.get('cart', {})
            
            # Use item_id as the key and store addons and quantity
            cart_key = str(item_id)
            if cart_key not in cart:
                cart[cart_key] = {
                    'quantity': 0,
                    'addons': [],
                    'item': food_item.name,
                    'price': float(food_item.price),
                    'image': food_item.image.url if food_item.image else ''
                }
            
            # Increment quantity
            cart[cart_key]['quantity'] += quantity
            
            # Update add-ons with validation
            if selected_addons:
                valid_addons = []
                for addon in selected_addons:
                    addon_id = addon.get('id')  # Get ID from addon object
                    if addon_id:
                        try:
                            addon_obj = AddOn.objects.get(id=addon_id, food_item_id=item_id)
                            valid_addons.append({
                                'id': addon_obj.id,
                                'name': addon_obj.name,
                                'price': float(addon_obj.price)
                            })
                            logger.debug(f"Validated addon for item {item_id}: {addon_obj.name} (ID: {addon_id})")
                        except AddOn.DoesNotExist:
                            logger.warning(f"Add-on with ID {addon_id} not found for item {item_id}")
                    else:
                        logger.warning(f"Invalid addon data for item {item_id}, missing ID: {addon}")
                if valid_addons:
                    cart[cart_key]['addons'] = valid_addons
                else:
                    logger.warning(f"No valid addons found for item {item_id} after validation")
            
            # Save cart to session
            request.session['cart'] = cart
            request.session.modified = True
            
            # Calculate cart count
            cart_count = sum(item['quantity'] for item in cart.values() if isinstance(item, dict))
            
            return JsonResponse({
                'success': True,
                'message': f"{food_item.name} added to cart",
                'cart_count': cart_count,
                'cart': cart  # Return updated cart for client sync
            })
            
        except Exception as e:
            logger.error(f"Error adding item {item_id} to cart: {str(e)} - Raw body: {request.body}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)


@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    
    # If cart is empty or in old format, initialize it
    if not cart or any(isinstance(v, int) for v in cart.values()):
        cart = {}
        request.session['cart'] = cart
        request.session.modified = True
    
    cart_items = []
    total_price = 0
    
    for cart_key, cart_data in cart.items():
        try:
            if not isinstance(cart_data, dict) or 'quantity' not in cart_data:
                continue
            
            item_id = int(cart_key)
            food_item = get_object_or_404(FoodItem, id=item_id)
            quantity = cart_data.get('quantity', 0)
            selected_addons = cart_data.get('addons', [])
            
            # Calculate item price
            item_price = float(food_item.price)
            addon_objects = []
            addon_total = 0
            
            if selected_addons:
                addon_objects = []
                for addon_data in selected_addons:
                    try:
                        addon_obj = AddOn.objects.get(id=addon_data['id'], food_item_id=item_id)
                        addon_objects.append({
                            'name': addon_obj.name,
                            'price': float(addon_obj.price)
                        })  # Store name and price directly
                        addon_total += float(addon_obj.price) * quantity  # Multiply addon price by quantity
                    except AddOn.DoesNotExist:
                        logger.warning(f"Add-on with ID {addon_data['id']} not found for item {item_id}")
            
            item_total = (item_price * quantity) + addon_total
            total_price += item_total
            
            cart_items.append({
                'food_item': food_item,
                'quantity': quantity,
                'addons': addon_objects,  # Pass list of dictionaries with name and price
                'item_price': item_price,
                'addon_total': addon_total,
                'total': item_total
            })
            
        except Exception as e:
            logger.error(f"Error processing cart item {cart_key}: {str(e)}")
            del cart[cart_key]
            request.session.modified = True
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    
    return render(request, 'cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        # Find all keys that start with the item_id
        keys_to_remove = []
        for key in cart.keys():
            if key.startswith(f"{item_id}_") or key == str(item_id):
                keys_to_remove.append(key)
        
        # Remove matched items
        for key in keys_to_remove:
            del cart[key]
            
        # Update session
        request.session['cart'] = cart
        request.session.modified = True
        
        if keys_to_remove:
            logger.debug(f"Successfully removed item {item_id} from cart")
        else:
            logger.warning(f"Attempted to remove non-existent item {item_id} from cart")
            
    return redirect('view_cart')


@login_required

def update_cart(request, item_id):

    if request.method == 'POST':

        cart = request.session.get('cart', {})

        str_item_id = str(item_id)

        action = request.POST.get('action')

        try:

            # Verify the item exists in database

            food_item = FoodItem.objects.get(id=item_id)

            # Check the structure of the cart item

            if str_item_id in cart:

                # If it's a dictionary with quantity

                if isinstance(cart[str_item_id], dict) and 'quantity' in cart[str_item_id]:

                    # Handle increment

                    if action == 'increment':

                        cart[str_item_id]['quantity'] += 1

                        logger.debug(f"Incremented item {item_id} to {cart[str_item_id]['quantity']}")

                    # Handle decrement

                    elif action == 'decrement':

                        if cart[str_item_id]['quantity'] > 1:

                            cart[str_item_id]['quantity'] -= 1

                            logger.debug(f"Decremented item {item_id} to {cart[str_item_id]['quantity']}")

                        else:

                            del cart[str_item_id]

                            logger.debug(f"Removed item {item_id} from cart due to zero quantity")

                # If it's just an integer (direct quantity)

                elif isinstance(cart[str_item_id], int):

                    # Handle increment

                    if action == 'increment':

                        cart[str_item_id] += 1

                        logger.debug(f"Incremented item {item_id} to {cart[str_item_id]}")

                    # Handle decrement

                    elif action == 'decrement':

                        if cart[str_item_id] > 1:

                            cart[str_item_id] -= 1

                            logger.debug(f"Decremented item {item_id} to {cart[str_item_id]}")

                        else:

                            del cart[str_item_id]

                            logger.debug(f"Removed item {item_id} from cart due to zero quantity")

            else:

                # Initialize the item in cart if it doesn't exist

                if action == 'increment':

                    # Check your cart structure - adjust this based on how you store items

                    cart[str_item_id] = {'quantity': 1}  # If you store as dict

                    # OR

                    # cart[str_item_id] = 1  # If you store as integer

            # Save changes to session

            request.session['cart'] = cart

            request.session.modified = True

        except FoodItem.DoesNotExist:

            logger.error(f"Attempted to update non-existent item {item_id}")

            return redirect('view_cart')

    return redirect('view_cart')

def get_cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(cart.values())
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': count})
    return count  # Return integer for non-AJAX requests


def update_instructions(request):
    if request.method == 'POST':
        try:
            item_id = request.POST.get('item_id')
            instructions = request.POST.get('instructions')
            
            cart_id = get_or_create_cart_id(request)
            cart_item = Cart.objects.get(cart_id=cart_id, food_item_id=item_id)
            cart_item.special_instructions = instructions
            cart_item.save()

            return JsonResponse({
                'success': True
            })

        except Cart.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Item not found in cart'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def send_welcome_email(user, table_number):
    subject = 'Welcome to Our Restaurant!'
    message = f"""
    Dear Valued Customer,
    
    Thank you for choosing to dine with us! 
    
    Your Details:
    - Email: {user.email}
    - Table Number: {table_number}
    
    You can now:
    - Browse our digital menu
    - Place orders directly from your table
    - Track your order status
    
    If you need any assistance, please don't hesitate to ask our staff.
    
    Enjoy your meal!
    
    Best regards,
    Restaurant Team
    """
    
    try:
        # Add debug logging
        logger.debug(f"Attempting to send email to {user.email}")
        logger.debug(f"Using EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        
        sent = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        if sent:
            logger.info(f"Welcome email sent successfully to {user.email}")
            return True
        else:
            logger.error(f"Failed to send welcome email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
        print(f"Email Error: {str(e)}")  # Print to console for immediate feedback
        return False

def verify_email(request, token):
    try:
        # Get the profile or return 404
        profile = get_object_or_404(UserProfile, verification_token=token)
        
        if not profile.email_verified:
            # Update profile
            profile.email_verified = True
            profile.verification_token = ''
            profile.save()
            
            # Log the user in
            auth_login(request, profile.user)
            
            # Add success message
            messages.success(request, 'Email verified successfully!')
            
            # Redirect to menu
            return redirect('menu')
        else:
            messages.info(request, 'Email was already verified')
            return redirect('menu')
            
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link')
        return redirect('login')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})

def send_verification_email(email, token):
    verification_link = f"http://localhost:8000/verify/{token}"
    subject = 'Verify your Restaurant Account'
    message = f'''
    Hello!
    
    Thank you for registering. Please click the link below to verify your email:
    
    {verification_link}
    
    If you didn't request this, please ignore this email.
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Use the email from settings
            [email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email sending failed: {str(e)}")  # For debugging

@login_required
def menu(request):
    # Clear the cart if it's in the old format
    cart = request.session.get('cart', {})
    if any(isinstance(v, int) for v in cart.values()):
        request.session['cart'] = {}
        cart = {}
    
    # Get all categories and their food items with related add-ons
    categories = Category.objects.all()
    food_items = FoodItem.objects.select_related('category').prefetch_related('addon_set').all()
    
    # Organize food items by category
    menu_by_category = {}
    for category in categories:
        menu_by_category[category] = food_items.filter(category=category)
    
    # Get user profile info
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'current_table': request.session.get('table_number')}
    )

    # Calculate cart count safely
    cart_count = sum(item.get('quantity', 0) for item in cart.values() if isinstance(item, dict))
    
    context = {
        'menu_by_category': menu_by_category,
        'user_email': request.user.email,
        'table_number': profile.current_table,
        'cart_count': cart_count,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser
    }
    
    return render(request, 'menu.html', context)

def get_local_ip():
    """Get the local IP address of the server"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error getting local IP: {str(e)}")
        return '192.168.0.1'  # fallback IP

def generate_qr(request, table_number):
    """
    Generate QR code for table login with debug logging
    """
    try:
        # Get local IP address
        local_ip = get_local_ip()
        
        # Create the login URL using local IP
        login_url = f"http://{local_ip}:8000/login/{table_number}/"
        
        # Debug print - this will show in your console
        print(f"Generated QR URL: {login_url}")
        logger.info(f"Generated QR URL: {login_url}")

        # Configure QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        
        qr.add_data(login_url)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save to buffer
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Return response
        response = HttpResponse(buffer, content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="table_{table_number}_qr.png"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating QR code for table {table_number}: {str(e)}")
        return HttpResponse(f"Error generating QR code: {str(e)}", status=500)


def login_view(request, table_number=None):
    # Get table number from either URL query parameter or POST data
    table_number = table_number or request.POST.get('table')
    
    # Redirect if user is already authenticated
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', 'menu'))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, 'login.html', {'table_number': table_number})
        
        try:
            # Create or get user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'is_staff': False,
                    'is_superuser': False
                }
            )
            
            # Log in the user
            auth_login(request, user)
            
            # Update user's current table
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.current_table = table_number
            profile.save()
            
            # Send welcome email for new users
            if created:
                send_welcome_email(user, table_number)
            
            return redirect('menu')
            
        except Exception as e:
            logger.error(f"Error creating or retrieving user: {e}")
            return redirect('error_page')
    
    # For GET requests, render the login page with table number
    return render(request, 'login.html', {'table_number': table_number})

def qr_codes_view(request):
    # You can adjust the range based on your restaurant's table numbers
    table_range = range(1, 21)  # This will create QR codes for tables 1-20
    return render(request, 'qr_codes.html', {'table_range': table_range})

# @login_required
# def login_view(request):
#     logger.debug("Login view accessed")
    
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         table_number = request.POST.get('table')

#         logger.debug(f"Attempting to log in user with email: {email}")

#         user, created = User.objects.get_or_create(
#             email=email,
#             defaults={
#                 'username': email,
#                 'is_staff': False,
#                 'is_superuser': False
#             }
#         )

#         auth_login(request, user)

#         profile, _ = UserProfile.objects.get_or_create(user=user)
#         profile.current_table = table_number
#         profile.save()

#         if created:
#             send_welcome_email(user, table_number)

#         logger.debug("User logged in successfully, redirecting to menu")
#         return redirect(request.GET.get('next', 'menu'))  # Redirect to the next URL or menu

#     if request.user.is_authenticated:
#         logger.debug("User is already authenticated, redirecting to menu")
#         return redirect(request.GET.get('next', 'menu'))  # Redirect to the next URL or menu

#     return render(request, 'login.html')

def logout_view(request):
    # Only clear user session, not admin session
    if request.session.key_prefix == 'user':
        auth_logout(request)
    return redirect('login')

def notify_admin_of_order(user, payment_method):
    subject = f"New Order from {user.email}"
    message = f"User {user.email} has placed an order using {payment_method}."
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],  # Set this in your settings.py
        fail_silently=False,
    )

@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty. Please add items to the cart before checking out.")
        return redirect('view_cart')

    try:
        total_price = 0
        items = []

        for item_id, cart_item in cart.items():
            # Extract real food item ID from key
            food_item_id = int(str(item_id).split('_')[0])
            food_item = FoodItem.objects.get(id=food_item_id)

            # Get quantity
            if isinstance(cart_item, dict) and 'quantity' in cart_item:
                quantity = cart_item['quantity']
            elif isinstance(cart_item, int):
                quantity = cart_item
            else:
                logger.error(f"Unexpected cart item structure for item {item_id}: {cart_item}")
                continue

            # Base price
            base_price = float(food_item.price) * quantity

            # Add-on price
            addon_total = 0
            addon_objects = []
            if isinstance(cart_item, dict) and 'addons' in cart_item:
                for addon_data in cart_item['addons']:
                    try:
                        addon_obj = AddOn.objects.get(id=addon_data['id'], food_item_id=food_item_id)
                        addon_objects.append(addon_obj)
                        addon_total += float(addon_data['price']) * quantity  # Multiply addon price by quantity
                    except AddOn.DoesNotExist:
                        logger.warning(f"Add-on with ID {addon_data['id']} not found for item {food_item_id}")

            # Final total for this item
            item_total = base_price + addon_total
            total_price += item_total

            items.append({
                'food_item': food_item,
                'quantity': quantity,
                'add_ons': addon_objects,  # Store add-on objects for display
                'base_price': base_price,
                'add_on_total': addon_total,
                'total': item_total
            })

        # Razorpay order creation
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_in_paise = int(total_price * 100)
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1'
        }
        razorpay_order = client.order.create(data=order_data)

        context = {
            'items': items,
            'total_price': total_price,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': amount_in_paise,
            'currency': 'INR'
        }
        
        # Add cart count to context
        cart_count = sum(
            item['quantity'] if isinstance(item, dict) and 'quantity' in item else item
            for item in cart.values()
        )
        context['cart_count'] = cart_count
        
        return render(request, 'payment.html', context)

    except Exception as e:
        logger.error(f"Error in checkout_view: {str(e)}")
        messages.error(request, "Unable to initialize payment. Please try again.")
        return redirect('view_cart')
    
    
def send_order_ready_email(user, table_number):
    subject = 'Your Order is Ready!'
    message = f"Dear {user.email},\n\nYour order is ready and will be served at table number {table_number}.\n\nThank you for dining with us!"
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@login_required
def complete_payment(request):
    # After payment is successful
    cart = Cart.objects.filter(user=request.user)
    if cart:
        # Create transaction
        total_amount = sum(item.menu_item.price * item.quantity for item in cart)
        transaction = Transaction.objects.create(
            user=request.user,
            total_amount=total_amount,
            table_number=request.session.get('table_number')
        )
        
        # Create transaction items
        for cart_item in cart:
            TransactionItem.objects.create(
                transaction=transaction,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                price=cart_item.menu_item.price,
                item_name=cart_item.menu_item.name
            )
        
        # Clear cart
        cart.delete()
        
        return redirect('transaction_success')

@login_required
def view_transactions(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'transactions.html', {'transactions': transactions})


@login_required
def reorder(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        # Clear existing cart
        Cart.objects.filter(user=request.user).delete()
        
        # Add transaction items to cart
        for item in transaction.items.all():
            if item.food_item and item.food_item.stock_quantity > 0:  # Check if food item exists and is in stock
                Cart.objects.create(
                    user=request.user,
                    food_item=item.food_item,
                    quantity=min(item.quantity, item.food_item.stock_quantity)  # Don't exceed available stock
                )
        
        messages.success(request, 'Items have been added to your cart')
        return redirect('view_cart')
    except Transaction.DoesNotExist:
        messages.error(request, 'Transaction not found')
        return redirect('view_transactions')
    

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        try:
            # Get the payment details from Razorpay response
            payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            # Verify the payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': signature
            }

            try:
                client.utility.verify_payment_signature(params_dict)
            except Exception as e:
                logger.error(f"Payment signature verification failed: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment verification failed'
                }, status=400)

            # Get cart items and calculate total
            cart = request.session.get('cart', {})
            total_amount = 0
            
            # First create the Transaction
            transaction = Transaction.objects.create(
                user=request.user,
                total_amount=0,  # Will update after calculating
                payment_id=payment_id,
                razorpay_order_id=razorpay_order_id,
                table_number=request.user.userprofile.current_table
            )

            # Create orders and transaction items
            for item_id, quantity in cart.items():
                try:
                    food_item = get_object_or_404(FoodItem, id=item_id)
                    item_total = food_item.price * quantity
                    total_amount += item_total

                    # Create Order
                    Order.objects.create(
                        user=request.user,
                        food_item=food_item,
                        quantity=quantity,
                        status='Confirmed',
                        payment_status='Completed',
                        payment_id=payment_id,
                        razorpay_order_id=razorpay_order_id
                    )

                    # Create TransactionItem
                    TransactionItem.objects.create(
                        transaction=transaction,
                        food_item=food_item,
                        quantity=quantity,
                        price=food_item.price,
                        item_name=food_item.name
                    )

                except Exception as e:
                    logger.error(f"Error processing item {item_id}: {str(e)}")
                    continue

            # Update transaction total
            transaction.total_amount = total_amount
            transaction.save()

            # Clear the cart
            request.session['cart'] = {}
            request.session.modified = True

            # Notify admin
            try:
                notify_admin_of_order(request.user, 'Razorpay')
            except Exception as e:
                logger.error(f"Error sending admin notification: {str(e)}")

            return JsonResponse({
                'status': 'success',
                'message': 'Payment successful!',
                'redirect_url': reverse('order_history')
            })

        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Payment processing failed'
            }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
#def home(request):
    #return render(request, 'home.html')  # Ensure 'home.html' exists in your templates folder

def get_addons(request, item_id):
    try:
        food_item = FoodItem.objects.get(id=item_id)
        addons = food_item.addon_set.all()
        addon_data = [{
            'id': addon.id,
            'name': addon.name,
            'price': float(addon.price)
        } for addon in addons]
        return JsonResponse({'success': True, 'addons': addon_data})
    except FoodItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Food item not found'}, status=404)

def checkout(request):
    return render(request, 'checkout.html')



