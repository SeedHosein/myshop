from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from products.models import Product
from .models import ProductReview
from .forms import ReviewForm

class AddReviewView(LoginRequiredMixin, View):
    template_name = 'reviews/add_review_form.html' # We'll need to create this template

    def dispatch(self, request, *args, **kwargs):
        returned = super().dispatch(request, *args, **kwargs)
        product = get_object_or_404(Product, slug=kwargs["product_slug"])
        # Check if user has already reviewed this product (optional, but good practice)
        existing_review = ProductReview.objects.filter(product=product, user=request.user).first()
        if existing_review:
            # Redirect or show message that they've already reviewed
            messages.error(request, "شما قبلا برای این محصول یک نظر ثبت کرده اید.")
            return redirect(reverse('products:product_detail', kwargs={'slug': kwargs["product_slug"]}))
        return returned
    
    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)

        form = ReviewForm()
        return render(request, self.template_name, {'form': form, 'product': product})

    def post(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            # Potentially set review status to pending if moderation is needed
            review.status = ProductReview.STATUS_PENDING
            review.save()
            # Add a success message (optional)
            messages.success(request, 'نظر شما ثبت شد. بعد از برسی پشتیبانی منتشر میشود.')
            return redirect(reverse('products:product_detail', kwargs={'slug': product_slug}))

        messages.error(request, "خطای غیر منتظره ای رخ داد. لطفا چند دقیقه دیگر دوباره تلاش کنید.")
        try:
            return redirect(reverse('products:product_detail', kwargs={'slug': product_slug}))
        except:
            return redirect(reverse('products:product_list'))
