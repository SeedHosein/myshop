from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, FormView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.utils.translation import gettext_lazy as _ # No longer needed
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from products.models import Product # Assuming Product model is in products app
from .models import Cart, CartItem, Order, OrderItem
from .forms import AddToCartForm, CheckoutForm, DiscountApplyForm
from discounts_and_campaigns.models import Discount # Import Discount model

# --- Cart Utility Functions (Session Based) --- #

def get_session_cart(session):
    cart_data = session.get('cart', {})
    if 'items' not in cart_data or not isinstance(cart_data['items'], dict):
        cart_data = {
            'items': {},
            'total_price': Decimal('0.00'),
            'item_count': 0,
            'discount_code': None,
            'discount_amount': Decimal('0.00'),
            'original_total_price': Decimal('0.00'),
        }
    cart_data['total_price'] = Decimal(str(cart_data.get('total_price', '0.00')))
    cart_data['discount_amount'] = Decimal(str(cart_data.get('discount_amount', '0.00')))
    cart_data['original_total_price'] = Decimal(str(cart_data.get('original_total_price', cart_data['total_price'])))
    # Ensure items is a dict
    if not isinstance(cart_data.get('items'), dict):
        cart_data['items'] = {}
    return cart_data

def save_session_cart(session, cart_data):
    cart_data['total_price'] = str(cart_data['total_price'])
    cart_data['discount_amount'] = str(cart_data['discount_amount'])
    cart_data['original_total_price'] = str(cart_data['original_total_price'])
    session['cart'] = cart_data
    session.modified = True

def calculate_session_cart_totals(cart_data):
    total_price = Decimal('0.00')
    item_count = 0
    # Ensure items is a dict before iterating
    if not isinstance(cart_data.get('items'), dict):
        cart_data['items'] = {}

    for item_details in cart_data.get('items', {}).values():
        total_price += Decimal(str(item_details.get('price', '0.00'))) * int(item_details.get('quantity', 0))
        item_count += int(item_details.get('quantity', 0))
    cart_data['original_total_price'] = total_price
    cart_data['item_count'] = item_count
    if cart_data.get('discount_code'):
        applied_discount_amount = Decimal(str(cart_data.get('discount_amount', '0.00')))
        cart_data['total_price'] = total_price - applied_discount_amount
    else:
        cart_data['total_price'] = total_price
        cart_data['discount_amount'] = Decimal('0.00')
    return cart_data

# --- End Cart Utility Functions --- # 

# --- Discount Application Logic ---
def apply_discount_code(cart_total, discount_code_str):
    """
    Applies a discount code to a given cart total.
    Returns a dictionary with discount details or an error message.
    {
        'success': True/False,
        'discount_amount': Decimal,
        'final_total': Decimal,
        'message': str (error or success message),
        'discount_code': str (if successful)
    }
    """
    now = timezone.now()
    try:
        discount = Discount.objects.get(code__iexact=discount_code_str, is_active=True, start_date__lte=now, end_date__gte=now)
    except Discount.DoesNotExist:
        return {'success': False, 'message': "کد تخفیف نامعتبر یا منقضی شده است."}

    if discount.min_cart_amount and cart_total < discount.min_cart_amount:
        return {'success': False, 'message': f"مبلغ سبد خرید کمتر از حداقل مبلغ ({discount.min_cart_amount} تومان) برای این تخفیف است."}

    discount_amount = Decimal('0.00')
    if discount.discount_type == 'percentage':
        # Ensure value is treated as percentage (e.g., 10 for 10%)
        discount_amount = (Decimal(str(discount.value)) / Decimal('100')) * cart_total
    elif discount.discount_type == 'fixed_amount':
        discount_amount = Decimal(str(discount.value))
    
    discount_amount = discount_amount.quantize(Decimal('0.01')) # Round to 2 decimal places

    final_total = cart_total - discount_amount
    if final_total < Decimal('0.00'):
        final_total = Decimal('0.00')
        discount_amount = cart_total # Discount cannot be more than total

    return {
        'success': True,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'message': f"تخفیف '{discount.code}' با موفقیت اعمال شد.",
        'discount_code': discount.code,
        'discount_name': discount.name
    }

