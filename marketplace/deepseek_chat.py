import os
import json
import httpx
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

@csrf_exempt
@require_http_methods(["POST"])
def deepseek_chat_view(request):
    """Handle DeepSeek API calls for user chatbot"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get API key from environment or settings
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', os.getenv('DEEPSEEK_API_KEY'))
        if not api_key:
            return JsonResponse({'error': 'API key not configured'}, status=500)
        
        # Call DeepSeek API
        import asyncio
        
        async def make_api_call():
            async with httpx.AsyncClient() as client:
                return await client.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {
                            'role': 'system',
                            'content': '''Ești asistentul virtual pentru Piața.ro, cel mai mare marketplace din România. Răspunde DOAR în română și ajută utilizatorii cu informații despre platformă.

Informații despre Piața.ro:
- Marketplace românesc pentru anunțuri gratuite
- Categorii: Auto, Imobiliare, Electronice, Modă, Casa & Grădina, Sport, Servicii
- Utilizatorii pot posta anunțuri gratuit
- Sistem de promovare cu credite pentru vizibilitate
- Mesagerie integrată între cumpărători și vânzători
- Sistem de favorite pentru anunțuri
- Verificare anunțuri pentru siguranță

Cum să folosești platforma:
1. Înregistrează-te gratuit
2. Postează anunțuri cu poze și descriere detaliată
3. Răspunde la mesaje rapid
4. Folosește filtrele pentru căutare
5. Promovează anunțurile importante cu credite

Siguranță:
- Nu da niciodată bani în avans
- Întâlnește-te în locuri publice
- Verifică produsul înainte de plată
- Raportează anunțuri suspecte

Fii concis, prietenos și ajută cu întrebări despre cumpărare, vânzare și folosirea platformei.'''
                        },
                        {
                            'role': 'user',
                            'content': user_message
                        }
                    ],
                    'max_tokens': 500,
                    'temperature': 0.7
                },
                    timeout=30.0
                )
        
        response = asyncio.run(make_api_call())
        
        if response.status_code == 200:
            result = response.json()
            return JsonResponse({
                'response': result['choices'][0]['message']['content']
            })
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return JsonResponse({
                'error': f"API Error: {error_data.get('error', {}).get('message', 'Unknown error')}"
            }, status=500)
                
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)