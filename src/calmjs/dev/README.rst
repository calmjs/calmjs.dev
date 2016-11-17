Module layout
=============

This module, ``calmjs.dev``, also follows the ``calmjs`` module layout
order, but for clarity sake, the list follows:

karma
    Karma specific module; provide a function to generate the skeleton
    configuration file, plus definition of shared constants.

utils
    Utilities for use here, and also for packages depending on this one.

dist
    Module that interfaces with distutils/setuptools helpers provided by
    ``calmjs``, for assisting with gathering registries for the tests.

toolchain
    Provide a skeleton toolchain for the execution of tests against pre-
    built artifacts, plus definitions of constants to be used within the
    ``Spec`` for a given run.

cli
    Module that provides the functions that call out to cli tools that
    will support the functionality needed by the calmjs framework, in
    the case for this module it would be the integration with ``karma``.

runtime
    The module that provides the classes and functions that aid with
    providing the entry point into calmjs from cli and elsewhere.
    Supports the generation of the texts for users from the shell.

As a general rule, a module should not inherit from modules listed below
their respective position on the above list.
