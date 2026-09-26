"""
Unit tests for US10: Marriage after 14.

The following 6 tests are implemented:

1. Husband is younger than 14 -> error
2. Wife is younger than 14 -> error
3. Both spouses are younger than 14 -> two errors
4. Husband is exactly 14 on marriage date -> no error
5. Wife is exactly 14 on marriage date -> no error
6. Both spouses are older than 14 -> no error

Run with: python3 -m unittest test_us10.py -v
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