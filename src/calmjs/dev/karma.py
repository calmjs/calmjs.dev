# -*- coding: utf-8 -*-
"""
Module that provides integration with karma.
"""

import logging
from os.path import curdir
from os.path import sep
from os.path import join
from os.path import realpath

logger = logging.getLogger(__name__)

# spec keys
AFTER_KARMA = 'after_karma'
BEFORE_KARMA = 'before_karma'
KARMA_ABORT_ON_TEST_FAILURE = 'karma_abort_on_test_failure'
KARMA_ADVICE_GROUP = 'karma_advice_group'
KARMA_BROWSERS = 'karma_browsers'
KARMA_CONFIG = 'karma_config'
KARMA_CONFIG_PATH = 'karma_config_path'
KARMA_CONFIG_WRITER = 'karma_config_writer'
KARMA_EXTRA_FRAMEWORKS = 'karma_extra_frameworks'
KARMA_RETURN_CODE = 'karma_return_code'
KARMA_SPEC_KEYS = 'karma_spec_keys'

# templates

KARMA_CONF_TEMPLATE = '''\
module.exports = function(config) {
    config.set(%s);
}
'''

# other constants
KARMA_CONF_JS = 'karma.conf.js'

# note that the actual tool, with default dependencies, show that the
# allowed values are clover, cobertura, html, json, json-summary, lcov,
# lcovonly, none, teamcity, text, text-lcov, text-summary
COVER_REPORT_TYPES = (
    ('html', {
        'subdir': 'html',
    }),
    ('lcov', {
        'subdir': 'lcov',
    }),
    ('lcovonly', {
        'file': 'coverage.lcov',
    }),
    ('json', {
        'file': 'coverage.json',
    }),
    ('text', {
    }),
)
COVER_REPORT_TYPE_OPTIONS = dict(COVER_REPORT_TYPES)
DEFAULT_COVER_REPORT_TYPE_OPTIONS = ('html', 'json', 'lcov', 'text')


def build_base_config(
        baseUrl='./',
        frameworks=('mocha', 'chai', 'expect', 'sinon'),  # extensible
        reporters=('spec', 'progress'),  # override/extensible
        port=9876,  # override
        colors=True,  # override
        logLevel='INFO',  # override
        browsers=('PhantomJS',),  # override
        captureTimeout=60000,  # override
        singleRun=True,  # override
        ):
    """
    Build a base karma configuration file.
    """

    def to_value(v):
        return list(v) if isinstance(v, tuple) else v

    return {k: to_value(v) for k, v in locals().items() if k in [
        'baseUrl', 'frameworks', 'reporters', 'port', 'colors', 'logLevel',
        'browsers', 'captureTimeout', 'singleRun',
    ]}


def build_coverage_reporter_config(report_key, report_dir, report_file):
    if report_key not in COVER_REPORT_TYPE_OPTIONS:
        logger.warning("coverage reporter '%s' not supported", report_key)
        return {}
    reporter = {
        'type': report_key,
        'dir': report_dir,
    }
    reporter.update(COVER_REPORT_TYPE_OPTIONS[report_key])
    # not relevant for a single report
    reporter.pop('subdir', None)
    if 'file' in reporter:
        if report_file:
            if report_file.startswith(curdir + sep):
                report_file = realpath(report_file)
            else:
                report_file = join(report_dir, report_file)
        else:
            report_file = join(report_dir, reporter['file'])
        reporter['file'] = report_file
    return reporter


def build_coverage_reporters_config(report_keys, report_dir, report_file):
    reporters = []
    report_set = set(report_keys)

    # have to generate the listing in order, otherwise fun debugging
    # happens
    for key, option in COVER_REPORT_TYPES:
        if key not in report_set:
            continue

        report_set.remove(key)
        reporter = {}
        reporter.update(option)

        # while 'subdir' is as documented, file... doesn't go there.
        if 'file' in reporter:
            reporter['file'] = realpath(join(report_dir, reporter['file']))
        # stitch the key back in as the type
        reporter['type'] = key
        reporters.append(reporter)

    for unsupported in report_set:
        logger.warning(
            "coverage reporter '%s' not supported", unsupported)

    return {
        'dir': report_dir,
        'reporters': reporters,
    }


def config_writer(driver, config, fd):
    """
    The default complete karma config writer.  Note that the invocation
    of the writer by the ``cli.KarmaDriver`` class only applies the
    latter two arguments, and it would construct a partial using itself
    to do so.

    The writer itself may be override by providing a function that takes
    two arguments to spec[KARMA_CONFIG_WRITER], and it may be a partial
    so that the values of spec and/or the toolchain (plus others) may be
    referenced from within the scope of the writer, for example:

        from functools import partial

        def some_writer(toolchain, spec, config, fd):
            fd.write(toolchain.process_test_config(spec, config))

        spec[KARMA_CONFIG_WRITER] = partial(some_writer, toolchain, spec)

    Naturally, the contents written must call config.set with the valid
    karma configuration settings in order for the execution of the test
    to occur correctly.
    """

    fd.write(KARMA_CONF_TEMPLATE % driver.dumps(config))
