Changelog
=========

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
