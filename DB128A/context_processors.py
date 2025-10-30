from django.conf import settings


def context_info(request):
    match settings.DB128A_CONTEXT:
        case 'video_conference':
            return {
                'context_info': {
                    'template_root': 'video_conference/',
                    'default_description': 'Informieren Sie sich über die Möglichkeiten von Videoverhandlungen an allen deutschen Zivilgerichten.',
                    'default_keywords': 'Gericht, Videoverhandlung, Video, Verhandlung, 128a, Online, Onlineverhandlung, Bewertung, Feedback',
                    'default_title': 'Videoverhandlungen an deutschen Gerichten',
                    'pre_title': ' - Videoverhandlung.de',
                    'icon_path': '/static/video_conference/icons/'
                }
            }
        case 'ai_usage':
            return {
                'context_info': {
                    'template_root': 'ai_usage/',
                    'default_description': 'Informieren Sie sich über die Nutzung von KI an allen deutschen Zivilgerichten.',
                    'default_keywords': 'Gericht, KI, Nutzung, Bewertung, Feedback',
                    'default_title': 'KI Nutzung an deutschen Gerichten', 'pre_title': ' - KI-Verhandlung.de',
                    'icon_path': '/static/ai_usage/icons/'
                }
            }
    raise Exception('Invalid DB128A context')