class CartDetailView(TemplateView):
    template_name = 'cart_and_orders/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items_active = []
        cart_items_saved_for_later = []
        total_price = 0
        item_count = 0
        context['SHOP_NAME'] = settings.SHOP_NAME

        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
            active_items_query = cart.items.filter(is_saved_for_later=False)
            saved_items_query = cart.items.filter(is_saved_for_later=True)
            
            for item in active_items_query:
                item_total = item.get_total_price()
                cart_items_active.append({
                    'item': item,
                    'product': item.product,
                    'quantity': item.quantity,
                    'total_price': item_total,
                    'update_form': AddToCartForm(initial={'quantity': item.quantity, 'product_id': item.product.id})
                })
            total_price = sum(i['total_price'] for i in cart_items_active)
            item_count = sum(i['quantity'] for i in cart_items_active)

            for item in saved_items_query:
                 cart_items_saved_for_later.append({
                    'item': item,
                    'product': item.product,
                    'quantity': item.quantity,
                    'total_price': item.get_total_price()
                })
            context['db_cart'] = cart # For direct reference if needed
            # Add discount info to context for authenticated user
            context['applied_discount_code'] = cart.applied_discount_code
            context['discount_amount'] = cart.discount_amount
            context['subtotal_cart_price'] = cart.subtotal_price # Explicitly pass subtotal
            context['final_cart_price'] = cart.final_price
            context['total_cart_items'] = cart.subtotal_price
        else:
            # Session cart
            session_cart_data = get_session_cart(self.request.session)
            for product_id_str, details in session_cart_data.get('items', {}).items():
                try:
                    product = Product.objects.get(id=int(product_id_str))
                    item_total = Decimal(details.get('price', '0.00')) * int(details.get('quantity', 0))
                    cart_items_active.append({
                        'product': product,
                        'quantity': details.get('quantity', 1),
                        'total_price': item_total,
                        'name_at_add': details.get('name'), # Store name in session in case product details change
                        'price_at_add': details.get('price'),
                        'update_form': AddToCartForm(initial={'quantity': details.get('quantity',1), 'product_id': product.id})
                    })
                except Product.DoesNotExist:
                    # Product might have been deleted, consider removing it from session cart here or notifying user
                    continue 
            total_price = session_cart_data.get('total_price', Decimal('0.00')) # This is now final price
            item_count = session_cart_data.get('item_count', 0)
            # Saved for later not typically handled in session carts without more complex structure

            context['applied_discount_code'] = session_cart_data.get('discount_code')
            context['discount_amount'] = Decimal(str(session_cart_data.get('discount_amount', '0.00')))
            context['subtotal_cart_price'] = Decimal(str(session_cart_data.get('original_total_price', '0.00')))
            context['final_cart_price'] = total_price # which is already discount-adjusted if applicable
            context['total_cart_items'] = item_count
            # Add a form for applying discount code
            context['discount_apply_form'] = DiscountApplyForm()
        context['cart_items_active'] = cart_items_active
        context['cart_items_saved_for_later'] = cart_items_saved_for_later
        context['total_cart_price'] = total_price # This might now be the discounted price
        context['total_cart_items'] = item_count
        # Add a form for applying discount code
        context['discount_apply_form'] = DiscountApplyForm()
        return context

