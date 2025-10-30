from django import template

register = template.Library()


@register.filter(name='create_ai_usage_pagination_url')
def create_ai_usage_pagination_url(request) -> str:
    url = '?page=1'
    if name := request.GET.get('name'):
        url += f'&name={name}'
    if court_state := request.GET.get('court_state'):
        url += f'&court_state={court_state}'
    if court_type := request.GET.get('court_type'):
        url += f'&court_type={court_type}'
    if ai_information := request.GET.get('ai_information'):
        url += f'&ai_information={ai_information}'
    return url
