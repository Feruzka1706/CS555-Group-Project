"""
Unit tests for US01 (Dates before current date) and US02 (Birth before marriage).

Run with:  python3 -m unittest test_us01_us02.py -v
"""

import unittest
import test_gedcom as gedcom

def makeIndividual(birthday="NA", death="NA", spouse="NA"):
    individual = gedcom.newIndividual()
    individual["birthday"] = birthday
    individual["BIRT_LINE"] = 10
    if death != "NA":
        individual["death"] = death
        individual["DEAT_LINE"] = 20
        individual["alive"] = "N"
    if spouse != "NA":
        individual["spouse"] = {spouse}
    else:
        individual["spouse"] = set()
    return individual


def makeFamily(husbandId="I1", wifeId="I2", married="2000-01-01", divorced="NA"):
    family = gedcom.newFamily()
    family["HUSB"] = husbandId
    family["WIFE"] = wifeId
    family["MARR"] = married
    family["DIV"] = divorced
    family["MARR_LINE"] = 40
    if divorced != "NA":
        family["DIV_LINE"] = 30
    return family

class TestUS01DatesBeforeCurrentDate(unittest.TestCase):
        
    def setUp(self):
        gedcom.errors.clear()

    def test_birth_after_current_date(self):
        individuals = {"I1": makeIndividual("2045-01-01")}
        families = {}
        gedcom.validate_us01_dates_before_current_date(families, individuals)
        self.assertEqual(gedcom.errors, [
            'ERROR: INDIVIDUAL: US01: 10: I1: Birthday 2045-01-01 occurs in the future'
        ])

    def test_death_after_current_date(self):
        individuals = {"I1": makeIndividual("2002-01-01", "2040-02-02")}
        families = {}
        gedcom.validate_us01_dates_before_current_date(families, individuals)
        self.assertEqual(gedcom.errors, [
            'ERROR: INDIVIDUAL: US01: 20: I1: Death 2040-02-02 occurs in the future'
        ])

    def test_marriage_after_current_date(self):
        individuals = {
            "I1": makeIndividual("1998-01-01"),
            "I2": makeIndividual("1997-01-01")
        }
        families = {
            "F1": makeFamily("I1", "I2", "2030-08-08")
        }
        gedcom.validate_us01_dates_before_current_date(families, individuals)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US01: 40: F1: Marriage date 2030-08-08 occurs in the future'
        ])

    def test_divorce_after_current_date(self):
        individuals = {
            "I1": makeIndividual("1998-01-01"),
            "I2": makeIndividual("1997-01-01")
        }
        families = {
            "F1": makeFamily("I1", "I2", "2024-08-08", "2030-07-08")
        }
        gedcom.validate_us01_dates_before_current_date(families, individuals)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US01: 30: F1: Divorce date 2030-07-08 occurs in the future'
        ])

    def test_all_dates_before_current_date(self):
        individuals = {
            "I1": makeIndividual("1990-01-01"),
            "I2": makeIndividual("1993-01-01")
        }
        families = {
            "F1": makeFamily("I1", "I2", "2021-08-08", "2024-07-08")
        }
        gedcom.validate_us01_dates_before_current_date(families, individuals)
        self.assertEqual(gedcom.errors, [])    

class TestUS02BirthBeforeMarriage(unittest.TestCase):
        
    def setUp(self):
        gedcom.errors.clear()

    def test_one_spouse_birth_after_marriage(self):
        individuals = {
            "I1": makeIndividual(birthday="2010-01-01", spouse="F1"),
            "I2": makeIndividual(birthday="1993-01-01", spouse="F1")
        }
        families = {
            "F1": makeFamily("I1", "I2", "2008-08-08")
        }
        gedcom.validate_us02_birth_before_marriage(families, individuals)
        self.assertEqual(gedcom.errors, [
            'ERROR: INDIVIDUAL: US02: 10: I1: Birth date 2010-01-01 occurs on or after marriage date 2008-08-08'
        ])

    def test_both_spouses_birth_after_marriage(self):
        individuals = {
            "I1": makeIndividual(birthday="2010-01-01", spouse="F1"),
            "I2": makeIndividual(birthday="2011-01-01", spouse="F1")
        }
        families = {
            "F1": makeFamily("I1", "I2", "2008-08-08")
        }
        gedcom.validate_us02_birth_before_marriage(families, individuals)
        self.assertEqual(gedcom.errors, [
            'ERROR: INDIVIDUAL: US02: 10: I1: Birth date 2010-01-01 occurs on or after marriage date 2008-08-08',
            'ERROR: INDIVIDUAL: US02: 10: I2: Birth date 2011-01-01 occurs on or after marriage date 2008-08-08'
        ])

    def test_both_spouses_birth_before_marriage(self):
        individuals = {
            "I1": makeIndividual(birthday="1990-01-01", spouse="F1"),
            "I2": makeIndividual(birthday="1991-01-20", spouse="F1")
        }
        families = {
            "F1": makeFamily("I1", "I2", "2008-08-08")
        }
        gedcom.validate_us02_birth_before_marriage(families, individuals)
        self.assertEqual(gedcom.errors, [])

if __name__ == "__main__":
    unittest.main()