class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        form = AddToCartForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            quantity = int(form.cleaned_data['quantity'])
            product = get_object_or_404(Product, id=product_id, is_active=True)

            if product.stock < quantity:
                msg = f"موجودی محصول '{product.name}' کافی نیست. موجودی فعلی: {product.stock}"
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': "موجودی کافی نیست.", 'current_stock': product.stock}, status=400)
                messages.error(request, msg)
                return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))

            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                cart_item, created = cart.items.get_or_create(
                    product=product,
                    is_saved_for_later=False, # Ensure we are targeting the active cart item
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                msg = f"تعداد محصول '{product.name}' در سبد شما بروزرسانی شد." if not created else f"محصول '{product.name}' به سبد شما اضافه شد."
                cart.save() # Recalculate totals and save cart discount info
            else:
                # Session cart
                session_cart = get_session_cart(request.session)
                product_id_str = str(product.id)
                if product_id_str in session_cart['items']:
                    session_cart['items'][product_id_str]['quantity'] += quantity
                    msg = f"تعداد محصول '{product.name}' در سبد شما بروزرسانی شد."
                else:
                    # Safely get the main image URL to prevent AttributeError
                    main_image_instance = product.images.filter(is_main=True).first()
                    image_url = main_image_instance.image.url if main_image_instance else ''

                    session_cart['items'][product_id_str] = {
                        'quantity': quantity,
                        'price': str(product.get_display_price),
                        'name': product.name,
                        'image_url': image_url,
                        'detail_url': product.get_absolute_url()
                    }
                    msg = f"محصول '{product.name}' به سبد شما اضافه شد."
                
                session_cart = calculate_session_cart_totals(session_cart) # Recalculates totals and re-applies discount if any
                save_session_cart(request.session, session_cart)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # For AJAX, return updated cart count and total, or full cart partial
                if request.user.is_authenticated:
                    cart = Cart.objects.get(user=request.user) # Re-fetch cart to get latest totals with discount
                    cart_total_items = cart.items.filter(is_saved_for_later=False).count()
                    cart_total_price = cart.final_price
                else:
                    cart_total_items = session_cart.get('item_count', 0)
                    cart_total_price = Decimal(str(session_cart.get('total_price', '0.00')))
                
                return JsonResponse({
                    'status': 'success',
                    'message': msg,
                    'cart_total_items': cart_total_items,
                    'cart_total_price': f'{cart_total_price:.2f}'
                })
            
            messages.success(request, msg)
            return redirect(request.META.get('HTTP_REFERER', 'cart_and_orders:cart_detail'))
        else:
            # Form is invalid
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "اطلاعات نامعتبر است.", 'errors': form.errors}, status=400)
            messages.error(request, "امکان افزودن محصول به سبد وجود ندارد. اطلاعات نامعتبر است.")
            return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))

class RemoveFromCartView(View):
    def post(self, request, item_id):
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            product_name = cart_item.product.name
            cart_item.delete()
            msg = f"محصول '{product_name}' از سبد شما حذف شد."
        else:
            session_cart = get_session_cart(request.session)
            product_id_str = str(item_id) # For session cart, item_id will be product_id
            if product_id_str in session_cart['items']:
                product_name = session_cart['items'][product_id_str].get('name', "محصول")
                del session_cart['items'][product_id_str]
                session_cart = calculate_session_cart_totals(session_cart)
                save_session_cart(request.session, session_cart)
                msg = f"محصول '{product_name}' از سبد شما حذف شد."
            else:
                msg = "مورد در سبد شما یافت نشد."
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg}, status=404)
                messages.error(request, msg)
                return redirect('cart_and_orders:cart_detail')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart_total_items = Cart.objects.get(user=request.user).items.filter(is_saved_for_later=False).count()
            cart_total_price = Cart.objects.get(user=request.user).subtotal_price if request.user.is_authenticated else session_cart.get('subtotal_price', 0)
            return JsonResponse({
                'status': 'success', 
                'message': msg,
                'cart_total_items': cart_total_items,
                'cart_total_price': f'{cart_total_price:.2f}',
                'removed_item_id': item_id # For updating UI
            })
        
        messages.success(request, msg)
        return redirect('cart_and_orders:cart_detail')

