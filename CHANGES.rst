Changelog
=========

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
