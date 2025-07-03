.. _config-file:

The mypy configuration file
===========================

Mypy supports reading configuration settings from a file.  By default
it uses the file ``mypy.ini`` with a fallback to ``.mypy.ini``, then ``setup.cfg`` in
the current directory, then ``$XDG_CONFIG_HOME/mypy/config``, then
``~/.config/mypy/config``, and finally ``.mypy.ini`` in the user home directory
if none of them are found; the :option:`--config-file <mypy --config-file>` command-line flag can be used
to read a different file instead (see :ref:`config-file-flag`).

It is important to understand that there is no merging of configuration
files, as it would lead to ambiguity.  The :option:`--config-file <mypy --config-file>` flag
has the highest precedence and must be correct; otherwise mypy will report
an error and exit.  Without command line option, mypy will look for defaults,
but will use only one of them.  The first one to read is ``mypy.ini``,
then ``.mypy.ini``, and finally ``setup.cfg``.

Most flags correspond closely to :ref:`command-line flags
<command-line>` but there are some differences in flag names and some
flags may take a different value based on the module being processed.

Some flags support user home directory and environment variable expansion.
To refer to the user home directory, use ``~`` at the beginning of the path.
To expand environment variables use ``$VARNAME`` or ``${VARNAME}``.


Config file format
******************

The configuration file format is the usual
:doc:`ini file <python:library/configparser>` format. It should contain
section names in square brackets and flag settings of the form
`NAME = VALUE`. Comments start with ``#`` characters.

- A section named ``[mypy]`` must be present.  This specifies
  the global flags. The ``setup.cfg`` file is an exception to this.

- Additional sections named ``[mypy-PATTERN1,PATTERN2,...]`` may be
  present, where ``PATTERN1``, ``PATTERN2``, etc., are comma-separated
  patterns of fully-qualified module names, with some components optionally
  replaced by the '*' character (e.g. ``foo.bar``, ``foo.bar.*``, ``foo.*.baz``).
  These sections specify additional flags that only apply to *modules*
  whose name matches at least one of the patterns.

  A pattern of the form ``qualified_module_name`` matches only the named module,
  while ``dotted_module_name.*`` matches ``dotted_module_name`` and any
  submodules (so ``foo.bar.*`` would match all of ``foo.bar``,
  ``foo.bar.baz``, and ``foo.bar.baz.quux``).

  Patterns may also be "unstructured" wildcards, in which stars may
  appear in the middle of a name (e.g
  ``site.*.migrations.*``). Stars match zero or more module
  components (so ``site.*.migrations.*`` can match ``site.migrations``).

  .. _config-precedence:

  When options conflict, the precedence order for configuration is:
    1. :ref:`Inline configuration <inline-config>` in the source file
    2. Sections with concrete module names (``foo.bar``)
    3. Sections with "unstructured" wildcard patterns (``foo.*.baz``),
       with sections later in the configuration file overriding
       sections earlier.
    4. Sections with "well-structured" wildcard patterns
       (``foo.bar.*``), with more specific overriding more general.
    5. Command line options.
    6. Top-level configuration file options.

The difference in precedence order between "structured" patterns (by
specificity) and "unstructured" patterns (by order in the file) is
unfortunate, and is subject to change in future versions.

.. note::

   The ``warn_unused_configs`` flag may be useful to debug misspelled
   section names.

.. note::

   Configuration flags are liable to change between releases.


Per-module and global options
*****************************

Some of the config options may be set either globally (in the ``[mypy]`` section)
or on a per-module basis (in sections like ``[mypy-foo.bar]``).

If you set an option both globally and for a specific module, the module configuration
options take precedence. This lets you set global defaults and override them on a
module-by-module basis. If multiple pattern sections match a module, :ref:`the options from the
most specific section are used where they disagree <config-precedence>`.

Some other options, as specified in their description,
may only be set in the global section (``[mypy]``).


Inverting option values
***********************

Options that take a boolean value may be inverted by adding ``no_`` to
their name or by (when applicable) swapping their prefix from
``disallow`` to ``allow`` (and vice versa).


Examples
********

Here is an example of a ``mypy.ini`` file. To use this config file, place it at the root
of your repo and run mypy.

.. code-block:: ini

    # Global options:

    [mypy]
    python_version = 2.7
    warn_return_any = True
    warn_unused_configs = True

    # Per-module options:

    [mypy-mycode.foo.*]
    disallow_untyped_defs = True

    [mypy-mycode.bar]
    warn_return_any = False

    [mypy-somelibrary]
    ignore_missing_imports = True

This config file specifies three global options in the ``[mypy]`` section. These three
options will:

1.  Type-check your entire project assuming it will be run using Python 2.7.
    (This is equivalent to using the :option:`--python-version 2.7 <mypy --python-version>` or :option:`-2 <mypy -2>` flag).

