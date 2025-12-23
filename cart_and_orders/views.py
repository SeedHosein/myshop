from django.shortcuts import render, redirect, get_object_or_404, _get_queryset
from django.views import View
from django.views.generic import TemplateView, FormView
from django.http import Http404, JsonResponse
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.utils.translation import gettext_lazy as _ # No longer needed
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from products.models import Product, ProductVariant
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

    # Bulk fetch products and variants to optimize DB queries
    product_ids = {item['product_id'] for item in cart_data.get('items', {}).values()}
    variant_ids = {item['variant_id'] for item in cart_data.get('items', {}).values() if item.get('variant_id')}
    
    products = Product.objects.filter(is_active=True).in_bulk(list(product_ids))
    variants = ProductVariant.objects.filter(is_active=True).in_bulk(list(variant_ids))

    for item_key, item_details in cart_data.get('items', {}).items():
        product = products.get(item_details['product_id'])
        if not product:
            continue

        price = product.get_display_price
        if item_details.get('variant_id'):
            variant = variants.get(item_details['variant_id'])
            if variant:
                price = variant.get_price
        
        quantity = int(item_details.get('quantity', 0))
        total_price += price * quantity
        item_count += quantity
        
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
    
    discount_amount = discount_amount.quantize(Decimal('0.01'))

    final_total = cart_total - discount_amount
    if final_total < Decimal('0.00'):
        final_total = Decimal('0.00')
        discount_amount = cart_total

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
        context['SHOP_NAME'] = settings.SHOP_NAME

        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
            # Use select_related to optimize fetching product and variant data
            active_items_query = cart.items.filter(is_saved_for_later=False).select_related('product', 'variant')
            saved_items_query = cart.items.filter(is_saved_for_later=True).select_related('product', 'variant')
            
            for item in active_items_query:
                stock_item = item.variant if item.variant else item.product
                if item.product.is_active and stock_item.stock > 0:
                    if stock_item.stock < item.quantity:
                        item.quantity = stock_item.stock
                        item.save()
                        
                        messages.warning(self.request, f"تعداد محصول '{str(item)}' به علت کم بودن موجودی محصول در سبد خرید شما به '{item.quantity}' کاهش یافت. قبل از اتمام کامل موجودی خرید خود را تکمیل کنید.")
                    cart_items_active.append({
                        'item': item,
                        'product': item.product,
                        'variant': item.variant,
                        'quantity': item.quantity,
                        'total_price': item.get_total_price(),
                        'update_form': AddToCartForm(initial={'quantity': item.quantity, 'product_id': item.product.id, 'variant_id': item.variant.id if item.variant else None})
                    })
                else:
                    item.delete()
                    messages.warning(self.request, f"محصول '{str(item)}' به علت اتمام موجودی از سبد شما حذف شد.")
            
            total_price = sum(i['total_price'] for i in cart_items_active)
            item_count = sum(i['quantity'] for i in cart_items_active)
            for item in saved_items_query:
                stock_item = item.variant if item.variant else item.product
                if item.product.is_active and stock_item.stock > 0:
                    if stock_item.stock < item.quantity:
                        item.quantity = stock_item.stock
                        item.save()
                        messages.warning(self.request, f"تعداد محصول '{str(item)}' به علت کم بودن موجودی محصول در سبد خرید بعدی شما به '{item.quantity}' کاهش یافت. قبل از اتمام کامل موجودی خرید خود را تکمیل کنید.")
                    cart_items_saved_for_later.append({
                        'item': item,
                        'product': item.product,
                        'variant': item.variant,
                        'quantity': item.quantity,
                        'total_price': item.get_total_price()
                    })
                else:
                    product_name = str(item)
                    item.delete()
                    messages.warning(self.request, f"محصول '{product_name}' به علت تمام شدن موجودی از سبد خرید بعدی شما حذف شد.")
            
            context['db_cart'] = cart
            context['applied_discount_code'] = cart.applied_discount_code
            context['discount_amount'] = cart.discount_amount
            context['subtotal_cart_price'] = cart.subtotal_price
            context['final_cart_price'] = cart.final_price
            context['total_cart_items'] = cart.total_items
        else:
            session_cart = get_session_cart(self.request.session)
            session_cart = calculate_session_cart_totals(session_cart)
            save_session_cart(self.request.session, session_cart)
            
            product_ids = [item['product_id'] for item in session_cart['items'].values()]
            variant_ids = [item['variant_id'] for item in session_cart['items'].values() if item.get('variant_id')]
            products = Product.objects.filter(is_active=True).in_bulk(product_ids)
            variants = ProductVariant.objects.filter(is_active=True).in_bulk(variant_ids)

            for item_key, item_data in list(session_cart['items'].items()): # Use list to allow deletion while iterating
                product = products.get(item_data['product_id'])
                if not product:
                    del session_cart['items'][item_key]
                    continue
                
                variant = None
                stock_to_check = product.stock
                if item_data.get('variant_id'):
                    variant = variants.get(item_data['variant_id'])
                    if not variant:
                        del session_cart['items'][item_key]
                        continue
                    stock_to_check = variant.stock
                
                if not product.is_active or stock_to_check <= 0:
                    del session_cart['items'][item_key]
                    messages.warning(self.request, f"محصول '{item_data["name"]}' به علت تمام شدن موجودی از سبد خرید شما حذف شد.")
                    continue
                
                price = variant.get_price if variant else product.get_display_price
                quantity = item_data['quantity']
                if stock_to_check < quantity:
                    quantity = stock_to_check
                    session_cart['items'][item_key]['quantity'] = quantity
                    messages.warning(self.request, f"تعداد محصول '{item_data["name"]}' به علت کم بودن موجودی محصول در سبد خرید شما به '{quantity}' کاهش یافت. قبل از اتمام کامل موجودی خرید خود را تکمیل کنید.")
                
                cart_items_active.append({
                    'item_key': item_key,
                    'product': product,
                    'variant': variant,
                    'quantity': quantity,
                    'total_price': price * quantity,
                    'update_form': AddToCartForm(initial={'quantity': quantity, 'product_id': product.id, 'variant_id': item_data.get('variant_id')})
                })
            
            save_session_cart(self.request.session, session_cart)
            context['cart_items_active'] = cart_items_active
            context['subtotal_cart_price'] = Decimal(str(session_cart.get('original_total_price', '0.00')))
            context['final_cart_price'] = Decimal(str(session_cart.get('total_price', '0.00')))
            context['total_cart_items'] = session_cart.get('item_count', 0)
            context['applied_discount_code'] = session_cart.get('discount_code')
            context['discount_amount'] = Decimal(str(session_cart.get('discount_amount', '0.00')))

        context['discount_apply_form'] = DiscountApplyForm()
        return context

