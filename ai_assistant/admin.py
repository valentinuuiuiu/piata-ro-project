from django.contrib import admin
from .models import (
    MCPServerConfig,
    ChatSessionLog,
    Conversation,
    Message,
    AdminQueryLog
)

class MCPServerConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'description')
    fields = ['name', 'url', 'description']

class ChatSessionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'started_at', 'status')
    fields = ['user', 'started_at', 'ended_at', 'status']
    readonly_fields = ('started_at',)

admin.site.register(MCPServerConfig, MCPServerConfigAdmin)
admin.site.register(ChatSessionLog, ChatSessionLogAdmin)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(AdminQueryLog)
