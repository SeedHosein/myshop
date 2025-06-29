from django import forms
# from django.utils.translation import gettext_lazy as _ # No longer needed

class AddToCartForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1, 
        initial=1, 
        label="تعداد", 
        widget=forms.NumberInput(attrs={'class': 'form-control quantity-input', 'style': 'max-width: 80px;'})
    )
    # You could add a field for product variants if you implement them later
    # variant_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None) # Allow passing the product instance
        super().__init__(*args, **kwargs)
        if self.product:
            self.fields['product_id'].initial = self.product.id
            # Potentially adjust max_value of quantity based on product.stock
            # self.fields['quantity'].widget.attrs['max'] = self.product.stock 
            # Note: server-side validation for stock is still crucial

class CheckoutForm(forms.Form):
    # These fields will be dynamically shown/hidden or pre-filled based on auth status and user profile
    # For guest checkout:
    email = forms.EmailField(label="آدرس ایمیل", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label="شماره تلفن همراه", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Shipping Address Fields (can be pre-filled from UserProfile if authenticated)
    first_name = forms.CharField(label="نام", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line_1 = forms.CharField(label="آدرس (خط ۱)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'خیابان، کوچه، پلاک، واحد'}))
    address_line_2 = forms.CharField(label="آدرس (خط ۲) (اختیاری)", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'جزئیات بیشتر مانند طبقه، واحد'}))
    city = forms.CharField(label="شهر", widget=forms.TextInput(attrs={'class': 'form-control'}))
    province = forms.CharField(label="استان", widget=forms.TextInput(attrs={'class': 'form-control'})) # Consider making this a ChoiceField later
    postal_code = forms.CharField(label="کد پستی", widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(label="کشور", initial="ایران", widget=forms.TextInput(attrs={'class': 'form-control'})) # Default or ChoiceField

    # Notes for the order
    notes = forms.CharField(label="یادداشت سفارش (اختیاری)", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'نکات مربوط به سفارش خود را اینجا بنویسید، مثلاً توضیحات خاص برای تحویل.'}))

    # Placeholder for payment method selection - to be implemented later
    # PAYMENT_CHOICES = [
    #     ('cod', _('Cash on Delivery')),
    #     ('online', _('Online Payment')),
    # ]
    # payment_method = forms.ChoiceField(label=_("Payment Method"), choices=PAYMENT_CHOICES, widget=forms.RadioSelect, initial='cod')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            # Pre-fill from UserProfile if available
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            # For email and phone, make them read-only or confirm
            self.fields['email'].initial = self.user.email
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['phone_number'].initial = self.user.phone_number
            self.fields['phone_number'].widget.attrs['readonly'] = True
            
            # If you have address fields directly on UserProfile or a linked Address model:
            if hasattr(self.user, 'address') and self.user.address: # Assuming UserProfile.address is a CharField
                self.fields['address_line_1'].initial = self.user.address
            if hasattr(self.user, 'city') and self.user.city:
                self.fields['city'].initial = self.user.city
            if hasattr(self.user, 'postal_code') and self.user.postal_code:
                self.fields['postal_code'].initial = self.user.postal_code
            # Add more pre-fills if your UserProfile has more granular address fields
        else:
            # For guests, email and phone are required for communication
            self.fields['email'].required = True
            self.fields['phone_number'].required = True

class DiscountApplyForm(forms.Form):
    code = forms.CharField(
        label="کد تخفیف", 
        max_length=50, 
        required=False, # Or True, depending on if you want to allow submitting an empty form to remove discount
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "کد تخفیف خود را وارد کنید"
        })
    ) 