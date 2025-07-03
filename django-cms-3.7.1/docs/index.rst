.. raw:: html

    <style>
        .row {clear: both}
        .row h2  {border-bottom: 1px solid gray;}

        .column img {border: 1px solid gray;}

        @media only screen and (min-width: 1000px),
               only screen and (min-width: 500px) and (max-width: 768px){

            .column {
                padding-left: 5px;
                padding-right: 5px;
                float: left;
            }

            .column3  {
                width: 33.3%;
            }

            .column2  {
                width: 50%;
            }
        }
    </style>


########################
django CMS documentation
########################

.. image:: /images/django-cms-logo.png
   :alt: django CMS logo

********
Overview
********

django CMS is a modern web publishing platform built with `Django`_, the web application framework "for
perfectionists with deadlines".

django CMS offers out-of-the-box support for the common features you'd expect
from a CMS, but can also be easily customised and extended by developers to
create a site that is tailored to their precise needs.


.. rst-class:: clearfix row

.. rst-class:: column column2

:ref:`tutorials` - start here
=============================

For the new django CMS developer, from installation to creating your own addon applications.

.. rst-class:: column column2

:ref:`how-to`
=============

Practical step-by-step guides for the more experienced developer, covering several important topics.

.. rst-class:: column column2

:ref:`key-topics`
=================

Explanation and analysis of some key concepts in django CMS.

.. rst-class:: column column2

:ref:`reference`
================

Technical reference material, for classes, methods, APIs, commands.



.. rst-class:: clearfix row

**************
Join us online
**************

django CMS is supported by a friendly and very knowledgeable community.

.. rst-class:: column column3

Our IRC channel, #django-cms, is on ``irc.freenode.net``. If you don't have an IRC client, you can
`join our IRC channel using the KiwiIRC web client
<https://kiwiirc.com/client/irc.freenode.net/django-cms>`_, which works pretty well.

.. rst-class:: column column3

Our `django CMS users email list <https://groups.google.com/forum/#!forum/django-cms>`_ is for
**general discussions** and the `django CMS developers email list
<https://groups.google.com/forum/#!forum/django-cms-developers>`_ for the
**development of django CMS**.

.. rst-class:: column column3

Our `StackOverflow <https://stackoverflow.com/questions/tagged/django-cms>`_ is for
**questions** around django CMS and it's plugin ecosystem.


***************
Why django CMS?
***************

django CMS is a well-tested CMS platform that powers sites both large and
small. Here are a few of the key features:

* robust internationalisation (i18n) support for creating multilingual sites
* front-end editing, providing rapid access to the content management interface
* support for a variety of editors with advanced text editing features.
* a flexible plugins system that lets developers put powerful tools at the
  fingertips of editors, without overwhelming them with a difficult interface

* ...and much more

There are other capable Django-based CMS platforms but here's why you should
consider django CMS:

* thorough documentation
* easy and comprehensive integration into existing projects - django CMS isn't a monolithic application
* a healthy, active and supportive developer community
* a strong culture of good code, including an emphasis on automated testing


.. _requirements:

***********************************************
Software version requirements and release notes
***********************************************

This document refers to version |release|.


Django/Python compatibility table
=================================

*LTS* in the table indicates a combination of Django and django CMS both covered
by a long-term support policy.

===========  === === === === === === ===  = === === === ==== ==== === === ======= =======
django CMS   Python                         Django
-----------  ---------------------------  - ---------------------------------------------
\            3.7 3.6 3.5 3.4 3.3 2.7 2.6    2.2 2.1 2.0 1.11 1.10 1.9 1.8 1.6/1.7 1.4/1.5
===========  === === === === === === ===  = === === === ==== ==== === === ======= =======
3.7.x        ✓   ✓   ✓   ✓   ✓   ✓   ⨯      LTS ✓   ✓   LTS  ⨯    ⨯   ⨯   ⨯       ⨯
3.6.x        ✓   ✓   ✓   ✓   ✓   ✓   ⨯      ✓   ✓   ✓   ✓    ⨯    ⨯   ⨯   ⨯       ⨯
3.5.x        ✓   ✓   ✓   ✓   ✓   ✓   ⨯      ⨯   ⨯   ⨯   ✓    ✓    ✓   ✓   ⨯       ⨯
3.4.5        ⨯   ✓   ✓   ✓   ✓   ✓   ⨯      ⨯   ⨯   ⨯   LTS  ✓    ✓   LTS ⨯       ⨯
3.4.2-3.4.4  ⨯   ⨯   ✓   ✓   ✓   ✓   ⨯      ⨯   ⨯   ⨯   ⨯    ✓    ✓   ✓   ⨯       ⨯
3.4.1        ⨯   ⨯   ✓   ✓   ✓   ✓   ⨯      ⨯   ⨯   ⨯   ⨯    ⨯    ✓   ✓   ⨯       ⨯
3.3.x        ⨯   ⨯   ✓   ✓   ✓   ✓   ⨯      ⨯   ⨯   ⨯   ⨯    ⨯    ✓   ✓   ⨯       ⨯
3.2.1-3.2.5  ⨯   ⨯   ✓   ✓   ✓   ✓   ✓      ⨯   ⨯   ⨯   ⨯    ⨯    ✓   ✓   ✓       ⨯
3.2.0        ⨯   ⨯   ⨯   ✓   ✓   ✓   ✓      ⨯   ⨯   ⨯   ⨯    ⨯    ⨯   ✓   ✓       ⨯
3.1.7        ⨯   ⨯   ⨯   ✓   ✓   ✓   ✓      ⨯   ⨯   ⨯   ⨯    ⨯    ⨯   ✓   ✓       ⨯
3.0.18       ⨯   ⨯   ⨯   ✓   ✓   ✓   ✓      ⨯   ⨯   ⨯   ⨯    ⨯    ⨯   ⨯   ✓       ✓
===========  === === === === === === ===  = === === === ==== ==== === === ======= =======



.. _Python: https://www.python.org
.. _Django: https://www.djangoproject.com


See the repository's ``setup.py`` for more specific details of dependencies, or the :ref:`release-notes` for
information about what is required or has changed in particular versions of the CMS.

The :ref:`installation how-to guide <installation>` provides an overview of other packages required in a django CMS
project.


.. toctree::
    :maxdepth: 2
    :hidden:

    introduction/index
    how_to/index
    topics/index
    reference/index
    contributing/index
    upgrade/index
    user/index
