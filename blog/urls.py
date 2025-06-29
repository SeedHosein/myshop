from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='post_list'),
    path('category/<str:category_slug>/', views.BlogListView.as_view(), name='post_list_by_category'),
    path('<str:slug>/', views.BlogDetailView.as_view(), name='post_detail'),
    path('<str:post_slug>/comment/', views.AddBlogCommentView.as_view(), name='add_blog_comment'),
]