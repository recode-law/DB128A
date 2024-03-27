from django import template

from helper.helper import is_member as raw_is_member

register = template.Library()


@register.filter(name='is_member')
def is_member(user, group_name) -> bool:
    return raw_is_member(user, group_name)
