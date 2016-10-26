# -*- coding: utf-8 -*-
import unittest
import json
from os.path import exists
from os.path import join
from pkg_resources import resource_filename

from calmjs.cli import node
from calmjs.cli import get_node_version
from calmjs.exc import ToolchainAbort
from calmjs.toolchain import NullToolchain
from calmjs.toolchain import Spec
from calmjs.toolchain import BEFORE_TEST
from calmjs.toolchain import AFTER_TEST
from calmjs.dev import cli

from calmjs.testing.utils import mkdtemp
from calmjs.testing.utils import stub_mod_call
from calmjs.testing.utils import stub_stdouts

# XXX static setup
karma = cli.KarmaDriver.create()
karma_version = karma.get_karma_version()
node_version = get_node_version()


class KarmaDriverTestSpecTestCase(unittest.TestCase):
    """
    Test the basic test_spec method, which accepts the spec to prepare
    the environment for which karma can be executed; as only the run
    method will actually run the test, this is safe to test.
    """

    def test_base(self):
        stub_mod_call(self, cli)
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


# TODO figure out whether using a whatever version found is sane instead
# of doing the manual setup.
@unittest.skipIf(karma_version is None, 'karma binary not found')
class KarmaDriverRunTestCase(unittest.TestCase):
    """
    Test on the actual run
    """

    def setUp(self):
        self.driver = cli.KarmaDriver.create()

    def test_version(self):
        # formalizing as part of test.
        version = self.driver.get_karma_version()
        self.assertIsNot(version, None)

    def test_empty_manual_run(self):
        build_dir = mkdtemp(self)
        toolchain = NullToolchain()
        spec = Spec(build_dir=build_dir)
        self.driver.setup_toolchain_spec(toolchain, spec)
        self.driver.test_spec(spec)
        # at least write that code.
        # TODO figure out whether empty tests always return 1
        self.assertIn('karma_return_code', spec)

    def test_standard_manual_tests_success_run(self):
        main = resource_filename('calmjs.dev', 'main.js')
        test_main = resource_filename('calmjs.dev.tests', 'test_main.js')
        spec = Spec(
            # null toolchain does not prepare this
            transpile_source_map={
                'calmjs/dev/main': main,
            },
            test_module_paths=[
                test_main,
            ]
        )
        toolchain = NullToolchain()
        self.driver.run(toolchain, spec)
        self.assertEqual(spec['karma_return_code'], 0)
        self.assertIn('link', spec)

    def test_standard_manual_tests_fail_run_abort(self):
        stub_stdouts(self)
        main = resource_filename('calmjs.dev', 'main.js')
        test_fail = resource_filename('calmjs.dev.tests', 'test_fail.js')
        spec = Spec(
            # null toolchain does not prepare this
            transpile_source_map={
                'calmjs/dev/main': main,
            },
            test_module_paths=[
                test_fail,
            ],
            # register abort
            karma_abort_on_test_failure=True,
        )
        toolchain = NullToolchain()
        with self.assertRaises(ToolchainAbort):
            self.driver.run(toolchain, spec)
        self.assertNotEqual(spec['karma_return_code'], 0)
        # linked not done
        self.assertNotIn('link', spec)

    def test_standard_manual_tests_fail_run_continued(self):
        stub_stdouts(self)
        main = resource_filename('calmjs.dev', 'main.js')
        test_fail = resource_filename('calmjs.dev.tests', 'test_fail.js')
        spec = Spec(
            # null toolchain does not prepare this
            transpile_source_map={
                'calmjs/dev/main': main,
            },
            test_module_paths=[
                test_fail,
            ],
            # register abort
            karma_abort_on_test_failure=False,
        )
        toolchain = NullToolchain()
        self.driver.run(toolchain, spec)
        self.assertNotEqual(spec['karma_return_code'], 0)
        # linked continued
        self.assertIn('link', spec)

    def test_standard_registry_run(self):
        main = resource_filename('calmjs.dev', 'main.js')
        spec = Spec(
            source_package_names=['calmjs.dev'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            # null toolchain does not prepare this
            transpile_source_map={
                'calmjs/dev/main': main,
            },
        )
        toolchain = NullToolchain()
        # as no abort registered.
        self.driver.run(toolchain, spec)
