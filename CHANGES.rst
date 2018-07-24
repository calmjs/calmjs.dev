Changelog
=========

2.2.0 (2018-07-24)
------------------

- Support the correct resolution of test child module registries, which
  was introduced in ``calmjs-3.3.0``.  [
  `#6 <https://github.com/calmjs/calmjs.dev/issues/6>`_
  ]
- Ensure that a missing karma binary is also correctly dealt with by the
  same set of exception and flags.  [
  `#7 <https://github.com/calmjs/calmjs.dev/issues/7>`_
  ]

2.1.0 (2018-05-28)
------------------

- Ensure the exit code indicates failure if the artifact test entry
  point references an import that cannot be resolved (failure to set up
  the test must result in a failure). [
  `#3 <https://github.com/calmjs/calmjs.dev/issues/3>`_
  ]
- Make use of the corrected semantics provided by calmjs-3.1.0 for the
  deferred export location verification, which also silences the
  calmjs-4.0.0 deprecation warning. [
  `#5 <https://github.com/calmjs/calmjs.dev/issues/5>`_
  ]

2.0.0 (2018-01-10)
------------------

- Migration to the calmjs-3.0.0 API.
- Bumped a number of dependencies on Node.js packages.
- The paths that are covered by the test coverage report are now
  recorded in the Spec as part of the test execution workflow through
  the KarmaDriver.
- Provide framework and command for testing of predefined artifacts
  generated for packages defined through the ``calmjs.artifacts``
  registry; ``calmjs.artifacts.tests`` registry was created such that
  toolchain packages may declare the test compliment builder functions
  to facilitate testing for their dependent packages.
- Implemented ``--cover-report-type`` flag to support the specification
  of multiple coverage report types to be generated, and ensured that
  the defined report types actually work (a karma/istanbul bug was
  found and a workaround was implemented).
- A number of internal code refactor, i.e. a number of internal API
  changes have happened.
- Deprecated ``--coverage-type`` flag, as it is inconsistently named and
  that features provided by ``--cover-report-type`` superseded this.
- Deprecated ``--test-package`` flag in favor of ``--test-with-package``
  for more clarity about the intention of that flag.

1.1.0 (2017-08-10)
------------------

- Tests are now automatically wrapped by a default template when served
  by karma to better limit the scope of the variables defined within
  each file.  This can be disabled using ``--no-wrap-tests`` flag on the
  ``karma`` runtime.

1.0.3 (2017-05-22)
------------------

- Move the ``--artifact`` and ``--cover-artifact`` flag up to the main
  ``karma`` runtime to permit wider and more flexible usage for all
  runners.
- Correctly report the path of missing specified artifacts in the logs.

1.0.2 (2017-01-27)
------------------

- Provide test prefix key and constant.

1.0.1 (2016-11-30)
------------------

- Correct the inability to launch standard graphical browsers directly
  via the runner under Windows.

1.0.0 (2016-11-18)
------------------

- Initial release of the development support for the calmjs framework.
- Include karma test runner integration as a calmjs runtime that can
  accept calmjs toolchain runtimes to facilitate testing.
- Generation of test coverage reports of JavaScript sources executed.
- Leverage the toolchain advice system for adding the test runner and
  also permit the modification of test configurations by toolchain
  implementations that require specific instructions for a successful
  execution of tests.
- Permit integration with other packages for testing artifacts generated
  by other systems.
