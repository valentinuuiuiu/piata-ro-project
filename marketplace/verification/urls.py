


from django.urls import path
from .views import *

urlpatterns = [
    path('start/', views.start_verification, name='start-verification'),
    path('status/', views.verification_status, name='verification-status'),
]


