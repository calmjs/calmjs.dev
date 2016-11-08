# -*- coding: utf-8 -*-
"""
This module provides interface to the karma cli runtime.
"""

import logging
import os
import re
from os.path import curdir
from os.path import join
from os.path import realpath
from os.path import sep
from subprocess import call

from calmjs.exc import AdviceAbort
from calmjs.exc import ToolchainAbort

from calmjs.toolchain import BEFORE_LINK
from calmjs.toolchain import BEFORE_TEST
from calmjs.toolchain import AFTER_TEST
from calmjs.toolchain import BUILD_DIR

from calmjs.toolchain import ARTIFACT_PATHS
from calmjs.toolchain import CALMJS_MODULE_REGISTRY_NAMES
from calmjs.toolchain import CALMJS_TEST_REGISTRY_NAMES
from calmjs.toolchain import SOURCE_PACKAGE_NAMES
from calmjs.toolchain import TEST_PACKAGE_NAMES
from calmjs.toolchain import TEST_MODULE_PATHS_MAP

from calmjs.cli import NodeDriver
from calmjs.cli import get_bin_version

from calmjs.dev import dist
from calmjs.dev import karma
from calmjs.dev import utils

from calmjs.dev.toolchain import COVERAGE_ENABLE
from calmjs.dev.toolchain import COVERAGE_TYPE
from calmjs.dev.toolchain import COVER_BUNDLE
from calmjs.dev.toolchain import COVER_REPORT_DIR
from calmjs.dev.toolchain import COVER_REPORT_FILE
from calmjs.dev.toolchain import COVER_TEST

from calmjs.dev.toolchain import COVERAGE_TYPE_DEFAULT
from calmjs.dev.toolchain import COVER_REPORT_DIR_DEFAULT

logger = logging.getLogger(__name__)


