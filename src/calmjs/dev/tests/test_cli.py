# -*- coding: utf-8 -*-
import unittest
import json
from os.path import basename
from os.path import curdir
from os.path import exists
from os.path import join
from os.path import realpath

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

    def test_valid_cover_file(self):
        driver = cli.KarmaDriver()
        self.assertTrue(driver._valid_cover_file('something.js'))
        self.assertTrue(driver._valid_cover_file('test_something.js'))
        self.assertFalse(driver._valid_cover_file('test_something.txt'))
        self.assertFalse(driver._valid_cover_file('__something__.js'))
        self.assertFalse(driver._valid_cover_file('dir/__something__/mod.js'))

    def test_filter_cover_path(self):
        def custom_filter(path):
            return path == 'custom.js'
        driver = cli.KarmaDriver()
        spec = Spec()
        self.assertTrue(driver.filter_cover_path(spec, 'something.js'))
        self.assertFalse(driver.filter_cover_path(spec, 'filtered.txt'))
        spec['cover_path_filter'] = custom_filter
        self.assertFalse(driver.filter_cover_path(spec, 'something.js'))
        self.assertTrue(driver.filter_cover_path(spec, 'custom.js'))

    def test_apply_preprocessors_config_null(self):
        driver = cli.KarmaDriver()
        config = {}
        driver._apply_preprocessors_config(config, {})
        self.assertEqual(config['preprocessors'], {})

    def test_apply_preprocessors_config_identity(self):
        driver = cli.KarmaDriver()
        preprocessors = {
            'some/**/*.js': ['something'],
        }
        config = {'preprocessors': preprocessors}
        driver._apply_preprocessors_config(config, {})
        self.assertIs(config['preprocessors'], preprocessors)

    def test_apply_preprocessors_config_new(self):
        driver = cli.KarmaDriver()
        config = {'preprocessors': {
            'some/**/*.js': ['something'],
        }}
        driver._apply_preprocessors_config(config, {'foo.js': ['other']})
        self.assertEqual(config['preprocessors'], {
            'some/**/*.js': ['something'],
            'foo.js': ['other'],
        })

    def test_apply_preprocessors_config_overlap(self):
        driver = cli.KarmaDriver()
        config = {'preprocessors': {
            'some/**/*.js': ['something'],
        }}
        driver._apply_preprocessors_config(config, {'some/**/*.js': ['other']})
        self.assertEqual(config['preprocessors'], {
            'some/**/*.js': ['something', 'other'],
        })

    def test_apply_preprocessors_config_correction(self):
        driver = cli.KarmaDriver()
        config = {'preprocessors': {
            'other.js': 'something',
            'some/**/*.js': 'something',
        }}
        driver._apply_preprocessors_config(config, {
            'some/**/*.js': ['other'],
            'need/**/*.js': 'fix',
        })
        self.assertEqual(config['preprocessors'], {
            'other.js': 'something',
            'some/**/*.js': ['something', 'other'],
            'need/**/*.js': ['fix'],
        })

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

    def test_setup_cover(self):
        build_dir = mkdtemp(self)
        toolchain = NullToolchain()
        spec = Spec(build_dir=build_dir, coverage_enable=True)
        driver = cli.KarmaDriver()
        driver.binary = None
        driver.setup_toolchain_spec(toolchain, spec)
        self.assertTrue(spec['generate_source_map'])

    def test_create_config_base(self):
        spec = Spec()
        driver = cli.KarmaDriver()
        driver.create_config(spec)
        self.assertEqual(spec['karma_config']['files'], [])

    def test_apply_wrap_tests(self):
        driver = cli.KarmaDriver()
        spec = Spec(
            no_wrap_tests=False,
        )

        config = {}
        test_module_path = [
            'some/path/testTemplate.tmpl',
            'some/path/testModule.js',
            'some/path/module.js',
            'test/path/file.js',
        ]

        driver._apply_wrap_tests(spec, config, test_module_path)
        self.assertEqual(config, {
            'preprocessors': {'some/path/testModule.js': ['wrap']},
            'wrapPreprocessor': {
                'template': '(function () { <%= contents %> })()'},
        })

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
            "using 'source_package_names' as fallback", log.getvalue(),
        )
        self.assertIn(
            "spec has no 'calmjs_test_registry_names' specified, "
            "using 'calmjs_module_registry_names' as fallback", log.getvalue(),
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

    def test_coverage_reporter_apply_default(self):
        spec = Spec(
            coverage_enable=True,
            no_wrap_tests=True,
        )
        driver = cli.KarmaDriver()
        config = {}
        driver._apply_coverage_reporters(spec, config)
        self.assertEqual(4, len(config['coverageReporter']['reporters']))

    def test_coverage_reporter_apply_singular(self):
        spec = Spec(
            coverage_enable=True,
            no_wrap_tests=True,
            cover_report_types=['html'],
        )
        driver = cli.KarmaDriver()
        config = {}
        driver._apply_coverage_reporters(spec, config)
        self.assertEqual({
            'type': 'html',
            'dir': realpath('coverage'),
        }, config['coverageReporter'])

    def test_coverage_reporter_apply_legacy(self):
        spec = Spec(
            coverage_enable=True,
            no_wrap_tests=True,
            coverage_type='html',
        )
        driver = cli.KarmaDriver()
        config = {}
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            driver._apply_coverage_reporters(spec, config)
        self.assertIn("WARNING", log.getvalue())
        self.assertIn("'coverage_type' is deprecated", log.getvalue())
        self.assertEqual({
            'type': 'html',
            'dir': realpath('coverage'),
        }, config['coverageReporter'])

    def test_coverage_apply(self):
        spec = Spec(
            coverage_enable=True,
        )
        driver = cli.KarmaDriver()
        config = {}
        driver._apply_coverage_config(spec, config, [
            'some_file.js', 'readme.txt'], ['test_path.js', 'foo.txt'])
        self.assertEqual(config['preprocessors'], {
            'some_file.js': ['coverage'],
        })

    def test_coverage_apply_cover_test(self):
        spec = Spec(
            coverage_enable=True,
            cover_test=True,
        )
        driver = cli.KarmaDriver()
        config = {}
        driver._apply_coverage_config(spec, config, [
            'some_file.js', 'readme.txt'], ['test_path.js', 'foo.txt'])
        self.assertEqual(spec['test_covered_test_paths'], {'test_path.js'})
        self.assertEqual(config['preprocessors'], {
            'some_file.js': ['coverage'],
            'test_path.js': ['coverage'],
        })

    def test_coverage_apply_custom_filter(self):
        spec = Spec(
            coverage_enable=True,
            cover_test=True,
            cover_path_filter=lambda p: p.endswith('.txt'),
        )
        driver = cli.KarmaDriver()
        config = {}
        driver._apply_coverage_config(spec, config, [
            'some_file.js', 'readme.txt'], ['test_path.js', 'foo.txt'])
        self.assertEqual(spec['test_covered_test_paths'], {'foo.txt'})
        self.assertEqual(config['preprocessors'], {
            'readme.txt': ['coverage'],
            'foo.txt': ['coverage'],
        })

    def test_create_config_with_coverage_standard_no_wrap(self):
        # this is usually provided by the toolchains themselves
        spec = Spec(
            test_package_names=['calmjs.dev'],
            source_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            bundled_targetpaths={'jquery': 'jquery.js'},
            # provide the other bits that normally get set up earlier.
            transpiled_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.js',
            },
            karma_spec_keys=['bundled_targetpaths', 'transpiled_targetpaths'],
            coverage_enable=True,
            no_wrap_tests=True,
        )
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        self.assertNotIn('test_fail.js', [
            basename(k) for k in spec['karma_config']['preprocessors']
        ])
        self.assertNotIn('jquery.js', spec['karma_config']['preprocessors'])
        self.assertIn('calmjs/dev/main.js', spec['karma_config']['files'])
        self.assertIn(
            'calmjs/dev/main.js', spec['karma_config']['preprocessors'])
        self.assertEqual(
            spec['karma_config']['coverageReporter']['dir'],
            realpath('coverage'),
        )
        # default specifies three different reporters.
        self.assertEqual(
            len(spec['karma_config']['coverageReporter']['reporters']), 4)
        self.assertEqual(
            spec['test_covered_build_dir_paths'], {'calmjs/dev/main.js'})
        self.assertNotIn('test_covered_test_paths', spec)
        self.assertNotIn('test_covered_artifact_paths', spec)

    def test_create_config_with_coverage_standard(self):
        # this is usually provided by the toolchains themselves
        spec = Spec(
            test_package_names=['calmjs.dev'],
            source_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            bundled_targetpaths={'jquery': 'jquery.js'},
            # provide the other bits that normally get set up earlier.
            transpiled_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.js',
            },
            karma_spec_keys=['bundled_targetpaths', 'transpiled_targetpaths'],
            coverage_enable=True,
            no_wrap_tests=False,
        )
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        preprocessors = spec['karma_config']['preprocessors']
        target = [k for k in preprocessors if basename(k) == 'test_fail.js'][0]
        self.assertEqual(preprocessors[target], ['wrap'])
        self.assertNotIn('jquery.js', spec['karma_config']['preprocessors'])
        self.assertIn('calmjs/dev/main.js', spec['karma_config']['files'])
        self.assertIn(
            'calmjs/dev/main.js', spec['karma_config']['preprocessors'])
        self.assertEqual(
            spec['karma_config']['coverageReporter']['dir'],
            realpath('coverage'),
        )
        # default specifies three different reporters.
        self.assertEqual(
            len(spec['karma_config']['coverageReporter']['reporters']), 4)

    def test_create_config_with_coverage_standard_specified_no_wrap(self):
        # this is usually provided by the toolchains themselves
        spec = Spec(
            test_package_names=['calmjs.dev'],
            source_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            bundled_targetpaths={'jquery': 'jquery.js'},
            # provide the other bits that normally get set up earlier.
            transpiled_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.js',
            },
            karma_spec_keys=['bundled_targetpaths', 'transpiled_targetpaths'],
            coverage_enable=True,
            cover_report_types=['lcov'],
            no_wrap_tests=True,
        )
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        self.assertNotIn('test_fail.js', [
            basename(k) for k in spec['karma_config']['preprocessors']
        ])
        self.assertNotIn('jquery.js', spec['karma_config']['preprocessors'])
        self.assertIn('calmjs/dev/main.js', spec['karma_config']['files'])
        self.assertIn(
            'calmjs/dev/main.js', spec['karma_config']['preprocessors'])
        self.assertEqual(spec['karma_config']['coverageReporter'], {
            'type': 'lcov',
            'dir': realpath('coverage'),
        })

    def test_create_config_with_coverage_standard_specified(self):
        # this is usually provided by the toolchains themselves
        spec = Spec(
            test_package_names=['calmjs.dev'],
            source_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            bundled_targetpaths={'jquery': 'jquery.js'},
            # provide the other bits that normally get set up earlier.
            transpiled_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.js',
            },
            karma_spec_keys=['bundled_targetpaths', 'transpiled_targetpaths'],
            coverage_enable=True,
            cover_report_types=['lcov'],
            no_wrap_tests=False,
        )
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        preprocessors = spec['karma_config']['preprocessors']
        target = [k for k in preprocessors if basename(k) == 'test_fail.js'][0]
        self.assertEqual(preprocessors[target], ['wrap'])
        self.assertNotIn('jquery.js', spec['karma_config']['preprocessors'])
        self.assertIn('calmjs/dev/main.js', spec['karma_config']['files'])
        self.assertIn(
            'calmjs/dev/main.js', spec['karma_config']['preprocessors'])
        self.assertEqual(spec['karma_config']['coverageReporter'], {
            'type': 'lcov',
            'dir': realpath('coverage'),
        })

    def test_create_config_with_coverage_alternative(self):
        # provide bundle and also include tests
        spec = Spec(
            test_package_names=['calmjs.dev'],
            source_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            bundled_targetpaths={'jquery': 'jquery.js'},
            # provide the other bits that normally get set up earlier.
            transpiled_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.js',
                'calmjs/dev/__main__': 'calmjs/dev/__main__.js',
            },
            # for testing the filtering
            css_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.css',
            },
            karma_spec_keys=[
                'bundled_targetpaths', 'transpiled_targetpaths',
                'css_targetpaths',
            ],
            coverage_enable=True,
            cover_bundle=True,
            cover_test=True,
            cover_report_types=['lcov'],
            no_wrap_tests=False,
        )
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        preprocessors = spec['karma_config']['preprocessors']
        target = [k for k in preprocessors if basename(k) == 'test_fail.js'][0]
        self.assertEqual(preprocessors[target], ['coverage', 'wrap'])
        self.assertIn('jquery.js', spec['karma_config']['preprocessors'])
        self.assertIn('calmjs/dev/main.js', spec['karma_config']['files'])
        self.assertIn(
            'calmjs/dev/main.js', spec['karma_config']['preprocessors'])
        self.assertNotIn(
            'calmjs/dev/main.css', spec['karma_config']['preprocessors'])
        self.assertNotIn(
            'calmjs/dev/__main__.js', spec['karma_config']['preprocessors'])
        self.assertEqual(spec['karma_config']['coverageReporter'], {
            'type': 'lcov',
            'dir': realpath('coverage'),
        })

        self.assertEqual(2, len(spec['test_covered_test_paths']))

    def test_create_config_with_coverage_alternative_file(self):
        # provide bundle and also include tests
        original = dict(
            test_package_names=['calmjs.dev'],
            source_package_names=['calmjs.dev'],
            calmjs_test_registry_names=['calmjs.dev.module.tests'],
            calmjs_module_registry_names=['calmjs.dev.module'],
            bundled_targetpaths={'jquery': 'jquery.js'},
            # provide the other bits that normally get set up earlier.
            transpiled_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.js',
                'calmjs/dev/__main__': 'calmjs/dev/__main__.js',
            },
            # for testing the filtering
            css_targetpaths={
                'calmjs/dev/main': 'calmjs/dev/main.css',
            },
            karma_spec_keys=[
                'bundled_targetpaths', 'transpiled_targetpaths',
                'css_targetpaths',
            ],
            coverage_enable=True,
            cover_report_types=['lcovonly'],
            cover_report_dir='lcov-coverage',
            cover_report_file='lcov.txt',
        )
        spec = Spec(original)
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        self.assertEqual(spec['karma_config']['coverageReporter'], {
            'type': 'lcovonly',
            'dir': realpath('lcov-coverage'),
            'file': join(realpath('lcov-coverage'), 'lcov.txt'),
        })

        original['cover_report_file'] = join(curdir, 'lcov.txt')
        spec = Spec(original)
        driver = cli.KarmaDriver()
        driver.create_config(spec)

        self.assertIn('coverage', spec['karma_config']['reporters'])
        self.assertEqual(spec['karma_config']['coverageReporter'], {
            'type': 'lcovonly',
            'dir': realpath('lcov-coverage'),
            'file': realpath('lcov.txt'),
        })

    def test_create_config_artifact_paths(self):
        driver = cli.KarmaDriver()
        spec = Spec(
            artifact_paths=[
                'test/artifact.css',
                'test/artifact.js',
            ],
            coverage_enable=True,
            cover_bundle=True,
            cover_artifact=True,
        )
        driver.create_config(spec)
        self.assertEqual(
            spec['test_covered_artifact_paths'], {'test/artifact.js'})

    def test_write_config_not_enough_info(self):
        build_dir = mkdtemp(self)
        spec = Spec(build_dir=build_dir)
        driver = cli.KarmaDriver()
        with pretty_logging(
                logger='calmjs.dev', stream=mocks.StringIO()) as log:
            driver.write_config(spec)
        self.assertIn(
            "no valid 'karma_config' in spec; cannot write 'karma.conf.js'",
            log.getvalue(),
        )
        self.assertFalse(exists(join(build_dir, 'karma.conf.js')))

    def test_write_config_base(self):
        build_dir = mkdtemp(self)
        spec = Spec(build_dir=build_dir, karma_config={})
        driver = cli.KarmaDriver()
        driver.write_config(spec)
        self.assertTrue(exists(join(build_dir, 'karma.conf.js')))

    def test_write_config_invalid_files(self):
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver()
        spec = Spec(build_dir=build_dir, karma_config={'files': None})
        driver.write_config(spec)
        self.assertTrue(exists(join(build_dir, 'karma.conf.js')))

    def test_write_config_invalid_artifact_paths(self):
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver()
        spec = Spec(
            build_dir=build_dir, karma_config={'files': []},
            artifact_paths=None,
        )
        driver.write_config(spec)
        self.assertTrue(exists(join(build_dir, 'karma.conf.js')))

    def test_write_config_valid_files_artifact_paths(self):
        build_dir = mkdtemp(self)
        driver = cli.KarmaDriver()
        spec = Spec(
            build_dir=build_dir, karma_config={'files': ['test/file']},
            artifact_paths=['test/artifact'],
        )
        driver.write_config(spec)
        with open(join(build_dir, 'karma.conf.js')) as fd:
            conf = fd.read()
        self.assertIn('test/file', conf)
        self.assertIn('test/artifact', conf)

# rest of cli related tests have been streamlined into runtime for
# setup and teardown optimisation.
