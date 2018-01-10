# -*- coding: utf-8 -*-
"""
This module provides handlers for the toolchain classes and instances
declared for the calmjs framework, reading the compile descriptions and
select the resulting spec targets for usage
"""

import logging
from itertools import chain
from os.path import pathsep
from argparse import SUPPRESS

from calmjs.argparse import StoreDelimitedList
from calmjs.argparse import StorePathSepDelimitedList
from calmjs.argparse import StoreRequirementList
from calmjs.argparse import metavar
from calmjs.toolchain import ADVICE_PACKAGES
from calmjs.toolchain import ARTIFACT_PATHS
from calmjs.toolchain import BUILD_DIR
from calmjs.toolchain import CALMJS_TEST_REGISTRY_NAMES
from calmjs.toolchain import TEST_PACKAGE_NAMES
from calmjs.runtime import BaseArtifactRegistryRuntime
from calmjs.runtime import ToolchainRuntime
from calmjs.runtime import DriverRuntime
from calmjs.runtime import Runtime

from calmjs.dev.cli import KarmaDriver
from calmjs.dev.cli import karma_verify_package_artifacts
from calmjs.dev.toolchain import prepare_spec_from_runtime
from calmjs.dev.toolchain import KarmaToolchain
from calmjs.dev.toolchain import COVERAGE_ENABLE
from calmjs.dev.toolchain import COVER_REPORT_TYPES
from calmjs.dev.toolchain import COVER_ARTIFACT
from calmjs.dev.toolchain import COVER_BUNDLE
from calmjs.dev.toolchain import COVER_REPORT_DIR
from calmjs.dev.toolchain import COVER_REPORT_FILE
from calmjs.dev.toolchain import COVER_TEST
from calmjs.dev.toolchain import COVERAGE_TYPE
from calmjs.dev.toolchain import NO_WRAP_TESTS
from calmjs.dev.karma import COVER_REPORT_TYPE_OPTIONS
from calmjs.dev.karma import DEFAULT_COVER_REPORT_TYPE_OPTIONS
from calmjs.dev.karma import KARMA_ABORT_ON_TEST_FAILURE
from calmjs.dev.karma import KARMA_BROWSERS
from calmjs.dev.karma import KARMA_EXTRA_FRAMEWORKS

logger = logging.getLogger(__name__)

CALMJS_DEV_RUNTIME_KARMA = 'calmjs.dev.runtime.karma'

__all__ = ['KarmaRuntime', 'karma']


