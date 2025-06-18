from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden


def is_member(user, group_name) -> bool:
    try:
        group = Group.objects.get(name=group_name)
        return user.is_superuser or group in user.groups.all()
    except Group.DoesNotExist:
        return False


def group_required(group_name):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not is_member(request.user, group_name):
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator