from django.db import models
from django.contrib.auth.models import User


def get_default_user():
    return User.objects.first()

class MCPServerConfig(models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChatSessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='open')

    def __str__(self):
        return f"Session {self.id} - {self.user.username}"

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=get_default_user)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    conversation = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    is_user = models.BooleanField(default=True)  # True for user message, False for AI
    timestamp = models.DateTimeField(auto_now_add=True)

class AdminQueryLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sql_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField()