class KarmaDriver(NodeDriver):
    """
    The karma driver
    """

    # dream cli?
    # calmjs karma --test-registry calmjs.tests nunja.tests \
    #     rjs --build-dir foo --source-registry calmjs.module nunja.mold -- \
    #     nunja
    # this way, must assert that the target DriverRuntime is of that
    # type, AND that its' cli_driver is a Toolchain instance.
    # or rather
    # calmjs karma --test-registry nunja.tests --source-registry nunja.mold
    # for a live mode

    # bundling of course will simply be
    # calmjs rjs --source-registry nunja.mold --export-filename nunja.js
    # then the testing of the bundle
    # calmjs karma --test-registry nunja.tests <packages> --with-artifact \
    #     nunja.js

    def __init__(
            self,
            binary='karma', karma_conf_js=karma.KARMA_CONF_JS,
            testrunner_advice_name=BEFORE_LINK,
            *a, **kw):
        """
        Arguments

        binary
            The name of the karma server binary; defaults to karma.
        karma_conf_js
            Name of generated config script; defaults to karma.conf.js
        testrunner_advice_name
            The advice name to trigger the test on.
        """

        super(KarmaDriver, self).__init__(*a, **kw)
        self.binary = binary
        self.testrunner_advice_name = testrunner_advice_name
        self.karma_conf_js = karma_conf_js

    def get_karma_version(self):
        kw = self._gen_call_kws()
        return get_bin_version(self.binary, version_flag='--version', kw=kw)

    def karma(self, spec):
        """
        Start karma with the provided spec
        """

        spec.handle(karma.BEFORE_KARMA)

        config_fn = join(spec[BUILD_DIR], self.karma_conf_js)
        # due to broken karma-plugins implementation, HOME is a required
        # environment variable (as often times they are joined with path
        # fragments without checking if they are undefined).  Reference:
        # <https://github.com/karma-runner/karma-firefox-launcher/pull/58>
        call_kw = self._gen_call_kws(
            HOME=os.environ.get('HOME', ''),
        )
        logger.info('invoking %s start %r', self.binary, config_fn)
        # TODO would be great if there is a way to "tee" the result into
        # both here and stdout.
        # perhaps the provided spec can contain well-defined keywords
        # that can be passed to the `call` function (extend call_kw).
        # For now at least log this down like so.
        binary = self.which() or self.which_with_node_modules()
        if binary is None:
            raise AdviceAbort('karma not found')
        # but actually run it with the '--color' flag, because otherwise
        # colors don't work consistently... Node.js tools in a nutshell.
        # ... at least disable colours in the config file will also make
        # this option disabled.
        spec[karma.KARMA_RETURN_CODE] = call(
            [binary, 'start', config_fn, '--color'], **call_kw)

        spec.handle(karma.AFTER_KARMA)

    def abort_on_test_failure(self, spec):
        if spec.get(karma.KARMA_RETURN_CODE):
            raise ToolchainAbort('karma exited with return code %s' % spec.get(
                karma.KARMA_RETURN_CODE))

    def warn_on_test_failure(self, spec):
        if spec.get(karma.KARMA_RETURN_CODE):
            logger.warning(
                'karma exited with return code %s; continuing as specified',
                spec.get(karma.KARMA_RETURN_CODE),
            )

    def _pick_spec_keys(
            self, spec, target, fallback,
            fallback_callback=None, default=None):
        # Extract the available data stored in the spec.
        if target in spec:
            result = spec.get(target)
            logger.debug("spec has '%s' explicitly specified", target)
            return result
        logger.debug(
            "spec has no '%s' specified, falling back to '%s'",
            target, fallback
        )
        result = spec.get(fallback, default)
        if fallback_callback:
            result = fallback_callback(result)
        return result

    def _valid_cover_file(self, path):
        return path.endswith('js') and not re.search('__\w*__', path)

    def _apply_coverage_config(self, spec, config, files, test_module_paths):
        if not spec.get(COVERAGE_ENABLE):
            return

        # for the preprocessors key
        paths = set(files)

        if not spec.get(COVER_BUNDLE):
            # remove all the bundled sources
            for path in spec.get('bundled_targets', {}).values():
                paths.discard(path)

        if spec.get(COVER_TEST):
            for path in test_module_paths:
                paths.add(path)

        # for the coverageReporter key
        coverage_reporter = {
            'type': spec.get(COVERAGE_TYPE, COVERAGE_TYPE_DEFAULT),
            'dir': realpath(spec.get(
                COVER_REPORT_DIR, COVER_REPORT_DIR_DEFAULT)),
        }

        if spec.get(COVER_REPORT_FILE):
            covfile = spec.get(COVER_REPORT_FILE)
            if covfile.startswith(curdir + sep):
                covfile = realpath(covfile)
            coverage_reporter['file'] = covfile

        # finally, modify the config
        config['reporters'] = list(config['reporters']) + ['coverage']
        config['preprocessors'] = {
            path: 'coverage' for path in paths if self._valid_cover_file(path)}
        config['coverageReporter'] = coverage_reporter

    def _create_config(self, spec, spec_keys):
        package_names = self._pick_spec_keys(
            spec, TEST_PACKAGE_NAMES, SOURCE_PACKAGE_NAMES, default=[])

        module_registries = self._pick_spec_keys(
            spec, CALMJS_TEST_REGISTRY_NAMES, CALMJS_MODULE_REGISTRY_NAMES,
            fallback_callback=lambda x: list(
                dist.map_registry_name_to_test(x)),
            default=[]
        )

        logger.info(
            "karma driver to extract tests from packages %r using "
            "registries %r for testing", package_names, module_registries,
        )

        # calculate, extract and persist the test module names
        test_module_paths_map = spec[TEST_MODULE_PATHS_MAP] = spec.get(
            TEST_MODULE_PATHS_MAP, {})
        test_module_paths_map.update(dist.get_module_registries_dependencies(
            package_names, module_registries))

        config = karma.build_base_config()
        files = list(utils.get_targets_from_spec(spec, spec_keys))
        test_module_paths = sorted(test_module_paths_map.values())

        config['files'] = files + test_module_paths
        self._apply_coverage_config(spec, config, files, test_module_paths)
        return config

    def create_config(self, spec):
        spec_keys = spec.get(karma.KARMA_SPEC_KEYS, [])
        spec[karma.KARMA_CONFIG] = self._create_config(spec, spec_keys)

    def _write_config(self, spec):
        # grab the config from the spec.
        karma_config = spec.get(karma.KARMA_CONFIG)
        if not isinstance(karma_config, dict):
            logger.error(
                "no valid '%s' in spec; cannot write '%s'",
                karma.KARMA_CONFIG, self.karma_conf_js,
            )
            return

        files = []
        # prepend the file listing with the source artifacts.
        for f in (spec.get(ARTIFACT_PATHS), karma_config.get('files')):
            if isinstance(f, (tuple, list)):
                files.extend(f)
        karma_config['files'] = files

        s = self.dumps(karma_config)
        build_dir = spec[BUILD_DIR]
        config_fn = join(build_dir, self.karma_conf_js)
        with open(config_fn, 'w') as fd:
            fd.write(karma.KARMA_CONF_TEMPLATE % s)
        return config_fn

    def write_config(self, spec):
        spec[karma.KARMA_CONFIG_PATH] = self._write_config(spec)

    def test_spec(self, spec):
        spec.handle(BEFORE_TEST)
        self.karma(spec)
        spec.handle(AFTER_TEST)

    def setup_toolchain_spec(self, toolchain, spec):
        """
        Setup a spec for execution.
        """

        spec[karma.KARMA_SPEC_KEYS] = utils.get_toolchain_targets_keys(
            toolchain, exclude_targets_from=())
        karma_advice_group = spec.get(
            karma.KARMA_ADVICE_GROUP, self.testrunner_advice_name)
        spec.advise(karma_advice_group, self.test_spec, spec)
        spec.advise(BEFORE_TEST, self.create_config, spec)
        spec.advise(karma.BEFORE_KARMA, self.write_config, spec)

        if spec.get(karma.KARMA_ABORT_ON_TEST_FAILURE):
            spec.advise(AFTER_TEST, self.abort_on_test_failure, spec)
        else:
            spec.advise(AFTER_TEST, self.warn_on_test_failure, spec)

    def run(self, toolchain, spec):
        """
        This is the test method invoked on a successful toolchain run.

        Will be invoked from a toolchain success
        """

        self.setup_toolchain_spec(toolchain, spec)
        toolchain(spec)
