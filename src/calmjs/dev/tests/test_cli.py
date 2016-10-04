# -*- coding: utf-8 -*-
import unittest
import json
from os.path import exists
from os.path import join
from pkg_resources import resource_filename

from calmjs.cli import node
from calmjs.cli import get_node_version
from calmjs.toolchain import NullToolchain
from calmjs.toolchain import Spec
from calmjs.toolchain import BEFORE_TEST
from calmjs.toolchain import AFTER_TEST
from calmjs.dev import cli

from calmjs.testing.utils import mkdtemp

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
        spec_keys = []
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver()
        spec = Spec(build_dir=build_dir)
        driver.test_spec(spec, spec_keys)
        self.assertTrue(exists(join(build_dir, 'karma.conf.js')))

    @unittest.skipIf(node_version is None, 'node.js not found')
    def test_config_written(self):
        spec_keys = []
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver()
        spec = Spec(build_dir=build_dir)
        driver.test_spec(spec, spec_keys)

        # verify that the resulting file is a function that expect a
        # function that accepts an object, that is the configuration.
        result = json.loads(node(
            'require("%s")({set: function(a) {\n'
            '    process.stdout.write(JSON.stringify(a));\n'
            '}});\n' % join(build_dir, 'karma.conf.js')
        )[0])
        self.assertTrue(isinstance(result, dict))

    def test_events(self):
        build_dir = mkdtemp(self)
        spec_keys = []
        events = []
        driver = cli.KarmaDriver()
        spec = Spec(build_dir=build_dir)
        spec.on_event(AFTER_TEST, events.append, AFTER_TEST)
        spec.on_event(BEFORE_TEST, events.append, BEFORE_TEST)
        spec.on_event(driver.RUN_KARMA, events.append, driver.RUN_KARMA)
        driver.test_spec(spec, spec_keys)
        # XXX should AFTER_TEST also run if test failed?
        # XXX what other events should apply, i.e. failure/error/success
        self.assertEqual(events, [BEFORE_TEST, driver.RUN_KARMA, AFTER_TEST])


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
        spec_keys = []
        spec = Spec(build_dir=build_dir)
        self.driver.test_spec(spec, spec_keys)
        self.driver.karma(spec)
        # at least write that code.
        # TODO figure out whether empty tests always return 1
        self.assertIn('karma_return_code', spec)

    def test_standard_success_run(self):
        main = resource_filename('calmjs.dev', 'main.js')
        test_main = resource_filename('calmjs.dev.tests', 'test_main.js')
        spec = Spec(
            transpile_source_map={
                'calmjs/dev/main': main,
            },
            test_modules=[
                test_main,
            ]
        )
        toolchain = NullToolchain()
        self.driver.run(toolchain, spec)
        self.assertEqual(spec['karma_return_code'], 0)
