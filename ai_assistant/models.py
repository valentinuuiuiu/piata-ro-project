from django.db import models
from django.contrib.auth.models import User


def get_default_user():
    return User.objects.first()

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=get_default_user)
    title = models.CharField(max_length=100, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    conversation = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    content = models.TextField(blank=True)  # New field for compatibility with views.py
    is_user = models.BooleanField(default=True)  # True for user message, False for AI
    role = models.CharField(max_length=20, default='user')  # New field for compatibility
    timestamp = models.DateTimeField(auto_now_add=True)
    mcp_tools_used = models.JSONField(default=list, blank=True)  # Store tools used

class AdminQueryLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sql_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField()
