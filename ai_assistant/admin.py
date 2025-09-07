from django.contrib import admin
from .models import (
    MCPServerConfig,
    ChatSessionLog,
    Conversation,
    Message,
    AdminQueryLog
)
from .views import AIAssistantAdmin

class MCPServerConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'description')
    fields = ['name', 'url', 'description']

class ChatSessionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'started_at', 'status')
    fields = ['user', 'started_at', 'ended_at', 'status']
    readonly_fields = ('started_at',)

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'id')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'is_user', 'timestamp')
    list_filter = ('is_user', 'timestamp')
    search_fields = ('text',)
    ordering = ('-timestamp',)

# Register model admins
admin.site.register(MCPServerConfig, MCPServerConfigAdmin)
admin.site.register(ChatSessionLog, ChatSessionLogAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(AdminQueryLog)

# Register the AI Assistant admin interface
admin.site.register([], AIAssistantAdmin)
