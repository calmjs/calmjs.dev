# -*- coding: utf-8 -*-
import unittest
import os

from calmjs.toolchain import Toolchain

from calmjs.dev import utils

from calmjs.testing.utils import stub_os_environ


class ExtractGuiEnvironKeysTestCase(unittest.TestCase):

    def test_base(self):
        stub_os_environ(self)
        os.environ.clear()
        self.assertEqual(utils.extract_gui_environ_keys(), {})

    def test_x11(self):
        stub_os_environ(self)
        os.environ.clear()
        os.environ['DISPLAY'] = ':0'
        self.assertEqual(utils.extract_gui_environ_keys(), {
            'DISPLAY': ':0',
        })

    def test_win32(self):
        stub_os_environ(self)
        os.environ.clear()
        os.environ['PROGRAMFILES'] = 'C:\\Program Files'
        self.assertEqual(utils.extract_gui_environ_keys(), {
            'PROGRAMFILES': 'C:\\Program Files',
        })


class ToolchainTargetsTestCase(unittest.TestCase):

    def test_grab_target_keys_standard(self):
        toolchain = Toolchain()
        result = list(utils.get_toolchain_targets_keys(toolchain))
        self.assertEqual(result, ['transpiled_targetpaths'])

    def test_grab_target_keys_no_exclude(self):
        toolchain = Toolchain()
        result = list(utils.get_toolchain_targets_keys(
            toolchain, exclude_targets_from=()))
        self.assertEqual(result, [
            'transpiled_targetpaths', 'bundled_targetpaths'])

    def test_grab_target_keys_explicit_target(self):
        # will generate these entries; toolchain just provide the
        # hints for values.
        toolchain = Toolchain()
        result = list(utils.get_toolchain_targets_keys(
            toolchain, include_targets_from=('explicit',)))
        self.assertEqual(result, ['explicit_targetpaths'])


class TargetsFromSpecTestCase(unittest.TestCase):

    def test_basic(self):
        spec = {
            'transpiled_targetpaths': {
                't1': '/path/to/t1.js',
                't2': '/path/to/t2.js',
            },
            'moved_targetpaths': {
                'm1': '/move/to/m1.js',
                'm2': '/move/to/m2.js',
            },
        }
        targets = ['transpiled_targetpaths', 'moved_targetpaths']
        result = utils.get_targets_from_spec(spec, targets)
        self.assertEqual(sorted(result), [
            '/move/to/m1.js', '/move/to/m2.js',
            '/path/to/t1.js', '/path/to/t2.js',
        ])

    def test_all_iter(self):
        spec = {
            'transpiled_targetpaths': {
                't1': '/path/to/t1.js',
                't2': '/path/to/t2.js',
            },
            'moved_targetpaths': {
                'm1': '/move/to/m1.js',
                'm2': '/move/to/m2.js',
            },
        }
        targets = iter(['transpiled_targetpaths', 'moved_targetpaths'])
        result = utils.get_targets_from_spec(spec, targets)
        self.assertEqual(sorted(result), [
            '/move/to/m1.js', '/move/to/m2.js',
            '/path/to/t1.js', '/path/to/t2.js',
        ])