class UpdateCartItemQuantityView(View):
    def post(self, request, item_id):
        new_quantity = int(request.POST.get('quantity', 0))
        if new_quantity <= 0:
            # Treat as removal or error
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "تعداد باید مثبت باشد."}, status=400)
            messages.error(request, "تعداد باید حداقل ۱ باشد. برای حذف از دکمه حذف استفاده کنید.")
            return redirect('cart_and_orders:cart_detail')
        
        item_total_price = 0

        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            if cart_item.product.stock < new_quantity:
                msg = f"موجودی برای '{cart_item.product.name}' کافی نیست. موجودی: {cart_item.product.stock}"
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg, 'current_stock': cart_item.product.stock}, status=400)
                messages.error(request, msg)
                return redirect('cart_and_orders:cart_detail')
            
            cart_item.quantity = new_quantity
            cart_item.save()
            item_total_price = cart_item.get_total_price()
            msg = f"تعداد برای '{cart_item.product.name}' بروزرسانی شد."
        else:
            session_cart = get_session_cart(request.session)
            product_id_str = str(item_id) # For session cart, item_id is product_id
            if product_id_str in session_cart['items']:
                try:
                    product = Product.objects.get(id=int(product_id_str))
                    if product.stock < new_quantity:
                        msg = f"موجودی برای '{product.name}' کافی نیست. موجودی: {product.stock}"
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                           return JsonResponse({'status': 'error', 'message': msg, 'current_stock': product.stock}, status=400)
                        messages.error(request, msg)
                        return redirect('cart_and_orders:cart_detail')

                    session_cart['items'][product_id_str]['quantity'] = new_quantity
                    item_total_price = Decimal(str(session_cart['items'][product_id_str]['price'])) * new_quantity
                    session_cart = calculate_session_cart_totals(session_cart) # Recalculates totals and re-applies discount if any
                    save_session_cart(request.session, session_cart)
                    msg = f"تعداد برای '{session_cart['items'][product_id_str]['name']}' بروزرسانی شد."
                except Product.DoesNotExist:
                    msg = "محصول یافت نشد."
                    # Optionally remove from session cart here
            else:
                msg = "مورد در سبد شما یافت نشد."
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg}, status=404)
                messages.error(request, msg)
                return redirect('cart_and_orders:cart_detail')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                cart = Cart.objects.get(user=request.user) # Re-fetch cart
                item_total_price_str = f"{item_total_price:.2f}"
                cart_total_items = cart.items.filter(is_saved_for_later=False).count()
                cart_total_price = f"{cart.final_price:.2f}"
            else:
                item_total_price_str = f"{item_total_price:.2f}"
                cart_total_items = session_cart.get('item_count', 0)
                cart_total_price = f"{Decimal(str(session_cart.get('subtotal_price', '0.00'))):.2f}"
            return JsonResponse({
                'status': 'success', 
                'message': msg,
                'cart_total_items': cart_total_items,
                'cart_total_price': cart_total_price,
                'item_id': item_id,
                'new_quantity': new_quantity,
                'item_total_price': item_total_price_str
            })
        
        messages.success(request, msg)
        return redirect('cart_and_orders:cart_detail')

class SaveForLaterView(View):
    def post(self, request, item_id):
        # This view currently only makes sense for authenticated users with DB cart items
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': "لطفا برای ذخیره آیتم‌ها وارد شوید."}, status=401)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = cart_item.product.name
        new_is_saved = not cart_item.is_saved_for_later
        # Check for duplicate before toggling
        duplicate = CartItem.objects.filter(cart=cart_item.cart, product=cart_item.product, is_saved_for_later=new_is_saved).exclude(id=cart_item.id).first()
        if duplicate:
            cart_item.quantity += duplicate.quantity
            duplicate.delete()
        cart_item.is_saved_for_later = new_is_saved
        cart_item.save()
        
        action_text = "برای بعد ذخیره شد" if cart_item.is_saved_for_later else "به سبد خرید بازگردانده شد"
        msg = f"محصول '{product_name}' {action_text}."

        # Recalculate cart totals for authenticated user
        cart = cart_item.cart
        cart_total_items = cart.items.filter(is_saved_for_later=False).count()
        cart_total_price = f"{cart.final_price:.2f}"
        active_items_count = cart.items.filter(is_saved_for_later=False).count()
        saved_items_count = cart.items.filter(is_saved_for_later=True).count()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': msg,
                'item_id': item_id,
                'is_saved': cart_item.is_saved_for_later,
                'cart_total_items': cart_total_items, # This is total of active items
                'cart_total_price': cart_total_price,
                'active_items_count': active_items_count,
                'saved_items_count': saved_items_count
            })

        messages.success(request, msg)
        return redirect('cart_and_orders:cart_detail')


