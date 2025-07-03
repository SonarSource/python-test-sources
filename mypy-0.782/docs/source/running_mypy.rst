.. _running-mypy:

Running mypy and managing imports
=================================

The :ref:`getting-started` page should have already introduced you
to the basics of how to run mypy -- pass in the files and directories
you want to type check via the command line::

    $ mypy foo.py bar.py some_directory

This page discusses in more detail how exactly to specify what files
you want mypy to type check, how mypy discovers imported modules,
and recommendations on how to handle any issues you may encounter
along the way.

If you are interested in learning about how to configure the
actual way mypy type checks your code, see our
:ref:`command-line` guide.


.. _specifying-code-to-be-checked:

Specifying code to be checked
*****************************

Mypy lets you specify what files it should type check in several
different ways.

1.  First, you can pass in paths to Python files and directories you
    want to type check. For example::

        $ mypy file_1.py foo/file_2.py file_3.pyi some/directory

    The above command tells mypy it should type check all of the provided
    files together. In addition, mypy will recursively type check the
    entire contents of any provided directories.

    For more details about how exactly this is done, see
    :ref:`Mapping file paths to modules <mapping-paths-to-modules>`.

2.  Second, you can use the :option:`-m <mypy -m>` flag (long form: :option:`--module <mypy --module>`) to
    specify a module name to be type checked. The name of a module
    is identical to the name you would use to import that module
    within a Python program. For example, running::

        $ mypy -m html.parser

    ...will type check the module ``html.parser`` (this happens to be
    a library stub).

    Mypy will use an algorithm very similar to the one Python uses to
    find where modules and imports are located on the file system.
    For more details, see :ref:`finding-imports`.

3.  Third, you can use the :option:`-p <mypy -p>` (long form: :option:`--package <mypy --package>`) flag to
    specify a package to be (recursively) type checked. This flag
    is almost identical to the :option:`-m <mypy -m>` flag except that if you give it
    a package name, mypy will recursively type check all submodules
    and subpackages of that package. For example, running::

        $ mypy -p html

    ...will type check the entire ``html`` package (of library stubs).
    In contrast, if we had used the :option:`-m <mypy -m>` flag, mypy would have type
    checked just ``html``'s ``__init__.py`` file and anything imported
    from there.

    Note that we can specify multiple packages and modules on the
    command line. For example::

      $ mypy --package p.a --package p.b --module c

4.  Fourth, you can also instruct mypy to directly type check small
    strings as programs by using the :option:`-c <mypy -c>` (long form: :option:`--command <mypy --command>`)
    flag. For example::

        $ mypy -c 'x = [1, 2]; print(x())'

    ...will type check the above string as a mini-program (and in this case,
    will report that ``List[int]`` is not callable).


Reading a list of files from a file
***********************************

Finally, any command-line argument starting with ``@`` reads additional
command-line arguments from the file following the ``@`` character.
This is primarily useful if you have a file containing a list of files
that you want to be type-checked: instead of using shell syntax like::

    $ mypy $(cat file_of_files.txt)

you can use this instead::

    $ mypy @file_of_files.txt

This file can technically also contain any command line flag, not
just file paths. However, if you want to configure many different
flags, the recommended approach is to use a
:ref:`configuration file <config-file>` instead.



How mypy handles imports
************************

When mypy encounters an ``import`` statement, it will first
:ref:`attempt to locate <finding-imports>` that module
or type stubs for that module in the file system. Mypy will then
type check the imported module. There are three different outcomes
of this process:

1.  Mypy is unable to follow the import: the module either does not
    exist, or is a third party library that does not use type hints.

2.  Mypy is able to follow and type check the import, but you did
    not want mypy to type check that module at all.

3.  Mypy is able to successfully both follow and type check the
    module, and you want mypy to type check that module.

The third outcome is what mypy will do in the ideal case. The following
sections will discuss what to do in the other two cases.

.. _ignore-missing-imports:

Missing imports
***************

When you import a module, mypy may report that it is unable to
follow the import.

This can cause errors that look like the following::

    main.py:1: error: No library stub file for standard library module 'antigravity'
    main.py:2: error: Skipping analyzing 'django': found module but no type hints or library stubs
    main.py:3: error: Cannot find implementation or library stub for module named 'this_module_does_not_exist'

If you get any of these errors on an import, mypy will assume the type of that
module is ``Any``, the dynamic type. This means attempting to access any
attribute of the module will automatically succeed:

