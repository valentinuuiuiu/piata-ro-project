from django.db import models
from django.contrib.auth.models import User


def get_default_user():
    return User.objects.first()

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
