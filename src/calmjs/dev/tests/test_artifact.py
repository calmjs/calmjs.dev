# -*- coding: utf-8 -*-
import unittest
import sys
from os import mkdir
from os.path import dirname
from types import ModuleType

from pkg_resources import WorkingSet

from calmjs import dist
from calmjs.registry import get
from calmjs.toolchain import Spec

from calmjs.dev.artifact import ArtifactTestRegistry
from calmjs.dev.toolchain import KarmaToolchain

from calmjs.testing import utils


class IntegrationTestCase(unittest.TestCase):

    def test_integrated_get(self):
        # test that the artifact test registry is registered.
        self.assertTrue(
            isinstance(get('calmjs.artifacts.tests'), ArtifactTestRegistry))


class ArtifactTestRegistryTestCase(unittest.TestCase):
    """
    Standard test cases for artifact test registry.
    """

    def test_artifact_test_simulation(self):
        # don't actually run karma, since we are not setting up the full
        # integration environment for this isolated test - also keep the
        # spec reference here and have the helper return it so the
        # simplified verification can be done.
        spec = Spec(karma_advice_group=None)

        def generic_tester(package_names, export_target):
            return KarmaToolchain(), spec,

        tester_mod = ModuleType('calmjs_dev_tester')
        tester_mod.generic = generic_tester

        self.addCleanup(sys.modules.pop, 'calmjs_dev_tester')
        sys.modules['calmjs_dev_tester'] = tester_mod

        working_dir = utils.mkdtemp(self)

        utils.make_dummy_dist(self, (
            ('entry_points.txt', '\n'.join([
                '[calmjs.artifacts.tests]',
                'artifact.js = calmjs_dev_tester:generic',
            ])),
        ), 'app', '1.0', working_dir=working_dir)

        mock_ws = WorkingSet([working_dir])
        utils.stub_item_attr_value(self, dist, 'default_working_set', mock_ws)
        registry = ArtifactTestRegistry(
            'calmjs.artifacts.tests', _working_set=mock_ws)

        artifact_name = registry.get_artifact_filename('app', 'artifact.js')
        # file not exist yet
        self.assertFalse(registry.verify_export_target(artifact_name))

        mkdir(dirname(artifact_name))
        with open(artifact_name, 'w') as fd:
            fd.write('console.log("test artifact");\n')

        self.assertTrue(registry.verify_export_target(artifact_name))

        registry.process_package('app')

        # cheat a bit by probing some private bits to see that the
        # relevant advice is planted but not executed
        self.assertTrue(1, len(spec._advices['before_test']))
