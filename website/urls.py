from django.urls import path
from . import views

urlpatterns = [
    # Website URLs
    path('', views.HomeView.as_view(), name='home'),
    path('weather/', views.weather_view, name='weather'),
    path('dashboard-preview/', views.dashboard_preview, name='dashboard_preview'),
    path('register-farm/', views.register_farm, name='register_farm'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]