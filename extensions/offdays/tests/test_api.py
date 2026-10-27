"""Tests for the Nager.Date API client (mocked network)."""

import json
import unittest
from unittest.mock import patch
from datetime import date

from offdays import api


US_2026_HOLIDAYS = [
    {"date": "2026-01-01", "localName": "New Year's Day", "name": "New Year's Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-01-19", "localName": "Martin Luther King, Jr. Day", "name": "Martin Luther King, Jr. Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-02-16", "localName": "Washington's Birthday", "name": "Presidents Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-05-25", "localName": "Memorial Day", "name": "Memorial Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-06-19", "localName": "Juneteenth National Independence Day", "name": "Juneteenth National Independence Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-07-03", "localName": "Independence Day", "name": "Independence Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-09-07", "localName": "Labor Day", "name": "Labour Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-11-11", "localName": "Veterans Day", "name": "Veterans Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-11-26", "localName": "Thanksgiving Day", "name": "Thanksgiving Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
    {"date": "2026-12-25", "localName": "Christmas Day", "name": "Christmas Day",
     "countryCode": "US", "fixed": False, "global": True, "counties": None,
     "launchYear": None, "types": ["Public", "Bank"]},
]


class TestFetchHolidays(unittest.TestCase):
    """Test API fetch functions with mocked urlopen."""

    @patch("offdays.api._urlopen")
    def test_fetch_holidays_parses_json(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(US_2026_HOLIDAYS).encode()
        )
        result = api.fetch_holidays("US", 2026)
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]["name"], "New Year's Day")
        mock_urlopen.assert_called_once()

    @patch("offdays.api._urlopen")
    def test_fetch_holidays_url_format(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b"[]"
        api.fetch_holidays("de", 2027)
        url_arg = mock_urlopen.call_args[0][0]
        self.assertIn("2027", url_arg)
        self.assertIn("DE", url_arg)  # uppercased

    @patch("offdays.api._urlopen")
    def test_fetch_countries(self, mock_urlopen):
        countries = [
            {"countryCode": "US", "name": "United States"},
            {"countryCode": "DE", "name": "Germany"},
        ]
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(countries).encode()
        )
        result = api.fetch_countries()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["countryCode"], "US")


class TestFetchHolidaysDirect(unittest.TestCase):
    """Integration-style tests with the live API (run only if network available)."""

    @unittest.skip("Network-dependent: run manually to verify real API")
    def test_live_fetch_us_2026(self):
        holidays = api.fetch_holidays("US", 2026)
        self.assertGreater(len(holidays), 5)
        self.assertTrue(all("date" in h for h in holidays))

    @unittest.skip("Network-dependent: run manually to verify real API")
    def test_live_fetch_countries(self):
        countries = api.fetch_countries()
        self.assertGreater(len(countries), 100)


if __name__ == "__main__":
    unittest.main()