# -*- coding: utf-8 -*-
"""
The obspy.clients.neic.client test suite.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import unittest

import obspy
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.util.decorator import vcr
from obspy.clients.neic import Client


# unix timestamp where this test has been recorded via vcr - needs to be set
# to newer timestamp if recorded later again
VCR_TIMESTAMP = 1485568123.7079487
NO_VCR_TIMESTAMP = UTCDateTime()
# determine which timestamp to use
USE_VCR = not getattr(obspy, '_no_vcr', False)
TIMESTAMP = USE_VCR and VCR_TIMESTAMP or NO_VCR_TIMESTAMP


class ClientTestCase(unittest.TestCase):
    """
    Test cases for obspy.clients.neic.client.Client.
    """
    @vcr
    def test_get_waveform(self):
        """
        Tests get_waveforms method. Tests against get_waveforms_nscl method.
        """
        client = Client(host="137.227.224.97", port=2061)
        # now - 5 hours
        t = UTCDateTime(TIMESTAMP) - 5 * 60 * 60
        duration = 1.0
        st = client.get_waveforms_nscl("IUANMO BH.00", t, duration)
        # try a series of requests, compare against get_waveforms_nscl
        args = [["IU", "ANMO", "00", "BH."],
                ["??", "ANMO", "0?", "BH[Z21]"],
                ["IU", "ANM.*", "00", "B??"],
                ["IU", "ANMO", "0*", "BH."],
                ]
        for args_ in args:
            st2 = client.get_waveforms(*args_, starttime=t,
                                       endtime=t + duration)
            self.assertEqual(st, st2)

    @vcr
    def test_get_waveform_nscl(self):
        """
        Tests get_waveforms_nscl method.
        """
        client = Client(host="137.227.224.97", port=2061)
        # now - 5 hours
        t = UTCDateTime(TIMESTAMP) - 5 * 60 * 60
        duration_long = 3600.0
        duration = 1.0
        components = ["1", "2", "Z"]
        # try one longer request to see if fetching multiple blocks works
        st = client.get_waveforms_nscl("IUANMO BH.00", t, duration_long)
        # merge to avoid failing tests simply due to gaps
        st.merge()
        st.sort()
        self.assertEqual(len(st), 3)
        for tr, component in zip(st, components):
            stats = tr.stats
            self.assertEqual(stats.station, "ANMO")
            self.assertEqual(stats.network, "IU")
            self.assertEqual(stats.location, "00")
            self.assertEqual(stats.channel, "BH" + component)
            self.assertEqual(stats.endtime - stats.starttime, duration_long)
            # if the following fails this is likely due to a change at the
            # requested station and simply has to be adapted
            self.assertEqual(stats.sampling_rate, 20.0)
            self.assertEqual(len(tr), 72001)
        # now use shorter piece, this is faster and less error prone (gaps etc)
        st = client.get_waveforms_nscl("IUANMO BH.00", t, duration)
        st.sort()
        # test returned stream
        self.assertEqual(len(st), 3)
        for tr, component in zip(st, components):
            stats = tr.stats
            self.assertEqual(stats.station, "ANMO")
            self.assertEqual(stats.network, "IU")
            self.assertEqual(stats.location, "00")
            self.assertEqual(stats.channel, "BH" + component)
            self.assertEqual(stats.endtime - stats.starttime, duration)
            # if the following fails this is likely due to a change at the
            # requested station and simply has to be adapted
            self.assertEqual(stats.sampling_rate, 20.0)
            self.assertEqual(len(tr), 21)

        # try a series of regex patterns that should return the same data
        st = client.get_waveforms_nscl("IUANMO BH", t, duration)
        patterns = ["IUANMO BH...",
                    "IUANMO BH.*",
                    "IUANMO BH[Z12].*",
                    "IUANMO BH[Z12]..",
                    "..ANMO BH.*"]
        for pattern in patterns:
            st2 = client.get_waveforms_nscl(pattern, t, duration)
            self.assertEqual(st, st2)


def suite():
    return unittest.makeSuite(ClientTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
