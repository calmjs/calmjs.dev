# -*- coding: utf-8 -*-
"""
Module that provides integration with karma.
"""

KARMA_CONF_TEMPLATE = '''\
module.exports = function(config) {
    config.set(%s);
}
'''

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

    return {k: v for k, v in locals().items() if k in [
        'baseUrl', 'frameworks', 'reporters', 'port', 'colors', 'logLevel',
        'browsers', 'captureTimeout', 'singleRun',
    ]}
