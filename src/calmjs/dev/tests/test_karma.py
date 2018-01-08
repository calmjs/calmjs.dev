# -*- coding: utf-8 -*-
import unittest
from os.path import join

from calmjs.dev import karma
from calmjs.testing.utils import mkdtemp
from calmjs.testing.mocks import StringIO
from calmjs.utils import pretty_logging


class BaseConfigTestCase(unittest.TestCase):

    def test_generate_base_config(self):
        result = karma.build_base_config()
        self.assertTrue(isinstance(result, dict))

    def test_coverage_reporter_builder(self):
        self.assertEqual({
            'type': 'html',
            'dir': 'somedir',
        }, karma.build_coverage_reporter_config('html', 'somedir', 'somefile'))

        self.assertEqual({
            'type': 'json',
            'dir': 'somedir',
            'file': join('somedir', 'somefile'),
        }, karma.build_coverage_reporter_config('json', 'somedir', 'somefile'))

        self.assertEqual({
            'type': 'json',
            'dir': 'somedir',
            'file': join('somedir', 'coverage.json'),
        }, karma.build_coverage_reporter_config('json', 'somedir', None))

    def test_coverage_reporter_builders(self):
        basedir = mkdtemp(self)
        reporters = karma.build_coverage_reporters_config(
            ['html', 'json'], basedir, 'somefile')
        self.assertEqual({
            'dir': basedir,
            'reporters': [{
                'type': 'html',
                'subdir': 'html',
            }, {
                'type': 'json',
                'file': join(basedir, 'coverage.json'),
            }]
        }, reporters)

    def test_coverage_reporter_builders_text(self):
        # because istanbul/karma/whatever/javascript is stupid and will
        # do the wrong thing and break silently if the ordering is done
        # in a way it doesn't like
        basedir = mkdtemp(self)
        reporters = karma.build_coverage_reporters_config(
            ['text', 'lcovonly', 'json'], basedir, 'somefile')
        self.assertEqual({
            'dir': basedir,
            'reporters': [{
                'type': 'lcovonly',
                'file': join(basedir, 'coverage.lcov'),
            }, {
                'type': 'json',
                'file': join(basedir, 'coverage.json'),
            }, {
                'type': 'text',
            }]
        }, reporters)

    def test_coverage_reporter_builder_invalid(self):
        with pretty_logging(logger='calmjs.dev', stream=StringIO()) as s:
            reporters = karma.build_coverage_reporter_config(
                'invalid_builder', 'somedir', 'somefile')

        self.assertIn(
            "coverage reporter 'invalid_builder' not supported", s.getvalue())
        self.assertEqual({}, reporters)

    def test_coverage_reporter_builders_invalid(self):
        with pretty_logging(logger='calmjs.dev', stream=StringIO()) as s:
            reporters = karma.build_coverage_reporters_config(
                ['invalid_builder'], 'somedir', 'somefile')

        self.assertIn(
            "coverage reporter 'invalid_builder' not supported", s.getvalue())
        self.assertEqual({'dir': 'somedir', 'reporters': []}, reporters)
