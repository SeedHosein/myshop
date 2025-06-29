from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import BlogPost, BlogCategory, BlogComment

User = get_user_model()

class BlogCommentTestCase(TestCase):
    def setUp(self):
        # Create a user for authentication
        self.user = User.objects.create_user(
            email='test@example.com', 
            password='password123'
        )
        
        # Create a blog post to comment on
        self.post = BlogPost.objects.create(
            title='Test Post',
            slug='test-post',
            content='This is a test post.',
            is_published=True
        )
        
        self.comment_url = reverse('blog:add_blog_comment', kwargs={'post_slug': self.post.slug})

    def test_anonymous_user_can_post_comment(self):
        """
        Tests that an anonymous user can successfully post a comment with valid data.
        """
        comment_data = {
            'name': 'Guest User',
            'email': 'guest@example.com',
            'comment': 'This is a great post!'
        }
        response = self.client.post(self.comment_url, comment_data)
        
        # Check for a successful redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BlogComment.objects.count(), 1)
        
        # Verify the comment details
        comment = BlogComment.objects.first()
        self.assertEqual(comment.name, 'Guest User')
        self.assertEqual(comment.post, self.post)
        self.assertIsNone(comment.user)

    def test_anonymous_user_comment_fails_without_name(self):
        """
        Tests that an anonymous user's comment fails if the name is missing.
        """
        comment_data = {
            'email': 'guest@example.com',
            'comment': 'This comment should fail.'
        }
        response = self.client.post(self.comment_url, comment_data)
        self.assertEqual(response.status_code, 302) # It redirects back with an error message
        self.assertEqual(BlogComment.objects.count(), 0)

    def test_authenticated_user_can_post_comment(self):
        """
        Tests that a logged-in user can successfully post a comment without providing name/email.
        """
        self.client.login(email='test@example.com', password='password123')
        
        comment_data = {
            'comment': 'A comment from a logged-in user.'
        }
        response = self.client.post(self.comment_url, comment_data)
        
        # Check for a successful redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BlogComment.objects.count(), 1)
        
        # Verify the comment details
        comment = BlogComment.objects.first()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.name, self.user.email) # The view sets the name from email if full name is not available
        self.assertEqual(comment.email, self.user.email) # The view sets the email
        self.assertEqual(comment.comment, 'A comment from a logged-in user.')

    def test_comment_is_pending_approval_by_default(self):
        """
        Tests that a new comment has the 'pending' status by default.
        """
        comment_data = {
            'name': 'Guest User',
            'email': 'guest@example.com',
            'comment': 'This comment should be pending.'
        }
        self.client.post(self.comment_url, comment_data)
        
        comment = BlogComment.objects.first()
        self.assertEqual(comment.status, BlogComment.STATUS_PENDING)
