# -*- coding: utf-8 -*-
import unittest
import json
from os.path import exists
from os.path import join

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

# rest of cli related tests have been streamlined into runtime for
# setup and teardown optimisation.
