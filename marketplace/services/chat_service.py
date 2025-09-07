"""
Chat Service for Piața.ro
Handles DeepSeek API integration and chat functionality
"""

import os
import json
import httpx
from django.conf import settings
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Data class for chat messages"""
    role: str
    content: str

@dataclass
class ChatResponse:
    """Data class for chat responses"""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool = True
    error: Optional[str] = None

class DeepSeekChatService:
    """Service for handling DeepSeek API interactions"""
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL = "deepseek-chat"
    
    def __init__(self):
        # Prefer settings, then environment, then try to load from .env file if running in DEBUG
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', None) or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key and getattr(settings, 'DEBUG', False):
            try:
                # Attempt a minimal .env loader to avoid hard dependency on django-environ
                env_path = os.path.join(getattr(settings, 'BASE_DIR', ''), '.env')
                if os.path.exists(env_path):
                    for line in open(env_path, 'r'):
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k == 'DEEPSEEK_API_KEY' and v:
                            os.environ['DEEPSEEK_API_KEY'] = v
                            self.api_key = v
                            break
            except Exception as _e:
                logger.debug(f"Optional .env read failed: {_e}")
        if not self.api_key:
            # Log once but allow service object creation so pages render; calls will still fail fast
            logger.warning("DeepSeek API key not configured. Chat service will not function.")
    
    async def chat_completion_async(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int = 500, 
        temperature: float = 0.7
    ) -> ChatResponse:
        """Async chat completion using DeepSeek API"""
        # Fail fast if key is missing to return a clean error upstream
        if not self.api_key:
            return ChatResponse(
                content="",
                model=self.MODEL,
                usage={},
                success=False,
                error="DeepSeek API key not configured"
            )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.api_key}'
                    },
                    json={
                        'model': self.MODEL,
                        'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
                        'max_tokens': max_tokens,
                        'temperature': temperature
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return ChatResponse(
                        content=result['choices'][0]['message']['content'],
                        model=result['model'],
                        usage=result.get('usage', {}),
                        success=True
                    )
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    return ChatResponse(
                        content="",
                        model=self.MODEL,
                        usage={},
                        success=False,
                        error=f"API Error: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    )
                    
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return ChatResponse(
                content="",
                model=self.MODEL,
                usage={},
                success=False,
                error=str(e)
            )
    
    def chat_completion(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int = 500, 
        temperature: float = 0.7
    ) -> ChatResponse:
        """Sync wrapper for chat completion"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.chat_completion_async(messages, max_tokens, temperature)
        )

class MarketplaceChatService:
    """Service for marketplace-specific chat functionality"""
    
    SYSTEM_PROMPTS = {
        'user': '''Ești asistentul virtual pentru Piața.ro, cel mai mare marketplace din România. Răspunde DOAR în română și ajută utilizatorii cu informații despre platformă.

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

Fii concis, prietenos și ajută cu întrebări despre cumpărare, vânzare și folosirea platformei.''',
        
        'admin': '''You are an AI assistant for Piața.ro marketplace admin panel powered by DeepSeek.

You help administrators with:
- Database operations and queries
- Marketing optimization and advertising strategies
- Inventory management and stock tracking
- User management and analytics
- Platform maintenance and monitoring

Be professional, concise, and provide actionable insights based on the data and tools available.'''
    }
    
    def __init__(self):
        self.deepseek_service = DeepSeekChatService()
    
    def create_user_chat_messages(self, user_message: str) -> List[ChatMessage]:
        """Create messages for user-facing chat"""
        return [
            ChatMessage(role="system", content=self.SYSTEM_PROMPTS['user']),
            ChatMessage(role="user", content=user_message)
        ]
    
    def create_admin_chat_messages(self, user_message: str, context: Optional[str] = None) -> List[ChatMessage]:
        """Create messages for admin chat with optional context"""
        messages = [ChatMessage(role="system", content=self.SYSTEM_PROMPTS['admin'])]
        
        if context:
            messages.append(ChatMessage(role="system", content=f"Context: {context}"))
        
        messages.append(ChatMessage(role="user", content=user_message))
        return messages
    
    async def user_chat_async(self, message: str) -> ChatResponse:
        """Handle user chat requests"""
        messages = self.create_user_chat_messages(message)
        return await self.deepseek_service.chat_completion_async(messages)
    
    async def admin_chat_async(self, message: str, context: Optional[str] = None) -> ChatResponse:
        """Handle admin chat requests"""
        messages = self.create_admin_chat_messages(message, context)
        return await self.deepseek_service.chat_completion_async(messages, temperature=0.3)
    
    def user_chat(self, message: str) -> ChatResponse:
        """Sync wrapper for user chat"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.user_chat_async(message))
    
    def admin_chat(self, message: str, context: Optional[str] = None) -> ChatResponse:
        """Sync wrapper for admin chat"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.admin_chat_async(message, context))

# Global instances
deepseek_service = DeepSeekChatService()
marketplace_chat_service = MarketplaceChatService()
