calmjs.dev
==========

A package that declares common development tools that integrates with
|calmjs|_ along with commonly used `Node.js`_ development frameworks.


Introduction
------------

In order to facilitate a standardized deployment of working Node.js
environments from within Python environments for the execution of
JavaScript tests provided by Python packages against their accompanied
JavaScript code, this package declares a set of commonly used
development packages in the ``devDependencies`` section in its
``package.json`` file which is declared through the ``calmjs``
extensions to |setuptools|_.  Other Python packages may then declare
their dependencies through ``setup.py`` to pick up and make use of the
following set of tools through the appropriate entry points to
``calmjs`` and/or ``setuptools`` command.

.. |calmjs| replace:: ``calmjs``
.. |calmjs.dev| replace:: ``calmjs.dev``
.. |calmjs.rjs| replace:: ``calmjs.rjs``
.. |setuptools| replace:: ``setuptools``
.. _calmjs: https://pypi.python.org/pypi/calmjs
.. _calmjs.rjs: https://pypi.python.org/pypi/calmjs.rjs
.. _Node.js: https://nodejs.org
.. _setuptools: https://pypi.python.org/pypi/setuptools


Features
--------

- Provides a set of commonly used development tools that are commonly
  used for testing JavaScript code.  In brief, these include:

  |karma|_
      Test runner for running tests included with packages against the
      JavaScript code contained there.
  |mocha|_
      A JavaScript test framework for writing unit tests for node.js or
      the browser.
  |phantomjs|_
      A headless webkit with JavaScript API capable of interfacing with
      karma; this enables the running of integration JavaScript tests.
  |sinon|_
      A set of spies stubs and mocks for JavaScript for working with a
      unit testing framework.

  Plus other integration packages that get them to work with each other,
  namely the various ``karma-*`` packages for integration with |karma|.
  For full details on the environment that will be installed through the
  |calmjs| framework, the command ``calmjs npm calmjs.dev`` can be
  invoked to view the ``package.json`` once this package is installed
  into a Python environment, or even install them into the current
  working directory.

- Through the use of the |calmjs| module registry system, Python
  packages can declare JavaScript sources that can be passed through
  specific toolchains that build them into deployable artifacts.  The
  |calmjs.dev| package provide a common framework for the generation of
  configuration files for the execution of tests through the karma test
  runner.

  The usage of this is typically through the |calmjs| runtime system.

.. |karma| replace:: ``karma``
.. |mocha| replace:: ``mocha``
.. |phantomjs| replace:: ``phantomjs``
.. |sinon| replace:: ``sinon``
.. _karma: https://www.npmjs.com/package/karma
.. _mocha: https://www.npmjs.com/package/mocha
.. _phantomjs: https://www.npmjs.com/package/phantomjs-prebuilt
.. _sinon: https://www.npmjs.com/package/sinon


Installation
------------

Currently under development, please install by cloning this repository
and run ``python setup.py develop`` within a working Python environment,
or follow the local framework or operating system's default method on
installation of development packages that have pulled this package in.

Installation of Node.js external dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As this package integrates a number of Node.js packages to achieve the
intended functionality of integration with that environment, Node.js
packages required by this package can be installed into the current
working directory through the |calmjs| executable with the included
|npm| command:

.. code:: sh

    $ calmjs npm --install calmjs.dev

Testing the installation
~~~~~~~~~~~~~~~~~~~~~~~~

Finally, to verify for the successful installation of |calmjs.dev|, the
included tests may be executed through this command:

.. code:: sh

    $ python -m unittest calmjs.dev.tests.make_suite

However, if the steps to install external Node.js dependencies to the
current directory was followed, the current directory may be specified
as the ``CALMJS_TEST_ENV`` environment variable.  Under POSIX compatible
shells this may be executed instead from within that directory:

.. code:: sh

    $ CALMJS_TEST_ENV=. python -m unittest calmjs.dev.tests.make_suite

Usage
-----

The default tool is meant to provide an injectable runtime that sits
before a |calmjs| toolchain runtime.  Currently, the standard way to use
this package is to use it in conjunction of the |calmjs.rjs|_ package
runtime.  For instance, one might execute the ``r.js`` tool through
|calmjs.rjs| like:

.. code:: sh

    $ calmjs rjs example.package

The above command would package all the JavaScript code provided by the
Python package ``example.package`` into an AMD bundle artifact through
``r.js``.  As the ``example.package`` may also provide tests for its
JavaScript code (naturally written in JavaScript), it may be executed
through the karma test runner provided by this package.  The command is
as simple as adding ``karma`` before the toolchain runtime, like:

.. code:: sh

    $ calmjs karma rjs example.package

This would apply a test advice to the ``rjs`` toolchain and invoke it.
Normally, before the bundling is done, the tests will be executed
against the transpiled sources in the build directory.

To run tests against pre-generated artifact files, |calmjs.dev| provides
a surrogate toolchain runtime specific for the ``karma`` command that
may be used to achieve this purpose.  For example, if one wishes to run
tests a bundle file ``bundle.js`` which they assumed to contain code
from ``example.package``, they may wish to run tests defined for that
package by invoking:

.. code:: sh

    $ calmjs karma run \
        --artifact=bundle.js \
        --test-package=example.package

However, for more complicated toolchains and packages this will probably
not work, as the generation of these artifacts typically involve extra
optional advices that have been added.  To address that, one may apply
the ``--toolchain-package`` flag which serves a similar purpose as the
``--optional-advice`` flag for certain toolchains.  For |calmjs.rjs|,
this is necessary.  The full command may be like so:

.. code:: sh

    $ calmjs karma run \
        --artifact=bundle.js \
        --test-package=example.package \
        --toolchain-package=calmjs.rjs

As with all |calmjs| tools, more help can be acquired by appending
``-h`` or ``--help`` to each of the runtime commands, i.e. ``calmjs
karma -h`` or ``calmjs karma run -h``.


Troubleshooting
---------------

The following may be some issues that may be encountered with standard
or typical usage of |calmjs.dev|.

ERROR [plugin]: "karma-..." plugin: ...
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A message specific to some plugin may result in the test runner not
being able to execute any test.  This is typically caused by certain
versions of karma test runner not being able to cleanly deal with
misbehaving plugins that is available in the ``node_modules`` directory.
If the plugin shown inside the quote (starting with ``karma-``) is
unnecessary for the execution of tests, it should be removed and the
test command should be executed again.


Contribute
----------

- Issue Tracker: https://github.com/calmjs/calmjs.dev/issues
- Source Code: https://github.com/calmjs/calmjs.dev

License
-------

|calmjs.dev| is licensed under the GPLv2 or later.
