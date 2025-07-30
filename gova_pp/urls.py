from django.urls import path
from . import views

app_name = 'gova_pp'

urlpatterns = [
    # Authentication
    path('login/', views.government_login, name='login'),
    path('logout/', views.government_logout, name='logout'),
    
    # Alerts URLs
    path('alerts/', views.alerts, name='alerts'),
    path('alerts/create/', views.create_alert, name='create_alert'),
    path('alerts/send/<int:alert_id>/', views.send_alert, name='send_alert'),
    path('alerts/delete/<int:alert_id>/', views.delete_alert, name='delete_alert'),
    path('reports/', views.reports, name='reports'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Messages
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    
    # Image Analysis
    path('analyze-image/<int:message_id>/', views.analyze_image, name='analyze_image'),
    
    # API endpoints
    path('api/receive-message/', views.receive_farmer_message, name='receive_farmer_message'),
]