# --- Checkout Process --- #
class CheckoutView(LoginRequiredMixin, FormView):
    template_name = 'cart_and_orders/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('cart_and_orders:order_confirmation') # Placeholder, will change after payment

    def dispatch(self, request, *args, **kwargs):
        # Check if cart is empty
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            if not cart.items.filter(is_saved_for_later=False).exists():
                messages.info(request, "سبد خرید شما خالی است. لطفاً قبل از پرداخت، محصولی اضافه کنید.")
                return redirect('products:product_list')
        # The 'else' block for anonymous users is removed.
        # LoginRequiredMixin (as the first inherited class) will handle redirection
        # for unauthenticated users to the login page.
        # If execution reaches this point for an anonymous user (it shouldn't if LRM is first),
        # super().dispatch() would call LRM's dispatch which then redirects.
        # If execution reaches here for an authenticated user, the above cart check ran.
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass user to form for pre-filling
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        
        if self.request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=self.request.user)
            context['cart'] = cart
            context['cart_items'] = cart.items.filter(is_saved_for_later=False)
            context['subtotal'] = cart.subtotal_price # Price before discount
            context['discount_amount'] = cart.discount_amount
            context['final_total'] = cart.final_price # Price after discount
            context['applied_discount_code'] = cart.applied_discount_code
        else:
            # Handle guest user checkout context from session
            session_cart = get_session_cart(self.request.session)
            cart_items = []
            for product_id_str, details in session_cart.get('items', {}).items():
                try:
                    product = Product.objects.get(id=int(product_id_str))
                    cart_items.append({
                        'product': product,
                        'quantity': details.get('quantity', 1),
                        'subtotal_price': Decimal(product.get_display_price) * int(details.get('quantity', 1)),
                    })
                except Product.DoesNotExist:
                    continue # Or handle missing product appropriately
            
            context['cart_items'] = cart_items
            context['subtotal'] = Decimal(str(session_cart.get('original_total_price', '0.00')))
            context['discount_amount'] = Decimal(str(session_cart.get('discount_amount', '0.00')))
            context['final_total'] = Decimal(str(session_cart.get('total_price', '0.00')))
            context['applied_discount_code'] = session_cart.get('discount_code')

        return context

    @transaction.atomic
    def form_valid(self, form):
        # This is where the Order object will be created.
        # Payment processing will come before or after this depending on the flow.
        # For now, we assume payment is handled and create the order.

        user = self.request.user if self.request.user.is_authenticated else None
        
        # Collect cart items and total
        cart_items_to_order = []
        final_total_amount = 0

        if user:
            cart = get_object_or_404(Cart, user=user)
            active_cart_items = cart.items.filter(is_saved_for_later=False)
            if not active_cart_items.exists():
                messages.error(self.request, "سبد خرید شما خالی است.")
                return redirect('cart_and_orders:cart_detail')
            
            for item in active_cart_items:
                if item.product.stock < item.quantity:
                    messages.error(self.request, f"موجودی محصول '{item.product.name}' ({item.quantity} عدد) کافی نیست. موجودی فعلی: {item.product.stock}. لطفا سبد خرید خود را بروزرسانی کنید.")
                    return redirect('cart_and_orders:cart_detail')
                cart_items_to_order.append(item)
                final_total_amount += item.get_total_price()
        else: # Guest checkout from session
            session_cart = get_session_cart(self.request.session)
            if not session_cart['items']:
                messages.error(self.request, "سبد خرید شما خالی است.")
                return redirect('cart_and_orders:cart_detail')

            for product_id_str, details in session_cart['items'].items():
                product = get_object_or_404(Product, id=int(product_id_str))
                quantity = int(details['quantity'])
                if product.stock < quantity:
                    messages.error(self.request, f"موجودی محصول '{product.name}' ({quantity} عدد) کافی نیست. موجودی فعلی: {product.stock}. لطفا سبد خرید خود را بروزرسانی کنید.")
                    return redirect('cart_and_orders:cart_detail')
                # Create pseudo CartItem-like dicts for consistency if needed, or just necessary data
                cart_items_to_order.append({
                    'product': product,
                    'quantity': quantity,
                    'price_at_purchase': product.get_display_price,
                    'product_name_at_purchase': product.name
                })
                final_total_amount += product.get_display_price * quantity

        # Create the Order
        if user:
            applied_discount_code = cart.applied_discount_code
            discount_amount = cart.discount_amount
            original_total_amount = cart.calculate_total_price() # Store pre-discount total
        else:
            session_cart = get_session_cart(self.request.session)
            applied_discount_code = session_cart.get('discount_code')
            discount_amount = Decimal(str(session_cart.get('discount_amount', '0.00')))
            original_total_amount = Decimal(str(session_cart.get('original_total_price', '0.00')))

        order = Order.objects.create(
            user=user,
            status=Order.PENDING, # Initial status
            total_amount=final_total_amount, # Final amount after discount
            # Billing Address
            billing_first_name=form.cleaned_data['billing_first_name'],
            billing_last_name=form.cleaned_data['billing_last_name'],
            billing_address=f"{form.cleaned_data['address_line_1']}\n{form.cleaned_data.get('address_line_2', '')}".strip(),
            billing_city=form.cleaned_data['city'],
            billing_postal_code=form.cleaned_data['postal_code'],
            billing_phone=form.cleaned_data['phone_number'] if not user else user.phone_number, # Use profile phone for logged in user
            
            # Assuming shipping is same as billing for now, or add separate form fields
            shipping_first_name=form.cleaned_data['shipping_first_name'],
            shipping_last_name=form.cleaned_data['shipping_last_name'],
            shipping_address=f"{form.cleaned_data['address_line_1']}\n{form.cleaned_data.get('address_line_2', '')}".strip(),
            shipping_city=form.cleaned_data['city'],
            shipping_postal_code=form.cleaned_data['postal_code'],
            shipping_phone=form.cleaned_data['phone_number'] if not user else user.phone_number,
            notes=form.cleaned_data.get('notes', ''),
            # Store discount information with the order
            applied_discount_code=applied_discount_code,
            discount_amount=discount_amount,
            original_total_amount=original_total_amount
        )
        order.order_number = f"CHK-{order.id:06d}" # Generate a simple order number
        order.save()

        # Create OrderItems
        for item_data in cart_items_to_order:
            if isinstance(item_data, CartItem): # Authenticated user
                OrderItem.objects.create(
                    order=order,
                    product=item_data.product,
                    quantity=item_data.quantity,
                    price_at_purchase=item_data.product.get_display_price(),
                    product_name_at_purchase=item_data.product.name
                )
                # Decrement stock
                item_data.product.stock -= item_data.quantity
                item_data.product.save()
            else: # Guest user (item_data is a dict)
                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    price_at_purchase=item_data['price_at_purchase'],
                    product_name_at_purchase=item_data['product_name_at_purchase']
                )
                # Decrement stock
                item_data['product'].stock -= item_data['quantity']
                item_data['product'].save()

        # Clear the cart after successful order creation
        if user:
            active_cart_items.delete() # Delete CartItem objects
        else:
            # Clear session cart
            save_session_cart(self.request.session, {'items': {}, 'total_price': 0.0, 'item_count': 0})

        # Store order_id in session for confirmation page (especially for guests)
        self.request.session['last_order_id'] = order.id

        messages.success(self.request, f"سفارش شما با شماره {order.order_number} با موفقیت ثبت شد! به زودی ایمیل تاییدیه دریافت خواهید کرد.")
        return super().form_valid(form) # Redirects to success_url


