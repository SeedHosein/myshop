from django import forms
from .models import ProductReview

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
        }
        labels = {
            'rating': 'امتیاز شما (از ۱ تا ۵)',
            'comment': 'نظر شما',
        }
        help_texts = {
            'comment': 'لطفاً نظر خود را در مورد این محصول بنویسید.',
        }
        error_messages = {
            'rating': {
                'required': 'لطفاً یک امتیاز انتخاب کنید.',
            },
            'comment': {
                'required': 'لطفاً نظر خود را وارد کنید.',
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].required = True
        self.fields['comment'].required = True