.. code-block:: python

    # Error: Cannot find implementation or library stub for module named 'does_not_exist'
    import does_not_exist

    # But this type checks, and x will have type 'Any'
    x = does_not_exist.foobar()

The next three sections describe what each error means and recommended next steps.

Missing type hints for standard library module
----------------------------------------------

If you are getting a "No library stub file for standard library module" error,
this means that you are attempting to import something from the standard library
which has not yet been annotated with type hints. In this case, try:

1.  Updating mypy and re-running it. It's possible type hints for that corner
    of the standard library were added in a newer version of mypy.

2.  Filing a bug report or submitting a pull request to
    `typeshed <https://github.com/python/typeshed>`_, the repository of type hints
    for the standard library that comes bundled with mypy.

    Changes to typeshed will come bundled with mypy the next time it's released.
    In the meantime, you can add a ``# type: ignore`` to the import to suppress
    the errors generated on that line. After upgrading, run mypy with the
    :option:`--warn-unused-ignores <mypy --warn-unused-ignores>` flag to help you
    find any ``# type: ignore`` annotations you no longer need.

.. _missing-type-hints-for-third-party-library:

Missing type hints for third party library
------------------------------------------

If you are getting a "Skipping analyzing X: found module but no type hints or library stubs",
error, this means mypy was able to find the module you were importing, but no
corresponding type hints.

Mypy will not try inferring the types of any 3rd party libraries you have installed
unless they either have declared themselves to be
:ref:`PEP 561 compliant stub package <installed-packages>` or have registered
themselves on `typeshed <https://github.com/python/typeshed>`_, the repository
of types for the standard library and some 3rd party libraries.

If you are getting this error, try:

1.  Upgrading the version of the library you're using, in case a newer version
    has started to include type hints.

2.  Searching to see if there is a :ref:`PEP 561 compliant stub package <installed-packages>`.
    corresponding to your third party library. Stub packages let you install
    type hints independently from the library itself.

    For example, if you want type hints for the ``django`` library, you can
    install the `django-stubs <https://pypi.org/project/django-stubs/>`_ package.

3.  :ref:`Writing your own stub files <stub-files>` containing type hints for
    the library. You can point mypy at your type hints either by passing
    them in via the command line, by using the  ``files`` or ``mypy_path``
    :ref:`config file options <config-file-import-discovery>`, or by
    adding the location to the ``MYPYPATH`` environment variable.

    These stub files do not need to be complete! A good strategy is to use
    stubgen, a program that comes bundled with mypy, to generate a first
    rough draft of the stubs. You can then iterate on just the parts of the
    library you need.

    If you want to share your work, you can try contributing your stubs back
    to the library -- see our documentation on creating
    :ref:`PEP 561 compliant packages <installed-packages>`.

If you are unable to find any existing type hints nor have time to write your
own, you can instead *suppress* the errors. All this will do is make mypy stop
reporting an error on the line containing the import: the imported module
will continue to be of type ``Any``.

1.  To suppress a *single* missing import error, add a ``# type: ignore`` at the end of the
    line containing the import.

2.  To suppress *all* missing import imports errors from a single library, add
    a section to your :ref:`mypy config file <config-file>` for that library setting
    ``ignore_missing_imports`` to True. For example, suppose your codebase
    makes heavy use of an (untyped) library named ``foobar``. You can silence
    all import errors associated with that library and that library alone by
    adding the following section to your config file::

        [mypy-foobar.*]
        ignore_missing_imports = True

    Note: this option is equivalent to adding a ``# type: ignore`` to every
    import of ``foobar`` in your codebase. For more information, see the
    documentation about configuring
    :ref:`import discovery <config-file-import-discovery>` in config files.
    The ``.*`` after ``foobar`` will ignore imports of ``foobar`` modules
    and subpackages in addition to the ``foobar`` top-level package namespace.

3.  To suppress *all* missing import errors for *all* libraries in your codebase,
    invoke mypy with the :option:`--ignore-missing-imports <mypy --ignore-missing-imports>` command line flag or set
    the ``ignore_missing_imports``
    :ref:`config file option <config-file-import-discovery>` to True
    in the *global* section of your mypy config file::

        [mypy]
        ignore_missing_imports = True

    We recommend using this approach only as a last resort: it's equivalent
    to adding a ``# type: ignore`` to all unresolved imports in your codebase.

Unable to find module
---------------------

