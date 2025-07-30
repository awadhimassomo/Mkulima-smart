from django import template

register = template.Library()

@register.filter
def get_activity_icon(activity_type):
    """
    Returns the appropriate Font Awesome icon class based on activity type.
    Uses Kikapu branding colors where appropriate.
    """
    icon_map = {
        'planting': 'fas fa-seedling text-kikapu-medium',
        'harvest': 'fas fa-harvest text-kikapu-tan',
        'irrigation': 'fas fa-tint text-blue-500',
        'fertilization': 'fas fa-pump-medical text-green-600',
        'pest_control': 'fas fa-bug text-red-500',
        'pruning': 'fas fa-cut text-gray-600',
        'weeding': 'fas fa-leaf text-green-700',
        'soil_testing': 'fas fa-flask text-amber-600',
        'livestock': 'fas fa-paw text-kikapu-tan',
        'veterinary': 'fas fa-syringe text-red-400',
        'market': 'fas fa-shopping-cart text-kikapu-medium',
        'training': 'fas fa-graduation-cap text-blue-600',
        'meeting': 'fas fa-users text-purple-500',
        'default': 'fas fa-calendar-check text-gray-500'
    }
    return icon_map.get(activity_type.lower(), icon_map['default'])

@register.filter
def format_activity_date(date_obj):
    """
    Formats the activity date in a user-friendly way.
    Example: "Today, 2:30 PM" or "Yesterday, 10:00 AM"
    """
    from django.utils import timezone
    from django.utils.timesince import timesince
    
    now = timezone.now()
    diff = now - date_obj
    
    if diff.days == 0 and now.date() == date_obj.date():
        return f"Today, {date_obj.strftime('%-I:%M %p')}"
    elif diff.days == 1 and now.date() == (date_obj.date() + timezone.timedelta(days=1)):
        return f"Yesterday, {date_obj.strftime('%-I:%M %p')}"
    elif diff.days < 7:
        return f"{timesince(date_obj).split(', ')[0]} ago"
    else:
        return date_obj.strftime("%b %d, %Y %-I:%M %p")
