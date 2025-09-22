"""
Chat Service for Piața.ro
Handles OpenRouter API integration and chat functionality
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

class OpenRouterChatService:
    """Service for handling OpenRouter API interactions"""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "openrouter/x-ai/grok-4-fast:free" # User's specified model
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', os.getenv('OPENROUTER_API_KEY'))
        self.model = getattr(settings, 'OPENROUTER_MODEL', os.getenv('OPENROUTER_MODEL', self.DEFAULT_MODEL))
        if not self.api_key:
            # Allow initialization without API key for scenarios like migrations
            logger.warning("OpenRouter API key not configured. Chat service will not function.")
            # raise ValueError("OpenRouter API key not configured") # Original line
    
    async def chat_completion_async(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int = 500, 
        temperature: float = 0.7
    ) -> ChatResponse:
        """Async chat completion using OpenRouter API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                # 'HTTP-Referer': 'https://yourdomain.com', # Optional: Add your site's URL
                # 'X-Title': 'Piața.ro Chat' # Optional: Add your site's name
            }
            payload = {
                'model': self.model,
                'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
                'max_tokens': max_tokens,
                'temperature': temperature
                # 'stream': False # Default, but can be enabled if supported
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # OpenRouter response structure might differ slightly from DeepSeek
                    # Ensure 'choices' and 'usage' are handled correctly
                    choice = result.get('choices', [{}])[0].get('message', {})
                    content = choice.get('content', '')
                    
                    return ChatResponse(
                        content=content,
                        model=result.get('model', self.model),
                        usage=result.get('usage', {}),
                        success=True
                    )
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_message = error_data.get('error', {}).get('message', 'Unknown API error')
                    if 'error' not in error_data: # Check if error is directly the message
                        error_message = str(error_data.get('error', error_data.get('message', 'Unknown API error')))

                    logger.error(f"OpenRouter API Error {response.status_code}: {error_message}")
                    return ChatResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"API Error {response.status_code}: {error_message}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"OpenRouter API request error: {e}")
            return ChatResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=f"Network error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"OpenRouter API general error: {e}")
            return ChatResponse(
                content="",
                model=self.model,
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
        
        'admin': '''You are an AI assistant for Piața.ro marketplace admin panel powered by OpenRouter.

You help administrators with:
- Database operations and queries
- Marketing optimization and advertising strategies
- Inventory management and stock tracking
- User management and analytics
- Platform maintenance and monitoring

Be professional, concise, and provide actionable insights based on the data and tools available.'''
    }
    
    def __init__(self):
        self.openrouter_service = OpenRouterChatService()
    
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
        return await self.openrouter_service.chat_completion_async(messages)
    
    async def admin_chat_async(self, message: str, context: Optional[str] = None) -> ChatResponse:
        """Handle admin chat requests"""
        messages = self.create_admin_chat_messages(message, context)
        return await self.openrouter_service.chat_completion_async(messages, temperature=0.3)
    
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
openrouter_service = OpenRouterChatService()
marketplace_chat_service = MarketplaceChatService()
