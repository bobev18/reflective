import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django2wrap.settings'

from django2wrap import views
from django.http import HttpRequest
request = HttpRequest()
request.method = 'POST'
request.POST = {'sendit': None}
# print('request', request)
x = views.chase(request, run_update_before_chase = True)
# html = x._container[0]
# print(html.count('#FF0000'))
# print('----')
# print(html)