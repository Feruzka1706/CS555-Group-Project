"""
Unit tests for US29: List deceased and US30: List living married.
Run with: python3 -m unittest test_us29_us30.py -v
"""

import unittest
import test_gedcom as gedcom


def makeIndividual(birthday="NA", death="NA", spouseFamilies=None):
    if spouseFamilies is None:
        spouseFamilies = set()

    return {
        "birthday": birthday,
        "death": death,
        "spouse": spouseFamilies
    }


def makeFamily(husbandId="I1", wifeId="I2", married="2020-01-01", divorced="NA"):
    return {
        "HUSB": husbandId,
        "WIFE": wifeId,
        "MARR": married,
        "DIV": divorced
    }


class TestUS29ListDeceased(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us29_single_deceased_person_should_be_listed(self):
        individuals = {
            "I1": makeIndividual("1950-01-01", "2020-01-01"),
            "I2": makeIndividual("1980-01-01")
        }

        deceased = gedcom.validate_us29_list_deceased(individuals)

        self.assertEqual(deceased, ["I1"])
        self.assertEqual(gedcom.errors, [])

    def test_us29_multiple_deceased_people_should_be_listed_in_id_order(self):
        individuals = {
            "I10": makeIndividual("1950-01-01", "2020-01-01"),
            "I2": makeIndividual("1960-01-01", "2021-01-01"),
            "I1": makeIndividual("1980-01-01")
        }

        deceased = gedcom.validate_us29_list_deceased(individuals)

        self.assertEqual(deceased, ["I2", "I10"])
        self.assertEqual(gedcom.errors, [])

    def test_us29_living_person_should_not_be_listed(self):
        individuals = {
            "I1": makeIndividual("1980-01-01")
        }

        deceased = gedcom.validate_us29_list_deceased(individuals)

        self.assertEqual(deceased, [])
        self.assertEqual(gedcom.errors, [])

    def test_us29_family_test_ged_should_include_known_deceased_people(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        deceased = gedcom.validate_us29_list_deceased(individuals)

        # Check known deceased people from existing GEDCOM test data.
        self.assertIn("I4", deceased)
        self.assertIn("I8", deceased)
        self.assertIn("I13", deceased)
        self.assertIn("I14", deceased)
        self.assertIn("I16", deceased)
        self.assertIn("I18", deceased)
        self.assertIn("I29", deceased)
        self.assertIn("I30", deceased)
        self.assertIn("I34", deceased)

        # Check known living people are not listed as deceased.
        self.assertNotIn("I1", deceased)
        self.assertNotIn("I2", deceased)
        self.assertNotIn("I3", deceased)
        self.assertNotIn("I6", deceased)
        self.assertNotIn("I10", deceased)
        self.assertNotIn("I11", deceased)
        self.assertNotIn("I21", deceased)
        self.assertNotIn("I22", deceased)

        self.assertEqual(gedcom.errors, [])


class TestUS30ListLivingMarried(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_us30_living_married_couple_should_be_listed(self):
        individuals = {
            "I1": makeIndividual("1980-01-01", spouseFamilies={"F1"}),
            "I2": makeIndividual("1982-01-01", spouseFamilies={"F1"})
        }
        families = {
            "F1": makeFamily(husbandId="I1", wifeId="I2", married="2010-01-01")
        }

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        self.assertEqual(livingMarried, ["I1", "I2"])
        self.assertEqual(gedcom.errors, [])

    def test_us30_divorced_couple_should_not_be_listed(self):
        individuals = {
            "I3": makeIndividual("1980-01-01", spouseFamilies={"F2"}),
            "I4": makeIndividual("1982-01-01", spouseFamilies={"F2"})
        }
        families = {
            "F2": makeFamily(husbandId="I3", wifeId="I4", married="2010-01-01", divorced="2020-01-01")
        }

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        self.assertEqual(livingMarried, [])
        self.assertEqual(gedcom.errors, [])

    def test_us30_widowed_person_should_not_be_listed(self):
        individuals = {
            "I5": makeIndividual("1980-01-01", death="2020-01-01", spouseFamilies={"F3"}),
            "I6": makeIndividual("1982-01-01", spouseFamilies={"F3"})
        }
        families = {
            "F3": makeFamily(husbandId="I5", wifeId="I6", married="2010-01-01")
        }

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        self.assertEqual(livingMarried, [])
        self.assertEqual(gedcom.errors, [])

    def test_us30_unmarried_living_person_should_not_be_listed(self):
        individuals = {
            "I7": makeIndividual("1990-01-01")
        }
        families = {}

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        self.assertEqual(livingMarried, [])
        self.assertEqual(gedcom.errors, [])

    def test_us30_missing_spouse_record_should_not_crash(self):
        individuals = {
            "I8": makeIndividual("1990-01-01", spouseFamilies={"F4"})
        }
        families = {
            "F4": makeFamily(husbandId="I8", wifeId="I99", married="2010-01-01")
        }

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        self.assertEqual(livingMarried, [])
        self.assertEqual(gedcom.errors, [])

    def test_us30_family_test_ged_should_include_known_living_married_people(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        # Check known living married people from existing GEDCOM test data.
        self.assertIn("I1", livingMarried)
        self.assertIn("I2", livingMarried)
        self.assertIn("I3", livingMarried)
        self.assertIn("I6", livingMarried)
        self.assertIn("I10", livingMarried)
        self.assertIn("I11", livingMarried)
        self.assertIn("I21", livingMarried)
        self.assertIn("I22", livingMarried)

        # Check known people who should not be listed.
        # I4 is deceased.
        self.assertNotIn("I4", livingMarried)

        # I8 is deceased.
        self.assertNotIn("I8", livingMarried)

        # I13 is deceased.
        self.assertNotIn("I13", livingMarried)

        # I14 is deceased.
        self.assertNotIn("I14", livingMarried)

        # I15 is divorced in F7.
        self.assertNotIn("I15", livingMarried)

        # I29 and I30 are deceased.
        self.assertNotIn("I29", livingMarried)
        self.assertNotIn("I30", livingMarried)

        # I35 and I36 are divorced in F12.
        self.assertNotIn("I35", livingMarried)
        self.assertNotIn("I36", livingMarried)

        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()