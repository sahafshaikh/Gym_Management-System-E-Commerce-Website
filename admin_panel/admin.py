from django.contrib import admin
from .models import AdminPanelActivity, AdminNotification

@admin.register(AdminPanelActivity)
class AdminPanelActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_affected', 'object_id', 'timestamp')
    list_filter = ('user', 'action', 'model_affected', 'timestamp')
    search_fields = ('user__username', 'action', 'model_affected', 'details')
    readonly_fields = ('user', 'action', 'model_affected', 'object_id', 'details', 'ip_address', 'timestamp')

@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message')

