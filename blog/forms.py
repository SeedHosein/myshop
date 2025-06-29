from django import forms
from django.core.exceptions import ValidationError
from .models import BlogComment

class BlogCommentForm(forms.ModelForm):
    class Meta:
        model = BlogComment
        fields = ['name', 'email', 'comment'] # Fields visible to the user
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام شما (اگر عضو نیستید)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل شما (اگر عضو نیستید, نمایش داده نمیشود)'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'دیدگاه خود را بنویسید...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # Allow passing the user to the form and store it
        super().__init__(*args, **kwargs)
        
        # If the user is authenticated, name and email can be pre-filled or hidden
        if self.user and self.user.is_authenticated:
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['name'].required = False
            self.fields['email'].required = False
        else:
            # For anonymous users, ensure name and email are required
            self.fields['name'].required = True
            self.fields['email'].required = True
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not (self.user and self.user.is_authenticated):
            if not name:
                raise ValidationError('نام برای کاربران مهمان الزامی است.')
        return name
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not (self.user and self.user.is_authenticated):
            if not email:
                raise ValidationError('ایمیل برای کاربران مهمان الزامی است.')
        return email
    
