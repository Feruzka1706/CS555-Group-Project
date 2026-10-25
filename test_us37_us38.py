"""
Unit tests for US37: List recent survivors and US38: List upcoming birthdays.
Run with: python3 -m unittest test_us37_us38.py -v
"""

import unittest
from datetime import date, timedelta

import test_gedcom as gedcom

# fixed "today" so the tests do not depend on the day they are run
TODAY = "2026-10-25"


def makeIndividual(name="Test /Person/", birthday="NA", death="NA"):
    return {
        "name": name,
        "birthday": birthday,
        "death": death
    }


def makeFamily(husbandId="NA", wifeId="NA", children=(), divorced="NA"):
    return {
        "HUSB": husbandId,
        "WIFE": wifeId,
        "CHIL": set(children),
        "MARR": "1970-01-01",
        "DIV": divorced
    }


class TestUS37ListRecentSurvivors(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us37_living_spouse_of_recent_death_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I2": makeIndividual(birthday="1952-01-01")
        }
        families = {"F1": makeFamily("I1", "I2")}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [("I1", "I2", "Spouse")])
        self.assertEqual(gedcom.errors, [])

    def test_us37_living_children_and_grandchildren_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I3": makeIndividual(birthday="1975-01-01"),
            "I4": makeIndividual(birthday="2000-01-01")
        }
        families = {
            "F1": makeFamily("I1", "NA", ["I3"]),
            "F2": makeFamily("I3", "NA", ["I4"])
        }

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [("I1", "I3", "Descendant"), ("I1", "I4", "Descendant")])

    def test_us37_deceased_spouse_and_descendants_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I2": makeIndividual(birthday="1952-01-01", death="2015-01-01"),
            "I3": makeIndividual(birthday="1975-01-01", death="2020-01-01")
        }
        families = {"F1": makeFamily("I1", "I2", ["I3"])}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [])

    def test_us37_divorced_spouse_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I2": makeIndividual(birthday="1952-01-01"),
            "I3": makeIndividual(birthday="1975-01-01")
        }
        families = {"F1": makeFamily("I1", "I2", ["I3"], divorced="1990-01-01")}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        # the ex-wife is not a survivor, but their child still is
        self.assertEqual(survivors, [("I1", "I3", "Descendant")])

    def test_us37_spouse_in_law_is_not_a_descendant(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I3": makeIndividual(birthday="1975-01-01"),
            "I5": makeIndividual(birthday="1976-01-01")
        }
        families = {
            "F1": makeFamily("I1", "NA", ["I3"]),
            "F2": makeFamily("I3", "I5")
        }

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [("I1", "I3", "Descendant")])

    def test_us37_death_exactly_30_days_ago_should_list_survivors(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-09-25"),
            "I2": makeIndividual(birthday="1952-01-01")
        }
        families = {"F1": makeFamily("I1", "I2")}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [("I1", "I2", "Spouse")])

    def test_us37_death_31_days_ago_should_not_list_survivors(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-09-24"),
            "I2": makeIndividual(birthday="1952-01-01"),
            "I3": makeIndividual(birthday="1975-01-01")
        }
        families = {"F1": makeFamily("I1", "I2", ["I3"])}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [])

    def test_us37_recent_death_with_no_family_lists_nobody(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15")
        }

        survivors = gedcom.validate_us37_list_recent_survivors({}, individuals, TODAY)

        self.assertEqual(survivors, [])

    def test_us37_missing_individual_records_are_skipped(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15")
        }
        families = {"F1": makeFamily("I1", "I99", ["I98"])}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [])

    def test_us37_survivor_is_listed_once_per_deceased_person(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I2": makeIndividual(birthday="1952-01-01")
        }
        # the same couple recorded in two families
        families = {
            "F1": makeFamily("I1", "I2"),
            "F2": makeFamily("I1", "I2")
        }

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [("I1", "I2", "Spouse")])

    def test_us37_two_recent_deaths_share_survivors(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death="2026-10-15"),
            "I2": makeIndividual(birthday="1952-01-01", death="2026-10-20"),
            "I3": makeIndividual(birthday="1975-01-01")
        }
        families = {"F1": makeFamily("I1", "I2", ["I3"])}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)

        self.assertEqual(survivors, [("I1", "I3", "Descendant"), ("I2", "I3", "Descendant")])

    def test_us37_defaults_to_current_date(self):
        individuals = {
            "I1": makeIndividual(birthday="1950-01-01", death=date.today().isoformat()),
            "I2": makeIndividual(birthday="1952-01-01")
        }
        families = {"F1": makeFamily("I1", "I2")}

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals)

        self.assertEqual(survivors, [("I1", "I2", "Spouse")])

    def test_us37_table_should_show_deceased_and_survivor(self):
        individuals = {
            "I1": makeIndividual("Henry /Test/", birthday="1950-01-01", death="2026-10-15"),
            "I2": makeIndividual("Grace /Test/", birthday="1952-01-01")
        }
        families = {"F1": makeFamily("I1", "I2")}

        table = gedcom.build_us37_recent_survivors_table(families, individuals, TODAY)

        self.assertEqual(table.title, "US37: Recent Survivors (Deaths in Last 30 Days)")
        self.assertEqual(
            table.field_names,
            ["Deceased ID", "Deceased Name", "Death Date", "Survivor ID", "Survivor Name", "Relationship"]
        )
        self.assertEqual(
            table.rows,
            [["I1", "Henry /Test/", "2026-10-15", "I2", "Grace /Test/", "Spouse"]]
        )

    def test_us37_family_test_ged_should_list_recent_survivors(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        survivors = gedcom.validate_us37_list_recent_survivors(families, individuals, TODAY)
        henrySurvivors = [s for s in survivors if s[0] == "I135"]

        self.assertEqual(henrySurvivors, [
            ("I135", "I136", "Spouse"),
            ("I135", "I137", "Descendant"),
            ("I135", "I140", "Descendant")
        ])
        survivorIds = [survivorId for _, survivorId, _ in survivors]
        self.assertNotIn("I138", survivorIds)  # deceased daughter
        self.assertNotIn("I139", survivorIds)  # daughter-in-law
        self.assertNotIn("I142", survivorIds)  # wife of a death 31 days ago
        self.assertEqual(gedcom.errors, [])


class TestUS38ListUpcomingBirthdays(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us38_birthday_in_next_30_days_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-11-10")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, ["I1"])
        self.assertEqual(gedcom.errors, [])

    def test_us38_birthday_today_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-10-25")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, ["I1"])

    def test_us38_birthday_exactly_30_days_away_should_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-11-24")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, ["I1"])

    def test_us38_birthday_31_days_away_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-11-25")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us38_birthday_that_already_passed_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-10-24")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us38_deceased_person_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="1930-11-01", death="2010-05-05")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us38_missing_birthday_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual()
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us38_born_today_or_in_future_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual(birthday="2026-10-25"),
            "I2": makeIndividual(birthday="2026-11-01")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us38_window_crosses_year_boundary(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-01-10"),
            "I2": makeIndividual(birthday="1990-02-10")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, "2026-12-20")

        self.assertEqual(upcoming, ["I1"])

    def test_us38_leap_day_birthday_in_non_leap_year(self):
        individuals = {
            "I1": makeIndividual(birthday="2000-02-29")
        }

        # 2027 is not a leap year, so the birthday is celebrated on 28 FEB
        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, "2027-02-01")

        self.assertEqual(upcoming, ["I1"])
        self.assertEqual(gedcom.getNextBirthday("2000-02-29", "2027-02-01"), "2027-02-28")
        self.assertEqual(gedcom.getNextBirthday("2000-02-29", "2028-02-01"), "2028-02-29")

    def test_us38_multiple_upcoming_birthdays_should_be_listed_in_id_order(self):
        individuals = {
            "I10": makeIndividual(birthday="1985-11-01"),
            "I2": makeIndividual(birthday="1995-11-20"),
            "I1": makeIndividual(birthday="1980-06-01")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertEqual(upcoming, ["I2", "I10"])

    def test_us38_defaults_to_current_date(self):
        nextWeek = date.today() + timedelta(days=7)
        individuals = {
            "I1": makeIndividual(birthday=f"2000-{nextWeek.month:02d}-{nextWeek.day:02d}")
        }

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals)

        self.assertEqual(upcoming, ["I1"])

    def test_us38_table_should_show_id_name_birthday_and_next_birthday(self):
        individuals = {
            "I1": makeIndividual("Sophie /Test/", birthday="2000-11-10"),
            "I2": makeIndividual("Mason /Test/", birthday="2001-06-01")
        }

        table = gedcom.build_us38_upcoming_birthdays_table(individuals, TODAY)

        self.assertEqual(table.title, "US38: Upcoming Birthdays (Next 30 Days)")
        self.assertEqual(table.field_names, ["ID", "Name", "Birthday", "Next Birthday"])
        self.assertEqual(table.rows, [["I1", "Sophie /Test/", "2000-11-10", "2026-11-10"]])

    def test_us38_family_test_ged_should_list_upcoming_birthdays(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        upcoming = gedcom.validate_us38_list_upcoming_birthdays(individuals, TODAY)

        self.assertIn("I143", upcoming)     # birthday in 16 days
        self.assertNotIn("I144", upcoming)  # birthday in 31 days
        self.assertNotIn("I145", upcoming)  # deceased
        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()
