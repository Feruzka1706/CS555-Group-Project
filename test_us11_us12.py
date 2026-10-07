import unittest
import test_gedcom as Group_project


class TestUS11(unittest.TestCase):

    def setUp(self):
        #clear the error list before each test
        Group_project.errors.clear()

    #test 1: Bigamy should be detected when a person
    #gets married to another spouse before the first marriage ends
    def test_bigamy(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "WIFE": "I2",
                "CHIL": set(),
                "MARR": "2010-01-01",
                "DIV": "2015-01-01",
                "MARR_LINE": 10,
                "DIV_LINE": 12,
                "FAM_LINE": 9
            },

            "F2": {
                "HUSB": "I1",
                "WIFE": "I3",
                "CHIL": set(),
                "MARR": "2013-01-01",
                "DIV": "NA",
                "MARR_LINE": 20,
                "DIV_LINE": "NA",
                "FAM_LINE": 19
            }
        }

        Group_project.validate_us11_no_bigamy(families)

        self.assertEqual(len(Group_project.errors), 1)
        self.assertIn("US11", Group_project.errors[0])
        self.assertIn("I1", Group_project.errors[0])

    #test 2: A second marriage after the first marriage ends
    #should NOT be considered bigamy
    def test_no_bigamy_after_divorce(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "WIFE": "I2",
                "CHIL": set(),
                "MARR": "2010-01-01",
                "DIV": "2012-01-01",
                "MARR_LINE": 10,
                "DIV_LINE": 12,
                "FAM_LINE": 9
            },

            "F2": {
                "HUSB": "I1",
                "WIFE": "I3",
                "CHIL": set(),
                "MARR": "2013-01-01",
                "DIV": "NA",
                "MARR_LINE": 20,
                "DIV_LINE": "NA",
                "FAM_LINE": 19
            }
        }

        Group_project.validate_us11_no_bigamy(families)

        self.assertEqual(len(Group_project.errors), 0)


class TestUS12(unittest.TestCase):

    def setUp(self):
        #clear the error list before each test
        Group_project.errors.clear()

    #test 1: mom is 60 years old when the child is born
    #produces a US12 error
    def test_mother_too_old(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "WIFE": "I2",
                "CHIL": {"I3"},
                "MARR": "1980-01-01",
                "DIV": "NA",
                "MARR_LINE": 10,
                "DIV_LINE": "NA",
                "FAM_LINE": 9
            }
        }

        individuals = {
            "I1": {
                "birthday": "1950-01-01",
                "BIRT_LINE": 2
            },

            "I2": {
                "birthday": "1950-01-01",
                "BIRT_LINE": 4
            },

            "I3": {
                "birthday": "2010-01-01",
                "BIRT_LINE": 15
            }
        }

        Group_project.validate_us12_parents_not_too_old(
            families, individuals
        )

        self.assertEqual(len(Group_project.errors), 1)
        self.assertIn("US12", Group_project.errors[0])
        self.assertIn("Mother", Group_project.errors[0])
        self.assertIn("I2", Group_project.errors[0])

    #test 2: father is 80 years old when the child is born
    #produce a US12 error
    def test_father_too_old(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "WIFE": "I2",
                "CHIL": {"I3"},
                "MARR": "1980-01-01",
                "DIV": "NA",
                "MARR_LINE": 10,
                "DIV_LINE": "NA",
                "FAM_LINE": 9
            }
        }

        individuals = {
            "I1": {
                "birthday": "1930-01-01",
                "BIRT_LINE": 2
            },

            "I2": {
                "birthday": "1960-01-01",
                "BIRT_LINE": 4
            },

            "I3": {
                "birthday": "2010-01-01",
                "BIRT_LINE": 15
            }
        }

        Group_project.validate_us12_parents_not_too_old(
            families, individuals
        )

        self.assertEqual(len(Group_project.errors), 1)
        self.assertIn("US12", Group_project.errors[0])
        self.assertIn("Father", Group_project.errors[0])
        self.assertIn("I1", Group_project.errors[0])

    #test 3: both parents are within the allowed age limits
    #should NOT produce an error
    def test_parents_not_too_old(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "WIFE": "I2",
                "CHIL": {"I3"},
                "MARR": "2000-01-01",
                "DIV": "NA",
                "MARR_LINE": 10,
                "DIV_LINE": "NA",
                "FAM_LINE": 9
            }
        }

        individuals = {
            "I1": {
                "birthday": "1980-01-01",
                "BIRT_LINE": 2
            },

            "I2": {
                "birthday": "1982-01-01",
                "BIRT_LINE": 4
            },

            "I3": {
                "birthday": "2010-01-01",
                "BIRT_LINE": 15
            }
        }

        Group_project.validate_us12_parents_not_too_old(
            families, individuals
        )

        self.assertEqual(len(Group_project.errors), 0)


if __name__ == "__main__":
    unittest.main()
