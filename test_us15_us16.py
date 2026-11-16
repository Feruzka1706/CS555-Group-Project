
import unittest
import Group_Project as Group_Project


class TestUS15US16(unittest.TestCase):

    def setUp(self):
        #clear errors before each test
        Group_Project.errors.clear()

    def tearDown(self):
        #clear errors after each test
        Group_Project.errors.clear()

    #US15 TESTS

    def test_us15_fourteen_siblings_passes(self):
        families = {
            "F1": {
                "CHIL": {f"I{i}" for i in range(1, 15)},
                "FAM_LINE": 10
            }
        }

        Group_Project.validate_us15_fewer_than_15_siblings(families)

        self.assertEqual(len(Group_Project.errors), 0)

    def test_us15_fifteen_siblings_fails(self):
        families = {
            "F1": {
                "CHIL": {f"I{i}" for i in range(1, 16)},
                "FAM_LINE": 10
            }
        }

        Group_Project.validate_us15_fewer_than_15_siblings(families)

        self.assertEqual(len(Group_Project.errors), 1)
        self.assertIn("US15", Group_Project.errors[0])
        self.assertIn("15 siblings", Group_Project.errors[0])

    #US16 TESTS

    def test_us16_same_last_name_passes(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "CHIL": {"I2", "I3"},
                "FAM_LINE": 10
            }
        }

        individuals = {
            "I1": {"name": "John /Smith/", "gender": "M"},
            "I2": {"name": "James /Smith/", "gender": "M"},
            "I3": {"name": "Robert /Smith/", "gender": "M"}
        }

        Group_Project.validate_us16_male_members_same_last_name(
            families, individuals
        )

        self.assertEqual(len(Group_Project.errors), 0)

    def test_us16_different_last_name_fails(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "CHIL": {"I2"},
                "FAM_LINE": 10
            }
        }

        individuals = {
            "I1": {"name": "John /Smith/", "gender": "M"},
            "I2": {"name": "James /Johnson/", "gender": "M"}
        }

        Group_Project.validate_us16_male_members_same_last_name(
            families, individuals
        )

        self.assertEqual(len(Group_Project.errors), 1)
        self.assertIn("US16", Group_Project.errors[0])
        self.assertIn("johnson", Group_Project.errors[0])
        self.assertIn("smith", Group_Project.errors[0])

    def test_us16_female_child_is_ignored(self):
        families = {
            "F1": {
                "HUSB": "I1",
                "CHIL": {"I2", "I3"},
                "FAM_LINE": 10
            }
        }

        individuals = {
            "I1": {"name": "John /Smith/", "gender": "M"},
            "I2": {"name": "James /Smith/", "gender": "M"},
            "I3": {"name": "Sarah /Johnson/", "gender": "F"}
        }

        Group_Project.validate_us16_male_members_same_last_name(
            families, individuals
        )

        self.assertEqual(len(Group_Project.errors), 0)


if __name__ == "__main__":
    unittest.main()

