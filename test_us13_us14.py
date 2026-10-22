
import unittest
import test_gedcom as gp


class TestUS13SiblingsSpacing(unittest.TestCase):

    def setUp(self):
        #clear errors before every test
        gp.errors.clear()

        self.individuals = {
            "I1": {
                "birthday": "2000-01-10",
                "BIRT_LINE": 10
            },
            "I2": {
                "birthday": "2000-01-12",
                "BIRT_LINE": 20
            },
            "I3": {
                "birthday": "2000-09-11",
                "BIRT_LINE": 30
            },
            "I4": {
                "birthday": "2000-01-11",
                "BIRT_LINE": 40
            },
            "I5": {
                "birthday": "NA",
                "BIRT_LINE": "NA"
            }
        }

        self.families = {
            "F1": {
                "CHIL": {"I1", "I2"},
                "FAM_LINE": 5,
                "MARR_LINE": "NA"
            }
        }

    def test_us13_reports_siblings_two_days_apart(self):
        gp.validate_us13_siblings_spacing(
            self.families, self.individuals
        )

        self.assertTrue(
            any("US13" in error for error in gp.errors)
        )

    def test_us13_allows_siblings_one_day_apart(self):
        self.families["F1"]["CHIL"] = {"I1", "I4"}

        gp.validate_us13_siblings_spacing(
            self.families, self.individuals
        )

        self.assertFalse(
            any("US13" in error for error in gp.errors)
        )

    def test_us13_allows_siblings_more_than_eight_months_apart(self):
        self.families["F1"]["CHIL"] = {"I1", "I3"}

        gp.validate_us13_siblings_spacing(
            self.families, self.individuals
        )

        self.assertFalse(
            any("US13" in error for error in gp.errors)
        )

    def test_us13_reports_siblings_exactly_eight_months_apart(self):
        self.individuals["I3"]["birthday"] = "2000-09-10"
        self.families["F1"]["CHIL"] = {"I1", "I3"}

        gp.validate_us13_siblings_spacing(
            self.families, self.individuals
        )

        self.assertTrue(
            any("US13" in error for error in gp.errors)
        )

    def test_us13_skips_missing_birthdays(self):
        self.families["F1"]["CHIL"] = {"I1", "I5"}

        gp.validate_us13_siblings_spacing(
            self.families, self.individuals
        )

        self.assertFalse(
            any("US13" in error for error in gp.errors)
        )


class TestUS14MultipleBirths(unittest.TestCase):

    def setUp(self):
        gp.errors.clear()

        self.individuals = {}

        #create six children born on the same date
        for i in range(1, 7):
            self.individuals[f"I{i}"] = {
                "birthday": "2000-05-15",
                "BIRT_LINE": i * 10
            }

        self.families = {
            "F1": {
                "CHIL": {f"I{i}" for i in range(1, 7)},
                "FAM_LINE": 5,
                "MARR_LINE": "NA"
            }
        }

    def test_us14_reports_six_children_born_same_day(self):
        gp.validate_us14_multiple_births_max_five(
            self.families, self.individuals
        )

        self.assertTrue(
            any("US14" in error for error in gp.errors)
        )

        self.assertTrue(
            any("6 siblings" in error for error in gp.errors)
        )

    def test_us14_allows_five_children_born_same_day(self):
        self.families["F1"]["CHIL"] = {
            "I1", "I2", "I3", "I4", "I5"
        }

        gp.validate_us14_multiple_births_max_five(
            self.families, self.individuals
        )

        self.assertFalse(
            any("US14" in error for error in gp.errors)
        )

    def test_us14_allows_six_children_on_different_dates(self):
        self.individuals["I6"]["birthday"] = "2000-05-16"

        gp.validate_us14_multiple_births_max_five(
            self.families, self.individuals
        )

        self.assertFalse(
            any("US14" in error for error in gp.errors)
        )

    def test_us14_skips_children_with_missing_birthdays(self):
        self.individuals["I6"]["birthday"] = "NA"

        gp.validate_us14_multiple_births_max_five(
            self.families, self.individuals
        )

        self.assertFalse(
            any("US14" in error for error in gp.errors)
        )


if __name__ == "__main__":
    unittest.main()
