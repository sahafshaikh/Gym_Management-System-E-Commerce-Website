from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile', 'gender', 'dob')
    search_fields = ('user__username', 'user__email', 'mobile')
    list_filter = ('gender',)