class OrderConfirmationView(TemplateView):
    template_name = 'cart_and_orders/order_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        last_order_id = self.request.session.get('last_order_id')
        if last_order_id:
            try:
                order = Order.objects.get(id=last_order_id)
                context['order'] = order
            except Order.DoesNotExist:
                context['error_message'] = "امکان بازیابی جزئیات سفارش شما وجود ندارد."
        else:
            context['info_message'] = "سفارش اخیری در این جلسه یافت نشد. اگر سفارشی ثبت کرده‌اید و آن را نمی‌بینید، لطفاً با پشتیبانی تماس بگیرید."
        return context


def merge_session_cart_to_db(request):
    if request.user.is_authenticated and 'cart' in request.session:
        session_cart_data = get_session_cart(request.session)
        if not session_cart_data.get('items'): # No items in session cart to merge
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
            return

        db_cart, created = Cart.objects.get_or_create(user=request.user)
        merged_item_count = 0

        for product_id_str, item_details in session_cart_data.get('items', {}).items():
            try:
                product = Product.objects.get(id=int(product_id_str))
                quantity = int(item_details.get('quantity', 1))
                if product.stock >= quantity:
                    cart_item, item_created = db_cart.items.get_or_create(
                        product=product,
                        is_saved_for_later=False,
                        defaults={'quantity': quantity}
                    )
                    if not item_created:
                        # If item already exists, add quantities, ensuring not to exceed stock
                        new_quantity = cart_item.quantity + quantity
                        cart_item.quantity = min(new_quantity, product.stock)
                        cart_item.save()
                    merged_item_count +=1
                else:
                    messages.warning(request, f"امکان ادغام محصول '{product.name}' به دلیل کمبود موجودی ({product.stock} عدد) وجود ندارد. این محصول به سبد شما اضافه نشد.")
            except Product.DoesNotExist:
                # Product from session cart no longer exists, skip it
                continue
        
        session_discount_code = session_cart_data.get('discount_code')
        if session_discount_code:
            # Attempt to re-apply session discount to the now merged DB cart
            # It's crucial to recalculate subtotal for the DB cart before applying discount
            db_cart.save() # This should trigger recalculation if properties are well-defined or a pre_save signal
            cart_total_for_discount = db_cart.subtotal_price # Get fresh subtotal
            result = apply_discount_code(cart_total_for_discount, session_discount_code)
            if result['success']:
                db_cart.applied_discount_code = result['discount_code']
                db_cart.discount_amount = result['discount_amount']
            else:
                 messages.warning(request, f"امکان اعمال مجدد تخفیف '{session_discount_code}' از جلسه قبلی شما وجود ندارد: {result['message']}")
        db_cart.save() # Save final cart state
        
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True
        if merged_item_count > 0:
            messages.success(request, "سبد خرید جلسه قبلی شما با سبد خرید حساب کاربری‌تان ادغام شد.")
        # Else, if no items were merged, maybe a silent success or a different message.

