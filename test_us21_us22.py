"""
Unit tests for US25 (Unique first names in families) and
US26 (Corresponding entries).

Run with:  python3 -m unittest test_us21_us22.py -v
"""

import unittest

import test_gedcom as gedcom


def makeIndividual(name="NA", birthday="NA", gender="NA", spouseFamilies=(), childFamilies=()):
    individual = gedcom.newIndividual()
    individual["name"] = name
    individual["birthday"] = birthday
    individual["gender"] = gender
    individual["BIRT_LINE"] = 10 if birthday != "NA" else "NA"
    individual["spouse"] = set(spouseFamilies)
    individual["child"] = set(childFamilies)
    individual["FAMS_LINES"] = {familyId: 20 for familyId in spouseFamilies}
    individual["FAMC_LINES"] = {familyId: 21 for familyId in childFamilies}
    return individual


def makeFamily(husbandId="NA", wifeId="NA", children=()):
    family = gedcom.newFamily()
    family["HUSB"] = husbandId
    family["WIFE"] = wifeId
    family["CHIL"] = set(children)
    family["MARR"] = "1995-01-01"
    family["MARR_LINE"] = 50
    family["FAM_LINE"] = 49
    family["HUSB_LINE"] = 51 if husbandId != "NA" else "NA"
    family["WIFE_LINE"] = 52 if wifeId != "NA" else "NA"
    family["CHIL_LINES"] = {childId: 53 for childId in children}
    return family