2.  Report an error whenever a function returns a value that is inferred
    to have type ``Any``.

3.  Report any config options that are unused by mypy. (This will help us catch typos
    when making changes to our config file).

Next, this module specifies three per-module options. The first two options change how mypy
type checks code in ``mycode.foo.*`` and ``mycode.bar``, which we assume here are two modules
that you wrote. The final config option changes how mypy type checks ``somelibrary``, which we
assume here is some 3rd party library you've installed and are importing. These options will:

1.  Selectively disallow untyped function definitions only within the ``mycode.foo``
    package -- that is, only for function definitions defined in the
    ``mycode/foo`` directory.

2.  Selectively *disable* the "function is returning any" warnings within
    ``mycode.bar`` only. This overrides the global default we set earlier.

3.  Suppress any error messages generated when your codebase tries importing the
    module ``somelibrary``. This is useful if ``somelibrary`` is some 3rd party library
    missing type hints.


.. _config-file-import-discovery:

Import discovery
****************

For more information, see the :ref:`Import discovery <import-discovery>`
section of the command line docs.

``mypy_path`` (string)
    Specifies the paths to use, after trying the paths from ``MYPYPATH`` environment
    variable.  Useful if you'd like to keep stubs in your repo, along with the config file.
    Multiple paths are always separated with a ``:`` or ``,`` regardless of the platform.
    User home directory and environment variables will be expanded.

    This option may only be set in the global section (``[mypy]``).

    **Note:** On Windows, use UNC paths to avoid using ``:`` (e.g. ``\\127.0.0.1\X$\MyDir`` where ``X`` is the drive letter).
    
