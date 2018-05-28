# -*- coding: utf-8 -*-
import unittest
import codecs
import os
import sys
import json
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import join
from os.path import normpath
from os.path import pathsep
from os.path import realpath
from textwrap import dedent
from types import ModuleType

from pkg_resources import resource_filename
from pkg_resources import WorkingSet

from calmjs.parse import es5
from calmjs.artifact import ArtifactRegistry
from calmjs.argparse import ArgumentParser
from calmjs.exc import ToolchainAbort
from calmjs.npm import get_npm_version
from calmjs.npm import Driver as NPMDriver
from calmjs.registry import _inst as root_registry
from calmjs.runtime import main
from calmjs.runtime import Runtime
from calmjs.runtime import ToolchainRuntime
from calmjs.toolchain import AdviceRegistry
from calmjs.toolchain import NullToolchain
from calmjs.toolchain import Spec
from calmjs.toolchain import CALMJS_TOOLCHAIN_ADVICE
from calmjs.utils import pretty_logging

from calmjs.dev import cli
from calmjs.dev.cli import KarmaDriver
from calmjs.dev.toolchain import TestToolchain
from calmjs.dev.toolchain import KarmaToolchain
from calmjs.dev.toolchain import prepare_spec_artifacts
from calmjs.dev.toolchain import update_spec_for_karma
from calmjs.dev.artifact import ArtifactTestRegistry
from calmjs.dev.karma import DEFAULT_COVER_REPORT_TYPE_OPTIONS
from calmjs.dev.runtime import init_argparser_common
from calmjs.dev.runtime import KarmaRuntime
from calmjs.dev.runtime import TestToolchainRuntime
from calmjs.dev.runtime import KarmaArtifactRuntime

from calmjs.testing import mocks
from calmjs.testing.utils import make_dummy_dist
from calmjs.testing.utils import mkdtemp
from calmjs.testing.utils import remember_cwd
from calmjs.testing.utils import rmtree
from calmjs.testing.utils import setup_class_install_environment
from calmjs.testing.utils import stub_base_which
from calmjs.testing.utils import stub_item_attr_value
from calmjs.testing.utils import stub_mod_call
from calmjs.testing.utils import stub_stdouts

npm_version = get_npm_version()


