# -*- coding: utf-8 -*-
"""
Management of the testing of prebuilt artifacts.

This is largely based on existing infrastructure provided by upstream,
the classes are subclasses and modified to handle the specific usage.

For a more complete documentation, please refer to calmjs.artifacts.
"""

from __future__ import absolute_import

from logging import getLogger
from calmjs.artifact import BaseArtifactRegistry
from calmjs.artifact import extract_builder_result
from calmjs.artifact import exists

from calmjs.dev.cli import KarmaDriver
from calmjs.dev.toolchain import KarmaToolchain

logger = getLogger(__name__)


class ArtifactTestRegistry(BaseArtifactRegistry):
    """
    A registry for setting up the tests against prebuilt artifacts.
    """

    def extract_builder_result(self, builder_result):
        return extract_builder_result(
            builder_result, toolchain_cls=KarmaToolchain)

    def verify_export_target(self, export_target):
        return exists(export_target)

    def execute_builder(self, entry_point, toolchain, spec):
        """
        Create the KarmaDriver and run the toolchain/spec through it,
        without generating further metadata.
        """

        KarmaDriver().create().run(toolchain, spec)
        return {}