If you are getting a "Cannot find implementation or library stub for module"
error, this means mypy was not able to find the module you are trying to
import, whether it comes bundled with type hints or not. If you are getting
this error, try:

1.  Making sure your import does not contain a typo.

2.  If the module is a third party library, making sure that mypy is able
    to find the interpreter containing the installed library.

    For example, if you are running your code in a virtualenv, make sure
    to install and use mypy within the virtualenv. Alternatively, if you
    want to use a globally installed mypy, set the
    :option:`--python-executable <mypy --python-executable>` command
    line flag to point the Python interpreter containing your installed
    third party packages.

2.  Reading the :ref:`finding-imports` section below to make sure you
    understand how exactly mypy searches for and finds modules and modify
    how you're invoking mypy accordingly.

3.  Directly specifying the directory containing the module you want to
    type check from the command line, by using the ``files`` or
    ``mypy_path`` :ref:`config file options <config-file-import-discovery>`,
    or by using the ``MYPYPATH`` environment variable.

    Note: if the module you are trying to import is actually a *submodule* of
    some package, you should specific the directory containing the *entire* package.
    For example, suppose you are trying to add the module ``foo.bar.baz``
    which is located at ``~/foo-project/src/foo/bar/baz.py``. In this case,
    you must run ``mypy ~/foo-project/src`` (or set the ``MYPYPATH`` to
    ``~/foo-project/src``.

4.  If you are using namespace packages -- packages which do not contain
    ``__init__.py`` files within each subfolder -- using the
    :option:`--namespace-packages <mypy --namespace-packages>` command
    line flag.

In some rare cases, you may get the "Cannot find implementation or library
stub for module" error even when the module is installed in your system.
This can happen when the module is both missing type hints and is installed
on your system in a unconventional way.

In this case, follow the steps above on how to handle
:ref:`missing type hints in third party libraries <missing-type-hints-for-third-party-library>`.

.. _follow-imports:

Following imports
*****************

Mypy is designed to :ref:`doggedly follow all imports <finding-imports>`,
even if the imported module is not a file you explicitly wanted mypy to check.

For example, suppose we have two modules ``mycode.foo`` and ``mycode.bar``:
the former has type hints and the latter does not. We run
``mypy -m mycode.foo`` and mypy discovers that ``mycode.foo`` imports
``mycode.bar``.

How do we want mypy to type check ``mycode.bar``? We can configure the
desired behavior by using the :option:`--follow-imports <mypy --follow-imports>` flag. This flag
accepts one of four string values:

-   ``normal`` (the default) follows all imports normally and
    type checks all top level code (as well as the bodies of all
    functions and methods with at least one type annotation in
    the signature).

-   ``silent`` behaves in the same way as ``normal`` but will
    additionally *suppress* any error messages.

-   ``skip`` will *not* follow imports and instead will silently
    replace the module (and *anything imported from it*) with an
    object of type ``Any``.

-   ``error`` behaves in the same way as ``skip`` but is not quite as
    silent -- it will flag the import as an error, like this::

        main.py:1: note: Import of 'mycode.bar' ignored
        main.py:1: note: (Using --follow-imports=error, module not passed on command line)

If you are starting a new codebase and plan on using type hints from
the start, we recommend you use either :option:`--follow-imports=normal <mypy --follow-imports>`
(the default) or :option:`--follow-imports=error <mypy --follow-imports>`. Either option will help
make sure you are not skipping checking any part of your codebase by
accident.

If you are planning on adding type hints to a large, existing code base,
we recommend you start by trying to make your entire codebase (including
files that do not use type hints) pass under :option:`--follow-imports=normal <mypy --follow-imports>`.
This is usually not too difficult to do: mypy is designed to report as
few error messages as possible when it is looking at unannotated code.

If doing this is intractable, we recommend passing mypy just the files
you want to type check and use :option:`--follow-imports=silent <mypy --follow-imports>`. Even if
mypy is unable to perfectly type check a file, it can still glean some
useful information by parsing it (for example, understanding what methods
a given object has). See :ref:`existing-code` for more recommendations.

We do not recommend using ``skip`` unless you know what you are doing:
while this option can be quite powerful, it can also cause many
hard-to-debug errors.



.. _mapping-paths-to-modules:

Mapping file paths to modules
*****************************

One of the main ways you can tell mypy what files to type check
is by providing mypy the paths to those files. For example::

    $ mypy file_1.py foo/file_2.py file_3.pyi some/directory

This section describes how exactly mypy maps the provided paths
to modules to type check.

- Files ending in ``.py`` (and stub files ending in ``.pyi``) are
  checked as Python modules.

- Files not ending in ``.py`` or ``.pyi`` are assumed to be Python
  scripts and checked as such.

- Directories representing Python packages (i.e. containing a
  ``__init__.py[i]`` file) are checked as Python packages; all
  submodules and subpackages will be checked (subpackages must
  themselves have a ``__init__.py[i]`` file).

- Directories that don't represent Python packages (i.e. not directly
  containing an ``__init__.py[i]`` file) are checked as follows:

  - All ``*.py[i]`` files contained directly therein are checked as
    toplevel Python modules;

  - All packages contained directly therein (i.e. immediate
    subdirectories with an ``__init__.py[i]`` file) are checked as
    toplevel Python packages.