class TestCommonArgparser(unittest.TestCase):
    """
    Test out some non-trivial parsing options in the common parser
    """

    def setUp(self):
        self.parser = ArgumentParser()
        init_argparser_common(self.parser)

    def parse(self, args):
        return self.parser.parse_known_args(args)[0]

    def test_parse_default_coverage_type(self):
        self.assertIs(
            DEFAULT_COVER_REPORT_TYPE_OPTIONS,
            self.parse([]).cover_report_types,
        )
        # default always show this
        self.assertIn('text', self.parse([]).cover_report_types)
        # check for deprecated option
        self.assertIsNone(self.parse([]).coverage_type)

    def test_parse_default_cover_report_type_legacy(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.assertEqual(
                'html',
                self.parse(['--coverage-type=html']).coverage_type)

            self.assertIn("will be removed by", str(w[0].message))
            # a somewhat more complete test
            config = {}
            driver = cli.KarmaDriver()
            with pretty_logging(
                    logger='calmjs.dev', stream=mocks.StringIO()) as log:
                # emulate the parsing into a spec
                spec = Spec(**vars(self.parse(['--coverage-type=html'])))
                driver._apply_coverage_reporters(spec, config)

        self.assertIn("WARNING", log.getvalue())
        self.assertIn("'coverage_type' is deprecated", log.getvalue())
        self.assertEqual({
            'type': 'html',
            'dir': realpath('coverage'),
        }, config['coverageReporter'])

    def test_parse_default_cover_report_type_legacy_default(self):
        import warnings
        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            self.assertEqual(
                'default',
                self.parse(['--coverage-type=default']).coverage_type)

            # a somewhat more complete test
            config = {}
            driver = cli.KarmaDriver()
            with pretty_logging(
                    logger='calmjs.dev', stream=mocks.StringIO()) as log:
                # emulate the parsing into a spec
                spec = Spec(**vars(self.parse(['--coverage-type=default'])))
                driver._apply_coverage_reporters(spec, config)

        self.assertNotIn("WARNING", log.getvalue())
        self.assertNotIn("'coverage_type' is deprecated", log.getvalue())
        # the default value actually is supported
        self.assertEqual(
            sorted(DEFAULT_COVER_REPORT_TYPE_OPTIONS),
            sorted([
                r['type'] for r in config['coverageReporter']['reporters']]),
        )

    def test_parse_default_cover_report_type_specified(self):
        self.assertEqual(
            ['html'],
            self.parse(['--cover-report-type=html']).cover_report_types)

    def test_parse_default_cover_report_type_specified_multiple(self):
        self.assertEqual(
            ['html', 'text'],
            self.parse(['--cover-report-type=html,text']).cover_report_types)

    def test_parse_default_cover_report_type_bad(self):
        stub_stdouts(self)
        with self.assertRaises(SystemExit):
            self.parse(['--cover-report-type=bad'])


class TestToolchainRuntimeTestCase(unittest.TestCase):

    def test_kwargs_to_spec(self):
        rt = TestToolchainRuntime(TestToolchain())
        spec = rt.kwargs_to_spec()
        self.assertTrue(isinstance(spec, Spec))

    def test_prepare_spec_artifacts(self):
        stub_stdouts(self)
        remember_cwd(self)
        tmpdir = mkdtemp(self)
        fake = join(tmpdir, 'fake.js')
        real = join(tmpdir, 'real.js')

        os.chdir(tmpdir)

        with open(real, 'w') as fd:
            fd.write('')

        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            # note the relative paths
            spec = Spec(artifact_paths=['real.js', 'fake.js'])
            prepare_spec_artifacts(spec)

        # note that the full path is now specified.
        self.assertEqual(spec['artifact_paths'], [real])
        self.assertIn('does not exists', log.getvalue())
        self.assertIn(fake, log.getvalue())

        # should still work with full paths.
        spec = Spec(artifact_paths=[real, fake])
        prepare_spec_artifacts(spec)
        self.assertEqual(spec['artifact_paths'], [real])

    def test_prepare_spec_artifacts_order(self):
        remember_cwd(self)
        tmpdir = mkdtemp(self)
        os.chdir(tmpdir)

        def touch(fn):
            with open(fn, 'w'):
                pass
            return fn

        names = ['art1.js', 'art2.js', 'art3.js']
        paths = [touch(join(tmpdir, n)) for n in names]

        spec = Spec(artifact_paths=names)
        prepare_spec_artifacts(spec)
        self.assertEqual(spec['artifact_paths'], paths)

        spec = Spec(artifact_paths=['art2.js', 'art1.js', 'art3.js'])
        prepare_spec_artifacts(spec)
        self.assertEqual(spec['artifact_paths'], [
            join(tmpdir, 'art2.js'),
            join(tmpdir, 'art1.js'),
            join(tmpdir, 'art3.js'),
        ])


class BaseRuntimeTestCase(unittest.TestCase):

    def test_update_spec_for_karma(self):
        spec = Spec(karma_abort_on_test_failure=1)
        update_spec_for_karma(spec, test_package_names=['default'])
        # values not provided via kwargs will be disappeared.
        self.assertEqual(dict(spec), {
            'test_package_names': ['default'],
        })

    def test_update_spec_for_karma_type_check(self):
        spec = Spec()
        update_spec_for_karma(spec, artifact_paths=['artifact.js'])
        # values not provided via kwargs will be disappeared.
        self.assertEqual(dict(spec), {
            'artifact_paths': ['artifact.js'],
        })

    def test_update_spec_for_karma_default_value_dropped(self):
        spec = Spec()
        update_spec_for_karma(spec, artifact_paths=[])
        # values not provided via kwargs will be disappeared.
        self.assertEqual(dict(spec), {})

    def test_command_stacking(self):

        def cleanup():
            del mocks.nrt
            del mocks.krt

        self.addCleanup(cleanup)

        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.runtime]\n'
            'fakerun = calmjs.testing.mocks:nrt\n'
            'fakekarma = calmjs.testing.mocks:krt\n'
        ),), 'example.package', '1.0')
        working_set = WorkingSet([self._calmjs_testing_tmpdir])

        mocks.nrt = TestToolchainRuntime(
            NullToolchain(), working_set=working_set)
        mocks.krt = KarmaRuntime(KarmaDriver(), working_set=working_set)

        runtime = Runtime(working_set=working_set)
        argparser = runtime.argparser

        ns = argparser.parse_args([
            'fakekarma',
            '--test-with-packages=pkg1', '--test-registries=dummy1',
        ])
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1'])
        self.assertEqual(ns.test_package_names, ['pkg1'])

        ns = argparser.parse_args([
            'fakekarma',
            '--test-with-packages=pkg1', '--test-registries=dummy1',
            'fakerun',
        ])
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1'])
        self.assertEqual(ns.test_package_names, ['pkg1'])

        ns = argparser.parse_args([
            'fakekarma',
            '--test-with-packages=pkg1', '--test-registries=dummy1',
            'fakerun',
            '--test-with-package=pkg2', '--test-registry=dummy2',
        ])
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1', 'dummy2'])
        self.assertEqual(ns.test_package_names, ['pkg1', 'pkg2'])

    def test_deprecation_test_package_flag(self):
        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.runtime]\n'
            'fakekarma = calmjs.testing.mocks:krt\n'
        ),), 'example.package', '1.0')
        working_set = WorkingSet([self._calmjs_testing_tmpdir])

        self.addCleanup(delattr, mocks, 'krt')
        mocks.krt = KarmaRuntime(KarmaDriver(), working_set=working_set)
        runtime = Runtime(working_set=working_set)
        argparser = runtime.argparser

        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            ns = argparser.parse_args([
                'fakekarma',
                '--test-package=pkg1', '--test-registries=dummy1',
            ])

        self.assertIn(
            "please use '--test-with-package' instead", str(w[0].message))
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1'])
        self.assertEqual(ns.test_package_names, ['pkg1'])

    def test_karma_runtime_arguments(self):
        stub_stdouts(self)
        stub_mod_call(self, cli)
        stub_base_which(self, 'karma')

        build_dir = mkdtemp(self)
        rt = KarmaRuntime(KarmaDriver())
        # the artifact in our case is identical to the source file
        artifact = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            'run', '--artifact', artifact,
            '--build-dir', build_dir,
            '--test-with-package', 'calmjs.dev',
            '--extra-frameworks', 'my_framework',
            '--browser', 'Chromium,Firefox',
        ])
        self.assertEqual(result['artifact_paths'], [artifact])
        self.assertTrue(exists(result['karma_config_path']))
        self.assertIn('karma_config_path', result)
        self.assertIn('my_framework', result['karma_config']['frameworks'])
        self.assertEqual(
            ['Chromium', 'Firefox'], result['karma_config']['browsers'])