class ApplyDiscountView(View):
    def post(self, request, *args, **kwargs):
        form = DiscountApplyForm(request.POST)
        if not form.is_valid():
            # Usually, the code field is the only one, so errors would be about it being empty if required
            # but our form allows empty for removal. This check is more for other potential form errors.
            return JsonResponse({'success': False, 'message': "اطلاعات فرم تخفیف نامعتبر است.", 'errors': form.errors})

        discount_code_str = form.cleaned_data.get('code', '').strip()

        if not discount_code_str: # Request to remove discount
            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                cart.clear_discount()
                return JsonResponse({
                    'success': True, 'message': "تخفیف حذف شد.",
                    'original_total': f"{cart.subtotal_price:.2f}",
                    'final_total': f"{cart.final_price:.2f}",
                    'discount_amount': f"{cart.discount_amount:.2f}", # Should be 0.00
                    'cart_total_items': cart.items.filter(is_saved_for_later=False).count(),
                    'applied_discount_code': None
                })
            else:
                session_cart = get_session_cart(request.session)
                session_cart['discount_code'] = None
                session_cart['discount_amount'] = Decimal('0.00')
                session_cart['total_price'] = session_cart['original_total_price'] # Revert to original
                save_session_cart(request.session, session_cart)
                return JsonResponse({
                    'success': True, 'message': "تخفیف حذف شد.",
                    'original_total': f"{Decimal(str(session_cart['original_total_price']))}",
                    'final_total': f"{Decimal(str(session_cart['total_price']))}",
                    'discount_amount': "0.00",
                    'cart_total_items': session_cart.get('item_count', 0),
                    'applied_discount_code': None
                })

        # Applying a discount code
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_total_before_discount = cart.subtotal_price
            result = apply_discount_code(cart_total_before_discount, discount_code_str)
            if result['success']:
                cart.applied_discount_code = result['discount_code']
                cart.discount_amount = result['discount_amount']
                cart.save()
                return JsonResponse({
                    'success': True, 'message': result['message'],
                    'discount_amount': f"{result['discount_amount']:.2f}",
                    'original_total': f"{cart_total_before_discount:.2f}",
                    'final_total': f"{result['final_total']:.2f}",
                    'cart_total_items': cart.items.filter(is_saved_for_later=False).count(),
                    'applied_discount_code': result['discount_code']
                })
            else:
                # Do not clear existing discount if new one is invalid, unless that's desired behavior
                # cart.clear_discount()
                return JsonResponse({'success': False, 'message': result['message']})
        else: # Session cart
            session_cart = get_session_cart(request.session)
            # Ensure original_total_price is up-to-date if items changed without full recalculation
            current_cart_total = calculate_session_cart_totals(session_cart)['original_total_price'] 
            
            if not session_cart['items']:
                 return JsonResponse({'success': False, 'message': "سبد خرید شما خالی است."})
            result = apply_discount_code(current_cart_total, discount_code_str)
            
            if result['success']:
                session_cart['discount_code'] = result['discount_code']
                session_cart['discount_amount'] = result['discount_amount']
                session_cart['total_price'] = result['final_total']
            else:
                # If new discount invalid, keep old one or clear? For now, just report error.
                # session_cart['discount_code'] = None
                # session_cart['discount_amount'] = Decimal('0.00')
                # session_cart['total_price'] = current_cart_total # Revert to total before this attempt
                pass # Message from result will be used
            save_session_cart(request.session, session_cart)
            return JsonResponse({
                'success': result['success'],
                'message': result['message'],
                'discount_amount': f"{result.get('discount_amount', Decimal('0.00')):.2f}",
                'original_total': f"{current_cart_total:.2f}", # This is the subtotal
                'final_total': f"{session_cart['total_price']:.2f}", # This is total after potential discount
                'cart_total_items': session_cart.get('item_count', 0),
                'applied_discount_code': session_cart.get('discount_code')
            })