def init_argparser_common(argparser):

    # default values as empty lists to not override existing values.

    argparser.add_argument(
        '--test-registry', default=[],
        dest=CALMJS_TEST_REGISTRY_NAMES, action=StoreDelimitedList,
        metavar='<registry>[,<registry>...]',
        help='comma separated list of registries to use for gathering '
             'JavaScript tests from the Python packages specified via the '
             'toolchain runtime; default behavior is to auto-select, '
             'verbose logging output will list the selection',
    )

    argparser.add_argument(
        '--test-registries', default=[],
        dest=CALMJS_TEST_REGISTRY_NAMES, action=StoreDelimitedList,
        help=SUPPRESS,
    )

    argparser.add_argument(
        '-u', '--test-with-package', default=[],
        metavar='<package>[,<package>...]',
        dest=TEST_PACKAGE_NAMES, action=StoreDelimitedList,
        help='explicitly specify Python package(s) to gather JavaScript tests '
             'from, overriding any automatic resolution that may be in place; '
             'no dependency resolution will be applied to acquire extra tests',
    )

    argparser.add_argument(
        '--test-with-packages', default=[],
        metavar='<package>[,<package>...]',
        dest=TEST_PACKAGE_NAMES, action=StoreDelimitedList,
        help=SUPPRESS,
    )

    # don't ever remove deprecation for --test-package, because it is
    # a very confusing flag in this context - the message will always
    # refer to the above, as the subject to be tested is provided, the
    # package providing the tests to test the subject with is what this
    # flag specifies, not the package to be tested.

    argparser.add_argument(
        '--test-package', default=[],
        metavar='<package>[,<package>...]',
        dest=TEST_PACKAGE_NAMES, action=StoreDelimitedList,
        deprecation="please use '--test-with-package' instead",
    )

    argparser.add_argument(
        '--test-packages', default=[],
        metavar='<package>[,<package>...]',
        dest=TEST_PACKAGE_NAMES, action=StoreDelimitedList,
        deprecation="please use '--test-with-packages' instead",
    )

    argparser.add_argument(
        '--browser', default=[],
        metavar='<browser>[,<browser>...]',
        dest=KARMA_BROWSERS, action=StoreDelimitedList,
        help="comma separated list of browsers to use for testing; they must "
             "be available within the current Node.js installation; values "
             "are case sensitive, refer to the documentation for the relevant "
             "karma-*-launcher npm modules; defaults to 'PhantomJS'",
    )

    argparser.add_argument(
        '--browsers', default=[],
        dest=KARMA_BROWSERS, action=StoreDelimitedList,
        help=SUPPRESS,
    )

    argparser.add_argument(
        '-c', '--coverage',
        dest=COVERAGE_ENABLE, action='store_true',
        help='enable coverage report',
    )

    argparser.add_argument(
        '--cover-report-dir',
        dest=COVER_REPORT_DIR, action='store', default='coverage',
        metavar=metavar('DIR'),
        help="location to store the coverage report; "
             "defaults to 'coverage'",
    )

    argparser.add_argument(
        '--cover-report-file',
        dest=COVER_REPORT_FILE, action='store',
        metavar=metavar('FILE'),
        help="location to write the coverage report file for the case where "
             "a single coverage type was specified and that the coverage type "
             "report is a single file; the default value is coverage type "
             "specific, and this option is omitted where not applicable, or "
             "when multiple coverage report types are specified",
    )

    argparser.add_argument(
        '--cover-report-type',
        dest=COVER_REPORT_TYPES,
        default=DEFAULT_COVER_REPORT_TYPE_OPTIONS,
        choices=sorted(COVER_REPORT_TYPE_OPTIONS.keys()),
        action=StoreDelimitedList,
        help="the type of coverage report to generate; "
             "the default is a custom multiple coverage report "
             "configuration",
    )

    argparser.add_argument(
        '--cover-report-types',
        dest=COVER_REPORT_TYPES,
        default=DEFAULT_COVER_REPORT_TYPE_OPTIONS,
        choices=sorted(COVER_REPORT_TYPE_OPTIONS.keys()),
        action=StoreDelimitedList,
        help=SUPPRESS,
    )

    argparser.add_argument(
        '--coverage-type',
        dest=COVERAGE_TYPE,
        default=None,
        choices=sorted(list(COVER_REPORT_TYPE_OPTIONS.keys()) + ['default']),
        action='store',
        deprecation="will be removed by calmjs.dev-3.0.0; please use "
                    "'--cover-report-type' instead",
    )

    argparser.add_argument(
        '--cover-test',
        dest=COVER_TEST, action='store_true',
        help="include test sources for coverage report",
    )

    argparser.add_argument(
        '--artifact', default=[],
        dest=ARTIFACT_PATHS, action=StorePathSepDelimitedList,
        metavar='<file>[%s<file>...]' % pathsep,
        help="artifact file(s) to be included for test execution; multiple "
             "files may be specified using multiple seperate flags, or be "
             "specified under a single flag with each path separated by the "
             "platform's path separation character '%s'" % pathsep,
    )

    argparser.add_argument(
        '--cover-artifact',
        dest=COVER_ARTIFACT, action='store_true',
        help="include artifacts for coverage report",
    )

    argparser.add_argument(
        '--no-wrap-tests', '--disable-wrap-tests',
        dest=NO_WRAP_TESTS, action='store_true',
        help="do not wrap tests with a function closure",
    )

    argparser.add_argument(
        '--wrap-tests', '--enable-wrap-tests',
        dest=NO_WRAP_TESTS, action='store_false',
        # help="tests with a function closure",
        help=SUPPRESS,
    )


class TestToolchainRuntime(ToolchainRuntime):
    """
    base karma runner for pre-built artifacts
    """

    def init_argparser_export_target(self, argparser):
        """
        There are no export targets
        """

    def init_argparser_build_dir(self, argparser):
        """
        The 'build dir' is use for just the karma configuration.
        """

        super(TestToolchainRuntime, self).init_argparser_build_dir(
            argparser, help=(
                'the build directory, where the generated files for the '
                'execution of karma will be written to; if unspecified, a '
                'new temporary directory will be created and removed once the '
                'test concludes'
            )
        )

    def init_argparser_optional_advice(self, argparser):
        """
        We have our own set of advices for the karma runtime, so
        disabling this.
        """

    def init_argparser(self, argparser):
        """
        Keep everything in parent as the overrides are applied above.
        The working directory option is also kept.
        """

        super(TestToolchainRuntime, self).init_argparser(argparser)

        argparser.add_argument(
            '--extra-frameworks', default=[],
            dest=KARMA_EXTRA_FRAMEWORKS, action=StoreDelimitedList,
            metavar='<framework>[,<framework>...]',
            help='comma separated list of extra frameworks to be added to '
                 'the generated karma configuration; the package for the '
                 'framework must exist for the current Node.js installation',
        )

        argparser.add_argument(
            '-t', '--toolchain-package', default=None,
            required=False, dest=ADVICE_PACKAGES,
            action=StoreRequirementList, maxlen=1,
            metavar=metavar('PACKAGE'),
            help='the name of the package that supplied the original '
                 'toolchain that created the artifacts selected; extras may '
                 'be permitted, consult the documentation for that package '
                 'for details; this is used for setting up advices for '
                 'getting karma to start correctly for whatever framework '
                 'that was used; only one may be specified',
        )

        argparser.add_argument(
            dest=TEST_PACKAGE_NAMES, nargs='*', default=[],
            metavar='<package>',
            help='Python package to gather JavaScript tests from; '
                 'no package dependency resolution will be applied'
        )

        init_argparser_common(argparser)

    def prepare_spec_export_target_checks(self, spec, **kwargs):
        """
        Do nothing, as no export targets.
        """


