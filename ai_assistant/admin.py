from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from .models import AdminQueryLog
import json

from marketplace.admin import admin_site

@admin.register(AdminQueryLog)
@admin.register(AdminQueryLog, site=admin_site)
class PiataAIAssistantAdmin(admin.ModelAdmin):
    list_display = ('user', 'sql_text', 'timestamp', 'duration')
    list_filter = ('user', 'timestamp')
    search_fields = ('sql_text', 'user__username')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('chat/', self.admin_site.admin_view(self.chat_view), name='piata_ai_assistant_chat'),
        ]
        return custom_urls + urls

    def chat_view(self, request):
        if request.method == 'POST':
            data = json.loads(request.body)
            query = data.get('query')
            user = request.user

            is_read_only = not user.is_superuser
            response = self.delegate_to_sql_agent(query, is_read_only)
            
            return JsonResponse(response)

        return render(request, 'admin/ai_assistant/piata_chat.html', {
            'title': 'Piata AI Assistant',
        })

    def delegate_to_sql_agent(self, query, is_read_only):
        try:
            with connection.cursor() as cursor:
                if is_read_only and not query.strip().upper().startswith('SELECT'):
                    return {'error': 'Only SELECT queries are allowed for your user level.'}

                cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    return {'columns': columns, 'rows': rows[:100]}
                else:
                    return {'message': 'Query executed successfully.'}
        except Exception as e:
            return {'error': str(e)}
