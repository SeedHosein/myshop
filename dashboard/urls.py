from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='dashboard_home'),

    # Discount URLs
    path('discounts/', views.DiscountListView.as_view(), name='discount_list'),
    path('discounts/add/', views.DiscountCreateUpdateView.as_view(), name='discount_add'),
    path('discounts/edit/<int:pk>/', views.DiscountCreateUpdateView.as_view(), name='discount_edit'),
    path('discounts/delete/<int:pk>/', views.DiscountDeleteView.as_view(), name='discount_delete'),

    # Campaign URLs
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/add/', views.CampaignCreateUpdateView.as_view(), name='campaign_add'),
    path('campaigns/edit/<int:pk>/', views.CampaignCreateUpdateView.as_view(), name='campaign_edit'),
    path('campaigns/delete/<int:pk>/', views.CampaignDeleteView.as_view(), name='campaign_delete'),

    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/add/', views.ProductCreateUpdateView.as_view(), name='product_add'),
    path('products/edit/<int:pk>/', views.ProductCreateUpdateView.as_view(), name='product_edit'),
    path('products/delete/<int:pk>/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateUpdateView.as_view(), name='category_add'),
    path('categories/edit/<int:pk>/', views.CategoryCreateUpdateView.as_view(), name='category_edit'),
    path('categories/delete/<int:pk>/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Blog Management URLs
    path('blog/', views.BlogListView.as_view(), name='blog_list'),
    path('blog/add/', views.BlogCreateUpdateView.as_view(), name='blog_add'),
    path('blog/edit/<int:pk>/', views.BlogCreateUpdateView.as_view(), name='blog_edit'),
    path('blog/delete/<int:pk>/', views.BlogDeleteView.as_view(), name='blog_delete'),

    # Blog Category Management URLs
    path('blog/categories/', views.BlogCategoryListView.as_view(), name='blog_category_list'),
    path('blog/categories/add/', views.BlogCategoryCreateUpdateView.as_view(), name='blog_category_add'),
    path('blog/categories/edit/<int:pk>/', views.BlogCategoryCreateUpdateView.as_view(), name='blog_category_edit'),
    path('blog/categories/delete/<int:pk>/', views.BlogCategoryDeleteView.as_view(), name='blog_category_delete'),

    # Blog Comment Management URLs
    path('blog/comments/', views.BlogCommentManagementView.as_view(), name='blog_comment_management'),
    path('blog/comments/update-status/', views.UpdateBlogCommentStatusView.as_view(), name='update_blog_comment_status'),

    # User Management URLs
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/edit/<int:pk>/', views.UserUpdateView.as_view(), name='user_edit'),

    # Product Review URLs
    path('reviews/', views.ProductReviewManagementView.as_view(), name='product_review_management'),
]