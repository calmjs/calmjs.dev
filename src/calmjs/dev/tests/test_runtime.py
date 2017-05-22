# -*- coding: utf-8 -*-
import unittest
import os
import sys
from os.path import exists
from os.path import join

from pkg_resources import resource_filename
from pkg_resources import WorkingSet

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
from calmjs.dev.runtime import prepare_spec_artifacts
from calmjs.dev.runtime import KarmaRuntime
from calmjs.dev.runtime import TestToolchainRuntime

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
        driver = KarmaDriver()
        runtime = KarmaRuntime(driver)
        spec = Spec(karma_abort_on_test_failure=1)
        runtime._update_spec_for_karma(spec, test_package_names=['default'])
        # values not provided via kwargs will be disappeared.
        self.assertEqual(dict(spec), {
            'test_package_names': ['default'],
        })

    def test_update_spec_for_karma_type_check(self):
        driver = KarmaDriver()
        runtime = KarmaRuntime(driver)
        spec = Spec()
        runtime._update_spec_for_karma(spec, artifact_paths=['artifact.js'])
        # values not provided via kwargs will be disappeared.
        self.assertEqual(dict(spec), {
            'artifact_paths': ['artifact.js'],
        })

    def test_update_spec_for_karma_default_value_dropped(self):
        driver = KarmaDriver()
        runtime = KarmaRuntime(driver)
        spec = Spec()
        runtime._update_spec_for_karma(spec, artifact_paths=[])
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
            '--test-packages=pkg1', '--test-registries=dummy1',
        ])
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1'])
        self.assertEqual(ns.test_package_names, ['pkg1'])

        ns = argparser.parse_args([
            'fakekarma',
            '--test-packages=pkg1', '--test-registries=dummy1',
            'fakerun',
        ])
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1'])
        self.assertEqual(ns.test_package_names, ['pkg1'])

        ns = argparser.parse_args([
            'fakekarma',
            '--test-packages=pkg1', '--test-registries=dummy1',
            'fakerun',
            '--test-package=pkg2', '--test-registry=dummy2',
        ])
        self.assertEqual(ns.calmjs_test_registry_names, ['dummy1', 'dummy2'])
        self.assertEqual(ns.test_package_names, ['pkg1', 'pkg2'])

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
            '--test-package', 'calmjs.dev',
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
            transpile_source_map={
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
            transpile_source_map={
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
            transpile_source_map={
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
            transpile_source_map={
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
                    transpile_source_map={
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
            '--test-package', 'no_such_pkg', '-vv',
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
            '--test-package', 'calmjs.dev',
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
        artifact = resource_filename('calmjs.dev', 'main.js')
        result = rt([
            '--artifact', artifact, 'run',
            '--build-dir', build_dir,
            '--test-registry', 'calmjs.dev.module.tests',
            '--test-package', 'calmjs.dev',
            '--coverage', '--cover-artifact',
            '--cover-report-dir', coverage_dir,
        ])
        self.assertIn('karma_config_path', result)
        self.assertEqual(result['artifact_paths'], [artifact])
        self.assertTrue(exists(result['karma_config_path']))
        # should exit cleanly
        self.assertNotIn(
            "karma exited with return code 1", sys.stderr.getvalue())
        self.assertIn(artifact, result['karma_config']['preprocessors'])
        self.assertTrue(exists(coverage_dir))

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
            '--test-package', 'calmjs.dev',
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
            '--test-package', 'calmjs.dev',
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
