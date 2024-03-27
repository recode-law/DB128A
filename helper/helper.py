from django.contrib.auth.models import Group


def is_member(user, group_name) -> bool:
    try:
        group = Group.objects.get(name=group_name)
        return user.is_superuser or group in user.groups.all()
    except Group.DoesNotExist:
        return False
