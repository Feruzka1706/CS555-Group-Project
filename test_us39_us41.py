"""
Unit tests for US39: List upcoming anniversaries and US41: Include partial dates.
Run with: python3 -m unittest test_us39_us41.py -v
Requires I162-I169 / F63-F66 (US39) and I170-I172 / F67 (US41) in family_test.ged.
"""

import os
import tempfile
import unittest

import test_gedcom as gedcom

# fixed "today" so the tests do not depend on the day they are run
TODAY = "2026-11-13"


def makeIndividual(name="Test /Person/", birthday="1960-01-01", death="NA"):
    return {
        "name": name,
        "birthday": birthday,
        "death": death
    }


def makeFamily(husbandId="I1", wifeId="I2", married="NA", divorced="NA"):
    return {
        "HUSB": husbandId,
        "WIFE": wifeId,
        "CHIL": set(),
        "MARR": married,
        "DIV": divorced
    }


def makeCouple(husbandDeath="NA", wifeDeath="NA"):
    return {
        "I1": makeIndividual("Arthur /Test/", "1960-03-05", husbandDeath),
        "I2": makeIndividual("Martha /Test/", "1962-07-12", wifeDeath)
    }


class TestUS39ListUpcomingAnniversaries(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us39_living_couple_with_anniversary_in_next_30_days_should_be_listed(self):
        families = {"F1": makeFamily(married="1985-12-01")}  # 18 days away

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, ["F1"])
        self.assertEqual(gedcom.errors, [])

    def test_us39_anniversary_today_should_be_listed(self):
        families = {"F1": makeFamily(married="1985-11-13")}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, ["F1"])

    def test_us39_anniversary_in_exactly_30_days_should_be_listed(self):
        families = {"F1": makeFamily(married="1985-12-13")}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, ["F1"])

    def test_us39_anniversary_in_31_days_should_not_be_listed(self):
        families = {"F1": makeFamily(married="1985-12-14")}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_anniversary_that_already_passed_this_year_should_not_be_listed(self):
        families = {"F1": makeFamily(married="1985-11-12")}  # yesterday, next one is in 364 days

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_anniversary_early_next_year_should_be_listed(self):
        families = {"F1": makeFamily(married="1985-01-05")}  # 16 days after 20 DEC

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), "2026-12-20")

        self.assertEqual(upcoming, ["F1"])

    def test_us39_divorced_couple_should_not_be_listed(self):
        families = {"F1": makeFamily(married="1990-11-25", divorced="2005-03-03")}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_couple_with_deceased_husband_should_not_be_listed(self):
        families = {"F1": makeFamily(married="1970-11-28")}
        individuals = makeCouple(husbandDeath="2020-01-10")

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_couple_with_deceased_wife_should_not_be_listed(self):
        families = {"F1": makeFamily(married="1970-11-28")}
        individuals = makeCouple(wifeDeath="2020-01-10")

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, individuals, TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_family_without_marriage_date_should_not_be_listed(self):
        families = {"F1": makeFamily(married="NA")}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_family_with_missing_spouse_should_not_be_listed(self):
        families = {
            "F1": makeFamily("I1", "NA", married="1985-12-01"),   # no wife
            "F2": makeFamily("I1", "I99", married="1985-12-01")   # wife has no record
        }

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_couple_married_today_should_not_be_listed(self):
        families = {"F1": makeFamily(married=TODAY)}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_couple_married_in_the_future_should_not_be_listed(self):
        families = {"F1": makeFamily(married="2026-12-01")}

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, [])

    def test_us39_29_feb_marriage_should_use_28_feb_in_non_leap_year(self):
        families = {"F1": makeFamily(married="1988-02-29")}

        # 2027 is not a leap year, so the anniversary is 28 FEB 2027
        self.assertEqual(
            gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), "2027-02-01"),
            ["F1"]
        )
        self.assertEqual(
            gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), "2027-03-01"),
            []
        )

    def test_us39_families_should_be_listed_in_id_order(self):
        families = {
            "F10": makeFamily(married="1985-12-01"),
            "F2": makeFamily(married="1990-11-20")
        }

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, makeCouple(), TODAY)

        self.assertEqual(upcoming, ["F2", "F10"])

    def test_us39_table_should_show_couple_marriage_date_and_next_anniversary(self):
        families = {
            "F1": makeFamily(married="1985-12-01"),
            "F2": makeFamily(married="1984-12-14")   # not upcoming
        }

        table = gedcom.build_us39_upcoming_anniversaries_table(families, makeCouple(), TODAY)

        self.assertEqual(table.title, "US39: Upcoming Anniversaries (Next 30 Days)")
        self.assertEqual(
            table.field_names,
            ["Family ID", "Husband ID", "Husband Name", "Wife ID", "Wife Name", "Married", "Next Anniversary"]
        )
        self.assertEqual(table.rows, [
            ["F1", "I1", "Arthur /Test/", "I2", "Martha /Test/", "1985-12-01", "2026-12-01"]
        ])

    def test_us39_family_test_ged_should_list_upcoming_anniversaries(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        upcoming = gedcom.validate_us39_list_upcoming_anniversaries(families, individuals, TODAY)

        self.assertIn("F63", upcoming)     # anniversary in 18 days
        self.assertNotIn("F64", upcoming)  # anniversary in 63 days
        self.assertNotIn("F65", upcoming)  # divorced
        self.assertNotIn("F66", upcoming)  # husband is deceased
        self.assertEqual(gedcom.errors, [])


class TestUS41IncludePartialDates(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us41_full_date_should_be_unchanged(self):
        self.assertEqual(gedcom.parse_us41_partial_date(["15", "MAY", "1990"]), "1990-05-15")
        self.assertEqual(gedcom.parse_us41_partial_date(["5", "MAY", "1990"]), "1990-05-05")
        self.assertEqual(
            gedcom.parse_us41_partial_date(["15", "MAY", "1990"]),
            gedcom.getDate(["15", "MAY", "1990"])
        )

    def test_us41_date_without_day_should_use_first_of_month(self):
        self.assertEqual(gedcom.parse_us41_partial_date(["MAY", "1990"]), "1990-05-01")
        self.assertEqual(gedcom.parse_us41_partial_date(["DEC", "2001"]), "2001-12-01")

    def test_us41_date_with_only_year_should_use_1_jan(self):
        self.assertEqual(gedcom.parse_us41_partial_date(["1990"]), "1990-01-01")

    def test_us41_partial_dates_should_work_with_date_helpers(self):
        birthday = gedcom.parse_us41_partial_date(["1970"])
        married = gedcom.parse_us41_partial_date(["JUN", "1995"])

        self.assertEqual(gedcom.compareDates(birthday, married), -1)
        self.assertEqual(gedcom.getAgeOnDate(birthday, married), 25)

    def test_us41_parse_gedcom_should_accept_partial_dates_for_every_event(self):
        gedcomText = "\n".join([
            "0 I1 INDI",
            "1 NAME Oscar /Partial/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1950",
            "1 DEAT",
            "2 DATE MAR 2010",
            "1 FAMS F1",
            "0 I2 INDI",
            "1 NAME Nina /Partial/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE APR 1952",
            "1 FAMS F1",
            "0 F1 FAM",
            "1 HUSB I1",
            "1 WIFE I2",
            "1 MARR",
            "2 DATE JUN 1975",
            "1 DIV",
            "2 DATE 1990",
            "0 TRLR",
            ""
        ])

        with tempfile.TemporaryDirectory() as tempDir:
            gedcomFile = os.path.join(tempDir, "partial_dates.ged")

            with open(gedcomFile, "w", encoding="utf-8") as outputFile:
                outputFile.write(gedcomText)

            individuals = {}
            families = {}
            gedcom.parseGedcom(gedcomFile, individuals, families)

        self.assertEqual(individuals["I1"]["birthday"], "1950-01-01")
        self.assertEqual(individuals["I1"]["BIRT_LINE"], 5)
        self.assertEqual(individuals["I1"]["death"], "2010-03-01")
        self.assertEqual(individuals["I1"]["DEAT_LINE"], 7)
        self.assertEqual(individuals["I1"]["alive"], "N")
        self.assertEqual(individuals["I1"]["age"], 60)   # US27 can use the partial dates
        self.assertEqual(individuals["I2"]["birthday"], "1952-04-01")
        self.assertEqual(families["F1"]["MARR"], "1975-06-01")
        self.assertEqual(families["F1"]["MARR_LINE"], 19)
        self.assertEqual(families["F1"]["DIV"], "1990-01-01")
        self.assertEqual(families["F1"]["DIV_LINE"], 21)
        self.assertEqual(gedcom.errors, [])

    def test_us41_family_test_ged_should_read_partial_dates(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        self.assertEqual(individuals["I170"]["birthday"], "1970-01-01")  # DATE 1970
        self.assertEqual(individuals["I171"]["birthday"], "1972-04-01")  # DATE APR 1972
        self.assertEqual(families["F67"]["MARR"], "1995-06-01")          # DATE JUN 1995
        self.assertEqual(individuals["I172"]["birthday"], "1920-03-01")  # DATE MAR 1920
        self.assertEqual(individuals["I172"]["death"], "2001-01-01")     # DATE 2001
        self.assertEqual(individuals["I172"]["age"], 80)
        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()
