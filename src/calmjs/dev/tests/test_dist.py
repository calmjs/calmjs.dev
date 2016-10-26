# -*- coding: utf-8 -*-
import unittest

from calmjs.dev import dist


class DistTestCase(unittest.TestCase):

    def test_get_module_registries_dependencies(self):
        results = dist.get_module_registries_dependencies(
            ['calmjs.dev'], ['calmjs.dev.module', 'calmjs.dev.module.tests'])

        self.assertEqual(sorted(results.keys()), [
            'calmjs/dev/main',
            'calmjs/dev/tests/test_fail',
            'calmjs/dev/tests/test_main',
        ])

    def test_get_module_default_test_registries_dependencies(self):
        results = dist.get_module_default_test_registries_dependencies(
            ['calmjs.dev'], ['calmjs.dev.module'])

        self.assertEqual(sorted(results.keys()), [
            'calmjs/dev/tests/test_fail',
            'calmjs/dev/tests/test_main',
        ])
