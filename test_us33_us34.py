"""Sprint 4: US33 List Orphans and US34 List Large Age Differences.
Run: python3 -m unittest test_us33_us34.py -v
Requires I146-I148 and F58 - US33 test records in family_test.ged.
"""

import unittest
import test_gedcom as gedcom


def person(birthday="NA", death="NA", name="Test /Person/"):
    result = gedcom.newIndividual()
    result.update({
        "birthday": birthday,
        "death": death,
        "name": name
    })
    result["alive"] = "N" if death != "NA" else "Y"
    return result


def family(husband="NA", wife="NA", children=(), married="NA"):
    result = gedcom.newFamily()
    result.update({
        "HUSB": husband,
        "WIFE": wife,
        "CHIL": set(children),
        "MARR": married
    })
    return result


class TestUS33ListOrphans(unittest.TestCase):
    def setUp(self):
        gedcom.errors.clear()

    def test_us33_child_under_18_with_both_parents_dead_is_listed(self):
        people = {
            "I1": person("1970-01-01", "2020-01-01"),
            "I2": person("1972-01-01", "2021-01-01"),
            "I3": person("2014-06-01")
        }
        families = {"F1": family("I1", "I2", ["I3"], "2000-01-01")}

        self.assertEqual(
            gedcom.validate_us33_list_orphans(families, people, today="2026-11-06"),
            ["I3"]
        )
        self.assertEqual(gedcom.errors, [])

    def test_us33_one_living_parent_not_listed(self):
        people = {
            "I1": person("1970-01-01", "2020-01-01"),
            "I2": person("1972-01-01"),
            "I3": person("2014-06-01")
        }
        families = {"F1": family("I1", "I2", ["I3"], "2000-01-01")}

        self.assertEqual(
            gedcom.validate_us33_list_orphans(families, people, today="2026-11-06"),
            []
        )

    def test_us33_exactly_18_not_listed(self):
        people = {
            "I1": person("1970-01-01", "2020-01-01"),
            "I2": person("1972-01-01", "2021-01-01"),
            "I3": person("2008-11-06")
        }
        families = {"F1": family("I1", "I2", ["I3"], "2000-01-01")}

        self.assertEqual(
            gedcom.validate_us33_list_orphans(families, people, today="2026-11-06"),
            []
        )

    def test_us33_deceased_child_not_listed(self):
        people = {
            "I1": person("1970-01-01", "2020-01-01"),
            "I2": person("1972-01-01", "2021-01-01"),
            "I3": person("2014-06-01", "2025-01-01")
        }
        families = {"F1": family("I1", "I2", ["I3"], "2000-01-01")}

        self.assertEqual(
            gedcom.validate_us33_list_orphans(families, people, today="2026-11-06"),
            []
        )

    def test_us33_future_parent_death_does_not_count_as_deceased_yet(self):
        people = {
            "I1": person("1970-01-01", "2030-01-01"),
            "I2": person("1972-01-01", "2021-01-01"),
            "I3": person("2014-06-01")
        }
        families = {"F1": family("I1", "I2", ["I3"], "2000-01-01")}

        self.assertEqual(
            gedcom.validate_us33_list_orphans(families, people, today="2026-11-06"),
            []
        )

    def test_us33_existing_gedcom_positive_and_negative_cases(self):
        people, families = {}, {}
        gedcom.parseGedcom("family_test.ged", people, families)

        result = gedcom.validate_us33_list_orphans(
            families, people, today="2026-11-06"
        )

        self.assertIn("I148", result)   # both parents dead and child is 12
        self.assertNotIn("I7", result) # under 18, but both parents are living
        self.assertNotIn("I31", result) # parents dead, but child is older than 18
        self.assertEqual(gedcom.errors, [])


class TestUS34ListLargeAgeDifferences(unittest.TestCase):
    def setUp(self):
        gedcom.errors.clear()

    def test_us34_older_spouse_more_than_twice_younger_is_listed(self):
        people = {
            "I1": person("1960-01-01"),
            "I2": person("1986-01-01")
        }
        families = {"F1": family("I1", "I2", married="2010-01-01")}

        self.assertEqual(
            gedcom.validate_us34_list_large_age_differences(families, people),
            ["F1"]
        )
        self.assertEqual(gedcom.errors, [])

    def test_us34_exactly_twice_as_old_is_not_listed(self):
        people = {
            "I1": person("1970-01-01"),
            "I2": person("1990-01-01")
        }
        families = {"F1": family("I1", "I2", married="2010-01-01")}

        # Ages at marriage are 40 and 20. US34 requires MORE than twice.
        self.assertEqual(
            gedcom.validate_us34_list_large_age_differences(families, people),
            []
        )

    def test_us34_less_than_twice_as_old_is_not_listed(self):
        people = {
            "I1": person("1970-01-01"),
            "I2": person("1980-01-01")
        }
        families = {"F1": family("I1", "I2", married="2010-01-01")}

        self.assertEqual(
            gedcom.validate_us34_list_large_age_differences(families, people),
            []
        )

    def test_us34_works_when_wife_is_older_spouse(self):
        people = {
            "I1": person("1990-01-01"),
            "I2": person("1950-01-01")
        }
        families = {"F1": family("I1", "I2", married="2010-01-01")}

        self.assertEqual(
            gedcom.validate_us34_list_large_age_differences(families, people),
            ["F1"]
        )

    def test_us34_missing_marriage_or_birth_data_is_skipped(self):
        people = {
            "I1": person("1960-01-01"),
            "I2": person()
        }
        families = {
            "F1": family("I1", "I2", married="2010-01-01"),
            "F2": family("I1", "I2")
        }

        self.assertEqual(
            gedcom.validate_us34_list_large_age_differences(families, people),
            []
        )

    def test_us34_existing_gedcom_known_positive_and_negative_cases(self):
        people, families = {}, {}
        gedcom.parseGedcom("family_test.ged", people, families)

        result = gedcom.validate_us34_list_large_age_differences(
            families, people
        )

        for family_id in ("F14", "F17", "F36", "F39", "F45"):
            self.assertIn(family_id, result)

        self.assertNotIn("F1", result)
        self.assertNotIn("F58", result)  # US33 family has normal spouse ages
        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()
