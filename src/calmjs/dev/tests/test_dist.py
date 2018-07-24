# -*- coding: utf-8 -*-
import unittest

from calmjs import base
from calmjs.dev import dist
from calmjs.testing.utils import stub_item_attr_value
from calmjs.testing.mocks import WorkingSet
from calmjs.testing.module import ChildModuleRegistry


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

    def test_map_registry_name_to_test(self):
        working_set = WorkingSet({})
        root = base.BaseModuleRegistry(
            'root.module', _working_set=working_set)
        child = ChildModuleRegistry(
            'root.module.child', _parent=root, _working_set=working_set)
        grandchild = ChildModuleRegistry(
            'root.module.child.child', _parent=child,
            _working_set=working_set)

        stub_item_attr_value(self, dist, 'get', {
            r.registry_name: r for r in [root, child, grandchild]}.get)

        # no assumptions are made about missing registries
        self.assertEqual([
            'missing.module.child.tests',
        ], list(dist.map_registry_name_to_test(['missing.module.child'])))

        # standard registry
        self.assertEqual([
            'root.module.tests',
        ], list(dist.map_registry_name_to_test(['root.module'])))

        # grandchild registry
        self.assertEqual([
            'root.module.tests.child.child',
        ], list(dist.map_registry_name_to_test(['root.module.child.child'])))
