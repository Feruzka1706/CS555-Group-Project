"""
Unit tests for US05: Marriage before death and US10: Marriage after 14.
Run with: python3 -m unittest test_us05_us10.py -v
"""

import unittest
import test_gedcom as gedcom


def makeIndividual(birthday="NA", death="NA"):
    individual = {
        "birthday": birthday,
        "death": death
    }
    return individual


def makeFamily(husbandId="I1", wifeId="I2", married="2020-01-01", marriageLine=10):
    family = {
        "HUSB": husbandId,
        "WIFE": wifeId,
        "MARR": married,
        "MARR_LINE": marriageLine
    }
    return family


class TestUS05MarriageBeforeDeath(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us05_marriage_after_husband_death_should_create_error(self):
        individuals = {
            "I1": makeIndividual("1980-01-01", "2010-01-01"),
            "I2": makeIndividual("1982-01-01")
        }

        families = {
            "F1": makeFamily(husbandId="I1", wifeId="I2", married="2015-01-01", marriageLine=10)
        }

        gedcom.validate_us05_marriage_before_death(families, individuals)

        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US05: 10: F1: Married 2015-01-01 after husband's (I1) death on 2010-01-01"
        ])

    def test_us05_marriage_after_wife_death_should_create_error(self):
        individuals = {
            "I3": makeIndividual("1970-01-01"),
            "I4": makeIndividual("1975-01-01", "2005-05-01")
        }

        families = {
            "F2": makeFamily(husbandId="I3", wifeId="I4", married="2010-05-01", marriageLine=20)
        }

        gedcom.validate_us05_marriage_before_death(families, individuals)

        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US05: 20: F2: Married 2010-05-01 after wife's (I4) death on 2005-05-01"
        ])

    def test_us05_marriage_after_both_spouses_death_should_create_two_errors(self):
        individuals = {
            "I5": makeIndividual("1960-01-01", "2010-01-01"),
            "I6": makeIndividual("1962-01-01", "2011-01-01")
        }

        families = {
            "F3": makeFamily(husbandId="I5", wifeId="I6", married="2015-01-01", marriageLine=30)
        }

        gedcom.validate_us05_marriage_before_death(families, individuals)

        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US05: 30: F3: Married 2015-01-01 after husband's (I5) death on 2010-01-01",
            "ERROR: FAMILY: US05: 30: F3: Married 2015-01-01 after wife's (I6) death on 2011-01-01"
        ])

    def test_us05_marriage_before_death_should_not_create_error(self):
        individuals = {
            "I7": makeIndividual("1970-01-01", "2015-01-01"),
            "I8": makeIndividual("1972-01-01", "2016-01-01")
        }

        families = {
            "F4": makeFamily(husbandId="I7", wifeId="I8", married="2000-01-01", marriageLine=40)
        }

        gedcom.validate_us05_marriage_before_death(families, individuals)

        self.assertEqual(gedcom.errors, [])

    def test_us05_marriage_on_same_day_as_death_should_not_create_error(self):
        individuals = {
            "I9": makeIndividual("1970-01-01", "2010-01-01"),
            "I10": makeIndividual("1972-01-01")
        }

        families = {
            "F5": makeFamily(husbandId="I9", wifeId="I10", married="2010-01-01", marriageLine=50)
        }

        gedcom.validate_us05_marriage_before_death(families, individuals)

        self.assertEqual(gedcom.errors, [])

    def test_us05_living_spouses_should_not_create_error(self):
        individuals = {
            "I11": makeIndividual("1980-01-01"),
            "I12": makeIndividual("1982-01-01")
        }

        families = {
            "F6": makeFamily(husbandId="I11", wifeId="I12", married="2020-01-01", marriageLine=60)
        }

        gedcom.validate_us05_marriage_before_death(families, individuals)

        self.assertEqual(gedcom.errors, [])


class TestUS10MarriageAfter14(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us10_husband_younger_than_14_should_create_error(self):
        individuals = {
            "I1": makeIndividual("2010-01-01"),
            "I2": makeIndividual("1990-01-01")
        }

        families = {
            "F1": makeFamily(husbandId="I1", wifeId="I2", marriageLine=10)
        }

        gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US10: 10: F1: Husband's (I1) age 10 is less than 14 at marriage on 2020-01-01"
        ])

    def test_us10_wife_younger_than_14_should_create_error(self):
        individuals = {
            "I3": makeIndividual("1990-01-01"),
            "I4": makeIndividual("2011-01-01")
        }

        families = {
            "F2": makeFamily(husbandId="I3", wifeId="I4", marriageLine=20)
        }

        gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US10: 20: F2: Wife's (I4) age 9 is less than 14 at marriage on 2020-01-01"
        ])

    def test_us10_both_spouses_younger_than_14_should_create_two_errors(self):
        individuals = {
            "I5": makeIndividual("2010-01-01"),
            "I6": makeIndividual("2011-01-01")
        }

        families = {
            "F3": makeFamily(husbandId="I5", wifeId="I6", marriageLine=30)
        }

        gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US10: 30: F3: Husband's (I5) age 10 is less than 14 at marriage on 2020-01-01",
            "ERROR: FAMILY: US10: 30: F3: Wife's (I6) age 9 is less than 14 at marriage on 2020-01-01"
        ])

    def test_us10_husband_exactly_14_should_not_create_error(self):
        individuals = {
            "I7": makeIndividual("2006-01-01"),
            "I8": makeIndividual("1990-01-01")
        }

        families = {
            "F4": makeFamily(husbandId="I7", wifeId="I8", marriageLine=40)
        }

        gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(gedcom.errors, [])

    def test_us10_wife_exactly_14_should_not_create_error(self):
        individuals = {
            "I9": makeIndividual("1990-01-01"),
            "I10": makeIndividual("2006-01-01")
        }

        families = {
            "F5": makeFamily(husbandId="I9", wifeId="I10", marriageLine=50)
        }

        gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(gedcom.errors, [])

    def test_us10_both_spouses_older_than_14_should_not_create_error(self):
        individuals = {
            "I11": makeIndividual("1990-01-01"),
            "I12": makeIndividual("1992-01-01")
        }

        families = {
            "F6": makeFamily(husbandId="I11", wifeId="I12", marriageLine=60)
        }

        gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()