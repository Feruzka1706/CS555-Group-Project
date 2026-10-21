"""Sprint 3: US31 List Living Single and US32 List Multiple Births.
Run: python3 -m unittest test_us31_us32.py -v
Requires I109 - US31 test records in family_test.ged.
"""
import unittest
import test_gedcom as gedcom


def person(birthday="NA", death="NA", spouse=(), name="Test /Person/"):
    result = gedcom.newIndividual()
    result.update({"birthday": birthday, "death": death, "spouse": set(spouse), "name": name})
    result["alive"] = "N" if death != "NA" else "Y"
    return result


def family(children=()):
    result = gedcom.newFamily()
    result["CHIL"] = set(children)
    return result


class TestUS31ListLivingSingle(unittest.TestCase):
    def setUp(self):
        gedcom.errors.clear()

    def test_us31_living_never_married_over_30_is_listed(self):
        people = {"I2": person("1990-01-01"), "I1": person("1980-01-01")}
        self.assertEqual(gedcom.validate_us31_list_living_single(people, today="2026-10-20"), ["I1", "I2"])
        self.assertEqual(gedcom.errors, [])

    def test_us31_under_30_not_listed(self):
        self.assertEqual(gedcom.validate_us31_list_living_single(
            {"I1": person("2000-01-01")}, today="2026-10-20"), [])

    def test_us31_exactly_30_not_listed(self):
        self.assertEqual(gedcom.validate_us31_list_living_single(
            {"I1": person("1996-10-20")}, today="2026-10-20"), [])

    def test_us31_birthday_boundary(self):
        data = {"I1": person("1995-10-21"), "I2": person("1995-10-20")}
        self.assertEqual(gedcom.validate_us31_list_living_single(data, today="2026-10-20"), ["I2"])

    def test_us31_married_and_deceased_not_listed(self):
        people = {"I1": person("1970-01-01", spouse={"F1"}),
                  "I2": person("1960-01-01", death="2020-01-01")}
        self.assertEqual(gedcom.validate_us31_list_living_single(people, today="2026-10-20"), [])

    def test_us31_spouse_from_family_not_fams_excluded(self):
        people = {"I1": person("1970-01-01")}
        families = {"F1": gedcom.newFamily()}
        families["F1"].update({"WIFE": "I1", "MARR": "1990-01-01"})
        self.assertEqual(gedcom.validate_us31_list_living_single(
            people, families, today="2026-10-20"), [])

    def test_us31_missing_birthday_not_listed(self):
        self.assertEqual(gedcom.validate_us31_list_living_single(
            {"I1": person()}, today="2026-10-20"), [])

    def test_us31_existing_gedcom_known_positive_and_negative(self):
        people, families = {}, {}
        gedcom.parseGedcom("family_test.ged", people, families)
        result = gedcom.validate_us31_list_living_single(people, families, today="2026-10-20")
        self.assertIn("I17", result)   # living, no spouse, over 30
        self.assertIn("I109", result)  # US31 record: Olivia, never married
        self.assertEqual(people["I109"]["spouse"], set())
        self.assertNotIn("I1", result)  # married
        self.assertNotIn("I16", result) # deceased
        self.assertNotIn("I86", result) # infant
        self.assertNotIn("I103", result) # spouse in F47 despite missing FAMS
        self.assertNotIn("I109", gedcom.validate_us31_list_living_single(
            people, families, today="2010-10-20"))  # age 25 in 2010
        self.assertEqual(gedcom.errors, [])


class TestUS32ListMultipleBirths(unittest.TestCase):
    def setUp(self):
        gedcom.errors.clear()

    def test_us32_twins_same_family_are_reported(self):
        people = {"I1": person("2000-01-01"), "I2": person("2000-01-01")}
        families = {"F1": family(["I1", "I2"])}
        self.assertEqual(gedcom.validate_us32_list_multiple_births(families, people),
                         [("F1", "2000-01-01", ("I1", "I2"))])
        self.assertEqual(gedcom.errors, [])

    def test_us32_triplets_are_grouped_as_one_multiple_birth(self):
        people = {i: person("2000-01-01") for i in ("I10", "I2", "I1")}
        families = {"F1": family(people)}
        self.assertEqual(gedcom.validate_us32_list_multiple_births(families, people),
                         [("F1", "2000-01-01", ("I1", "I2", "I10"))])

    def test_us32_different_birthdays_do_not_count(self):
        people = {"I1": person("2000-01-01"), "I2": person("2000-01-02")}
        self.assertEqual(gedcom.validate_us32_list_multiple_births(
            {"F1": family(people)}, people), [])

    def test_us32_same_date_in_different_families_does_not_count(self):
        people = {"I1": person("2000-01-01"), "I2": person("2000-01-01")}
        families = {"F1": family(["I1"]), "F2": family(["I2"])}
        self.assertEqual(gedcom.validate_us32_list_multiple_births(families, people), [])

    def test_us32_missing_dates_and_records_are_skipped(self):
        people = {"I1": person(), "I2": person("2000-01-01")}
        self.assertEqual(gedcom.validate_us32_list_multiple_births(
            {"F1": family(["I1", "I2", "I99"])}, people), [])

    def test_us32_separate_birth_groups_are_preserved(self):
        people = {"I1": person("2000-01-01"), "I2": person("2000-01-01"),
                  "I3": person("2001-02-02"), "I4": person("2001-02-02")}
        self.assertEqual(gedcom.validate_us32_list_multiple_births(
            {"F1": family(people)}, people),
            [("F1", "2000-01-01", ("I1", "I2")),
             ("F1", "2001-02-02", ("I3", "I4"))])

    def test_us32_existing_gedcom_family_f46_triplets(self):
        people, families = {}, {}
        gedcom.parseGedcom("family_test.ged", people, families)
        groups = gedcom.validate_us32_list_multiple_births(families, people)
        self.assertIn(("F46", "2000-01-01", ("I98", "I99", "I100")), groups)
        self.assertEqual(gedcom.errors, [])


if __name__ == "__main__":
    unittest.main()
