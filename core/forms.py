from django import forms
from .models import Workout, ClassBooking, ClassSchedule, ContactMessage, Newsletter

class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ['name', 'duration', 'calories', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ClassBookingForm(forms.ModelForm):
    class Meta:
        model = ClassBooking
        fields = ['class_schedule', 'booking_date']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_schedule'].queryset = ClassSchedule.objects.all().select_related('gym_class')
        self.fields['class_schedule'].label_from_instance = lambda obj: f"{obj.gym_class.name} - {obj.day} at {obj.time}"

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['email']

