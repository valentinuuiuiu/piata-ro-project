
"""
Tests for the AI Assistant module
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Conversation, Message
from .validators import InputValidator
import json


class InputValidatorTests(TestCase):
    """Test input validation functionality"""
    
    def test_valid_message(self):
        """Test validation of a normal message"""
        result = InputValidator.validate_message("Hello, how are you?")
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['sanitized'], "Hello, how are you?")
    
    def test_empty_message(self):
        """Test validation of empty message"""
        result = InputValidator.validate_message("")
        self.assertFalse(result['valid'])
        self.assertIn("Message cannot be empty", result['errors'])
    
    def test_sql_injection_detection(self):
        """Test SQL injection detection"""
        malicious_input = "SELECT * FROM users WHERE 1=1"
        result = InputValidator.validate_message(malicious_input)
        self.assertFalse(result['valid'])
        self.assertIn("Potentially malicious SQL detected", result['errors'])
    
    def test_xss_detection(self):
        """Test XSS detection"""
        malicious_input = "<script>alert('xss')</script>"
        result = InputValidator.validate_message(malicious_input)
        self.assertFalse(result['valid'])
        self.assertIn("Potentially malicious content detected", result['errors'])
    
    def test_message_sanitization(self):
        """Test message sanitization"""
        dirty_input = "Hello\x00\x01\x02World"
        result = InputValidator.validate_message(dirty_input)
        self.assertTrue(result['valid'])
        self.assertEqual(result['sanitized'], "HelloWorld")
    
    def test_conversation_title_validation(self):
        """Test conversation title validation"""
        # Valid title
        result = InputValidator.validate_conversation_title("My Conversation")
        self.assertTrue(result['valid'])
        
        # Empty title
        result = InputValidator.validate_conversation_title("")
        self.assertFalse(result['valid'])
        self.assertIn("Title cannot be empty", result['errors'])
        
        # Too long title
        long_title = "a" * 101
        result = InputValidator.validate_conversation_title(long_title)
        self.assertFalse(result['valid'])
        self.assertIn("Title too long (max 100 characters)", result['errors'])
    
    def test_api_key_validation(self):
        """Test API key format validation"""
        # Valid DeepSeek key format
        self.assertTrue(InputValidator.validate_api_key("sk-1234567890abcdef"))
        
        # Invalid formats
        self.assertFalse(InputValidator.validate_api_key(""))
        self.assertFalse(InputValidator.validate_api_key("invalid-key"))
        self.assertFalse(InputValidator.validate_api_key("sk_no_dashes"))


class ConversationTests(TestCase):
    """Test conversation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_conversation(self):
        """Test creating a new conversation"""
        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation"
        )
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNotNone(conversation.updated_at)
    
    def test_create_message(self):
        """Test creating messages"""
        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation"
        )
        
        # User message
        user_msg = Message.objects.create(
            conversation=conversation,
            role='user',
            content="Hello",
            text="Hello",
            is_user=True
        )
        
        # Assistant message
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content="Hi there!",
            text="Hi there!",
            is_user=False
        )
        
        self.assertEqual(user_msg.conversation, conversation)
        self.assertEqual(assistant_msg.conversation, conversation)
        self.assertEqual(conversation.messages.count(), 2)


class ChatAPITests(TestCase):
    """Test the chat API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True  # Required for admin access
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_chat_api_get_method_not_allowed(self):
        """Test that GET method is not allowed"""
        response = self.client.get(reverse('ai_assistant:ai_chat_api'))
        self.assertEqual(response.status_code, 405)
    
    def test_chat_api_unauthenticated(self):
        """Test unauthenticated access"""
        self.client.logout()
        response = self.client.post(
            reverse('ai_assistant:ai_chat_api'),
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_chat_api_valid_message(self):
        """Test sending a valid message"""
        response = self.client.post(
            reverse('ai_assistant:ai_chat_api'),
            data=json.dumps({'message': 'Hello, how are you?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('response', data)
        self.assertIn('conversation_id', data)
    
    def test_chat_api_empty_message(self):
        """Test sending an empty message"""
        response = self.client.post(
            reverse('ai_assistant:ai_chat_api'),
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_chat_api_malicious_input(self):
        """Test handling of malicious input"""
        response = self.client.post(
            reverse('ai_assistant:ai_chat_api'),
            data=json.dumps({'message': '<script>alert("xss")</script>'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_chat_api_with_conversation(self):
        """Test chat with existing conversation"""
        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation"
        )
        
        response = self.client.post(
            reverse('ai_assistant:ai_chat_api'),
            data=json.dumps({
                'message': 'Hello',
                'conversation_id': conversation.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['conversation_id'], conversation.id)
