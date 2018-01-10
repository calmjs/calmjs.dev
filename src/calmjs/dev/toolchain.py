# -*- coding: utf-8 -*-
import logging
from os.path import exists
from os.path import realpath

from calmjs.toolchain import Toolchain
from calmjs.toolchain import ARTIFACT_PATHS
from calmjs.toolchain import CALMJS_MODULE_REGISTRY_NAMES
from calmjs.toolchain import CALMJS_TEST_REGISTRY_NAMES
from calmjs.toolchain import TEST_PACKAGE_NAMES
from calmjs.toolchain import BUILD_DIR
from calmjs.dist import flatten_module_registry_names

from calmjs.dev.karma import KARMA_BROWSERS
from calmjs.dev.karma import KARMA_EXTRA_FRAMEWORKS
from calmjs.dev.karma import KARMA_ABORT_ON_TEST_FAILURE

logger = logging.getLogger(__name__)

# reserved terms
# flag for enabling coverage through karma-coverage (istanbul)
COVERAGE_ENABLE = 'coverage_enable'
# the types of the coverage report to generate
COVER_REPORT_TYPES = 'cover_report_types'
# deprecated flag - this only specifies the legacy singular option
COVERAGE_TYPE = 'coverage_type'
# flag for including coverage report for artifacts
COVER_ARTIFACT = 'cover_artifact'
# flag for including coverage report for bundled modules
COVER_BUNDLE = 'cover_bundle'
# an optional filter function to filter out what paths to be covered.
COVER_PATH_FILTER = 'cover_path_filter'
# the dir to write the coverage report to
COVER_REPORT_DIR = 'cover_report_dir'
# the file to write the coverage report to for selected reporters.
COVER_REPORT_FILE = 'cover_report_file'
# flag for including coverage report for tests.
COVER_TEST = 'cover_test'
# no wrap tests with a function closure
NO_WRAP_TESTS = 'no_wrap_tests'
# test filename prefix
TEST_FILENAME_PREFIX = 'test_filename_prefix'

# the paths to be covered by the tests
# artifacts that were covered
TEST_COVERED_ARTIFACT_PATHS = 'test_covered_artifact_paths'
# paths relative to the build_dir (i.e. inside it) that are covered
TEST_COVERED_BUILD_DIR_PATHS = 'test_covered_build_dir_paths'
# the test paths that were covered
TEST_COVERED_TEST_PATHS = 'test_covered_test_paths'

COVER_REPORT_DIR_DEFAULT = 'coverage'
TEST_FILENAME_PREFIX_DEFAULT = 'test'

# BBB backward compat
COVERAGE_TYPE_DEFAULT = 'default'


def prepare_spec_artifacts(spec):

    def checkpaths(paths):
        for p in paths:
            realp = realpath(p)
            if not exists(realp):
                logger.warning(
                    "specified artifact '%s' does not exists", realp)
                continue
            logger.debug("specified artifact '%s' found", realp)
            yield realp

    # do not sort this list, it is provided with a specific order
    if spec.get(ARTIFACT_PATHS):
        # do this to conform to usage for artifact_paths in spec.
        spec[ARTIFACT_PATHS] = list(checkpaths(spec.get(ARTIFACT_PATHS)))


def update_spec_for_karma(spec, **kwargs):
    # This method assigns default values of the specific type to
    # the spec, complimenting a toolchain runtime's kwargs_to_spec
    # method, to ensure that they are added correctly.
    post_process_group = (
        # default value, and keys to be assigned that
        (None, [
            KARMA_ABORT_ON_TEST_FAILURE,
            COVERAGE_ENABLE,
            COVER_REPORT_DIR,
            COVER_REPORT_FILE,
            COVER_ARTIFACT,
            COVER_BUNDLE,
            COVER_TEST,
            NO_WRAP_TESTS,
            BUILD_DIR,
            # deprecated flag
            COVERAGE_TYPE,
        ]),
        # For all list types.
        ([], [
            ARTIFACT_PATHS,
            CALMJS_TEST_REGISTRY_NAMES,
            COVER_REPORT_TYPES,
            TEST_PACKAGE_NAMES,
            KARMA_BROWSERS,
            KARMA_EXTRA_FRAMEWORKS,
        ]),
    )
    for defaultvalue, post_process in post_process_group:
        for key in post_process:
            if kwargs.get(key, defaultvalue) != defaultvalue:
                if defaultvalue is None:
                    spec[key] = kwargs[key]
                else:
                    # shallow copy.
                    spec[key] = type(defaultvalue)(kwargs[key])
            else:
                # pop them out from spec
                spec.pop(key, None)


def prepare_spec_from_runtime(runtime, **kwargs):
    spec = runtime.kwargs_to_spec(**kwargs)

    # The above runtime specific method MAY strip off all keys that
    # it doesn't understand; so for the critical keys that the karma
    # runtime require/supply, plug them back in like so:
    update_spec_for_karma(spec, **kwargs)
    prepare_spec_artifacts(spec)

    return spec


class TestToolchain(Toolchain):
    """
    A toolchain that truly does nothing, except to fit in with the
    pattern of getting tests up, and to serve as a safe location for
    other toolchains to register advice steps that they normally add as
    part of their execution.
    """

    def compile(self, spec):
        """
        Do nothing.
        """

    def prepare(self, spec):
        """
        Do nothing.
        """

    def assemble(self, spec):
        """
        Do nothing.
        """

    def link(self, spec):
        """
        Do nothing.
        """


class KarmaToolchain(TestToolchain):
    """
    This one specifically for karma.
    """

    def prepare(self, spec):
        # simply add the registry names provided by as test package
        # names
        spec[CALMJS_MODULE_REGISTRY_NAMES] = flatten_module_registry_names(
            spec.get(TEST_PACKAGE_NAMES, []))
