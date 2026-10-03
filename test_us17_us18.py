"""
Unit tests for US17 (No marriages to descendants) and
US18 (Siblings should not marry).

Run with:  python3 -m unittest test_us17_us18.py -v
"""

import unittest

import test_gedcom as gedcom


def makeFamily(husbandId="NA", wifeId="NA", children=(), marriageLine=50):
    family = gedcom.newFamily()
    family["HUSB"] = husbandId
    family["WIFE"] = wifeId
    family["CHIL"] = set(children)
    family["MARR"] = "2000-01-01"
    family["MARR_LINE"] = marriageLine
    family["FAM_LINE"] = marriageLine - 1
    return family


class TestUS17NoMarriagesToDescendants(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_father_marries_daughter(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I1", "I3", marriageLine=80),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US17: 80: F2: Husband (I1) is married to his descendant, wife (I3)"
        ])

    def test_mother_marries_son(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I3", "I2", marriageLine=80),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US17: 80: F2: Wife (I2) is married to her descendant, husband (I3)"
        ])

    def test_grandmother_marries_grandson(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I3", "I4", ["I5"]),
            "F3": makeFamily("I5", "I2"),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertIn("F3: Wife (I2) is married to her descendant, husband (I5)", gedcom.errors[0])

    def test_great_grandfather_marries_great_granddaughter(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I3", "I4", ["I5"]),
            "F3": makeFamily("I5", "I6", ["I7"]),
            "F4": makeFamily("I1", "I7"),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertIn("F4: Husband (I1) is married to his descendant, wife (I7)", gedcom.errors[0])

    def test_unrelated_spouses_are_valid(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I3", "I4"),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(gedcom.errors, [])

    def test_remarriage_to_unrelated_person_is_valid(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I1", "I4", ["I5"]),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(gedcom.errors, [])

    def test_missing_spouse_is_skipped(self):
        families = {"F1": makeFamily("I1", "NA", ["I2"])}
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertEqual(gedcom.errors, [])

    def test_no_marriage_date_uses_family_line(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I1", "I3", marriageLine=80),
        }
        families["F2"]["MARR_LINE"] = "NA"
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertIn("US17: 79: F2:", gedcom.errors[0])

    def test_cycle_in_data_does_not_loop_forever(self):
        # I1 is listed as a child of their own child: bad data, but must not hang
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I3", "I4", ["I1"]),
        }
        gedcom.validate_us17_no_marriages_to_descendants(families)
        self.assertTrue(len(gedcom.errors) >= 1)


class TestUS18SiblingsShouldNotMarry(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_brother_and_sister_marry(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3", "I4"]),
            "F2": makeFamily("I3", "I4", marriageLine=80),
        }
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US18: 80: F2: Husband (I3) and wife (I4) are siblings"
        ])

    def test_half_siblings_through_father(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I1", "I4", ["I5"]),
            "F3": makeFamily("I3", "I5", marriageLine=80),
        }
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US18: 80: F3: Husband (I3) and wife (I5) are half-siblings"
        ])

    def test_half_siblings_through_mother(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I4", "I2", ["I5"]),
            "F3": makeFamily("I3", "I5"),
        }
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(len(gedcom.errors), 1)
        self.assertIn("are half-siblings", gedcom.errors[0])

    def test_cousins_are_not_siblings(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3", "I4"]),
            "F2": makeFamily("I3", "I5", ["I7"]),
            "F3": makeFamily("I6", "I4", ["I8"]),
            "F4": makeFamily("I7", "I8"),
        }
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_unrelated_spouses_are_valid(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3"]),
            "F2": makeFamily("I4", "I5", ["I6"]),
            "F3": makeFamily("I3", "I6"),
        }
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_spouses_with_no_parents_listed_are_valid(self):
        families = {"F1": makeFamily("I1", "I2")}
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_missing_spouse_is_skipped(self):
        families = {
            "F1": makeFamily("I1", "I2", ["I3", "I4"]),
            "F2": makeFamily("I3", "NA"),
        }
        gedcom.validate_us18_siblings_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])


class TestFamilyTestGed(unittest.TestCase):
    """Checks that family_test.ged produces exactly the expected US17 / US18 errors."""

    def setUp(self):
        gedcom.errors.clear()
        self.individuals = {}
        self.families = {}
        gedcom.parseGedcom("family_test.ged", self.individuals, self.families)

    def test_us17_errors_in_gedcom(self):
        gedcom.validate_us17_no_marriages_to_descendants(self.families)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US17: 422: F14: Husband (I37) is married to his descendant, wife (I39)",
            "ERROR: FAMILY: US17: 483: F17: Wife (I41) is married to her descendant, husband (I44)"
        ])

    def test_us18_errors_in_gedcom(self):
        gedcom.validate_us18_siblings_should_not_marry(self.families)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US18: 528: F19: Husband (I47) and wife (I48) are siblings",
            "ERROR: FAMILY: US18: 589: F22: Husband (I51) and wife (I53) are half-siblings"
        ])


if __name__ == "__main__":
    unittest.main()