class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        form = AddToCartForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            variant_id = form.cleaned_data.get('variant_id')
            quantity = form.cleaned_data['quantity']
            
            product = get_object_or_404(Product, id=product_id, is_active=True)
            variant = None
            if variant_id:
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product, is_active=True)

            stock_to_check = variant.stock if variant else product.stock
            item_name = str(variant) if variant else product.name

            if stock_to_check < quantity:
                msg = f"موجودی محصول '{item_name}' کافی نیست. موجودی فعلی: {stock_to_check}"
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg, 'current_stock': stock_to_check}, status=400)
                messages.error(request, msg)
                return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))

            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                cart_item, created = cart.items.get_or_create(
                    product=product,
                    variant=variant,
                    is_saved_for_later=False,
                    defaults={'quantity': quantity}
                )
                if not created:
                    if stock_to_check < (cart_item.quantity+quantity):
                        msg = f"موجودی محصول '{item_name}' کافی نیست. موجودی فعلی: {stock_to_check}"
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({'status': 'error', 'message': msg, 'current_stock': stock_to_check}, status=400)
                        messages.error(request, msg)
                        return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))

                    cart_item.quantity += quantity
                    msg = f"تعداد محصول {item_name} افزایش یافت."
                else:
                    msg = f"محصول '{item_name}' به سبد شما اضافه شد."
                cart_item.save()
            else:
                cart = get_session_cart(request.session)
                item_key = f"{product_id}-{variant_id}" if variant_id else str(product_id)
                
                if item_key in cart['items']:
                    cart['items'][item_key]['quantity'] += quantity
                    msg = f"تعداد محصول {item_name} افزایش یافت."
                else:
                    price = variant.get_price if variant else product.get_display_price
                    cart['items'][item_key] = {
                        'product_id': product_id, 'variant_id': variant_id, 
                        'quantity': quantity, 'price': str(price), 'name': item_name
                    }
                    msg = f"محصول '{item_name}' به سبد خرید اضافه شد."
                cart = calculate_session_cart_totals(cart)
                save_session_cart(request.session, cart)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                item_id = cart_item.id if request.user.is_authenticated else item_key
                total_items = cart.total_items if request.user.is_authenticated else cart['item_count']
                return JsonResponse({
                    'status': 'success', 
                    'message': msg,
                    'cart_total_items': total_items,
                    'item_id': str(item_id),
                })
            
            messages.success(request, msg)
            return redirect('cart_and_orders:cart_detail')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': "اطلاعات نامعتبر است.", 'errors': form.errors}, status=400)
        messages.error(request, "اطلاعات ارسالی برای افزودن به سبد خرید نامعتبر است.")
        return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


