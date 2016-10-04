# -*- coding: utf-8 -*-
import unittest

from calmjs.dev import karma


class BaseConfigTestCase(unittest.TestCase):

    def test_generate_base_config(self):
        result = karma.build_base_config()
        self.assertTrue(isinstance(result, dict))