class TestUS21CorrectGenderForRole(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()
    
    def test_husband_is_female(self):
        individuals = {"H1": makeIndividual(gender="F", spouseFamilies=["F1"]),
                       "W1": makeIndividual(gender="F", spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: FAMILY: US21: 51: F1: Husband (H1) is not male.", gedcom.errors[0])

    def test_wife_is_male(self):
        individuals = {"H1": makeIndividual(gender="M", spouseFamilies=["F1"]),
                       "W1": makeIndividual(gender="M", spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: FAMILY: US21: 52: F1: Wife (W1) is not female.", gedcom.errors[0])

    def test_wife_is_male_husband_is_female(self):
        individuals = {"H1": makeIndividual(gender="F", spouseFamilies=["F1"]),
                       "W1": makeIndividual(gender="M", spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: FAMILY: US21: 51: F1: Husband (H1) is not male.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US21: 52: F1: Wife (W1) is not female.", gedcom.errors)

    def test_husband_missing_gender(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual(gender="F", spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: FAMILY: US21: 51: F1: Husband (H1) is not male.", gedcom.errors[0])

    def test_wife_missing_gender(self):
        individuals = {"H1": makeIndividual(gender="M", spouseFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: FAMILY: US21: 52: F1: Wife (W1) is not female.", gedcom.errors[0])

    def test_wife_and_husband_both_missing_genders(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: FAMILY: US21: 51: F1: Husband (H1) is not male.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US21: 52: F1: Wife (W1) is not female.", gedcom.errors)

    def test_wife_does_not_exist(self):
        # Corresponding entries are handled in US26. No error is returned from US21
        # to avoid redundancies.
        individuals = {"H1": makeIndividual(gender="M", spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 0)

    def test_husband_does_not_exist(self):
        # Corresponding entries are handled in US26. No error is returned from US21
        # to avoid redundancies.
        individuals = {"W1": makeIndividual(gender="F", spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 0)

    def test_neither_spouse_exists(self):
        # Corresponding entries are handled in US26. No error is returned from US21
        # to avoid redundancies.
        individuals = {}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us21_correct_gender_for_role(families, individuals)
        self.assertEqual(len(gedcom.errors), 0)

class TestUS22UniqueIds(unittest.TestCase):
    """
    The standard families and individuals dictionaries (used in all other stories) 
    cannot store multiple individuals' information using the same ID.
    
    Therefore, US22 uses allFamilies and allIndividuals to track records with duplicate IDs instead: 

    allFamilies maps family ID -> array of line numbers for the corresponding family record(s).
    allIndividuals maps individual ID -> array of line numbers for the corresponding individual record(s).
    """

    def setUp(self):
        gedcom.errors.clear()
    
    def test_individual_repeated_once(self):
        allIndividuals = {"I1": [12, 90], "I2": [60]}
        allFamilies = {"F1": [190], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: INDIVIDUAL: US22: 12, 90: I1 is not a unique individual ID.", gedcom.errors[0])

    def test_individual_repeated_twice(self):
        allIndividuals = {"I1": [12, 90, 45], "I2": [60]}
        allFamilies = {"F1": [190], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: INDIVIDUAL: US22: 12, 90, 45: I1 is not a unique individual ID.", gedcom.errors[0])

    def test_two_individuals_repeated_once(self):
        allIndividuals = {"I1": [12, 90], "I2": [60, 1000]}
        allFamilies = {"F1": [190], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: INDIVIDUAL: US22: 12, 90: I1 is not a unique individual ID.", gedcom.errors)
        self.assertIn("ERROR: INDIVIDUAL: US22: 60, 1000: I2 is not a unique individual ID.", gedcom.errors)

    def test_two_individuals_repeated_twice(self):
        allIndividuals = {"I1": [12, 90, 800], "I2": [60, 700, 1000]}
        allFamilies = {"F1": [190], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: INDIVIDUAL: US22: 12, 90, 800: I1 is not a unique individual ID.", gedcom.errors)
        self.assertIn("ERROR: INDIVIDUAL: US22: 60, 700, 1000: I2 is not a unique individual ID.", gedcom.errors)

    def test_family_repeated_once(self):
        allIndividuals = {"I1": [12], "I2": [60]}
        allFamilies = {"F1": [90, 190], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: FAMILY: US22: 90, 190: F1 is not a unique family ID.", gedcom.errors[0])

    def test_family_repeated_twice(self):
        allIndividuals = {"I1": [12], "I2": [60]}
        allFamilies = {"F1": [90, 190, 300], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertEqual("ERROR: FAMILY: US22: 90, 190, 300: F1 is not a unique family ID.", gedcom.errors[0])

    def test_two_families_repeated_once(self):
        allIndividuals = {"I1": [12], "I2": [60]}
        allFamilies = {"F1": [90, 190], "F2": [205, 300]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: FAMILY: US22: 90, 190: F1 is not a unique family ID.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US22: 205, 300: F2 is not a unique family ID.", gedcom.errors)

    def test_two_families_repeated_twice(self):
        allIndividuals = {"I1": [12], "I2": [60]}
        allFamilies = {"F1": [90, 190, 900], "F2": [205, 300, 600]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: FAMILY: US22: 90, 190, 900: F1 is not a unique family ID.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US22: 205, 300, 600: F2 is not a unique family ID.", gedcom.errors)

    def test_one_individual_and_one_family_repeat(self):
        allIndividuals = {"I1": [12, 30], "I2": [60]}
        allFamilies = {"F1": [90, 190], "F2": [205]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("ERROR: INDIVIDUAL: US22: 12, 30: I1 is not a unique individual ID.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US22: 90, 190: F1 is not a unique family ID.", gedcom.errors)

    def test_two_individuals_and_two_families_repeat(self):
        allIndividuals = {"I1": [12, 30], "I2": [60, 70]}
        allFamilies = {"F1": [90, 190], "F2": [205, 300]}
        gedcom.validate_us22_unique_ids(allFamilies, allIndividuals)
        self.assertEqual(len(gedcom.errors), 4)
        self.assertIn("ERROR: INDIVIDUAL: US22: 12, 30: I1 is not a unique individual ID.", gedcom.errors)
        self.assertIn("ERROR: INDIVIDUAL: US22: 60, 70: I2 is not a unique individual ID.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US22: 90, 190: F1 is not a unique family ID.", gedcom.errors)
        self.assertIn("ERROR: FAMILY: US22: 205, 300: F2 is not a unique family ID.", gedcom.errors)

    