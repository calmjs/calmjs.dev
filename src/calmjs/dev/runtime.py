# -*- coding: utf-8 -*-
"""
This module provides handlers for the toolchain classes and instances
declared for the calmjs framework, reading the compile descriptions and
select the resulting spec targets for usage
"""

import logging

from calmjs.argparse import StoreDelimitedList
from calmjs.runtime import ToolchainRuntime
from calmjs.runtime import DriverRuntime
from calmjs.runtime import Runtime

from calmjs.dev.cli import KarmaDriver

logger = logging.getLogger(__name__)

__all__ = ['KarmaRuntime', 'karma']


# TODO figure out how to do a test on a bundle.  Probably one way is to
# specify the location of the bundle, and similar to above but also make
# use of the test_registries and generate the karma config for that and
# run it against the bundle.


class KarmaRuntime(Runtime, DriverRuntime):
    """
    The runtime class for karma
    """

    def __init__(
            self, cli_driver,
            description='karma testrunner integration for calmjs',
            *a, **kw):
        super(KarmaRuntime, self).__init__(
            cli_driver=cli_driver, description=description, *a, **kw)

    def entry_point_load_validated(self, entry_point):
        # to avoid trying to import this again, check entry_point first
        if entry_point.name == 'karma':
            return False

        inst = super(KarmaRuntime, self).entry_point_load_validated(
            entry_point)
        if not isinstance(inst, ToolchainRuntime):
            logger.debug(
                "filtering out entry point '%s' as it does not lead to a "
                "calmjs.runtime.ToolchainRuntime in KarmaRuntime.",
                entry_point
            )
            return False
        return inst

    def init_argparser(self, argparser):
        super(KarmaRuntime, self).init_argparser(argparser)

        argparser.add_argument(
            '--test-registry', default=None,
            dest='test_registries', action=StoreDelimitedList,
            help='comma separated list of registries to use for gathering '
                 'JavaScript tests from the given Python packages; default '
                 'behavior is to auto-select, enable verbose output to check '
                 'to see which ones were selected',
        )

    def run(self, argparser, **kwargs):
        # have to rely on the local one, because the passed in one will
        # be the root one.
        details = self.get_argparser_details(self.argparser)
        runtime = details.runtimes.get(kwargs.pop(self.action_key))
        if not runtime:
            # only work for python>3.3 typically as the python 2.7
            # argparser will choke without sufficient arguments.
            logger.warning('no runtime provided; please retry with -h option')
            # not using self.argparser because it will not have the
            # global flag set from the global argparser.
            return

        spec = runtime.kwargs_to_spec(**kwargs)
        toolchain = runtime.toolchain
        self.cli_driver.run(toolchain, spec)
        return spec

karma = KarmaRuntime(KarmaDriver.create())