``files`` (comma-separated list of strings)
    A comma-separated list of paths which should be checked by mypy if none are given on the command
    line. Supports recursive file globbing using :py:mod:`glob`, where ``*`` (e.g. ``*.py``) matches
    files in the current directory and ``**/`` (e.g. ``**/*.py``) matches files in any directories below
    the current one. User home directory and environment variables will be expanded.

    This option may only be set in the global section (``[mypy]``).

``namespace_packages`` (bool, default False)
    Enables :pep:`420` style namespace packages.  See :ref:`the
    corresponding flag <import-discovery>` for more information.

    This option may only be set in the global section (``[mypy]``).

``ignore_missing_imports`` (bool, default False)
    Suppresses error messages about imports that cannot be resolved.

    If this option is used in a per-module section, the module name should
    match the name of the *imported* module, not the module containing the
    import statement.

``follow_imports`` (string, default ``normal``)
    Directs what to do with imports when the imported module is found
    as a ``.py`` file and not part of the files, modules and packages
    provided on the command line.

    The four possible values are ``normal``, ``silent``, ``skip`` and
    ``error``.  For explanations see the discussion for the
    :ref:`--follow-imports <follow-imports>` command line flag.

    If this option is used in a per-module section, the module name should
    match the name of the *imported* module, not the module containing the
    import statement.

``follow_imports_for_stubs`` (bool, default False)
    Determines whether to respect the ``follow_imports`` setting even for
    stub (``.pyi``) files.

    Used in conjunction with ``follow_imports=skip``, this can be used
    to suppress the import of a module from ``typeshed``, replacing it
    with ``Any``.

    Used in conjunction with ``follow_imports=error``, this can be used
    to make any use of a particular ``typeshed`` module an error.

``python_executable`` (string)
    Specifies the path to the Python executable to inspect to collect
    a list of available :ref:`PEP 561 packages <installed-packages>`. User
    home directory and environment variables will be expanded. Defaults to
    the executable used to run mypy.

    This option may only be set in the global section (``[mypy]``).

``no_site_packages`` (bool, default False)
    Disables using type information in installed packages (see :pep:`561`).
    This will also disable searching for a usable Python executable. This acts
    the same as :option:`--no-site-packages <mypy --no-site-packages>` command
    line flag.

``no_silence_site_packages`` (bool, default False)
    Enables reporting error messages generated within installed packages (see
    :pep:`561` for more details on distributing type information). Those error
    messages are suppressed by default, since you are usually not able to
    control errors in 3rd party code.

    This option may only be set in the global section (``[mypy]``).


Platform configuration
**********************

``python_version`` (string)
    Specifies the Python version used to parse and check the target
    program.  The string should be in the format ``DIGIT.DIGIT`` --
    for example ``2.7``.  The default is the version of the Python
    interpreter used to run mypy.

    This option may only be set in the global section (``[mypy]``).

``platform`` (string)
    Specifies the OS platform for the target program, for example
    ``darwin`` or ``win32`` (meaning OS X or Windows, respectively).
    The default is the current platform as revealed by Python's
    :py:data:`sys.platform` variable.

    This option may only be set in the global section (``[mypy]``).

``always_true`` (comma-separated list of strings)
    Specifies a list of variables that mypy will treat as
    compile-time constants that are always true.

``always_false`` (comma-separated list of strings)
    Specifies a list of variables that mypy will treat as
    compile-time constants that are always false.


Disallow dynamic typing
***********************

For more information, see the :ref:`Disallow dynamic typing <disallow-dynamic-typing>`
section of the command line docs.

``disallow_any_unimported`` (bool, default False)
    Disallows usage of types that come from unfollowed imports (anything imported from
    an unfollowed import is automatically given a type of ``Any``).

``disallow_any_expr`` (bool, default False)
    Disallows all expressions in the module that have type ``Any``.

``disallow_any_decorated`` (bool, default False)
    Disallows functions that have ``Any`` in their signature after decorator transformation.

``disallow_any_explicit`` (bool, default False)
    Disallows explicit ``Any`` in type positions such as type annotations and generic
    type parameters.

``disallow_any_generics`` (bool, default False)
    Disallows usage of generic types that do not specify explicit type parameters.

``disallow_subclassing_any`` (bool, default False)
    Disallows subclassing a value of type ``Any``.


Untyped definitions and calls
*****************************

For more information, see the :ref:`Untyped definitions and calls <untyped-definitions-and-calls>`
section of the command line docs.

``disallow_untyped_calls`` (bool, default False)
    Disallows calling functions without type annotations from functions with type
    annotations.

``disallow_untyped_defs`` (bool, default False)
    Disallows defining functions without type annotations or with incomplete type
    annotations.

``disallow_incomplete_defs`` (bool, default False)
    Disallows defining functions with incomplete type annotations.

``check_untyped_defs`` (bool, default False)
    Type-checks the interior of functions without type annotations.

``disallow_untyped_decorators`` (bool, default False)
    Reports an error whenever a function with type annotations is decorated with a
    decorator without annotations.


.. _config-file-none-and-optional-handling:

None and Optional handling
**************************

For more information, see the :ref:`None and Optional handling <none-and-optional-handling>`
section of the command line docs.

``no_implicit_optional`` (bool, default False)
    Changes the treatment of arguments with a default value of ``None`` by not implicitly
    making their type :py:data:`~typing.Optional`.

``strict_optional`` (bool, default True)
    Enables or disables strict Optional checks. If False, mypy treats ``None``
    as compatible with every type.

    **Note:** This was False by default in mypy versions earlier than 0.600.


Configuring warnings
********************

For more information, see the :ref:`Configuring warnings <configuring-warnings>`
section of the command line docs.

``warn_redundant_casts`` (bool, default False)
    Warns about casting an expression to its inferred type.

    This option may only be set in the global section (``[mypy]``).

``warn_unused_ignores`` (bool, default False)
    Warns about unneeded ``# type: ignore`` comments.

``warn_no_return`` (bool, default True)
    Shows errors for missing return statements on some execution paths.

``warn_return_any`` (bool, default False)
    Shows a warning when returning a value with type ``Any`` from a function
    declared with a non- ``Any`` return type.

``warn_unreachable`` (bool, default False)
    Shows a warning when encountering any code inferred to be unreachable or
    redundant after performing type analysis.


Suppressing errors
******************

Note: these configuration options are available in the config file only. There is
no analog available via the command line options.

``show_none_errors`` (bool, default True)
    Shows errors related to strict ``None`` checking, if the global ``strict_optional``
    flag is enabled.

``ignore_errors`` (bool, default False)
    Ignores all non-fatal errors.


Miscellaneous strictness flags
******************************

``allow_untyped_globals`` (bool, default False)
    Causes mypy to suppress errors caused by not being able to fully
    infer the types of global and class variables.

``allow_redefinition`` (bool, default False)
    Allows variables to be redefined with an arbitrary type, as long as the redefinition
    is in the same block and nesting level as the original definition.

``implicit_reexport`` (bool, default True)
    By default, imported values to a module are treated as exported and mypy allows
    other modules to import them. When false, mypy will not re-export unless
    the item is imported using from-as or is included in ``__all__``. Note that mypy
    treats stub files as if this is always disabled. For example:

    .. code-block:: python

       # This won't re-export the value
       from foo import bar
       # This will re-export it as bar and allow other modules to import it
       from foo import bar as bar
       # This will also re-export bar
       from foo import bar
       __all__ = ['bar']

``strict_equality``  (bool, default False)
   Prohibit equality checks, identity checks, and container checks between
   non-overlapping types.


Configuring error messages
**************************

For more information, see the :ref:`Configuring error messages <configuring-error-messages>`
section of the command line docs.

These options may only be set in the global section (``[mypy]``).

``show_error_context`` (bool, default False)
    Prefixes each error with the relevant context.

``show_column_numbers`` (bool, default False)
    Shows column numbers in error messages.

``show_error_codes`` (bool, default False)
    Shows error codes in error messages. See :ref:`error-codes` for more information.

``pretty`` (bool, default False)
    Use visually nicer output in error messages: use soft word wrap,
    show source code snippets, and show error location markers.

``color_output`` (bool, default True)
    Shows error messages with color enabled.

``error_summary`` (bool, default True)
    Shows a short summary line after error messages.

``show_absolute_path`` (bool, default False)
    Show absolute paths to files.


Incremental mode
****************

These options may only be set in the global section (``[mypy]``).

``incremental`` (bool, default True)
    Enables :ref:`incremental mode <incremental>`.

``cache_dir`` (string, default ``.mypy_cache``)
    Specifies the location where mypy stores incremental cache info.
    User home directory and environment variables will be expanded.
    This setting will be overridden by the ``MYPY_CACHE_DIR`` environment
    variable.

    Note that the cache is only read when incremental mode is enabled
    but is always written to, unless the value is set to ``/dev/null``
    (UNIX) or ``nul`` (Windows).

``sqlite_cache`` (bool, default False)
    Use an `SQLite`_ database to store the cache.

``cache_fine_grained`` (bool, default False)
    Include fine-grained dependency information in the cache for the mypy daemon.

``skip_version_check`` (bool, default False)
    Makes mypy use incremental cache data even if it was generated by a
    different version of mypy. (By default, mypy will perform a version
    check and regenerate the cache if it was written by older versions of mypy.)

``skip_cache_mtime_checks`` (bool, default False)
    Skip cache internal consistency checks based on mtime.


Advanced options
****************

These options may only be set in the global section (``[mypy]``).

``pdb`` (bool, default False)
    Invokes pdb on fatal error.

``show_traceback`` (bool, default False)
    Shows traceback on fatal error.

``raise_exceptions`` (bool, default False)
    Raise exception on fatal error.

``custom_typing_module`` (string)
    Specifies a custom module to use as a substitute for the :py:mod:`typing` module.

``custom_typeshed_dir`` (string)
    Specifies an alternative directory to look for stubs instead of the
    default ``typeshed`` directory. User home directory and environment
    variables will be expanded.

``warn_incomplete_stub`` (bool, default False)
    Warns about missing type annotations in typeshed.  This is only relevant
    in combination with ``disallow_untyped_defs`` or ``disallow_incomplete_defs``.


Report generation
*****************

If these options are set, mypy will generate a report in the specified
format into the specified directory.

``any_exprs_report`` (string)
    Causes mypy to generate a text file report documenting how many
    expressions of type ``Any`` are present within your codebase.

``cobertura_xml_report`` (string)
    Causes mypy to generate a Cobertura XML type checking coverage report.

    You must install the `lxml`_ library to generate this report.

``html_report`` / ``xslt_html_report`` (string)
    Causes mypy to generate an HTML type checking coverage report.

    You must install the `lxml`_ library to generate this report.

``linecount_report`` (string)
    Causes mypy to generate a text file report documenting the functions
    and lines that are typed and untyped within your codebase.

``linecoverage_report`` (string)
    Causes mypy to generate a JSON file that maps each source file's
    absolute filename to a list of line numbers that belong to typed
    functions in that file.

``lineprecision_report`` (string)
    Causes mypy to generate a flat text file report with per-module
    statistics of how many lines are typechecked etc.

``txt_report`` / ``xslt_txt_report`` (string)
    Causes mypy to generate a text file type checking coverage report.

    You must install the `lxml`_ library to generate this report.

``xml_report`` (string)
    Causes mypy to generate an XML type checking coverage report.

    You must install the `lxml`_ library to generate this report.


Miscellaneous
*************

These options may only be set in the global section (``[mypy]``).

``junit_xml`` (string)
    Causes mypy to generate a JUnit XML test result document with
    type checking results. This can make it easier to integrate mypy
    with continuous integration (CI) tools.

``scripts_are_modules`` (bool, default False)
    Makes script ``x`` become module ``x`` instead of ``__main__``.  This is
    useful when checking multiple scripts in a single run.

``warn_unused_configs`` (bool, default False)
    Warns about per-module sections in the config file that do not
    match any files processed when invoking mypy.
    (This requires turning off incremental mode using ``incremental = False``.)

``verbosity`` (integer, default 0)
    Controls how much debug output will be generated.  Higher numbers are more verbose.

.. _lxml: https://pypi.org/project/lxml/
.. _SQLite: https://www.sqlite.org/
