from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ai_assistant_view, name='ai_assistant'),
    path('chat/', views.ai_chat_api, name='ai_chat_api'),
    path('new/', views.new_conversation, name='new_conversation'),
    path('delete/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('status/', views.ai_status, name='ai_status'),
]
