# -*- coding: utf-8 -*-

import importlib

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

from cms.utils.conf import get_cms_setting


def get_request_ip_resolver():
    """
    This is the recommended method for obtaining the specified
    CMS_REQUEST_IP_RESOLVER as it also does some basic import validation.

    Returns the resolver or raises an ImproperlyConfigured exception.
    """
    module, attribute = get_cms_setting('REQUEST_IP_RESOLVER').rsplit('.', 1)
    try:
        ip_resolver_module = importlib.import_module(module)
        ip_resolver = getattr(ip_resolver_module, attribute)
    except ImportError:
        raise ImproperlyConfigured(
            _('Unable to find the specified CMS_REQUEST_IP_RESOLVER module: '
              '"{0}".').format(module))
    except AttributeError:
        raise ImproperlyConfigured(
            _('Unable to find the specified CMS_REQUEST_IP_RESOLVER function: '
              '"{0}" in module "{1}".').format(attribute, module))
    return ip_resolver


def default_request_ip_resolver(request):
    """
    This is a hybrid request IP resolver that attempts should address most
    cases. Order is important here. A 'REAL_IP' header supersedes an
    'X_FORWARDED_FOR' header which supersedes a 'REMOTE_ADDR' header.
    """
    return (
        real_ip(request) or
        x_forwarded_ip(request) or
        remote_addr_ip(request)
    )


def real_ip(request):
    """
    Returns the IP Address contained in the HTTP_X_REAL_IP headers, if
    present. Otherwise, `None`.

    Should handle Nginx and some other WSGI servers.
    """
    return request.META.get('HTTP_X_REAL_IP')


def remote_addr_ip(request):
    """
    Returns the IP Address contained in the 'REMOTE_ADDR' header, if
    present. Otherwise, `None`.

    Should be suitable for local-development servers and some HTTP servers.
    """
    return request.META.get('REMOTE_ADDR')


def x_forwarded_ip(request):
    """
    Returns the IP Address contained in the 'HTTP_X_FORWARDED_FOR' header, if
    present. Otherwise, `None`.

    Should handle properly configured proxy servers.
    """
    ip_address_list = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address_list:
        ip_address_list = ip_address_list.split(',')
        return ip_address_list[0]
