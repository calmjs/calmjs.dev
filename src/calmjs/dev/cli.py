# -*- coding: utf-8 -*-
"""
This module provides interface to the karma cli runtime.
"""

import logging
from os.path import join
from subprocess import call

from calmjs.toolchain import BEFORE_TEST
from calmjs.toolchain import AFTER_TEST
from calmjs.toolchain import AFTER_FINALIZE
from calmjs.toolchain import BUILD_DIR

from calmjs.toolchain import CALMJS_MODULE_REGISTRY_NAMES
from calmjs.toolchain import SOURCE_PACKAGE_NAMES
from calmjs.toolchain import TEST_MODULE_PATHS

from calmjs.cli import NodeDriver
from calmjs.cli import get_bin_version

from calmjs.dev import dist
from calmjs.dev import karma
from calmjs.dev import utils

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
            testrunner_advice_name=AFTER_FINALIZE,
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
        call_kw = self._gen_call_kws()
        logger.info('invoking %s start %r', self.binary, config_fn)
        # TODO would be great if there is a way to "tee" the result into
        # both here and stdout.
        # perhaps the provided spec can contain well-defined keywords
        # that can be passed to the `call` function (extend call_kw).
        # For now at least log this down like so.
        binary = self.which()
        spec['karma_return_code'] = call(
            [self.binary, 'start', config_fn], **call_kw)

        spec.handle(karma.AFTER_KARMA)

    def _create_config(self, spec, spec_keys):
        # Extract the available data stored in the spec.
        source_package_names = spec.get(SOURCE_PACKAGE_NAMES)
        module_registries = spec.get(CALMJS_MODULE_REGISTRY_NAMES, [])

        # calculate, extract and persist the test module names
        test_module_paths = spec[TEST_MODULE_PATHS] = spec.get(
            TEST_MODULE_PATHS, [])
        test_module_paths.extend(
            dist.get_module_default_test_registries_dependencies(
                source_package_names, module_registries).values())

        config = karma.build_base_config()
        files = utils.get_targets_from_spec(spec, spec_keys)
        config['files'] = list(files) + test_module_paths
        return config

    def create_config(self, spec):
        spec_keys = spec[karma.KARMA_SPEC_KEYS]
        spec[karma.KARMA_CONFIG] = self._create_config(spec, spec_keys)

    def _write_config(self, spec):
        # grab the config from the spec.
        s = self.dumps(spec[karma.KARMA_CONFIG])
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
        Setup a spec for execution
        """

        spec[karma.KARMA_SPEC_KEYS] = utils.get_toolchain_targets_keys(
            toolchain, exclude_targets_from=())
        spec.advise(self.testrunner_advice_name, self.test_spec, spec)
        spec.advise(BEFORE_TEST, self.create_config, spec)
        spec.advise(karma.BEFORE_KARMA, self.write_config, spec)

    def run(self, toolchain, spec):
        """
        This is the test method invoked on a successful toolchain run.

        Will be invoked from a toolchain success
        """

        # XXX the runtime analogous will have to deal with getting the
        # actual runtime and then use its make_spec method to generate
        # the spec.
        # XXX the list of include/exclude need to be provided to here
        # somehow?
        self.setup_toolchain_spec(toolchain, spec)
        toolchain(spec)