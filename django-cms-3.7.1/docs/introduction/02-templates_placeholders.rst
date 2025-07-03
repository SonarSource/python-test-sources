########################
Templates & Placeholders
########################

In this tutorial we'll introduce Placeholders, and we're also going to show how
you can make your own HTML templates CMS-ready.


*********
Templates
*********

You can use HTML templates to customise the look of your website, define
Placeholders to mark sections for managed content and use special tags to
generate menus and more.

You can define multiple templates, with different layouts or built-in
components, and choose them for each page as required. A page's template
can be switched for another at any time.

You'll find the site's templates in ``mysite/templates``.

By default, pages in your site will use the ``fullwidth.html`` template, the first one listed in
the project's ``settings.py`` ``CMS_TEMPLATES`` tuple:

..  code-block:: python
    :emphasize-lines: 3

    CMS_TEMPLATES = (
        ## Customize this
        ('fullwidth.html', 'Fullwidth'),
        ('sidebar_left.html', 'Sidebar Left'),
        ('sidebar_right.html', 'Sidebar Right')
    )


************
Placeholders
************

Placeholders are an easy way to define sections in an HTML template that will
be filled with content from the database when the page is rendered. This
content is edited using django CMS's frontend editing mechanism, using Django
template tags.

``fullwidth.html`` contains a single placeholder, ``{% placeholder "content" %}``.

You'll also see ``{% load cms_tags %}`` in that file - ``cms_tags`` is the
required template tag library.

If you're not already familiar with Django template tags, you can find out more in the `Django documentation
<https://docs.djangoproject.com/en/dev/topics/templates/>`_.

Add a couple of new placeholders to ``fullwidth.html``, ``{% placeholder "feature" %}`` and ``{%
placeholder "splashbox" %}`` inside the ``{% block content %}`` section. For example:

.. code-block:: html+django
   :emphasize-lines: 2,4

    {% block content %}
        {% placeholder "feature" %}
        {% placeholder "content" %}
        {% placeholder "splashbox" %}
    {% endblock content %}

If you switch to *Structure* mode, you'll see the new placeholders available for use.

.. image:: /introduction/images/new-placeholder.png
   :alt: the new 'splashbox' placeholder
   :align: center


*******************
Static Placeholders
*******************

The content of the placeholders we've encountered so far is different for
every page. Sometimes though you'll want to have a section on your website
which should be the same on every single page, such as a footer block.

You *could* hard-code your footer into the template, but it would be nicer to be
able to manage it through the CMS. This is what **static placeholders** are for.

Static placeholders are an easy way to display the same content on multiple
locations on your website. Static placeholders act almost like normal
placeholders, except for the fact that once a static placeholder is created and
you added content to it, it will be saved globally. Even when you remove the
static placeholders from a template, you can reuse them later.

So let's add a footer to all our pages. Since we want our footer on every
single page, we should add it to our **base template**
(``mysite/templates/base.html``). Place it near the end of the HTML ``<body>`` element:

.. code-block:: html+django
   :emphasize-lines: 1-3

        <footer>
          {% static_placeholder 'footer' %}
        </footer>


        {% render_block "js" %}
    </body>

Save the template and return to your browser. Refresh any page in Structure mode, and you'll
see the new static placeholder.

.. image:: /introduction/images/static-placeholder.png
   :alt: a static placeholder
   :align: center

..  note::

    To reduce clutter in the interface, the plugins in static placeholders are hidden by default.
    Click or tap on the name of the static placeholder to reveal/hide them.

If you add some content to the new static placeholder in the usual way, you'll see that it
appears on your site's other pages too.


***************
Rendering Menus
***************

In order to render the CMS's menu in your template you can use the :doc:`show_menu
</reference/navigation>` tag.

Any template that uses ``show_menu`` must load the CMS's ``menu_tags`` library
first:

.. code-block:: html+django

    {% load menu_tags %}

The menu we use in ``mysite/templates/base.html`` is:

.. code-block:: html+django

    <ul class="nav navbar-nav">
        {% show_menu 0 100 100 100 "menu.html" %}
    </ul>

The options control the levels of the site hierarchy that are displayed in the menu tree - but you don't need to worry about exactly what they do at this stage.

Next we'll look at :ref:`integrating_applications`.