One more thing about checking modules and packages: if the directory
*containing* a module or package specified on the command line has an
``__init__.py[i]`` file, mypy assigns these an absolute module name by
crawling up the path until no ``__init__.py[i]`` file is found.

For example, suppose we run the command ``mypy foo/bar/baz.py`` where
``foo/bar/__init__.py`` exists but ``foo/__init__.py`` does not.  Then
the module name assumed is ``bar.baz`` and the directory ``foo`` is
added to mypy's module search path.

On the other hand, if ``foo/bar/__init__.py`` did not exist, ``foo/bar``
would be added to the module search path instead, and the module name
assumed is just ``baz``.

If a script (a file not ending in ``.py[i]``) is processed, the module
name assumed is ``__main__`` (matching the behavior of the
Python interpreter), unless :option:`--scripts-are-modules <mypy --scripts-are-modules>` is passed.


.. _finding-imports:

How imports are found
*********************

When mypy encounters an ``import`` statement or receives module
names from the command line via the :option:`--module <mypy --module>` or :option:`--package <mypy --package>`
flags, mypy tries to find the module on the file system similar
to the way Python finds it. However, there are some differences.

First, mypy has its own search path.
This is computed from the following items:

- The ``MYPYPATH`` environment variable
  (a colon-separated list of directories).
- The ``mypy_path`` :ref:`config file option <config-file-import-discovery>`.
- The directories containing the sources given on the command line
  (see below).
- The installed packages marked as safe for type checking (see
  :ref:`PEP 561 support <installed-packages>`)
- The relevant directories of the
  `typeshed <https://github.com/python/typeshed>`_ repo.

.. note::

    You cannot point to a :pep:`561` package via the ``MYPYPATH``, it must be
    installed (see :ref:`PEP 561 support <installed-packages>`)

For sources given on the command line, the path is adjusted by crawling
up from the given file or package to the nearest directory that does not
contain an ``__init__.py`` or ``__init__.pyi`` file. If the given path
is relative, it will only crawl as far as the current working directory.

Second, mypy searches for stub files in addition to regular Python files
and packages.
The rules for searching for a module ``foo`` are as follows:

- The search looks in each of the directories in the search path
  (see above) until a match is found.
- If a package named ``foo`` is found (i.e. a directory
  ``foo`` containing an ``__init__.py`` or ``__init__.pyi`` file)
  that's a match.
- If a stub file named ``foo.pyi`` is found, that's a match.
- If a Python module named ``foo.py`` is found, that's a match.

These matches are tried in order, so that if multiple matches are found
in the same directory on the search path
(e.g. a package and a Python file, or a stub file and a Python file)
the first one in the above list wins.

In particular, if a Python file and a stub file are both present in the
same directory on the search path, only the stub file is used.
(However, if the files are in different directories, the one found
in the earlier directory is used.)

Other advice and best practices
*******************************

There are multiple ways of telling mypy what files to type check, ranging
from passing in command line arguments to using the ``files`` or ``mypy_path``
:ref:`config file options <config-file-import-discovery>` to setting the
``MYPYPATH`` environment variable.

However, in practice, it is usually sufficient to just use either
command line arguments or the ``files`` config file option (the two
are largely interchangeable).

Setting ``mypy_path``/``MYPYPATH`` is mostly useful in the case
where you want to try running mypy against multiple distinct
sets of files that happen to share some common dependencies.

For example, if you have multiple projects that happen to be
using the same set of work-in-progress stubs, it could be
convenient to just have your ``MYPYPATH`` point to a single
directory containing the stubs.
