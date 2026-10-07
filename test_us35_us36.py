"""
Unit tests for US35: List recent births and US36: List recent deaths.
Run with: python3 -m unittest test_us35_us36.py -v
"""

import unittest
from datetime import date

import test_gedcom as gedcom

# fixed "today" so the tests do not depend on the day they are run
TODAY = "2026-10-03"


def makeIndividual(name="Test /Person/", birthday="NA", death="NA"):
    return {
        "name": name,
        "birthday": birthday,
        "death": death
    }


class TestUS35ListRecentBirths(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us35_person_born_in_last_30_days_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-09-20")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, ["I1"])
        self.assertEqual(gedcom.errors, [])

    def test_us35_person_born_today_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-10-03")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, ["I1"])

    def test_us35_person_born_exactly_30_days_ago_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-09-03")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, ["I1"])

    def test_us35_person_born_31_days_ago_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-09-02")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, [])

    def test_us35_person_born_in_future_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-10-04")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, [])

    def test_us35_missing_birthday_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual()
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, [])

    def test_us35_window_crosses_year_boundary(self):
        individuals = {
            "I1": makeIndividual(birthday="2025-12-20"),
            "I2": makeIndividual(birthday="2025-12-01")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, "2026-01-05")

        self.assertEqual(recentBirths, ["I1"])

    def test_us35_multiple_recent_births_should_be_listed_in_id_order(self):
        individuals = {
            "I10": makeIndividual(birthday="2026-09-25"),
            "I2": makeIndividual(birthday="2026-09-10"),
            "I1": makeIndividual(birthday="1980-01-01")
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertEqual(recentBirths, ["I2", "I10"])

    def test_us35_defaults_to_current_date(self):
        individuals = {
            "I1": makeIndividual(birthday=date.today().isoformat())
        }

        recentBirths = gedcom.validate_us35_list_recent_births(individuals)

        self.assertEqual(recentBirths, ["I1"])

    def test_us35_table_should_show_id_name_and_birthday(self):
        individuals = {
            "I1": makeIndividual("Lily /RecentBirth/", birthday="2026-09-20"),
            "I2": makeIndividual("Old /Person/", birthday="1980-01-01")
        }

        table = gedcom.build_us35_recent_births_table(individuals, TODAY)

        self.assertEqual(table.title, "US35: Recent Births (Last 30 Days)")
        self.assertEqual(table.field_names, ["ID", "Name", "Birthday"])
        self.assertEqual(table.rows, [["I1", "Lily /RecentBirth/", "2026-09-20"]])

    def test_us35_family_test_ged_should_list_recent_births(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        recentBirths = gedcom.validate_us35_list_recent_births(individuals, TODAY)

        self.assertIn("I86", recentBirths)
        self.assertNotIn("I87", recentBirths)
        self.assertEqual(gedcom.errors, [])


class TestUS36ListRecentDeaths(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us36_person_died_in_last_30_days_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death="2026-09-25")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, ["I1"])
        self.assertEqual(gedcom.errors, [])

    def test_us36_person_died_today_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death="2026-10-03")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, ["I1"])

    def test_us36_person_died_exactly_30_days_ago_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death="2026-09-03")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, ["I1"])

    def test_us36_person_died_31_days_ago_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death="2026-09-02")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, [])

    def test_us36_death_in_future_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death="2075-01-01")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, [])

    def test_us36_living_person_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-09-20")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, [])

    def test_us36_window_crosses_leap_day(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death="2024-02-01"),
            "I2": makeIndividual(birthday="1940-05-15", death="2024-01-31")
        }

        # 2024-01-31 to 2024-03-02 is 31 days because of 29 FEB 2024
        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, "2024-03-02")

        self.assertEqual(recentDeaths, ["I1"])

    def test_us36_multiple_recent_deaths_should_be_listed_in_id_order(self):
        individuals = {
            "I10": makeIndividual(birthday="1950-01-01", death="2026-09-30"),
            "I2": makeIndividual(birthday="1960-01-01", death="2026-09-15"),
            "I1": makeIndividual(birthday="1970-01-01", death="2000-01-01")
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertEqual(recentDeaths, ["I2", "I10"])

    def test_us36_defaults_to_current_date(self):
        individuals = {
            "I1": makeIndividual(birthday="1940-05-15", death=date.today().isoformat())
        }

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals)

        self.assertEqual(recentDeaths, ["I1"])

    def test_us36_table_should_show_id_name_and_death_date(self):
        individuals = {
            "I1": makeIndividual("Arthur /RecentDeath/", birthday="1940-05-15", death="2026-09-25"),
            "I2": makeIndividual("Old /Death/", birthday="1940-05-15", death="2000-01-01")
        }

        table = gedcom.build_us36_recent_deaths_table(individuals, TODAY)

        self.assertEqual(table.title, "US36: Recent Deaths (Last 30 Days)")
        self.assertEqual(table.field_names, ["ID", "Name", "Death Date"])
        self.assertEqual(table.rows, [["I1", "Arthur /RecentDeath/", "2026-09-25"]])

    def test_us36_family_test_ged_should_list_recent_deaths(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        recentDeaths = gedcom.validate_us36_list_recent_deaths(individuals, TODAY)

        self.assertIn("I88", recentDeaths)
        self.assertNotIn("I89", recentDeaths)
        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()
