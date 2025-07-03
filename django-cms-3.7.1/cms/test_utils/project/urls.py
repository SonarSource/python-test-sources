
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.views import LoginView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve
from django.views.i18n import JavaScriptCatalog

from cms.utils.conf import get_cms_setting
from cms.test_utils.project.sampleapp.forms import LoginForm, LoginForm2, LoginForm3
from cms.test_utils.project.placeholderapp.views import example_view, latest_view
from cms.test_utils.project.sampleapp.views import plain_view

admin.autodiscover()

urlpatterns = [
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^media/cms/(?P<path>.*)$', serve,
        {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    url(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
]

urlpatterns += staticfiles_urlpatterns()


urlpatterns += i18n_patterns(
    url(r'^sample/login_other/$', LoginView.as_view(),
        kwargs={'authentication_form': LoginForm2}),
    url(r'^sample/login/$', LoginView.as_view(),
        kwargs={'authentication_form': LoginForm}),
    url(r'^sample/login3/$', LoginView.as_view(),
        kwargs={'authentication_form': LoginForm3}),
    url(r'^admin/', admin.site.urls),
    url(r'^example/$', example_view),
    url(r'^example/latest/$', latest_view),
    url(r'^plain_view/$', plain_view),
    url(r'^', include('cms.urls')),
)
