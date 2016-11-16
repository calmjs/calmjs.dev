calmjs.dev
==========

Package within the `Calmjs framework`_ for the support and development
of Python packages that include JavaScript for their full functionality.

.. image:: https://travis-ci.org/calmjs/calmjs.dev.svg?branch=master
    :target: https://travis-ci.org/calmjs/calmjs.dev
.. image:: https://ci.appveyor.com/api/projects/status/0mxtiaf2j98w5fy6/branch/master?svg=true
    :target: https://ci.appveyor.com/project/metatoaster/calmjs-dev/branch/master
.. image:: https://coveralls.io/repos/github/calmjs/calmjs.dev/badge.svg?branch=master
    :target: https://coveralls.io/github/calmjs/calmjs.dev?branch=master


Introduction
------------

Python packages can ship JavaScript code.  This situation is commonly
found in situations where frontend functionalities that enhance user
experience that require interactions with backend Python code running on
the server.  In order to facilitate the testing of those JavaScript code
from those Python packages, commonly `Node.js`_ packages and frameworks
are often used to achieve this.  However, the configurations files for
the Node.js/JavaScript package dependencies, along with the building of
artifacts and testing of the JavaScript provided by those Python
packages are very specific to the project and generally not portable.
If multiple such packages are required for a downstream Python project,
the scripts and definition files for building of artifacts and testing
generally have to be manually modified, which is typically a very
aggravating and error-prone process.

The Calmjs framework, however, provides the means for Python packages to
declare the JavaScript modules they are to export, and this package,
|calmjs.dev|, provides the means to consume those information such that
the JavaScript tests declared within those Python packages can be
executed without having to manually construct and verify the paths to
the source and tests files, no matter where they are within the
environment, provided they are properly declared through the Calmjs
framework.  The tests can then run either against the JavaScript sources
provided by the Python package through the artifact generation
framework, or against prebuilt artifacts that contain those
functionalities.  Naturally, the support for the artifact generation
framework requires integration with the Calmjs framework; currently, the
support of AMD is implemented through the |calmjs.rjs|_ package.

.. |calmjs| replace:: ``calmjs``
.. |calmjs.dev| replace:: ``calmjs.dev``
.. |calmjs.rjs| replace:: ``calmjs.rjs``
.. |setuptools| replace:: ``setuptools``
.. _Calmjs framework: https://pypi.python.org/pypi/calmjs
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
  into a Python environment.  For installation, please refer to the
  following section.

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
