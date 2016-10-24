# -*- coding: utf-8 -*-
import unittest
import sys
from os.path import exists
from os.path import join

import pkg_resources

from calmjs.runtime import main
from calmjs.runtime import ToolchainRuntime
from calmjs.toolchain import NullToolchain
from calmjs.utils import pretty_logging

from calmjs.dev.cli import KarmaDriver
from calmjs.dev.runtime import KarmaRuntime

from calmjs.testing import mocks
from calmjs.testing.utils import make_dummy_dist
from calmjs.testing.utils import mkdtemp
from calmjs.testing.utils import stub_item_attr_value
from calmjs.testing.utils import stub_stdouts


class RuntimeTestCase(unittest.TestCase):

    # XXX need actual setup through calmjs npm --install

    def test_correct_initialization(self):
        # due to multiple inheritance, this should be checked.
        driver = KarmaDriver()
        runtime = KarmaRuntime(driver)

        self.assertIs(runtime.cli_driver, driver)
        self.assertIsNone(runtime.package_name)

    def test_init_argparser(self):
        runtime = KarmaRuntime(KarmaDriver())
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            argparser = runtime.argparser

        self.assertIn(
            "filtering out entry point 'npm = calmjs.npm:npm.runtime' "
            "as it does not lead to a calmjs.runtime.ToolchainRuntime in "
            "KarmaRuntime.", log.getvalue()
        )

        stream = mocks.StringIO()
        argparser.print_help(file=stream)
        self.assertIn('--test-registry', stream.getvalue())

    def test_init_argparser_with_valid_toolchains(self):
        stub_item_attr_value(
            self, mocks, 'dummy',
            ToolchainRuntime(NullToolchain()),
        )

        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.runtime]\n'
            'null = calmjs.testing.mocks:dummy\n'
        ),), 'example.package', '1.0')
        working_set = pkg_resources.WorkingSet([self._calmjs_testing_tmpdir])

        runtime = KarmaRuntime(KarmaDriver(), working_set=working_set)
        argparser = runtime.argparser
        stream = mocks.StringIO()
        argparser.print_help(file=stream)
        self.assertIn('--test-registry', stream.getvalue())
        self.assertIn('null', stream.getvalue())

    def test_karma_runtime_integration(self):
        target = join(mkdtemp(self), 'target')
        build_dir = mkdtemp(self)
        stub_item_attr_value(
            self, mocks, 'dummy',
            ToolchainRuntime(NullToolchain()),
        )
        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.runtime]\n'
            'null = calmjs.testing.mocks:dummy\n'
        ),), 'example.package', '1.0')
        working_set = pkg_resources.WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(KarmaDriver.create(), working_set=working_set)
        result = rt(
            ['null', '--export-target', target, '--build-dir', build_dir])
        self.assertIn('karma_config_path', result)
        self.assertTrue(exists(result['karma_config_path']))

    def test_missing_runtime_arg(self):
        stub_stdouts(self)
        stub_item_attr_value(
            self, mocks, 'dummy',
            ToolchainRuntime(NullToolchain()),
        )
        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.runtime]\n'
            'null = calmjs.testing.mocks:dummy\n'
        ),), 'example.package', '1.0')
        working_set = pkg_resources.WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(KarmaDriver.create(), working_set=working_set)
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            rt([])
        self.assertIn('no runtime provided', log.getvalue())

    def test_main_integration(self):
        stub_stdouts(self)
        with self.assertRaises(SystemExit):
            main(['karma', '-h'])
        self.assertIn('karma testrunner', sys.stdout.getvalue())
