"""
Unit tests for US06 (Divorce before death) and US07 (Less than 150 years old).

Run with:  python3 -m unittest test_us06_us07.py -v
"""

import unittest

import test_gedcom as gedcom


def makeIndividual(birthday="NA", death="NA"):
    individual = gedcom.newIndividual()
    individual["birthday"] = birthday
    individual["BIRT_LINE"] = 10
    if death != "NA":
        individual["death"] = death
        individual["DEAT_LINE"] = 20
        individual["alive"] = "N"
    return individual


def makeFamily(husbandId="I1", wifeId="I2", married="2000-01-01", divorced="NA"):
    family = gedcom.newFamily()
    family["HUSB"] = husbandId
    family["WIFE"] = wifeId
    family["MARR"] = married
    family["DIV"] = divorced
    if divorced != "NA":
        family["DIV_LINE"] = 30
    return family


class TestUS06DivorceBeforeDeath(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_divorce_after_husband_death(self):
        individuals = {"I1": makeIndividual("1960-01-01", "2010-01-01"),
                       "I2": makeIndividual("1962-01-01")}
        families = {"F1": makeFamily(divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US06: 30: F1: Divorced 2012-01-01 after husband's (I1) death on 2010-01-01"
        ])

    def test_divorce_after_wife_death(self):
        individuals = {"I1": makeIndividual("1960-01-01"),
                       "I2": makeIndividual("1962-01-01", "2010-01-01")}
        families = {"F1": makeFamily(divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US06: 30: F1: Divorced 2012-01-01 after wife's (I2) death on 2010-01-01"
        ])

    def test_divorce_after_both_deaths(self):
        individuals = {"I1": makeIndividual("1960-01-01", "2009-01-01"),
                       "I2": makeIndividual("1962-01-01", "2010-01-01")}
        families = {"F1": makeFamily(divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(len(gedcom.errors), 2)

    def test_divorce_before_death_is_valid(self):
        individuals = {"I1": makeIndividual("1960-01-01", "2015-01-01"),
                       "I2": makeIndividual("1962-01-01", "2016-01-01")}
        families = {"F1": makeFamily(divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_divorce_on_day_of_death_is_valid(self):
        individuals = {"I1": makeIndividual("1960-01-01", "2012-01-01"),
                       "I2": makeIndividual("1962-01-01")}
        families = {"F1": makeFamily(divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_no_divorce_is_valid(self):
        individuals = {"I1": makeIndividual("1960-01-01", "2010-01-01"),
                       "I2": makeIndividual("1962-01-01")}
        families = {"F1": makeFamily()}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_living_spouses_are_valid(self):
        individuals = {"I1": makeIndividual("1960-01-01"),
                       "I2": makeIndividual("1962-01-01")}
        families = {"F1": makeFamily(divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_missing_spouse_record_does_not_crash(self):
        individuals = {"I1": makeIndividual("1960-01-01")}
        families = {"F1": makeFamily(wifeId="I99", divorced="2012-01-01")}
        gedcom.validate_us06_divorce_before_death(families, individuals)
        self.assertEqual(gedcom.errors, [])


class TestUS07LessThan150YearsOld(unittest.TestCase):

    TODAY = "2026-09-24"  # fixed date so the tests never change over time

    def setUp(self):
        gedcom.errors.clear()

    def test_dead_older_than_150(self):
        individuals = {"I1": makeIndividual("1800-01-01", "1960-01-01")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US07: 20: I1: More than 150 years old at death - Birth 1800-01-01: Death 1960-01-01"
        ])

    def test_dead_exactly_150_is_error(self):
        individuals = {"I1": makeIndividual("1800-01-01", "1950-01-01")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(len(gedcom.errors), 1)

    def test_dead_one_day_before_150_is_valid(self):
        individuals = {"I1": makeIndividual("1800-01-02", "1950-01-01")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(gedcom.errors, [])

    def test_living_older_than_150(self):
        individuals = {"I1": makeIndividual("1850-01-01")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US07: 10: I1: More than 150 years old - Birth 1850-01-01"
        ])

    def test_living_turns_150_today_is_error(self):
        individuals = {"I1": makeIndividual("1876-09-24")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(len(gedcom.errors), 1)

    def test_living_turns_150_tomorrow_is_valid(self):
        individuals = {"I1": makeIndividual("1876-09-25")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(gedcom.errors, [])

    def test_normal_ages_are_valid(self):
        individuals = {"I1": makeIndividual("1950-01-01"),
                       "I2": makeIndividual("1920-01-01", "2010-01-01")}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(gedcom.errors, [])

    def test_missing_birthday_is_skipped(self):
        individuals = {"I1": makeIndividual()}
        gedcom.validate_us07_less_than_150_years_old(individuals, self.TODAY)
        self.assertEqual(gedcom.errors, [])


class TestFamilyTestGed(unittest.TestCase):
    """Checks that family_test.ged produces the expected US06 / US07 errors."""

    def setUp(self):
        gedcom.errors.clear()
        self.individuals = {}
        self.families = {}
        gedcom.parseGedcom("family_test.ged", self.individuals, self.families)

    def test_us06_errors_in_gedcom(self):
        gedcom.validate_us06_divorce_before_death(self.families, self.individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US06: 166: F7: Divorced 2018-06-01 after husband's (I14) death on 2015-01-01"
        ])

    def test_us07_errors_in_gedcom(self):
        gedcom.validate_us07_less_than_150_years_old(self.individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US07: 177: I16: More than 150 years old at death - Birth 1800-01-01: Death 1960-01-01",
            "ERROR: INDIVIDUAL: US07: 184: I17: More than 150 years old - Birth 1850-01-01"
        ])


if __name__ == "__main__":
    unittest.main()
