# -*- coding: utf-8 -*-

from cms.signals.apphook import debug_server_restart, trigger_server_restart
from cms.signals.permissions import post_save_user, post_save_user_group, pre_save_user, pre_delete_user, pre_save_group, pre_delete_group, pre_save_pagepermission, pre_delete_pagepermission, pre_save_globalpagepermission, pre_delete_globalpagepermission
from cms.utils.conf import get_cms_setting

from django.db.models import signals
from django.dispatch import Signal

from cms.models import PagePermission, GlobalPagePermission, PageUser, PageUserGroup
from django.conf import settings
from django.contrib.auth.models import User, Group

#################### Our own signals ###################

# fired after page location is changed - is moved from one node to other
page_moved = Signal(providing_args=["instance"])

# fired after page gets published - copied to public model - there may be more
# than one instances published before this signal gets called
post_publish = Signal(providing_args=["instance", "language"])
post_unpublish = Signal(providing_args=["instance", "language"])

# fired if a public page with an apphook is added or changed
urls_need_reloading = Signal(providing_args=[])

# *disclaimer*
# The generic object operation signals are very likely to change
# as their usage evolves.
# As a result, rely on these at your own risk
pre_obj_operation = Signal(
    providing_args=[
        "operation",
        "request",
        "token",
        "obj",
    ]
)

post_obj_operation = Signal(
    providing_args=[
        "operation",
        "request",
        "token",
        "obj",
    ]
)

pre_placeholder_operation = Signal(
    providing_args=[
        "operation",
        "request",
        "language",
        "token",
        "origin",
    ]
)

post_placeholder_operation = Signal(
    providing_args=[
        "operation",
        "request",
        "language",
        "token",
        "origin",
    ]
)


################### apphook reloading ###################

if settings.DEBUG:
    urls_need_reloading.connect(debug_server_restart)


urls_need_reloading.connect(
    trigger_server_restart,
    dispatch_uid='aldryn-apphook-reload-handle-urls-need-reloading'
)

###################### permissions #######################

if get_cms_setting('PERMISSION'):
    # only if permissions are in use
    signals.pre_save.connect(pre_save_user, sender=User, dispatch_uid='cms_pre_save_user')
    signals.post_save.connect(post_save_user, sender=User, dispatch_uid='cms_post_save_user')
    signals.pre_delete.connect(pre_delete_user, sender=User, dispatch_uid='cms_pre_delete_user')

    signals.pre_save.connect(pre_save_user, sender=PageUser, dispatch_uid='cms_pre_save_pageuser')
    signals.pre_delete.connect(pre_delete_user, sender=PageUser, dispatch_uid='cms_pre_delete_pageuser')

    signals.pre_save.connect(pre_save_group, sender=Group, dispatch_uid='cms_pre_save_group')
    signals.post_save.connect(post_save_user_group, sender=Group, dispatch_uid='cms_post_save_group')
    signals.pre_delete.connect(pre_delete_group, sender=Group, dispatch_uid='cms_post_save_group')

    signals.pre_save.connect(pre_save_group, sender=PageUserGroup, dispatch_uid='cms_pre_save_pageusergroup')
    signals.pre_delete.connect(pre_delete_group, sender=PageUserGroup, dispatch_uid='cms_pre_delete_pageusergroup')

    signals.pre_save.connect(pre_save_pagepermission, sender=PagePermission, dispatch_uid='cms_pre_save_pagepermission')
    signals.pre_delete.connect(pre_delete_pagepermission, sender=PagePermission,
                               dispatch_uid='cms_pre_delete_pagepermission')

    signals.pre_save.connect(pre_save_globalpagepermission, sender=GlobalPagePermission,
                             dispatch_uid='cms_pre_save_globalpagepermission')
    signals.pre_delete.connect(pre_delete_globalpagepermission, sender=GlobalPagePermission,
                               dispatch_uid='cms_pre_delete_globalpagepermission')
