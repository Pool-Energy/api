import os
import yaml


def custom_settings():
    django_settings = os.environ.get('DJANGO_SETTINGS_FILE')
    if django_settings and os.path.exists(django_settings):
        with open(django_settings, 'r') as f:
            django_settings = yaml.safe_load(f)
    django_settings = django_settings or {}
    return django_settings

def drf_version(result, generator, request, public):
    result['info']['version'] = 'v1.0'
    result.pop('x-version', None)
    return result

def drf_servers(result, generator, request, public):
    if request is not None:
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        result['servers'] = [
            {
                'url': f'{scheme}://{host}/api/v1.0',
                'description': 'High-Level REST API'
            }
        ]
    return result
