# -*- coding: utf-8 -*-
import unittest

from calmjs.dev import toolchain


class UpdateSpecForKarmaTestCase(unittest.TestCase):
    """
    This function originally compliments the kwargs_to_spec method
    provided by the toolchain runtime classes, which may more may not
    faithfully capture and provide all the values as expected for the
    execution of karma.  It also makes the assumption that the toolchain
    will not prematurely transform the provided kwargs into some other
    form which the reassignment may cause breakage with what it might
    expect.
    """

    def test_update_spec_for_karma_empty(self):
        # should work for a bare dict.
        spec = {}
        toolchain.update_spec_for_karma(spec)
        self.assertEqual(spec, {})

    def test_update_spec_for_karma_kwarg_priority(self):
        # since the kwargs values always have priority, whatever got
        # present in spec but without kwargs is going to be assumed to
        # be of the default value, and those are removed
        spec = {'build_dir': 'target.js'}
        toolchain.update_spec_for_karma(spec)
        self.assertEqual(spec, {})

    def test_update_spec_for_karma_kwarg_present(self):
        # with the kwargs value provided, the new value will be set.
        spec = {'build_dir': 'target.js'}
        toolchain.update_spec_for_karma(spec, build_dir='new.js')
        self.assertEqual(spec, {'build_dir': 'new.js'})

    def test_update_spec_for_karma_kwarg_list(self):
        # the list should NOT change
        names = ['demo1', 'demo2']
        spec = {}
        toolchain.update_spec_for_karma(spec, test_package_names=names)
        self.assertEqual(spec, {'test_package_names': ['demo1', 'demo2']})
        self.assertIsNot(spec['test_package_names'], names)
        spec['test_package_names'].append('demo3')
        # remain unchanged.
        self.assertEqual(names, ['demo1', 'demo2'])
