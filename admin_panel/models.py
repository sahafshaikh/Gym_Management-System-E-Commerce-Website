from django.db import models
from django.contrib.auth.models import User

class AdminPanelActivity(models.Model):
    """
    Model to track admin panel activities for audit purposes
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    model_affected = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
    
    class Meta:
        verbose_name = "Admin Panel Activity"
        verbose_name_plural = "Admin Panel Activities"
        ordering = ['-timestamp']

class AdminNotification(models.Model):
    """
    Model for admin notifications
    """
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