class RemoveFromCartView(View):
    def post(self, request, item_id=-1):
        if item_id == -1:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "کالا در سبد پیدا نشد."}, status=404)
            raise Http404("کالا در سبد پیدا نشد.")
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            cart_item = cart.items.filter(id=item_id)
            if cart_item:
                cart_item = cart_item[0]
            else:
                raise Http404(
                    "کالا در سبد خرید شما یافت نشد."
                )
            product_name = str(cart_item.variant) if cart_item.variant else cart_item.product.name
            cart_item.delete()
            msg = f"محصول '{product_name}' از سبد شما حذف شد."
            
            session_cart = {
                'total_price': 0,
                'discount_amount': 0,
                'original_total_price': 0,
                'item_count': cart.total_items
            }
            save_session_cart(request.session, session_cart)
        else:
            session_cart = get_session_cart(request.session)
            if item_id in session_cart['items']:
                product_name = session_cart['items'][item_id].get('name', 'انتخابی')
                del session_cart['items'][item_id]
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
            # For AJAX, return updated cart count and total, or full cart partial
            if request.user.is_authenticated:
                cart_total_price = cart.final_price
                cart_total_items = cart.total_items
            else:
                cart_total_items = session_cart.get('item_count', 0)
                cart_total_price = Decimal(str(session_cart.get('total_price', '0.00')))
            return JsonResponse({
                'status': 'success', 
                'message': msg,
                'cart_total_items': cart_total_items,
                'cart_total_price': f'{cart_total_price:.2f}',
                'removed_item_id': item_id, # For updating UI
                'item_id': ""
            })
        
        messages.success(request, msg)
        return redirect('cart_and_orders:cart_detail')


class UpdateCartItemQuantityView(View):
    def post(self, request, item_id=-1):
        if item_id == -1:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "کالا در سبد پیدا نشد."}, status=404)
            raise Http404("کالا در سبد پیدا نشد.")
        new_quantity = int(request.POST.get('quantity', 0))
        if new_quantity <= 0:
            # Treat as removal or error
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "تعداد باید مثبت باشد."}, status=400)
            messages.error(request, "تعداد باید حداقل ۱ باشد. برای حذف از دکمه حذف استفاده کنید.")
            return redirect('cart_and_orders:cart_detail')
            
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            cart_item = cart.items.filter(id=item_id)
            if cart_item:
                cart_item = cart_item[0]
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': "کالا در سبد پیدا نشد."}, status=404)
                messages.error(request, "کالا در سبد پیدا نشد.")
                return redirect('cart_and_orders:cart_detail')
            
            if cart_item.variant:
                stock_to_check = cart_item.variant.stock
                item_name = str(cart_item.variant)
            else:
                stock_to_check = cart_item.product.stock
                item_name = product.name
                
            if stock_to_check < new_quantity:
                msg = f"موجودی برای '{item_name}' کافی نیست. موجودی: {stock_to_check}"
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg, 'current_stock': cart_item.product.stock}, status=400)
                messages.error(request, msg)
                return redirect('cart_and_orders:cart_detail')
            
            cart_item.quantity = new_quantity
            cart_item.save()
            msg = f"تعداد برای '{item_name}' بروزرسانی شد."
            
            session_cart = {
                'total_price': 0,
                'discount_amount': 0,
                'original_total_price': 0,
                'item_count': cart.total_items
            }
            save_session_cart(request.session, session_cart)
        else:
            session_cart = get_session_cart(request.session)
            if item_id in session_cart['items']:
                product_id = session_cart['items'][item_id]['product_id']
                variant_id = session_cart['items'][item_id].get('variant_id')
                try:
                    product = get_object_or_404(Product, id=product_id)
                    stock_to_check = product.stock
                    if variant_id:
                        variant = get_object_or_404(ProductVariant, id=variant_id)
                        stock_to_check = variant.stock
                    
                    if stock_to_check < new_quantity:
                        msg = f"موجودی برای '{session_cart['items'][item_id]['name']}' کافی نیست. موجودی: {stock_to_check}"
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({'status': 'error', 'message': msg, 'current_stock': stock_to_check}, status=400)
                        messages.error(request, msg)
                        return redirect('cart_and_orders:cart_detail')
                    
                    session_cart['items'][item_id]['quantity'] = new_quantity
                    session_cart = calculate_session_cart_totals(session_cart)
                    save_session_cart(request.session, session_cart)
                    msg = f"تعداد برای '{session_cart['items'][item_id]['name']}' بروزرسانی شد."
                except Product.DoesNotExist:
                    msg = "کالا یافت نشد."
                    del session_cart['items'][item_id]
                    session_cart = calculate_session_cart_totals(session_cart)
                    save_session_cart(request.session, session_cart)
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'status': 'error', 'message': msg}, status=404)
                    messages.error(request, msg)
                    return redirect('cart_and_orders:cart_detail')
            else:
                msg = "کالا در سبد شما یافت نشد."
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg}, status=404)
                messages.error(request, msg)
                return redirect('cart_and_orders:cart_detail')

        return redirect('cart_and_orders:cart_detail')