@unittest.skipIf(npm_version is None, 'npm not found.')
class CliRuntimeTestCase(unittest.TestCase):
    """
    This test class does bring in some tests more specifically for the
    cli module, but given the overhead of setting up the environment
    through npm it is probably best to do it once, and that will be here
    in this TestCase class.
    """

    @classmethod
    def setUpClass(cls):
        # nosetest will still execute setUpClass, so the test condition
        # will need to be checked here also.
        if npm_version is None:  # pragma: no cover
            return
        cls._cwd = os.getcwd()
        setup_class_install_environment(
            cls, NPMDriver, ['calmjs.dev'], production=False)
        # immediately go into there for the node_modules.
        os.chdir(cls._env_root)

    @classmethod
    def tearDownClass(cls):
        # Ditto, as per above.
        if npm_version is None:  # pragma: no cover
            return
        os.chdir(cls._cwd)
        rmtree(cls._cls_tmpdir)

    def setUp(self):
        self.driver = KarmaDriver.create()

    # Here are some extended cli tests that need the actual karma
    # runtime, but not the runtime wrapper class.

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
            transpile_sourcepath={
                'calmjs/dev/main': main,
            },
            test_module_paths_map={
                'calmjs/test_main': test_main,
            },
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
            transpile_sourcepath={
                'calmjs/dev/main': main,
            },
            test_module_paths_map={
                'calmjs/test_fail': test_fail,
            },
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
            transpile_sourcepath={
                'calmjs/dev/main': main,
            },
            test_module_paths_map={
                'calmjs/test_fail': test_fail,
            },
            # register warning
            karma_abort_on_test_failure=False,
        )
        toolchain = NullToolchain()
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            self.driver.run(toolchain, spec)
        self.assertNotEqual(spec['karma_return_code'], 0)
        # linked continued
        self.assertIn('link', spec)
        self.assertIn(
            "karma exited with return code 1; continuing as specified",
            log.getvalue()
        )

    def test_standard_registry_run(self):
        main = resource_filename('calmjs.dev', 'main.js')
        spec = Spec(
            source_package_names=['calmjs.dev'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            # null toolchain does not prepare this
            transpile_sourcepath={
                'calmjs/dev/main': main,
            },
        )
        toolchain = NullToolchain()
        # as no abort registered.
        self.driver.run(toolchain, spec)

    # Now we have the proper runtime tests.

    def test_correct_initialization(self):
        # due to multiple inheritance, this should be checked.
        driver = KarmaDriver()
        runtime = KarmaRuntime(driver)
        self.assertIs(runtime.cli_driver, driver)
        self.assertIsNone(runtime.package_name)

    def test_init_argparser(self):
        runtime = KarmaRuntime(self.driver)
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
        working_set = WorkingSet([self._calmjs_testing_tmpdir])

        runtime = KarmaRuntime(self.driver, working_set=working_set)
        argparser = runtime.argparser
        stream = mocks.StringIO()
        argparser.print_help(file=stream)
        self.assertIn('--test-registry', stream.getvalue())
        self.assertIn('null', stream.getvalue())

    def test_karma_runtime_integration_default_abort_on_error(self):
        stub_stdouts(self)
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
        working_set = WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(self.driver, working_set=working_set)
        result = rt(
            ['null', '--export-target', target, '--build-dir', build_dir])
        self.assertFalse(result)
        # defer this to the next test.
        # self.assertIn('karma_config_path', result)
        # self.assertTrue(exists(result['karma_config_path']))
        # self.assertTrue(result.get('karma_abort_on_test_failure'))

    def test_karma_runtime_integration_ignore_error(self):
        stub_stdouts(self)
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
        working_set = WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(self.driver, working_set=working_set)
        result = rt([
            '-I', 'null', '--export-target', target, '--build-dir', build_dir,
        ])
        self.assertIn('karma_config_path', result)
        self.assertTrue(exists(result['karma_config_path']))
        self.assertFalse(result.get('karma_abort_on_test_failure'))
        self.assertIn(
            "karma exited with return code 1; continuing as specified",
            sys.stderr.getvalue()
        )

        # ensure coverage isn't run at all.
        coverage_report_dir = join(build_dir, 'coverage')
        self.assertFalse(exists(coverage_report_dir))

    def test_karma_runtime_integration_coverage(self):

        class DummyToolchain(NullToolchain):
            """
            Need this step to prepare some actual sources from this
            project, and we are cheating a bit due to the lack of actual
            registry setup.
            """

            def prepare(self, spec):
                # manually set up the source and the tests.
                main = resource_filename(
                    'calmjs.dev', 'main.js')
                test_main = resource_filename(
                    'calmjs.dev.tests', 'test_main.js')
                spec.update(dict(
                    transpile_sourcepath={
                        'calmjs/dev/main': main,
                    },
                    test_module_paths_map={
                        'calmjs/test_main': test_main,
                    },
                ))

        stub_stdouts(self)
        target = join(mkdtemp(self), 'target')
        build_dir = mkdtemp(self)
        coverage_report_dir = join(build_dir, 'coverage')
        # ensure this does not already exist
        self.assertFalse(exists(coverage_report_dir))

        stub_item_attr_value(
            self, mocks, 'dummy',
            ToolchainRuntime(DummyToolchain()),
        )
        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.runtime]\n'
            'null = calmjs.testing.mocks:dummy\n'
        ),), 'example.package', '1.0')
        working_set = WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(self.driver, working_set=working_set)
        result = rt([
            '--coverage', '--cover-report-dir', coverage_report_dir,
            'null', '--export-target', target, '--build-dir', build_dir,
        ])

        # ensure coverage report created
        self.assertTrue(result['coverage_enable'])
        self.assertTrue(exists(coverage_report_dir))

    def test_karma_runtime_integration_explicit_arguments(self):
        stub_stdouts(self)
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
        working_set = WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(self.driver, working_set=working_set)
        result = rt([
            '--test-registry', 'calmjs.no_such_registry',
            '--test-with-package', 'no_such_pkg', '-vv',
            '-I', 'null', '--export-target', target, '--build-dir', build_dir,
        ])
        self.assertIn('karma_config_path', result)
        self.assertTrue(exists(result['karma_config_path']))
        self.assertFalse(result.get('karma_abort_on_test_failure'))
        self.assertIn(
            "karma exited with return code 1; continuing as specified",
            sys.stderr.getvalue()
        )
        self.assertIn(
            "spec has 'test_package_names' explicitly specified",
            sys.stderr.getvalue()
        )
        self.assertIn(
            "spec has 'calmjs_test_registry_names' explicitly specified",
            sys.stderr.getvalue()
        )
        self.assertIn(
            "karma driver to extract tests from packages ['no_such_pkg'] "
            "using registries ['calmjs.no_such_registry'] for testing",
            sys.stderr.getvalue()
        )

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
        working_set = WorkingSet([self._calmjs_testing_tmpdir])
        rt = KarmaRuntime(self.driver, working_set=working_set)
        rt([])
        # standard help printed
        self.assertIn('usage:', sys.stdout.getvalue())
        self.assertIn(
            'karma testrunner integration for calmjs', sys.stdout.getvalue())

    def test_main_integration(self):
        stub_stdouts(self)
        with self.assertRaises(SystemExit):
            main(['karma', '-h'])
        self.assertIn('karma testrunner', sys.stdout.getvalue())

    def test_karma_runtime_run_success_run(self):
        stub_stdouts(self)

        def cleanup():
            root_registry.records.pop('calmjs.dev.module.tests', None)

        self.addCleanup(cleanup)

        build_dir = mkdtemp(self)
        # manipulate the registry to remove the fail test
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            'run', '--artifact', artifact,
            '--build-dir', build_dir,
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-with-package', 'calmjs.dev',
            '-vv',
        ])
        self.assertIn('karma_config_path', result)
        self.assertTrue(exists(result['karma_config_path']))
        self.assertEqual(result['artifact_paths'], [artifact])
        # should exit cleanly
        self.assertNotIn(
            "karma exited with return code 1", sys.stderr.getvalue())
        # should be clean of other error messages
        self.assertNotIn("WARNING", sys.stderr.getvalue())
        self.assertNotIn("ERROR", sys.stderr.getvalue())
        self.assertNotIn("CRITICAL", sys.stderr.getvalue())
        # plenty of info though
        self.assertIn("INFO", sys.stderr.getvalue())

    def test_karma_runtime_multiple_artifacts_single_arg(self):
        stub_stdouts(self)
        extra_artifact = join(mkdtemp(self), 'lib.js')
        with open(extra_artifact, 'w') as fd:
            fd.write(dedent("""
            'use strict';

            var Lib = function(args) {
            };

            Lib.prototype.add2 = function (i) {
                return i + i;
            };
            """))

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact = resource_filename('calmjs.dev', 'main.js')
        rt([
            'run', '--artifact', pathsep.join([artifact, extra_artifact]),
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-with-package', 'calmjs.dev',
            '-vv',
        ])
        logs = sys.stderr.getvalue()
        self.assertIn("specified artifact '%s' found" % artifact, logs)
        self.assertIn("specified artifact '%s' found" % extra_artifact, logs)

    def test_karma_runtime_multiple_artifacts_multi_args(self):
        stub_stdouts(self)
        extra_artifact = join(mkdtemp(self), 'lib.js')
        with open(extra_artifact, 'w') as fd:
            fd.write(dedent("""
            'use strict';

            var Lib = function(args) {
            };

            Lib.prototype.add2 = function (i) {
                return i + i;
            };
            """))

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact = resource_filename('calmjs.dev', 'main.js')
        rt([
            'run',
            '--artifact', artifact, '--artifact', extra_artifact,
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-with-package', 'calmjs.dev',
            '-vv',
        ])
        logs = sys.stderr.getvalue()
        self.assertIn("specified artifact '%s' found" % artifact, logs)
        self.assertIn("specified artifact '%s' found" % extra_artifact, logs)

    def test_karma_runtime_run_artifact_cover(self):
        stub_stdouts(self)

        def cleanup():
            root_registry.records.pop('calmjs.dev.module.tests', None)

        self.addCleanup(cleanup)

        build_dir = mkdtemp(self)
        coverage_dir = join(mkdtemp(self), 'coverage')
        # manipulate the registry to remove the fail test
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact_fn = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            '--artifact', artifact_fn, 'run',
            '--build-dir', build_dir,
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-with-package', 'calmjs.dev',
            '--coverage', '--cover-artifact',
            '--cover-report-dir', coverage_dir,
        ])
        self.assertIn('karma_config_path', result)
        self.assertEqual(result['artifact_paths'], [artifact_fn])
        self.assertTrue(exists(result['karma_config_path']))
        # should exit cleanly
        self.assertNotIn(
            "karma exited with return code 1", sys.stderr.getvalue())
        self.assertIn(artifact_fn, result['karma_config']['preprocessors'])
        self.assertTrue(exists(coverage_dir))

        # verify that the coverage report actually got generated
        with open(join(coverage_dir, 'coverage.json')) as fd:
            self.assertIn(normpath(artifact_fn), {
                normpath(k): v for k, v in json.load(fd).items()
            })

        with open(join(coverage_dir, 'lcov', 'lcov.info')) as fd:
            self.assertIn(basename(artifact_fn), fd.read())

    def create_coverage_report(self, report_type):
        stub_stdouts(self)
        self.addCleanup(
            root_registry.records.pop, 'calmjs.dev.module.tests', None)

        build_dir = mkdtemp(self)
        coverage_dir = join(mkdtemp(self), 'coverage')
        # manipulate the registry to remove the fail test
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact_fn = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            '--artifact', artifact_fn, 'run',
            '--build-dir', build_dir,
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-with-package', 'calmjs.dev',
            '--coverage', '--cover-artifact',
            '--cover-report-type', report_type,
            '--cover-report-dir', coverage_dir,
        ])
        self.assertIn('karma_config_path', result)
        self.assertEqual(result['artifact_paths'], [artifact_fn])
        self.assertTrue(exists(result['karma_config_path']))
        # should exit cleanly
        self.assertNotIn(
            "karma exited with return code 1", sys.stderr.getvalue())
        self.assertIn(artifact_fn, result['karma_config']['preprocessors'])
        self.assertTrue(exists(coverage_dir))

        return coverage_dir, artifact_fn

    def test_karma_runtime_run_artifact_cover_report_type_text_lcov(self):
        coverage_dir, artifact_fn = self.create_coverage_report('text,lcov')
        # shouldn't be generated.
        self.assertFalse(exists(join(coverage_dir, 'coverage.json')))
        # verify that the coverage report actually got generated
        with open(join(coverage_dir, 'lcov', 'lcov.info')) as fd:
            self.assertIn(basename(artifact_fn), fd.read())

    def test_karma_runtime_run_artifact_cover_report_type_lcov_text(self):
        coverage_dir, artifact_fn = self.create_coverage_report('lcov,text')
        # shouldn't be generated.
        self.assertFalse(exists(join(coverage_dir, 'coverage.json')))
        # verify that the coverage report actually got generated
        with open(join(coverage_dir, 'lcov', 'lcov.info')) as fd:
            self.assertIn(basename(artifact_fn), fd.read())

    def test_karma_runtime_run_artifact_cover_report_type_text_json(self):
        coverage_dir, artifact_fn = self.create_coverage_report('text,json')
        # shouldn't be generated.
        self.assertFalse(exists(join(coverage_dir, 'lcov', 'lcov.info')))
        # verify that the coverage report actually got generated
        with open(join(coverage_dir, 'coverage.json')) as fd:
            self.assertIn(normpath(artifact_fn), {
                normpath(k): v for k, v in json.load(fd).items()
            })

    def test_karma_runtime_run_artifact_cover_report_type_json_text(self):
        coverage_dir, artifact_fn = self.create_coverage_report('json,text')
        # shouldn't be generated.
        self.assertFalse(exists(join(coverage_dir, 'lcov', 'lcov.info')))
        # verify that the coverage report actually got generated
        with open(join(coverage_dir, 'coverage.json')) as fd:
            self.assertIn(normpath(artifact_fn), {
                normpath(k): v for k, v in json.load(fd).items()
            })

    def test_karma_runtime_run_toolchain_package(self):
        def cleanup():
            root_registry.records.pop('calmjs.dev.module.tests', None)
            root_registry.records.pop(CALMJS_TOOLCHAIN_ADVICE, None)

        self.addCleanup(cleanup)
        stub_stdouts(self)

        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.toolchain.advice]\n'
            'calmjs.dev.toolchain:KarmaToolchain'
            ' = calmjs.tests.test_toolchain:dummy\n'
        ),), 'example.package', '1.0')
        working_set = WorkingSet([self._calmjs_testing_tmpdir])

        root_registry.records[
            CALMJS_TOOLCHAIN_ADVICE] = AdviceRegistry(
                CALMJS_TOOLCHAIN_ADVICE, _working_set=working_set)

        # manipulate the registry to remove the fail test
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            '--artifact', artifact, 'run',
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-with-package', 'calmjs.dev',
            '--toolchain-package', 'example.package',
        ])
        self.assertIn('karma_config_path', result)
        self.assertEqual(result['artifact_paths'], [artifact])
        # the spec key is written.
        self.assertEqual(result['dummy'], ['dummy'])

    def test_karma_runtime_run_toolchain_auto_test_registry(self):
        def cleanup():
            root_registry.records.pop('calmjs.dev.module.tests', None)
            root_registry.records.pop(CALMJS_TOOLCHAIN_ADVICE, None)

        self.addCleanup(cleanup)
        stub_stdouts(self)

        make_dummy_dist(self, ((
            'entry_points.txt',
            '[calmjs.toolchain.advice]\n'
            'calmjs.dev.toolchain:KarmaToolchain'
            ' = calmjs.tests.test_toolchain:dummy\n'
        ),), 'example.package', '1.0')

        # in the main distribution we did not define this to avoid
        # potential contamination of test data by this package with the
        # rest of the framework, so we stub that function

        _called = []

        def fake_flatten_module_registry_names(package_names):
            _called.extend(package_names)
            return ['calmjs.dev.module']

        from calmjs.dev import toolchain
        stub_item_attr_value(
            self, toolchain, 'flatten_module_registry_names',
            fake_flatten_module_registry_names
        )

        working_set = WorkingSet([self._calmjs_testing_tmpdir])

        root_registry.records[
            CALMJS_TOOLCHAIN_ADVICE] = AdviceRegistry(
                CALMJS_TOOLCHAIN_ADVICE, _working_set=working_set)

        # manipulate the registry to remove the fail test
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')

        # use the full blown runtime
        rt = KarmaRuntime(self.driver)
        # the artifact in our case is identical to the source file
        artifact = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            'run', '--artifact', artifact,
            '--test-with-package', 'calmjs.dev',
            '--toolchain-package', 'example.package',
        ])
        self.assertIn('calmjs.dev', _called)
        self.assertIn('karma_config_path', result)
        self.assertEqual(result['artifact_paths'], [artifact])
        # the spec key is written.
        self.assertEqual(result['dummy'], ['dummy'])
        self.assertEqual(
            result['calmjs_module_registry_names'], ['calmjs.dev.module'])
        self.assertIn(
            'calmjs/dev/tests/test_main', result['test_module_paths_map'])

    def setup_karma_artifact_runtime(self):

        def export_target_only(package_names, export_target):
            spec = Spec(
                export_target=export_target,
                test_package_names=package_names,
                # typically, the toolchain test advice will be advised
                # to the spec which will then set these up.
                calmjs_test_registry_names=['calmjs.dev.module.tests'],
            )
            return KarmaToolchain(), spec,

        def generic_tester(package_names, export_target):
            toolchain, spec = export_target_only(package_names, export_target)
            spec['artifact_paths'] = [export_target]
            return toolchain, spec

        tester_mod = ModuleType('calmjs_dev_tester')
        tester_mod.generic = generic_tester
        tester_mod.export = export_target_only

        self.addCleanup(sys.modules.pop, 'calmjs_dev_tester')
        self.addCleanup(
            root_registry.records.pop, 'calmjs.dev.module.tests', None)
        sys.modules['calmjs_dev_tester'] = tester_mod

        working_dir = mkdtemp(self)

        make_dummy_dist(self, (
            ('entry_points.txt', '\n'.join([
                '[calmjs.artifacts.tests]',
                'artifact.js = calmjs_dev_tester:generic',
                'export_target.js = calmjs_dev_tester:export',
            ])),
        ), 'calmjs.dev', '1.0', working_dir=working_dir)

        make_dummy_dist(self, (
            ('entry_points.txt', '\n'.join([
                '[calmjs.artifacts.tests]',
                'missing.js = calmjs_dev_tester:generic',
            ])),
        ), 'missing', '1.0', working_dir=working_dir)

        make_dummy_dist(self, (
            ('entry_points.txt', '\n'.join([
                # this won't actually generate an artifact, but that is
                # not what is being tested.
                '[calmjs.artifacts]',
                'testless.js = calmjs_dev_tester:generic',
            ])),
        ), 'testless', '1.0', working_dir=working_dir)

        make_dummy_dist(self, (
            ('entry_points.txt', '\n'.join([
                # the tester is missing.
                '[calmjs.artifacts.tests]',
                'artifact.js = not_installed:tester',
            ])),
        ), 'depsmissing', '1.0', working_dir=working_dir)

        make_dummy_dist(self, (
            ('entry_points.txt', '\n'.join([
            ])),
        ), 'nothing', '1.0', working_dir=working_dir)

        # simply inject the "artifact" for this package into the
        # registry
        mock_ws = WorkingSet([working_dir])
        registry = ArtifactTestRegistry(
            'calmjs.artifacts.tests', _working_set=mock_ws)

        # produce the "artifact" by simply the local main.js
        main_js = resource_filename('calmjs.dev', 'main.js')
        artifact_target = registry.get_artifact_filename(
            'calmjs.dev', 'artifact.js')
        export_target = registry.get_artifact_filename(
            'calmjs.dev', 'export_target.js')
        os.mkdir(dirname(artifact_target))
        with open(main_js) as reader:
            with open(artifact_target, 'w') as writer:
                writer.write(reader.read())
            reader.seek(0)
            with open(export_target, 'w') as writer:
                writer.write(reader.read())

        # assign this dummy registry to the root records with cleanup
        self.addCleanup(root_registry.records.pop, 'calmjs.artifacts.tests')
        root_registry.records['calmjs.artifacts.tests'] = registry

        # include the artifact registry, too.
        self.addCleanup(root_registry.records.pop, 'calmjs.artifacts')
        artifact_registry = ArtifactRegistry(
            'calmjs.artifacts', _working_set=mock_ws)
        root_registry.records['calmjs.artifacts'] = artifact_registry

        # use the verify artifact runtime directly
        return KarmaArtifactRuntime()

    def test_artifact_verify_fail_continue(self):
        # since there is a failure test case
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        self.assertFalse(rt(['calmjs.dev']))
        self.assertIn('continuing as specified', sys.stderr.getvalue())
        self.assertNotIn(
            "no artifacts or tests defined for package 'calmjs.dev'",
            sys.stderr.getvalue(),
        )

    def test_artifact_verify_fail_exit_first(self):
        # should not explode if the abort is triggered
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        self.assertFalse(rt(['calmjs.dev', '-x']))
        self.assertIn(
            'terminating due to expected unrecoverable condition',
            sys.stderr.getvalue()
        )

    def test_artifact_verify_success(self):
        # should not explode if the abort is triggered
        # manipulate the registry to remove the fail test
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')

        # should finally pass
        self.assertTrue(rt(['calmjs.dev']))

    def test_artifact_verify_manual(self):
        # not using the runtime but use it to setup the test environment
        self.setup_karma_artifact_runtime()
        # manually invoke the cli API directly
        self.assertFalse(cli.karma_verify_package_artifacts(['calmjs.dev']))
        # try again after removing the fail test
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')
        self.assertTrue(cli.karma_verify_package_artifacts(['calmjs.dev']))

    def test_artifact_verify_success_report(self):
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        report_dir = join(mkdtemp(self), 'reports')
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')
        # also ensure that the options
        self.assertTrue(rt([
            'calmjs.dev',
            '--coverage',
            '--cover-report-dir', report_dir,
            '--cover-artifact',
        ]))

        self.assertTrue(exists(report_dir))

    def test_artifact_verify_fail_at_missing_artifact(self):
        # missing packages should also fail by default
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        self.assertFalse(rt(['missing']))
        self.assertIn('artifact not found:', sys.stderr.getvalue())
        self.assertIn('missing.js', sys.stderr.getvalue())

    def test_artifact_verify_success_at_no_declaration_or_artifact(self):
        # missing tests for packages without artifacts can't fail.
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')
        self.assertTrue(rt(['-v', 'calmjs.dev', 'nothing']))
        self.assertNotIn(
            "no artifacts or tests defined for package 'calmjs.dev'",
            sys.stderr.getvalue(),
        )
        self.assertIn(
            "no artifacts or tests defined for package 'nothing'",
            sys.stderr.getvalue(),
        )

    def test_artifact_verify_fail_at_missing_test_for_artifact(self):
        # missing tests for packages with artifacts must fail
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')
        self.assertFalse(rt(['calmjs.dev', 'testless']))
        self.assertNotIn(
            "no artifacts or tests defined for package 'calmjs.dev'",
            sys.stderr.getvalue(),
        )
        self.assertIn(
            "no test found for artifacts declared for package 'testless'",
            sys.stderr.getvalue(),
        )

    def test_artifact_verify_fail_at_python_deps_missing(self):
        # entry_point referenced a package not installed, it should fail
        # too.
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        self.assertFalse(rt(['depsmissing']))
        self.assertIn(
            "unable to import the target builder for the "
            "entry point 'artifact.js = not_installed:tester' from "
            "package 'depsmissing 1.0'",
            sys.stderr.getvalue(),
        )

    def test_artifact_verify_fail_at_replacement(self):
        # failure happening because there are no tests found when
        # execution for them are set up.
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        self.assertFalse(rt([
            '-vv', 'calmjs.dev', '--test-with-package', 'missing'
        ]))
        # though mostly the tests is for the capturing of these messages
        self.assertIn("spec['test_package_names'] was", sys.stderr.getvalue())
        self.assertIn("calmjs.dev'] replaced with", sys.stderr.getvalue())
        self.assertIn("missing']", sys.stderr.getvalue())

    def test_artifact_verify_extra_artifacts_with_build_dir(self):
        # this one is provided only as convenience; this may be useful
        # for builders that construct a partial artifacts but using a
        # test rule that doesn't provide some requirements, or for
        # testing whether inclusion of that other artifact will cause
        # interference with the expected functionality of the artifact
        # to be tested with.

        extra_js = join(mkdtemp(self), 'extra.js')
        extra_test = join(mkdtemp(self), 'test_extra.js')

        with open(extra_js, 'w') as fd:
            fd.write('var extra = {value: "artifact"};')

        with open(extra_test, 'w') as fd:
            fd.write(dedent("""
            'use strict';

            describe('emulated extra test', function() {
                it('extra artifact provided', function() {
                    expect(window.extra.value).to.equal("artifact");
                });
            });
            """.strip()))

        build_dir = mkdtemp(self)
        stub_stdouts(self)
        rt = self.setup_karma_artifact_runtime()
        # remove the fail test.
        reg = root_registry.get('calmjs.dev.module.tests')
        reg.records['calmjs.dev.tests'].pop('calmjs/dev/tests/test_fail', '')
        # inject our extra test to ensure the artifact that got added
        # still gets tested.
        reg.records['calmjs.dev.tests'][
            'calmjs/dev/tests/test_extra'] = extra_test
        self.assertTrue(rt([
            '-vv',
            '--artifact', extra_js,
            '--build-dir', build_dir,
            '-u', 'calmjs.dev',
            'calmjs.dev',
        ]))
        stderr = sys.stderr.getvalue()
        self.assertIn("specified artifact '%s' found" % extra_js, stderr)
        self.assertIn("artifact.js' found", stderr)

        with codecs.open(
                join(build_dir, 'karma.conf.js'), encoding='utf8') as fd:
            rawconf = es5(fd.read())

        # manually and lazily extract the configuration portion
        config = json.loads(str(
            rawconf.children()[0].expr.right.elements[0].expr.args.items[0]))
        # the extra specified artifact must be before the rest.
        self.assertEqual(config['files'][0], extra_js)
