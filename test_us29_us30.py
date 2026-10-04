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

    def test_us29_family_test_ged_should_list_existing_deceased_people(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        deceased = gedcom.validate_us29_list_deceased(individuals)

        # I38 and I40 are from the US17 test data
        self.assertEqual(deceased, ["I4", "I8", "I13", "I14", "I16", "I18", "I29", "I30", "I34",
                                    "I38", "I40"])
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

    def test_us30_family_test_ged_should_list_existing_living_married_people(self):
        individuals = {}
        families = {}
        gedcom.parseGedcom("family_test.ged", individuals, families)

        livingMarried = gedcom.validate_us30_list_living_married(families, individuals)

        # I37-I53 are from the US17 / US18 test data. I38 and I40 are deceased,
        # and I50 is divorced (F20), so they are not listed.
        self.assertEqual(livingMarried, ["I1", "I2", "I3", "I6", "I10", "I11", "I21", "I22",
                                         "I37", "I39", "I41", "I42", "I43", "I44", "I45", "I46",
                                         "I47", "I48", "I49", "I51", "I52", "I53", "I60", "I61",
                                         "I62", "I63", "I64", "I65", "I66", "I67", "I68", "I69",
                                         "I70", "I71", "I72", "I73", "I74", "I75", "I76", "I77",
                                         "I78", "I79"])
        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()