class SaveForLaterView(View):
    def post(self, request, item_id):
        # This view currently only makes sense for authenticated users with DB cart items
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': "لطفا برای ذخیره کالا ها در سبد بعدی وارد شوید."}, status=401)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        item_name = str(cart_item.variant) if cart_item.variant else cart_item.product.name
        new_status = not cart_item.is_saved_for_later
        
        duplicate_item = CartItem.objects.filter(
            cart=cart_item.cart, 
            product=cart_item.product, 
            variant=cart_item.variant, 
            is_saved_for_later=new_status
        ).exclude(id=cart_item.id).first()

        if duplicate_item:
            duplicate_item.quantity += cart_item.quantity
            duplicate_item.save()
            cart_item.delete()
        else:
            cart_item.is_saved_for_later = new_status
            cart_item.save()
        
        action_text = "برای بعد ذخیره شد" if cart_item.is_saved_for_later else "به سبد خرید بازگردانده شد"
        msg = f"محصول '{item_name}' {action_text}."

        # Recalculate cart totals for authenticated user
        cart = cart_item.cart
        cart_total_price = f"{cart.final_price:.2f}"
        cart_total_items = cart.total_items
        saved_items_count = sum(item.quantity for item in cart.items.filter(is_saved_for_later=True))

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': msg,
                'item_id': item_id,
                'is_saved': cart_item.is_saved_for_later,
                'cart_total_items': cart_total_items, # This is total of active items
                'cart_total_price': cart_total_price,
                'saved_items_count': saved_items_count
            })

        messages.success(request, msg)
        return redirect('cart_and_orders:cart_detail')


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = 'cart_and_orders/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('cart_and_orders:order_confirmation')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if cart is empty
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            if not cart.items.filter(is_saved_for_later=False).exists():
                messages.error(request, "سبد خرید شما خالی است. لطفاً قبل از پرداخت، محصولی اضافه کنید.")
                return redirect('products:product_list')
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
            context['cart'] = calculate_session_cart_totals(get_session_cart(self.request.session))
        return context

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            messages.info(self.request, "برای تکمیل خرید، لطفا وارد شوید یا ثبت نام کنید.")
            return redirect(f"{reverse('accounts:login')}?next={reverse('cart_and_orders:checkout')}")

        with transaction.atomic():
        
            # Collect cart items and total
            cart_items_to_order = []
            final_total_amount = 0

            cart = get_object_or_404(Cart, user=self.request.user)
            active_cart_items = cart.items.filter(is_saved_for_later=False)
            if not active_cart_items.exists():
                messages.error(self.request, "سبد خرید شما خالی است.")
                return redirect('cart_and_orders:cart_detail')
            
            for item in active_cart_items:
                stock_to_check = item.variant.stock if item.variant else item.product.stock
                item_name = str(item.variant) if item.variant else item.product.name
                if stock_to_check < item.quantity:
                    messages.error(self.request, f"موجودی محصول '{item_name}' ({item.quantity} عدد) کافی نیست. موجودی فعلی: {stock_to_check}. لطفا سبد خرید خود را بروزرسانی کنید.")
                    return redirect('cart_and_orders:cart_detail')
                cart_items_to_order.append(item)
                final_total_amount += item.get_total_price()
            
            applied_discount_code = cart.applied_discount_code
            discount_amount = cart.discount_amount
            original_total_amount = cart.subtotal_price()
            order = Order.objects.create(
                user=self.request.user,
                total_amount=cart.final_price,
                applied_discount_code=cart.applied_discount_code,
                discount_amount=cart.discount_amount,
                original_total_amount=cart.subtotal_price,
                billing_name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                billing_address=form.cleaned_data['address_line_1'],
                billing_city=form.cleaned_data['city'],
                billing_postal_code=form.cleaned_data['postal_code'],
                billing_phone=form.cleaned_data['phone_number'],
                shipping_name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                shipping_address=form.cleaned_data['address_line_1'],
                shipping_city=form.cleaned_data['city'],
                shipping_postal_code=form.cleaned_data['postal_code'],
                shipping_phone=form.cleaned_data['phone_number'],
                notes=form.cleaned_data.get('notes', '')
            )
            for item in cart.items.filter(is_saved_for_later=False):
                price = item.get_total_price() / item.quantity # Price per item
                name = str(item)
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity,
                    price_at_purchase=price,
                    product_name_at_purchase=name
                )
                stock_item = item.variant if item.variant else item.product
                stock_item.stock -= item.quantity
                stock_item.save()
            
            cart.items.filter(is_saved_for_later=False).delete()
            cart.clear_discount()

        self.request.session['last_order_id'] = order.id
        return super().form_valid(form)

