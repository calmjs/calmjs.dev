# -*- coding: utf-8 -*-
import unittest
import json
from os.path import basename
from os.path import exists
from os.path import join

from calmjs.cli import node
from calmjs.cli import get_node_version
from calmjs.exc import ToolchainAbort
from calmjs.toolchain import NullToolchain
from calmjs.toolchain import Spec
from calmjs.toolchain import BEFORE_TEST
from calmjs.toolchain import AFTER_TEST
from calmjs.utils import pretty_logging

from calmjs.dev import cli

from calmjs.testing import mocks
from calmjs.testing.utils import mkdtemp
from calmjs.testing.utils import stub_mod_call
from calmjs.testing.utils import stub_base_which

node_version = get_node_version()


class KarmaDriverTestSpecTestCase(unittest.TestCase):
    """
    Test the basic test_spec method, which accepts the spec to prepare
    the environment for which karma can be executed; as only the run
    method will actually run the test, this is safe to test.
    """

    def test_base(self):
        stub_mod_call(self, cli)
        stub_base_which(self)
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver.create()
        toolchain = NullToolchain()
        spec = Spec(build_dir=build_dir)
        driver.setup_toolchain_spec(toolchain, spec)
        driver.test_spec(spec)

        conf = join(build_dir, 'karma.conf.js')
        self.assertTrue(exists(conf))
        args = self.call_args[0][0]
        self.assertIn('karma', args[0])
        self.assertEqual('start', args[1])
        self.assertEqual(conf, args[2])

    @unittest.skipIf(node_version is None, 'node.js not found')
    def test_config_written_correctly(self):
        stub_mod_call(self, cli)
        stub_base_which(self)
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver.create()
        toolchain = NullToolchain()
        spec = Spec(build_dir=build_dir)
        driver.setup_toolchain_spec(toolchain, spec)
        driver.test_spec(spec)

        # verify that the resulting file is a function that expect a
        # function that accepts an object, that is the configuration.
        result = json.loads(node(
            'require("%s")({set: function(a) {\n'
            '    process.stdout.write(JSON.stringify(a));\n'
            '}});\n' % join(build_dir, 'karma.conf.js').replace('\\', '\\\\')
        )[0])
        self.assertTrue(isinstance(result, dict))

    def test_advices(self):
        stub_base_which(self)
        stub_mod_call(self, cli)
        build_dir = mkdtemp(self)
        advices = []
        driver = cli.KarmaDriver.create()
        spec = Spec(build_dir=build_dir)
        spec.advise(AFTER_TEST, advices.append, AFTER_TEST)
        spec.advise(BEFORE_TEST, advices.append, BEFORE_TEST)
        driver.test_spec(spec)
        # XXX should AFTER_TEST also run if test failed?
        # XXX what other advices should apply, i.e. failure/error/success
        self.assertEqual(advices, [BEFORE_TEST, AFTER_TEST])

    def test_broken_binary(self):
        build_dir = mkdtemp(self)
        toolchain = NullToolchain()
        spec = Spec(build_dir=build_dir)
        driver = cli.KarmaDriver()
        driver.binary = None
        driver.setup_toolchain_spec(toolchain, spec)
        with self.assertRaises(ToolchainAbort):
            driver.test_spec(spec)
        self.assertNotIn('karma_return_code', spec)

    def test_create_config_base(self):
        spec = Spec()
        driver = cli.KarmaDriver()
        driver.create_config(spec)
        self.assertEqual(spec['karma_config']['files'], [])

    def test_create_config_source_specified_no_explicit_tests(self):
        # this is usually provided by the toolchains themselves
        spec = Spec(
            source_package_names=['calmjs.dev'],
            calmjs_module_registry_names=['calmjs.dev.module'],
        )
        driver = cli.KarmaDriver()
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            driver.create_config(spec)

        self.assertEqual(
            sorted(basename(i) for i in spec['karma_config']['files']),
            ['test_fail.js', 'test_main.js'],
        )
        self.assertIn(
            "spec has no 'test_package_names' specified, "
            "falling back to 'source_package_names'", log.getvalue(),
        )
        self.assertIn(
            "spec has no 'calmjs_test_registry_names' specified, "
            "falling back to 'calmjs_module_registry_names'", log.getvalue(),
        )
        self.assertIn(
            "karma driver to extract tests from packages ['calmjs.dev'] "
            "using registries ['calmjs.dev.module.tests'] for testing",
            log.getvalue(),
        )

    def test_create_config_source_specified_explicit_specification(self):
        # this is usually provided by the toolchains themselves
        spec = Spec(
            test_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            source_package_names=['calmjs.dev'],
            calmjs_module_registry_names=['calmjs.dev.module'],
        )
        driver = cli.KarmaDriver()
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            driver.create_config(spec)

        self.assertEqual(
            sorted(basename(i) for i in spec['karma_config']['files']),
            ['test_fail.js', 'test_main.js'],
        )
        self.assertIn(
            "spec has 'test_package_names' explicitly specified",
            log.getvalue(),
        )
        self.assertIn(
            "spec has 'calmjs_test_registry_names' explicitly specified",
            log.getvalue(),
        )
        self.assertIn(
            "karma driver to extract tests from packages ['calmjs.dev'] "
            "using registries ['calmjs.dev.module.tests'] for testing",
            log.getvalue(),
        )

# rest of cli related tests have been streamlined into runtime for
# setup and teardown optimisation.
