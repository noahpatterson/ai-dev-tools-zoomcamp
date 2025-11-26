from django import forms
from .models import Todo

class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['title', 'description', 'completed', 'due_date', 'category']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
