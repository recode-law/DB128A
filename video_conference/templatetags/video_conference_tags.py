from django import template

register = template.Library()


@register.filter(name='create_video_conference_pagination_url')
def create_video_conference_pagination_url(request) -> str:
    url = '?page=1'
    if name := request.GET.get('name'):
        url += f'&name={name}'
    if court_state := request.GET.get('court_state'):
        url += f'&court_state={court_state}'
    if court_type := request.GET.get('court_type'):
        url += f'&court_type={court_type}'
    if online_service_possible := request.GET.get('online_service_possible'):
        url += f'&online_service_possible={online_service_possible}'
    if provides_online_service := request.GET.get('provides_online_service'):
        url += f'&provides_online_service={provides_online_service}'
    return url
