calmjs.dev
==========

Package for aiding the development of JavaScript code to be provided as
part of Python packages through integration with `Node.js`_ development
tools into a Python environment via the `Calmjs framework`_.

.. image:: https://travis-ci.org/calmjs/calmjs.dev.svg?branch=1.1.x
    :target: https://travis-ci.org/calmjs/calmjs.dev
.. image:: https://ci.appveyor.com/api/projects/status/0mxtiaf2j98w5fy6/branch/1.1.x?svg=true
    :target: https://ci.appveyor.com/project/metatoaster/calmjs-dev/branch/1.1.x
.. image:: https://coveralls.io/repos/github/calmjs/calmjs.dev/badge.svg?branch=1.1.x
    :target: https://coveralls.io/github/calmjs/calmjs.dev?branch=1.1.x


Introduction
------------

Python packages can contain arbitrary resource files, which can include
JavaScript sources.  This situation is commonly found in packages that
provide frontend functionalities that enhance user experience that
require interactions with a related backend Python code running on the
server provided by the given package.  In order to facilitate the
testing of those JavaScript code from those Python packages, commonly
`Node.js`_ packages and frameworks are often used to achieve this.

Typically, for the management of this dependency, this often require two
or more separate package management systems that are not properly aware
of each other, resulting in often cumbersome linkage or needless
duplication of packages installed on a given system.  Moreover, the
configurations files for the Node.js/JavaScript package dependencies,
along with the building of artifacts and testing of the JavaScript
provided by those Python packages are very specific to the given project
and generally not portable.  If multiple such packages are required for
a downstream Python project, the scripts and definition files for
building of artifacts and testing generally have to be manually
modified, which is often a very aggravating and error-prone process.

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
.. |npm| replace:: ``npm``
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
      A set of spies, stubs and mocks for JavaScript, for working with
      unit testing frameworks.

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

As the goal of |calmjs.dev| is to integrate Node.js development tools
into a Python environment, both Node.js and |npm| are required to be
available within the target installation environment; if they are not
installed please follow the installation steps for `Node.js`_
appropriate for the target operating system/environment/platform.

Naturally, since this is achieved through |calmjs|, it will need to be
available in the target installation environment; however, this is
achieved simply by installing |calmjs.dev| through ``pip`` from PyPI.

.. code:: sh

    $ pip install calmjs.dev

Alternative installation methods (for developers, advanced users)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Development is still ongoing with |calmjs.dev|, for the latest features
and bug fixes, the development version may be desirable; however, the
|calmjs| package *must* be installed first, otherwise the metadata must
be regenerated after the installation, which can be achieved like so:

.. code:: sh

    $ pip install git+https://github.com/calmjs/calmjs.git#egg=calmjs

Alternatively, the git repository can be cloned directly and execute
``python setup.py develop`` while inside the root of the source
directory.  Failure to do so will result in failure to install the
development packages via |calmjs| from |npm|.  This failure can be
verified by tests for this package failed to correctly execute, and the
appearance of ``distribution option: 'package_json'`` warning message
while installing this package.

As |calmjs| is declared as both a namespace and a package, mixing
installation methods as described above when installing with other
|calmjs| packages may result in the module importer being unable to look
up the target files.  If such an error does arise please remove all
modules and only stick with a single installation method for all
packages within the |calmjs| namespace.

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

Do note a number of failures during execution of Karma may appear; this
is normal as these are tests that involve the simulation of failures to
ensure proper error handling on real test failures.

Usage
-----

The default tool is meant to provide an injectable runtime that sits
before a |calmjs| toolchain runtime that is responsible for the
generation of deployable artifacts, such as AMD bundles through
RequireJS.  Currently, the standard way to use this package is to use it
in conjunction of the |calmjs.rjs|_ package runtime.  For instance, one
might execute the ``r.js`` tool through |calmjs.rjs| like:

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
karma -h`` or ``calmjs karma run -h``.  Replacing the ``-h`` flag with
``-V`` will report the version information for the underlying packages
associated with the respective runtime used.

More on testing in conjunction with artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``--artifact`` flag can also be specified directly on the ``karma``
runner; this has the consequence of enabling the testing of limited or
explicitly mapped JavaScript sources exported by specific Python
modules.  What this means is that instead of building and testing all
the dependency modules along with a given module, all those dependencies
can be applied to the test environment as a separate, complete artifact.
This has the effect of removing the dependency sources from the build
directory such that coverage report no longer shows up, with the bonus
of also testing the artifact whether or not the it is compatible with
the sources being tested.  An example with the ``nunja.stock`` package
which requires ``nunja``:

.. code:: sh

    $ calmjs rjs nunja
    $ calmjs karma --cover-artifact --artifact=nunja.js --coverage \
        --cover-test rjs nunja.stock --source-map-method=explicit

The first command produces the artifact file ``nunja.js``, which is then
immediately used by the subsequent command which explicitly filters out
all other sources not specified.  Otherwise, the standard way is that
the dependencies will also be included into the test and the resulting
artifact file.


Troubleshooting
---------------

The following may be some issues that may be encountered with standard
or typical usage of |calmjs.dev|.

Error: No provider for "framework:mocha"! (Resolving: framework:mocha)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most likely cause of this error is that the |npm| dependencies
specified for this package is not available for the current Node.js
environment.  Please ensure that is installed before trying again.  One
method is to prepend |calmjs.dev| to the ``calmjs npm`` install command,
e.g:

.. code:: sh

    $ calmjs npm --install calmjs.dev ...

Alternatively, package developers can have extras that requires this
package, and instruct downstream users interested in the development of
that package to install and use the package with that extras flag
enabled.  For instance, ``nunja`` has the support for that:

.. code:: sh

    $ calmjs npm --install nunja[dev]

ERROR [plugin]: "karma-..." plugin: ...
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A message specific to some plugin may result in the test runner not
being able to execute any test.  This is typically caused by certain
versions of karma test runner not being able to cleanly deal with
misbehaving plugins that is available in the ``node_modules`` directory.
If the plugin shown inside the quote (starting with ``karma-``) is
unnecessary for the execution of tests, it should be removed and the
test command should be executed again.

UserWarning: Unknown distribution option: 'package_json'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Installation using the development method will show the above message if
|calmjs| was not already installed into the current environment.  Please
either reinstall, or regenerate the metadata by running:

.. code:: sh

    $ python setup.py egg_info

In the root of the |calmjs.dev| source directory to ensure correct
behavior of this package.


Contribute
----------

- Issue Tracker: https://github.com/calmjs/calmjs.dev/issues
- Source Code: https://github.com/calmjs/calmjs.dev


Legal
-----

The Calmjs project is copyright (c) 2016 Auckland Bioengineering
Institute, University of Auckland.  |calmjs.dev| is licensed under the
terms of the GPLv2 or later.
