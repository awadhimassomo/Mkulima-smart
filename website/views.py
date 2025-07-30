from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Create your views here.

class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any context data needed for the homepage
        context['current_year'] = timezone.now().year
        return context

def weather_view(request):
    # Weather view will be implemented with OpenWeatherMap API integration
    context = {
        'current_weather': None,  # Will be populated with API data
        'forecast': [],          # Will contain forecast data
    }
    return render(request, 'weather.html', context)

def dashboard_preview(request):
    from datetime import datetime, timedelta
    
    # Sample data for dashboard preview with proper dates for activities
    now = timezone.now()
    
    context = {
        'stats': {
            'total_farms': 1248,
            'active_users': 856,
            'crop_yield': '24.5T',
            'revenue': 'TSh 12.8M',
        },
        'recent_activities': [
            {'icon': 'planting', 'title': 'Planted maize in North Field', 'date': now - timedelta(hours=2)},
            {'icon': 'irrigation', 'title': 'Scheduled irrigation for tomorrow', 'date': now - timedelta(days=1)},
            {'icon': 'pest_control', 'title': 'Applied pest control in South Field', 'date': now - timedelta(days=2, hours=5)},
            {'icon': 'harvest', 'title': 'Harvested beans from West Field', 'date': now - timedelta(days=3)},
            {'icon': 'soil_testing', 'title': 'Completed soil testing in East Field', 'date': now - timedelta(weeks=1)},
        ],
        'market_prices': [
            ('Maize', 'TSh 1,200/kg'),
            ('Beans', 'TSh 3,500/kg'),
            ('Rice', 'TSh 2,800/kg'),
            ('Coffee', 'TSh 8,500/kg'),
            ('Cashew Nuts', 'TSh 6,200/kg'),
        ],
        'features': [
            {'icon': 'chart-line', 'title': 'Crop Analytics', 'description': 'Track your crop growth and health'},
            {'icon': 'calendar-alt', 'title': 'Farming Calendar', 'description': 'Plan your farming activities'},
            {'icon': 'shopping-cart', 'title': 'Market Prices', 'description': 'Latest prices for your produce'},
            {'icon': 'clipboard-list', 'title': 'Farm Records', 'description': 'Digital record keeping'},
        ]
    }
    return render(request, 'dashboard_preview.html', context)

def register_farm(request):
    if request.method == 'POST':
        # Process form submission
        # This will be implemented with form handling
        messages.success(request, 'Thank you for registering your farm! We will contact you soon.')
        return redirect('home')
    
    # For GET request, show the registration form
    regions = [
        'Arusha', 'Dar es Salaam', 'Dodoma', 'Geita', 'Iringa',
        'Kagera', 'Katavi', 'Kigoma', 'Kilimanjaro', 'Lindi',
        'Manyara', 'Mara', 'Mbeya', 'Mjini Magharibi', 'Morogoro',
        'Mtwara', 'Mwanza', 'Njombe', 'Pemba North', 'Pemba South',
        'Pwani', 'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu',
        'Singida', 'Songwe', 'Tabora', 'Tanga', 'Unguja North',
        'Unguja South'
    ]
    
    context = {
        'regions': sorted(regions),
        'farm_types': ['Crop Farming', 'Animal Husbandry', 'Mixed Farming', 'Horticulture', 'Aquaculture'],
    }
    return render(request, 'register_farm.html', context)

class ContactView(View):
    template_name = 'contact.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Save to database (to be implemented)
        # contact = ContactFormSubmission(
        #     name=name,
        #     email=email,
        #     phone=phone,
        #     subject=subject,
        #     message=message
        # )
        # contact.save()
        
        # Send email notification (configure email settings in settings.py)
        try:
            subject = f"New Contact Form Submission: {subject}"
            context = {
                'name': name,
                'email': email,
                'phone': phone,
                'subject': subject,
                'message': message,
            }
            html_message = render_to_string('emails/contact_form.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Send confirmation email to user
            user_subject = "Thank you for contacting Mkulima"
            user_context = {'name': name}
            user_html_message = render_to_string('emails/contact_confirmation.html', user_context)
            user_plain_message = strip_tags(user_html_message)
            
            send_mail(
                subject=user_subject,
                message=user_plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=user_html_message,
                fail_silently=True,
            )
            
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
        except Exception as e:
            messages.error(request, 'There was an error sending your message. Please try again later.')
            # Log the error for debugging
            print(f"Error sending contact form: {str(e)}")
        
        return redirect('contact')
