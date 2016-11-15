# -*- coding: utf-8 -*-
"""
Module that provides integration with karma.
"""

# spec keys
AFTER_KARMA = 'after_karma'
BEFORE_KARMA = 'before_karma'
KARMA_ABORT_ON_TEST_FAILURE = 'karma_abort_on_test_failure'
KARMA_ADVICE_GROUP = 'karma_advice_group'
KARMA_BROWSERS = 'karma_browsers'
KARMA_CONFIG = 'karma_config'
KARMA_CONFIG_PATH = 'karma_config_path'
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
