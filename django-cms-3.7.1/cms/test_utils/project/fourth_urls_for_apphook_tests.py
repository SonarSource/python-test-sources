from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from cms.utils.conf import get_cms_setting
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^media/cms/(?P<path>.*)$', serve,
        {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    url(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
]

urlpatterns += i18n_patterns(
    url(r'^', include('cms.test_utils.project.fourth_cms_urls_for_apphook_tests')),
)
