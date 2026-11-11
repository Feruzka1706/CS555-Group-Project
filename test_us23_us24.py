"""
Unit tests for US23 (Unique name and birth date) and
US24 (Unique families by spouses).

Run with:  python3 -m unittest test_us23_us24.py -v OR python -m unittest test_us23_us24.py -v
"""

import unittest

import test_gedcom as gedcom


def makeIndividual(name, birthday, indi_line="NA", gender="NA"):
    individual = gedcom.newIndividual()
    individual["name"] = name
    individual["birthday"] = birthday
    individual["gender"] = gender
    individual["INDI_LINE"] = indi_line
    return individual

def makeFamily(husbandId="NA", wifeId="NA", children=(), marr="NA", famLine="NA"):
    family = gedcom.newFamily()
    family["HUSB"] = husbandId
    family["WIFE"] = wifeId
    family["CHIL"] = set(children)
    family["MARR"] = marr
    family["MARR_LINE"] = 50
    family["FAM_LINE"] = 49 if famLine == "NA" else famLine
    family["HUSB_LINE"] = 51 if husbandId != "NA" else "NA"
    family["WIFE_LINE"] = 52 if wifeId != "NA" else "NA"
    family["CHIL_LINES"] = {childId: 53 for childId in children}
    return family

class TestUS23UniqueFirstNameAndBirthDate(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def check(self, individuals):
        """Run US23 on a list of individuals given as {id: (name, birthday)}."""
        individuals = {id: makeIndividual(name, birthday, indi_line, gender)
                       for id, (name, birthday, indi_line, gender) in individuals.items()}
        gedcom.validate_us23_unique_name_and_birth_date(individuals)

    def test_same_first_name_and_birth_date_is_error(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "2000-01-01", 20, "M")})
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US23: 10, 20: Individuals I1 and I2 have the same first name (Josh /LastName/) and birth date (2000-01-01)"
        ])

    def test_same_first_name_and_birth_date_diff_genders_is_error(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "2000-01-01", 20, "F")})
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US23: 10, 20: Individuals I1 and I2 have the same first name (Josh /LastName/) and birth date (2000-01-01)"
        ])

    def test_same_first_name_and_birth_date_3_people_is_error(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "2000-01-01", 20, "M"),
                    "I3": ("Josh /LastName/", "2000-01-01", 30, "M")})
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US23: 10, 20, 30: Individuals I1, I2 and I3 have the same first name (Josh /LastName/) and birth date (2000-01-01)"
        ])

    def test_multiple_repeats(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "2000-01-01", 20, "M"),
                    "I3": ("Josh /LastName/", "2000-01-01", 30, "M"),
                    "I4": ("Alice /AlsoRepeated/", "2001-01-01", 40, "F"),
                    "I5": ("Alice /AlsoRepeated/", "2001-01-01", 50, "F"),
                    "I6": ("Tom /Unique/", "2000-01-01", 60, "M")})
        self.assertEqual(gedcom.errors, [
            "ERROR: INDIVIDUAL: US23: 10, 20, 30: Individuals I1, I2 and I3 have the same first name (Josh /LastName/) and birth date (2000-01-01)",
            "ERROR: INDIVIDUAL: US23: 40, 50: Individuals I4 and I5 have the same first name (Alice /AlsoRepeated/) and birth date (2001-01-01)"
        ])

    def test_missing_first_name_is_valid(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("NA", "2000-01-01", 20, "M")})
        self.assertEqual(gedcom.errors, [])

    def test_missing_birthday_is_valid(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "NA", 20, "M")})
        self.assertEqual(gedcom.errors, [])

    def test_both_missing_birthdays_is_valid(self):
        self.check({"I1": ("Josh /LastName/", "NA", 10, "M"),
                    "I2": ("Josh /LastName/", "NA", 20, "M")})
        self.assertEqual(gedcom.errors, []) 

    def test_both_missing_names_and_birthdays_is_valid(self):
        self.check({"I1": ("NA", "NA", 10, "M"),
                    "I2": ("NA", "NA", 20, "M")})
        self.assertEqual(gedcom.errors, []) 


    def test_diff_birthday_is_valid(self):
        self.check({"I1": ("Josh /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "2000-01-02", 20, "M")})
        self.assertEqual(gedcom.errors, [])

    def test_diff_name_is_valid(self):
        self.check({"I1": ("John /LastName/", "2000-01-01", 10, "M"),
                    "I2": ("Josh /LastName/", "2000-01-01", 20, "M")})
        self.assertEqual(gedcom.errors, [])

class TestUS24UniqueFamiliesBySpouses(unittest.TestCase):

    def setUp(self):
        gedcom.errors.clear()

    def test_same_husband_name_and_wife_name_and_marriage_date_is_error(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2025-03-03", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US24: 50, 70: Families F1 and F2 share the same husband name (Bob /Potter/), wife name (Ginny /Potter/), and marriage date (2025-03-03)"
        ])

    def test_same_husband_and_wife_and_marriage_date_is_error(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H1", "W1", marr="2025-03-03", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US24: 50, 70: Families F1 and F2 share the same husband name (Bob /Potter/), wife name (Ginny /Potter/), and marriage date (2025-03-03)"
        ])

    def test_three_families_with_same_spouse_names_and_marriage_date_is_error(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
            "H3": makeIndividual("Bob /Potter/", "1980-01-01", gender="M"),
            "W3": makeIndividual("Ginny /Potter/", "1981-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2025-03-03", famLine=70),
            "F3": makeFamily("H3", "W3", marr="2025-03-03", famLine=90),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US24: 50, 70, 90: Families F1, F2 and F3 share the same husband name (Bob /Potter/), wife name (Ginny /Potter/), and marriage date (2025-03-03)"
        ])

    def test_only_two_families_match_is_error(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
            "H3": makeIndividual("Ash /Potter/", "1979-01-01", gender="M"),
            "W3": makeIndividual("Rebecca /Potter/", "1978-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2025-03-03", famLine=70),
            "F3": makeFamily("H3", "W3", marr="2025-03-03", famLine=90),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US24: 50, 70: Families F1 and F2 share the same husband name (Bob /Potter/), wife name (Ginny /Potter/), and marriage date (2025-03-03)"
        ])

    def test_more_than_one_repeated_family_is_error(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),

            "H3": makeIndividual("Percy /Jackson/", "1998-04-07", gender="M"),
            "W3": makeIndividual("Annabeth /Chase/", "1999-11-16", gender="F"),
            "H4": makeIndividual("Percy /Jackson/", "1998-04-07", gender="M"),
            "W4": makeIndividual("Annabeth /Chase/", "1999-11-16", gender="F")
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2025-03-03", famLine=70),
            "F3": makeFamily("H3", "W3", marr="2026-10-10", famLine=100),
            "F4": makeFamily("H4", "W4", marr="2026-10-10", famLine=120),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [
            "ERROR: FAMILY: US24: 50, 70: Families F1 and F2 share the same husband name (Bob /Potter/), wife name (Ginny /Potter/), and marriage date (2025-03-03)",
            "ERROR: FAMILY: US24: 100, 120: Families F3 and F4 share the same husband name (Percy /Jackson/), wife name (Annabeth /Chase/), and marriage date (2026-10-10)"
        ])       

    def test_same_names_switched_roles_is_valid(self):
        individuals = {
            "H1": makeIndividual("Alex /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Blake /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Blake /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Alex /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2025-03-03", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_one_family_missing_marriage_date_is_valid(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-03-03", famLine=50),
            "F2": makeFamily("H2", "W2", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_both_families_missing_marriage_date_is_valid(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", famLine=50),
            "F2": makeFamily("H2", "W2", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_diff_marriage_dates_is_valid(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-01-01", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2026-01-01", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_same_husband_diff_wife_is_valid(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Bob /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Rebecca /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-01-01", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2026-01-01", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_same_wife_diff_husband_is_valid(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
            "H2": makeIndividual("Jake /Potter/", "1990-01-01", gender="M"),
            "W2": makeIndividual("Ginny /Potter/", "1991-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-01-01", famLine=50),
            "F2": makeFamily("H2", "W2", marr="2026-01-01", famLine=70),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])

    def test_one_family_is_valid(self):
        individuals = {
            "H1": makeIndividual("Bob /Potter/", "2000-01-01", gender="M"),
            "W1": makeIndividual("Ginny /Potter/", "2001-01-01", gender="F"),
        }
        families = {
            "F1": makeFamily("H1", "W1", marr="2025-01-01", famLine=50),
        }
        gedcom.validate_us24_unique_families_by_spouse(families, individuals)
        self.assertEqual(gedcom.errors, [])       