class KarmaArtifactRuntime(BaseArtifactRegistryRuntime):
    """
    karma runner for testing of pre-built artifacts in packages
    """

    def init_argparser(self, argparser):
        """
        Keep everything in parent as the overrides are applied above.
        The working directory option is also kept.
        """

        # skipping the direct parent as the complete invocation/setup
        # is manually done.
        super(BaseArtifactRegistryRuntime, self).init_argparser(argparser)
        init_argparser_common(argparser)

        argparser.add_argument(
            '-x', '--exit-first',
            dest=KARMA_ABORT_ON_TEST_FAILURE, action='store_true',
            help='abort on the first failed artifact',
        )

        # since the default doesn't provide this as a toolchain runtime,
        # but the underlying execution model supports this (as it makes
        # use of toolchain and its execution model), provide this as a
        # hidden option for the use case that require this.
        argparser.add_argument(
            '--build-dir', default=None, dest=BUILD_DIR,
            metavar=metavar(BUILD_DIR), help=SUPPRESS,
        )

        self.init_argparser_package_names(
            argparser, help='Python packages to verify artifacts for')

    def run(self, argparser=None, package_names=[], **kwargs):
        return karma_verify_package_artifacts(package_names, **kwargs)


class KarmaRuntime(Runtime, DriverRuntime):
    """
    The runtime class for karma
    """

    def __init__(
            self, cli_driver,
            action_key='karma_runtime',
            karma_entry_point_group=CALMJS_DEV_RUNTIME_KARMA,
            description='karma testrunner integration for calmjs',
            *a, **kw):
        self.karma_entry_point_group = karma_entry_point_group
        super(KarmaRuntime, self).__init__(
            cli_driver=cli_driver, description=description,
            action_key=action_key, *a, **kw)

    def entry_point_load_validated(self, entry_point):
        # to avoid trying to import this again, check entry_point first
        if entry_point.name == 'karma':
            return False

        inst = super(KarmaRuntime, self).entry_point_load_validated(
            entry_point)
        if not isinstance(inst, ToolchainRuntime):
            logger.debug(
                "filtering out entry point '%s' as it does not lead to a "
                "calmjs.runtime.ToolchainRuntime in KarmaRuntime.",
                entry_point
            )
            return False
        return inst

    def iter_entry_points(self):
        for ep in sorted(
                chain(*tuple(map(self.working_set.iter_entry_points, (
                    self.karma_entry_point_group, self.entry_point_group)))),
                key=lambda ep: ep.name):
            yield ep

    def init_argparser(self, argparser):
        super(KarmaRuntime, self).init_argparser(argparser)

        init_argparser_common(argparser)

        argparser.add_argument(
            '--cover-bundle',
            dest=COVER_BUNDLE, action='store_true',
            help="include bundled sources for coverage report",
        )

        argparser.add_argument(
            '-I', '--ignore-errors',
            dest=KARMA_ABORT_ON_TEST_FAILURE, action='store_false',
            help='do not abort execution on failure',
        )

    def _run_runtime(self, runtime, **kwargs):
        spec = prepare_spec_from_runtime(runtime, **kwargs)
        toolchain = runtime.toolchain
        self.cli_driver.run(toolchain, spec)
        return spec

    def run(self, argparser, **kwargs):
        # have to rely on the local one, because the passed in one will
        # be the root one.
        details = self.get_argparser_details(self.argparser)
        runtime = details.runtimes.get(kwargs.pop(self.action_key))
        if runtime:
            return self._run_runtime(runtime, **kwargs)

        argparser.print_help()
        return


# this will be registered to the karma specific thing.
run = TestToolchainRuntime(KarmaToolchain())
karma = KarmaRuntime(KarmaDriver.create())
artifact_karma = KarmaArtifactRuntime()
