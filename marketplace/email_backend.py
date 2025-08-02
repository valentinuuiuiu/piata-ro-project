import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage
from typing import Iterable
import os


class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = os.getenv('RESEND_API_KEY')
        if self.api_key:
            resend.api_key = self.api_key

    def send_messages(self, email_messages: Iterable[EmailMessage]) -> int:
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        
        if not self.api_key:
            if not self.fail_silently:
                raise Exception("RESEND_API_KEY not configured")
            return 0

        sent_count = 0
        email_messages = list(email_messages)  # Convert to list for processing
        
        try:
            # Convert Django EmailMessage to Resend format
            resend_messages = []
            
            for email_message in email_messages:
                # Handle both string and list recipients
                to_addresses = []
                if isinstance(email_message.to, str):
                    to_addresses = [email_message.to]
                else:
                    to_addresses = list(email_message.to)
                
                # Create Resend email params
                params = {
                    "from": email_message.from_email,
                    "to": to_addresses,
                    "subject": email_message.subject,
                }
                
                # Add body content
                if email_message.body:
                    params["text"] = email_message.body
                
                # Add HTML content if available
                if hasattr(email_message, 'alternatives') and email_message.alternatives:
                    for content, content_type in email_message.alternatives:
                        if content_type == 'text/html':
                            params["html"] = content
                            break
                
                resend_messages.append(params)
            
            # Send emails
            if len(resend_messages) == 1:
                # Send single email
                resend.Emails.send(resend_messages[0])
                sent_count = 1
            else:
                # Send batch emails
                resend.Batch.send(resend_messages)
                sent_count = len(resend_messages)
                
        except Exception as e:
            if not self.fail_silently:
                raise
            # If we're failing silently, return 0 sent messages
            sent_count = 0
            
        return sent_count
