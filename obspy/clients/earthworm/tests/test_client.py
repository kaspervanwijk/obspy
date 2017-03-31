# -*- coding: utf-8 -*-
"""
The obspy.clients.earthworm.client test suite.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import unittest

import obspy
from obspy import read
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.util import NamedTemporaryFile
from obspy.core.util.decorator import vcr
from obspy.clients.earthworm import Client


# unix timestamp where this test has been recorded via vcr - needs to be set
# to newer timestamp if recorded later again
VCR_TIMESTAMP = 1485568123.7079487
NO_VCR_TIMESTAMP = UTCDateTime()
# determine which timestamp to use
USE_VCR = not getattr(obspy, '_no_vcr', False)
TIMESTAMP = USE_VCR and VCR_TIMESTAMP or NO_VCR_TIMESTAMP


class ClientTestCase(unittest.TestCase):
    """
    Test cases for obspy.clients.earthworm.client.Client.
    """
    def setUp(self):
        # Monkey patch: set lower default precision of all UTCDateTime objects
        UTCDateTime.DEFAULT_PRECISION = 4
        self.client = Client("pubavo1.wr.usgs.gov", 16022, timeout=30.0)

    def tearDown(self):
        # restore default precision of all UTCDateTime objects
        UTCDateTime.DEFAULT_PRECISION = 6

    @vcr
    def test_get_waveform(self):
        """
        Tests get_waveforms method.
        """
        client = self.client
        start = UTCDateTime(TIMESTAMP) - 3600
        end = start + 1.0
        # example 1 -- 1 channel, cleanup
        stream = client.get_waveforms('AV', 'ACH', '', 'EHE', start, end)
        self.assertEqual(len(stream), 1)
        delta = stream[0].stats.delta
        trace = stream[0]
        self.assertTrue(len(trace) in (100, 101))
        self.assertGreaterEqual(trace.stats.starttime, start - delta)
        self.assertLessEqual(trace.stats.starttime, start + delta)
        self.assertGreaterEqual(trace.stats.endtime, end - delta)
        self.assertLessEqual(trace.stats.endtime, end + delta)
        self.assertEqual(trace.stats.network, 'AV')
        self.assertEqual(trace.stats.station, 'ACH')
        self.assertEqual(trace.stats.location, '')
        self.assertEqual(trace.stats.channel, 'EHE')
        # example 2 -- 1 channel, no cleanup
        stream = client.get_waveforms('AV', 'ACH', '', 'EHE', start, end,
                                      cleanup=False)
        self.assertGreaterEqual(len(stream), 2)
        summed_length = sum(len(tr) for tr in stream)
        self.assertTrue(summed_length in (100, 101))
        self.assertGreaterEqual(stream[0].stats.starttime, start - delta)
        self.assertLessEqual(stream[0].stats.starttime, start + delta)
        self.assertGreaterEqual(stream[-1].stats.endtime, end - delta)
        self.assertLessEqual(stream[-1].stats.endtime, end + delta)
        for trace in stream:
            self.assertEqual(trace.stats.network, 'AV')
            self.assertEqual(trace.stats.station, 'ACH')
            self.assertEqual(trace.stats.location, '')
            self.assertEqual(trace.stats.channel, 'EHE')
        # example 3 -- component wildcarded with '?'
        stream = client.get_waveforms('AV', 'ACH', '', 'EH?', start, end)
        self.assertEqual(len(stream), 3)
        for trace in stream:
            self.assertTrue(len(trace) in (100, 101))
            self.assertGreaterEqual(trace.stats.starttime, start - delta)
            self.assertLessEqual(trace.stats.starttime, start + delta)
            self.assertGreaterEqual(trace.stats.endtime, end - delta)
            self.assertLessEqual(trace.stats.endtime, end + delta)
            self.assertEqual(trace.stats.network, 'AV')
            self.assertEqual(trace.stats.station, 'ACH')
            self.assertEqual(trace.stats.location, '')
        self.assertEqual(stream[0].stats.channel, 'EHZ')
        self.assertEqual(stream[1].stats.channel, 'EHN')
        self.assertEqual(stream[2].stats.channel, 'EHE')

    @vcr
    def test_save_waveform(self):
        """
        Tests save_waveforms method.
        """
        # initialize client
        client = self.client
        start = UTCDateTime(TIMESTAMP) - 3600
        end = start + 1.0
        with NamedTemporaryFile() as tf:
            testfile = tf.name
            # 1 channel, cleanup (using SLIST to avoid dependencies)
            client.save_waveforms(testfile, 'AV', 'ACH', '', 'EHE', start, end,
                                  format="SLIST")
            stream = read(testfile)
        self.assertEqual(len(stream), 1)
        delta = stream[0].stats.delta
        trace = stream[0]
        self.assertEqual(len(trace), 101)
        self.assertGreaterEqual(trace.stats.starttime, start - delta)
        self.assertLessEqual(trace.stats.starttime, start + delta)
        self.assertGreaterEqual(trace.stats.endtime, end - delta)
        self.assertLessEqual(trace.stats.endtime, end + delta)
        self.assertEqual(trace.stats.network, 'AV')
        self.assertEqual(trace.stats.station, 'ACH')
        self.assertEqual(trace.stats.location, '')
        self.assertEqual(trace.stats.channel, 'EHE')

    @vcr
    def test_availability(self):
        data = self.client.get_availability()
        seeds = ["%s.%s.%s.%s" % (d[0], d[1], d[2], d[3]) for d in data]
        self.assertIn('AV.ACH.--.EHZ', seeds)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ClientTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
