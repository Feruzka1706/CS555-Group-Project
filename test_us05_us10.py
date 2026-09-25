import unittest
import test_gedcom

"""
For US10 story below 60 Tests are implemented:

1. Husband is younger than 14 → error
2. Wife is younger than 14 → error
3. Both spouses are younger than 14 → two errors
4. Husband is exactly 14 on marriage date → no error
5. Wife is exactly 14 on marriage date → no error
6. Both spouses are older than 14 → no error
"""
class TestUS10MarriageAfter14(unittest.TestCase):

    def setUp(self):
        test_gedcom.errors.clear()

    def test_us10_husband_younger_than_14_should_create_error(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "WIFE": "I2",
                "MARR": "2020-01-01",
                "MARR_LINE": "10"
            }
        }

        individuals = {
            "I1": {
                "birthday": "2010-01-01",
                "death": "NA"
            },
            "I2": {
                "birthday": "1990-01-01",
                "death": "NA"
            }
        }

        test_gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(len(test_gedcom.errors), 1)
        self.assertIn("ERROR: FAMILY: US10", test_gedcom.errors[0])
        self.assertIn("Husband's (I1)", test_gedcom.errors[0])
        self.assertIn("less than 14", test_gedcom.errors[0])

    def test_us10_wife_younger_than_14_should_create_error(self):
        families = {
            "F2": {
                "HUSB": "I3",
                "WIFE": "I4",
                "MARR": "2020-01-01",
                "MARR_LINE": "20"
            }
        }

        individuals = {
            "I3": {
                "birthday": "1990-01-01",
                "death": "NA"
            },
            "I4": {
                "birthday": "2011-01-01",
                "death": "NA"
            }
        }

        test_gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(len(test_gedcom.errors), 1)
        self.assertIn("ERROR: FAMILY: US10", test_gedcom.errors[0])
        self.assertIn("Wife's (I4)", test_gedcom.errors[0])
        self.assertIn("less than 14", test_gedcom.errors[0])

    def test_us10_both_spouses_younger_than_14_should_create_two_errors(self):
        families = {
            "F3": {
                "HUSB": "I5",
                "WIFE": "I6",
                "MARR": "2020-01-01",
                "MARR_LINE": "30"
            }
        }

        individuals = {
            "I5": {
                "birthday": "2010-01-01",
                "death": "NA"
            },
            "I6": {
                "birthday": "2011-01-01",
                "death": "NA"
            }
        }

        test_gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(len(test_gedcom.errors), 2)
        self.assertIn("Husband's (I5)", test_gedcom.errors[0])
        self.assertIn("Wife's (I6)", test_gedcom.errors[1])

    def test_us10_husband_exactly_14_should_not_create_error(self):
        families = {
            "F4": {
                "HUSB": "I7",
                "WIFE": "I8",
                "MARR": "2020-01-01",
                "MARR_LINE": "40"
            }
        }

        individuals = {
            "I7": {
                "birthday": "2006-01-01",
                "death": "NA"
            },
            "I8": {
                "birthday": "1990-01-01",
                "death": "NA"
            }
        }

        test_gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(len(test_gedcom.errors), 0)

    def test_us10_wife_exactly_14_should_not_create_error(self):
        families = {
            "F5": {
                "HUSB": "I9",
                "WIFE": "I10",
                "MARR": "2020-01-01",
                "MARR_LINE": "50"
            }
        }

        individuals = {
            "I9": {
                "birthday": "1990-01-01",
                "death": "NA"
            },
            "I10": {
                "birthday": "2006-01-01",
                "death": "NA"
            }
        }

        test_gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(len(test_gedcom.errors), 0)

    def test_us10_both_spouses_older_than_14_should_not_create_error(self):
        families = {
            "F6": {
                "HUSB": "I11",
                "WIFE": "I12",
                "MARR": "2020-01-01",
                "MARR_LINE": "60"
            }
        }

        individuals = {
            "I11": {
                "birthday": "1990-01-01",
                "death": "NA"
            },
            "I12": {
                "birthday": "1992-01-01",
                "death": "NA"
            }
        }

        test_gedcom.validate_us10_marriage_after_14(families, individuals)

        self.assertEqual(len(test_gedcom.errors), 0)


if __name__ == "__main__":
    unittest.main()