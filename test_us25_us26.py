"""
Unit tests for US25 (Unique first names in families) and
US26 (Corresponding entries).

Run with:  python3 -m unittest test_us25_us26.py -v
"""

import unittest

import test_gedcom as gedcom


def makeIndividual(name="NA", birthday="NA", spouseFamilies=(), childFamilies=()):
    individual = gedcom.newIndividual()
    individual["name"] = name
    individual["birthday"] = birthday
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


class TestGetFirstName(unittest.TestCase):

    def test_first_name_from_gedcom_name(self):
        self.assertEqual(gedcom.getFirstName("Emma /Johnson/"), "emma")

    def test_only_first_given_name_is_used(self):
        self.assertEqual(gedcom.getFirstName("Ava Marie /Twin/"), "ava")

    def test_missing_name(self):
        self.assertEqual(gedcom.getFirstName("NA"), "NA")
        self.assertEqual(gedcom.getFirstName("/Smith/"), "NA")


class TestUS25UniqueFirstNamesInFamilies(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def check(self, children):
        """Run US25 on one family F1 whose children are given as {id: (name, birthday)}."""
        individuals = {childId: makeIndividual(name, birthday)
                       for childId, (name, birthday) in children.items()}
        families = {"F1": makeFamily("H1", "W1", children.keys())}
        gedcom.validate_us25_unique_first_names_in_families(families, individuals)

    def test_same_first_name_and_birth_date_is_error(self):
        self.check({"I1": ("Ava /Twin/", "2000-01-01"),
                    "I2": ("Ava /Twin/", "2000-01-01")})
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US25: 10: F1: Children I1 and I2 have the same first name "
            "(Ava) and birth date (2000-01-01)"
        ])

    def test_twins_with_different_names_are_valid(self):
        self.check({"I1": ("Ava /Twin/", "2000-01-01"),
                    "I2": ("Mia /Twin/", "2000-01-01")})
        self.assertEqual(gedcom.errors, [])

    def test_same_name_different_birth_date_is_valid(self):
        self.check({"I1": ("Ava /Twin/", "2000-01-01"),
                    "I2": ("Ava /Twin/", "2003-05-05")})
        self.assertEqual(gedcom.errors, [])

    def test_middle_name_and_case_do_not_matter(self):
        self.check({"I1": ("Ava /Twin/", "2000-01-01"),
                    "I2": ("AVA Marie /Twin/", "2000-01-01")})
        self.assertEqual(len(gedcom.errors), 1)

    def test_three_matching_children_report_two_errors(self):
        self.check({"I1": ("Ava /Twin/", "2000-01-01"),
                    "I2": ("Ava /Twin/", "2000-01-01"),
                    "I10": ("Ava /Twin/", "2000-01-01")})
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("Children I1 and I2", gedcom.errors[0])
        self.assertIn("Children I1 and I10", gedcom.errors[1])

    def test_same_name_in_different_families_is_valid(self):
        individuals = {"I1": makeIndividual("Ava /A/", "2000-01-01"),
                       "I2": makeIndividual("Ava /B/", "2000-01-01")}
        families = {"F1": makeFamily("H1", "W1", ["I1"]),
                    "F2": makeFamily("H2", "W2", ["I2"])}
        gedcom.validate_us25_unique_first_names_in_families(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_missing_name_or_birthday_is_skipped(self):
        self.check({"I1": ("Ava /Twin/", "NA"),
                    "I2": ("Ava /Twin/", "NA"),
                    "I3": ("NA", "2000-01-01"),
                    "I4": ("NA", "2000-01-01")})
        self.assertEqual(gedcom.errors, [])

    def test_missing_child_record_does_not_crash(self):
        families = {"F1": makeFamily("H1", "W1", ["I99"])}
        gedcom.validate_us25_unique_first_names_in_families(families, {})
        self.assertEqual(gedcom.errors, [])


class TestUS26CorrespondingEntries(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_consistent_records_are_valid(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"]),
                       "C1": makeIndividual(childFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1", ["C1"])}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_fams_not_matched_by_family(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"]),
                       "X1": makeIndividual(spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US26: 20: X1: Spouse in family F1 (FAMS), "
            "but F1 does not list X1 as husband or wife"
        ])

    def test_famc_not_matched_by_family(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"]),
                       "C1": makeIndividual(childFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US26: 21: C1: Child in family F1 (FAMC), "
            "but F1 does not list C1 as a child"
        ])

    def test_reference_to_missing_family(self):
        individuals = {"I1": makeIndividual(spouseFamilies=["F9"], childFamilies=["F8"])}
        gedcom.validate_us26_corresponding_entries({}, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US26: 20: I1: Spouse in family F9 (FAMS), but family F9 does not exist",
            "ERROR: INDIVIDUAL: US26: 21: I1: Child in family F8 (FAMC), but family F8 does not exist"
        ])

    def test_husband_without_fams(self):
        individuals = {"H1": makeIndividual(),
                       "W1": makeIndividual(spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US26: 51: F1: Lists H1 as husband, "
            "but H1 does not list F1 as a spouse family (FAMS)"
        ])

    def test_wife_without_fams(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual()}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US26: 52: F1: Lists W1 as wife, "
            "but W1 does not list F1 as a spouse family (FAMS)"
        ])

    def test_child_without_famc(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"]),
                       "C1": makeIndividual()}
        families = {"F1": makeFamily("H1", "W1", ["C1"])}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US26: 53: F1: Lists C1 as a child, "
            "but C1 does not list F1 as a child family (FAMC)"
        ])

    def test_family_references_missing_individuals(self):
        families = {"F1": makeFamily("H9", "W9", ["C9"])}
        gedcom.validate_us26_corresponding_entries(families, {})
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US26: 51: F1: Lists H9 as husband, but individual H9 does not exist",
            "ERROR: FAMILY: US26: 52: F1: Lists W9 as wife, but individual W9 does not exist",
            "ERROR: FAMILY: US26: 53: F1: Lists C9 as a child, but individual C9 does not exist"
        ])

    def test_family_without_wife_is_valid(self):
        individuals = {"H1": makeIndividual(spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1")}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_spouse_listed_as_child_instead_is_error(self):
        # H1 lists F1 as FAMC, but F1 has H1 as husband: wrong role on both sides
        individuals = {"H1": makeIndividual(childFamilies=["F1"]),
                       "W1": makeIndividual(spouseFamilies=["F1"])}
        families = {"F1": makeFamily("H1", "W1")}
        gedcom.validate_us26_corresponding_entries(families, individuals)
        self.assertEqual(len(gedcom.errors), 2)
        self.assertIn("INDIVIDUAL: US26: 21: H1: Child in family F1", gedcom.errors[0])
        self.assertIn("FAMILY: US26: 51: F1: Lists H1 as husband", gedcom.errors[1])


class TestParserRecordsLineNumbers(unittest.TestCase):
    """US26 needs the line of every FAMS / FAMC / HUSB / WIFE / CHIL tag."""

    def setUp(self):
        self.individuals = {}
        self.families = {}
        gedcom.parseGedcom("family_test.ged", self.individuals, self.families)

    def test_individual_lines(self):
        self.assertEqual(self.individuals["I3"]["FAMC_LINES"], {"F1": 26})
        self.assertEqual(self.individuals["I3"]["FAMS_LINES"], {"F2": 27, "F3": 28})

    def test_family_lines(self):
        family = self.families["F1"]
        self.assertEqual(family["HUSB_LINE"], 63)
        self.assertEqual(family["WIFE_LINE"], 64)
        self.assertEqual(family["CHIL_LINES"], {"I3": 65})


class TestFamilyTestGed(unittest.TestCase):
    """Checks that family_test.ged produces exactly the expected US25 / US26 errors."""

    def setUp(self):
        gedcom.errors.clear()
        self.individuals = {}
        self.families = {}
        gedcom.parseGedcom("family_test.ged", self.individuals, self.families)

    def test_us25_errors_in_gedcom(self):
        gedcom.validate_us25_unique_first_names_in_families(self.families, self.individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US25: 1014: F46: Children I98 and I99 have the same first name "
            "(Ava) and birth date (2000-01-01)"
        ])

    def test_us26_errors_in_gedcom(self):
        gedcom.validate_us26_corresponding_entries(self.families, self.individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US26: 1079: I106: Child in family F47 (FAMC), but F47 does not list I106 as a child",
            "ERROR: INDIVIDUAL: US26: 1087: I107: Spouse in family F47 (FAMS), but F47 does not list I107 as husband or wife",
            "ERROR: INDIVIDUAL: US26: 1103: I108: Child in family F48 (FAMC), but family F48 does not exist",
            "ERROR: FAMILY: US26: 1093: F47: Lists I103 as wife, but I103 does not list F47 as a spouse family (FAMS)",
            "ERROR: FAMILY: US26: 1095: F47: Lists I105 as a child, but I105 does not list F47 as a child family (FAMC)"
        ])


if __name__ == "__main__":
    unittest.main()
