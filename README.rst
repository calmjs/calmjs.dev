calmjs.dev
==========

A package that declares common development tools that integrates with
|calmjs|_ along with commonly used |nodejs|_ development frameworks.
These declarations can then be invoked by packages that depend on this
one to instantiate the actual environment with the declared frameworks
installed.


Introduction
------------

To facilitate standardized deployment of working |nodejs|_ environments,
and also for the execution of tests provided by Python packages against
the JavaScript code that they might include, this package declares
commonly used ``devDependencies`` in its ``package.json`` file which is
declared through the ``calmjs`` extensions to |setuptools|_.  Other
Python packages may then declare their dependencies through ``setup.py``
to pick up and make use of the following set of tools through the
appropriate entry points to ``calmjs`` and/or ``setuptools`` command.

.. |calmjs| replace:: ``calmjs``
.. |nodejs| replace:: ``nodejs``
.. |setuptools| replace:: ``setuptools``
.. _calmjs: https://pypi.python.org/pypi/calmjs
.. _nodejs: https://nodejs.org
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

- Through the use of ``calmjs.module`` registry, which exposes the
  declared Python modules as providers of JavaScript modules, generate
  the required configuration files for the supported JavaScript
  development tools.  Details of the various implementation will be
  specific to the software packages involved.

- A declared set of development dependencies.  This is reusable through
  the |setuptools|_ extensions provided by |calmjs|_.

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


Usage
-----

- Issue Tracker: https://github.com/calmjs/calmjs.dev/issues
- Source Code: https://github.com/calmjs/calmjs.dev


License
-------

``calmjs.dev`` is licensed under the GPLv2 or later.
