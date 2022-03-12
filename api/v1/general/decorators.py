import json

# from django.contrib.auth.decorators import user_passes_test
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from general.models import Mode


def check_mode(function):
    def wrap(request, *args, **kwargs):
        mode, created = Mode.objects.get_or_create(id=1)
        readonly = mode.readonly
        maintenance = mode.maintenance
        down = mode.down

        if down:
            if request.is_ajax():
                response_data = {}
                response_data['status'] = 'false'
                response_data['message'] = "Application currently down. Please try again later."
                response_data['static_message'] = "true"
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                return HttpResponseRedirect(reverse('api_v1_general:down'))
        elif readonly:
            if request.is_ajax():
                response_data = {}
                response_data['status'] = 'false'
                response_data['message'] = "Application now readonly mode. please try again later."
                response_data['static_message'] = "true"
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                return HttpResponseRedirect(reverse('api_v1_general:read_only'))

        return function(request, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap