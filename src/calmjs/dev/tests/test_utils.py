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
