# -*- coding: utf-8 -*-
import unittest

from calmjs.toolchain import Toolchain

from calmjs.dev import utils


class ToolchainTargetsTestCase(unittest.TestCase):

    def test_grab_target_keys_standard(self):
        toolchain = Toolchain()
        result = list(utils.get_toolchain_targets_keys(toolchain))
        self.assertEqual(result, ['transpiled_targets'])

    def test_grab_target_keys_no_exclude(self):
        toolchain = Toolchain()
        result = list(utils.get_toolchain_targets_keys(
            toolchain, exclude_targets_from=()))
        self.assertEqual(result, ['transpiled_targets', 'bundled_targets'])

    def test_grab_target_keys_explicit_target(self):
        # will generate these entries; toolchain just provide the
        # hints for values.
        toolchain = Toolchain()
        result = list(utils.get_toolchain_targets_keys(
            toolchain, include_targets_from=('explicit',)))
        self.assertEqual(result, ['explicit_targets'])


class TargetsFromSpecTestCase(unittest.TestCase):

    def test_basic(self):
        spec = {
            'transpiled_targets': {
                't1': '/path/to/t1.js',
                't2': '/path/to/t2.js',
            },
            'moved_targets': {
                'm1': '/move/to/m1.js',
                'm2': '/move/to/m2.js',
            },
        }
        targets = ['transpiled_targets', 'moved_targets']
        result = utils.get_targets_from_spec(spec, targets)
        self.assertEqual(sorted(result), [
            '/move/to/m1.js', '/move/to/m2.js',
            '/path/to/t1.js', '/path/to/t2.js',
        ])

    def test_all_iter(self):
        spec = {
            'transpiled_targets': {
                't1': '/path/to/t1.js',
                't2': '/path/to/t2.js',
            },
            'moved_targets': {
                'm1': '/move/to/m1.js',
                'm2': '/move/to/m2.js',
            },
        }
        targets = iter(['transpiled_targets', 'moved_targets'])
        result = utils.get_targets_from_spec(spec, targets)
        self.assertEqual(sorted(result), [
            '/move/to/m1.js', '/move/to/m2.js',
            '/path/to/t1.js', '/path/to/t2.js',
        ])