class OrderConfirmationView(TemplateView):
    template_name = 'cart_and_orders/order_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.get('last_order_id')
        if not order_id:
            raise Http404("سفارش یافت نشد.")
            
        order = get_object_or_404(Order, id=order_id)
        if self.request.user.is_authenticated and order.user != self.request.user:
            raise Http404
            
        context['order'] = order
        if 'last_order_id' in self.request.session:
            del self.request.session['last_order_id']
        return context

class ApplyDiscountView(View):
    def post(self, request, *args, **kwargs):
        form = DiscountApplyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            now = timezone.now()
            try:
                discount = Discount.objects.get(code__iexact=code, is_active=True, valid_from__lte=now, valid_to__gte=now)
                
                if request.user.is_authenticated:
                    cart = get_object_or_404(Cart, user=request.user)
                    cart.apply_discount(discount)
                else:
                    session_cart = get_session_cart(request.session)
                    total = session_cart.get('original_total_price', Decimal('0.00'))
                    discount_amount = (total * discount.percentage) / 100
                    session_cart['discount_code'] = discount.code
                    session_cart['discount_amount'] = str(discount_amount)
                    session_cart = calculate_session_cart_totals(session_cart)
                    save_session_cart(request.session, session_cart)

                messages.success(request, f"کد تخفیف '{code}' اعمال شد.")
            except Discount.DoesNotExist:
                messages.error(request, "کد تخفیف نامعتبر است.")
        return redirect('cart_and_orders:cart_detail')

def merge_session_cart_to_db(request):
    if request.user.is_authenticated and 'cart' in request.session:
        session_cart = get_session_cart(request.session)
        if not session_cart.get('items'):
            if 'cart' in request.session:
                del request.session['cart']
            return

        db_cart, _ = Cart.objects.get_or_create(user=request.user)
        for item_key, details in session_cart['items'].items():
            try:
                parts = item_key.split('-')
                product_id = int(parts[0])
                variant_id = int(parts[1]) if len(parts) > 1 and parts[1] != 'None' else None

                product = Product.objects.get(id=product_id)
                variant = ProductVariant.objects.get(id=variant_id) if variant_id else None
                
                db_item, created = db_cart.items.get_or_create(
                    product=product,
                    variant=variant,
                    is_saved_for_later=False,
                    defaults={'quantity': details['quantity']}
                )
                if not created:
                    db_item.quantity += details['quantity']
                    db_item.save()

            except (Product.DoesNotExist, ProductVariant.DoesNotExist, ValueError, IndexError):
                continue
        
        del request.session['cart']
        messages.success(request, "سبد خرید شما با موفقیت به حساب کاربری‌تان منتقل شد.")

