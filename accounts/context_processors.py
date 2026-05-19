from .models import Message, Notification


def portal_context(request):
    if request.user.is_authenticated:
        unread = Message.objects.filter(recipient=request.user, is_read=False).count()
        alerts = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_messages': unread, 'unread_notifications': alerts}
    return {'unread_messages': 0, 'unread_notifications': 0}
