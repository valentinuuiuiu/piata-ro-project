
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

def contact_view(request):
    """View for displaying contact form"""
    try:
        return render(request, 'marketplace/contact.html')
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Error loading contact page: {str(e)}")
        return redirect('marketplace:home')

def handle_contact_form(request):
    """View for processing contact form submissions"""
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            message = request.POST.get('message')
            
            send_mail(
                f'Contact Form Submission from {name}',
                message,
                email,
                ['ionutbaltag3@gmail.com'],  # Updated email
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully! We'll contact you at our WhatsApp: 0040746856119")
        except Exception as e:
            messages.error(request, f"Error sending message: {str(e)}")
        
        return redirect('marketplace:contact')
    
    return redirect('marketplace:contact')
