from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import django2wrap.views
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', django2wrap.views.homepage, name='homepage'),
    url(r'^chase/$', 'django2wrap.views.chase', {'run_update_before_chase': True}),
    url(r'^chased/$', 'django2wrap.views.chase'),
    url(r'^weekly/$', 'django2wrap.views.weekly'), #, {'run_update_before_chase': True}),
    url(r'^weekly_/$', 'django2wrap.views.weekly', {'run_update_before_chase': False}),
    url(r'^monthly/(?P<sfdc>\w+?)/$', 'django2wrap.views.monthly'),
    url(r'^case/(?P<number>\d+?)/(?P<sfdc>WLK|RSL)*$', django2wrap.views.update_case, name='1case'),
    url(r'^escalation/$', django2wrap.views.escalation_form, name='escalation form'),
    url(r'^license/$', django2wrap.views.license_form, name='license form'),
    url(r'^listen/$', django2wrap.views.listen, name='player'),
    url(r'^listen/(?P<callid>\d+?)/$', django2wrap.views.listen, name='player'),
    url(r'^listen/(?P<agent>\w+?)/(?P<file_name>.+?\.mp3)/$', django2wrap.views.listen, name='player'),
    url(r'^sync/', django2wrap.views.sync, name='sync'),
    # url(r'^dashboard/', django2wrap.views.dashboard, name='dashboard'),
    (r'^admin/', include(admin.site.urls)),
)

# from django.conf import settings

# if settings.DEBUG:
#     urlpatterns += patterns('',
#         (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
#         (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
#     )