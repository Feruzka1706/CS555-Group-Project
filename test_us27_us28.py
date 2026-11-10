"""
Unit tests for US27 (Include individual ages) and US28 (Order siblings by age).

Run with:  python3 -m unittest test_us27_us28.py -v
Requires I151-I155 / F60 (US28 test records) in family_test.ged.
"""

import unittest

import test_gedcom as gedcom


TODAY = "2026-11-07"  # fixed date so the tests never change over time


def makeIndividual(birthday="NA", death="NA", name="NA"):
    individual = gedcom.newIndividual()
    individual["name"] = name
    individual["birthday"] = birthday
    if death != "NA":
        individual["death"] = death
        individual["alive"] = "N"
    return individual


def makeFamily(children=()):
    family = gedcom.newFamily()
    family["HUSB"] = "H1"
    family["WIFE"] = "W1"
    family["CHIL"] = set(children)
    return family


class TestUS27IncludeIndividualAges(unittest.TestCase):

    def test_living_person_age_after_birthday(self):
        self.assertEqual(gedcom.calculate_us27_age(makeIndividual("1990-03-15"), TODAY), 36)

    def test_living_person_age_on_birthday(self):
        self.assertEqual(gedcom.calculate_us27_age(makeIndividual("1990-11-07"), TODAY), 36)

    def test_living_person_age_day_before_birthday(self):
        # the old days / 365 calculation got this case wrong (it said 36)
        self.assertEqual(gedcom.calculate_us27_age(makeIndividual("1990-11-08"), TODAY), 35)

    def test_deceased_person_uses_age_at_death(self):
        individual = makeIndividual("1940-05-15", death="2010-05-14")
        self.assertEqual(gedcom.calculate_us27_age(individual, TODAY), 69)

    def test_born_today_is_zero(self):
        self.assertEqual(gedcom.calculate_us27_age(makeIndividual(TODAY), TODAY), 0)

    def test_missing_birthday_is_na(self):
        self.assertEqual(gedcom.calculate_us27_age(makeIndividual(), TODAY), "NA")

    def test_future_birthday_is_na(self):
        # reported by US01; a negative age would be misleading
        self.assertEqual(gedcom.calculate_us27_age(makeIndividual("2029-03-10"), TODAY), "NA")

    def test_death_before_birth_is_na(self):
        # reported by US03; a negative age would be misleading
        individual = makeIndividual("1980-01-01", death="1977-01-01")
        self.assertEqual(gedcom.calculate_us27_age(individual, TODAY), "NA")

    def test_default_today_is_used_when_not_given(self):
        age = gedcom.calculate_us27_age(makeIndividual("2000-01-01"))
        self.assertIsInstance(age, int)
        self.assertGreaterEqual(age, 26)


class TestUS28OrderSiblingsByAge(unittest.TestCase):

    def test_children_are_listed_oldest_first(self):
        individuals = {"I1": makeIndividual("2000-03-01"),
                       "I2": makeIndividual("1988-05-10"),
                       "I3": makeIndividual("1994-07-20")}
        family = makeFamily(["I1", "I2", "I3"])
        self.assertEqual(gedcom.validate_us28_list_siblings_by_age(family, individuals),
                         ["I2", "I3", "I1"])

    def test_birthday_not_id_decides_the_order(self):
        # I10 is the oldest even though its ID sorts after I9
        individuals = {"I9": makeIndividual("2005-01-01"),
                       "I10": makeIndividual("1999-01-01")}
        family = makeFamily(["I9", "I10"])
        self.assertEqual(gedcom.validate_us28_list_siblings_by_age(family, individuals),
                         ["I10", "I9"])

    def test_same_month_different_year(self):
        individuals = {"I1": makeIndividual("2010-12-01"),
                       "I2": makeIndividual("2009-12-31")}
        family = makeFamily(["I1", "I2"])
        self.assertEqual(gedcom.validate_us28_list_siblings_by_age(family, individuals),
                         ["I2", "I1"])

    def test_twins_are_ordered_by_id(self):
        individuals = {"I12": makeIndividual("2000-01-01"),
                       "I2": makeIndividual("2000-01-01"),
                       "I3": makeIndividual("1998-06-01")}
        family = makeFamily(["I12", "I2", "I3"])
        self.assertEqual(gedcom.validate_us28_list_siblings_by_age(family, individuals),
                         ["I3", "I2", "I12"])

    def test_missing_birthday_and_missing_record_are_last(self):
        individuals = {"I1": makeIndividual("2000-01-01"),
                       "I2": makeIndividual()}
        family = makeFamily(["I2", "I99", "I1"])
        self.assertEqual(gedcom.validate_us28_list_siblings_by_age(family, individuals),
                         ["I1", "I2", "I99"])

    def test_family_with_no_children(self):
        self.assertEqual(gedcom.validate_us28_list_siblings_by_age(makeFamily(), {}), [])

    def test_report_table_rows(self):
        individuals = {"I1": makeIndividual("2000-03-01", name="Lucy /A/"),
                       "I2": makeIndividual("1988-05-10", name="James /A/"),
                       "I3": makeIndividual("1990-01-01", name="Only /Child/")}
        families = {"F1": makeFamily(["I1", "I2"]),
                    "F2": makeFamily(["I3"])}   # one child: no siblings, not listed
        table = gedcom.build_us28_siblings_by_age_table(families, individuals, TODAY)
        self.assertEqual(table.title, "US28: Siblings by Age (Oldest First)")
        self.assertEqual([list(row) for row in table.rows], [
            ["F1", 1, "I2", "James /A/", "1988-05-10", 38],
            ["F1", 2, "I1", "Lucy /A/", "2000-03-01", 26]
        ])


class TestFamilyTestGed(unittest.TestCase):
    """Checks US27 / US28 against the records in family_test.ged."""

    def setUp(self):
        self.individuals = {}
        self.families = {}
        gedcom.parseGedcom("family_test.ged", self.individuals, self.families)

    def test_us27_parser_uses_exact_ages(self):
        self.assertEqual(self.individuals["I20"]["age"], "NA")   # born in the future
        self.assertEqual(self.individuals["I34"]["age"], "NA")   # died before birth
        self.assertEqual(self.individuals["I16"]["age"], 160)    # age at death

    def test_us28_f60_children_listed_youngest_first_are_sorted(self):
        self.assertEqual(sorted(self.families["F60"]["CHIL"]), ["I153", "I154", "I155"])
        self.assertEqual(
            gedcom.validate_us28_list_siblings_by_age(self.families["F60"], self.individuals),
            ["I154", "I155", "I153"]
        )

    def test_us28_f10_walker_children(self):
        self.assertEqual(
            gedcom.validate_us28_list_siblings_by_age(self.families["F10"], self.individuals),
            ["I25", "I26", "I27", "I28"]
        )

    def test_us28_f46_twins_by_id_then_younger_sibling(self):
        self.assertEqual(
            gedcom.validate_us28_list_siblings_by_age(self.families["F46"], self.individuals),
            ["I98", "I99", "I100", "I101"]
        )


if __name__ == "__main__":
    unittest.main()
