# -*- coding: utf-8 -*-
from calmjs.toolchain import Toolchain


class TestToolchain(Toolchain):
    """
    A toolchain that truly does nothing, except to fit in with the
    pattern of getting tests up, and to serve as a safe location for
    other toolchains to register advice steps that they normally add as
    part of their execution.
    """

    def compile(self, spec):
        """
        Do nothing.
        """

    def prepare(self, spec):
        """
        Do nothing.
        """

    def assemble(self, spec):
        """
        Do nothing.
        """

    def link(self, spec):
        """
        Do nothing.
        """


class KarmaToolchain(TestToolchain):
    """
    This one specifically for karma.
    """
