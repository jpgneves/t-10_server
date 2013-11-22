from teeminus10_helpers import *
import unittest

class TestInTimeOfDay(unittest.TestCase):
    def setUp(self):
        self.location = ephem.city('London')
        self.location.date = datetime(2013, 03, 14, 9, 0, 0)
        self.pass_day_time = datetime(2013, 03, 14, 12, 0, 0)
        self.pass_night_time = datetime(2013, 03, 14, 0, 0, 0)
        
    def test_pass_in_whatever_time(self):
        self.assertTrue(in_time_of_day(self.location, self.pass_day_time, "whatever"))
        self.assertTrue(in_time_of_day(self.location, self.pass_night_time, "whatever"))

    def test_pass_in_day_time(self):
        self.assertTrue(in_time_of_day(self.location, self.pass_day_time, "day"))
        self.assertFalse(in_time_of_day(self.location, self.pass_night_time, "day"))

    def test_pass_in_night_time(self):
        self.assertFalse(in_time_of_day(self.location, self.pass_day_time, "night"))
        self.assertTrue(in_time_of_day(self.location, self.pass_night_time, "night"))
