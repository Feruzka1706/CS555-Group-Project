"""
Unit tests for US19 and US20
Run with:  python3 -m unittest test_us19_us20.py -v
"""

import unittest
import test_gedcom as gedcom

def makeIndividual(birthday="NA", death="NA", spouse="NA", child="NA", gender="NA"):
    individual = gedcom.newIndividual()
    individual["birthday"] = birthday
    individual["BIRT_LINE"] = 10
    if death != "NA":
        individual["death"] = death
        individual["DEAT_LINE"] = 20
        individual["alive"] = "N"
    if spouse != "NA":
        individual["spouse"] = {spouse}
    else:
        individual["spouse"] = set()
    if child != "NA":
        individual["child"] = child #pass in a set
    if gender != "NA":
        individual["gender"] = gender
    return individual


def makeFamily(husbandId="I1", wifeId="I2", married="2000-01-01", divorced="NA", child="NA"):
    family = gedcom.newFamily()
    family["HUSB"] = husbandId
    family["WIFE"] = wifeId
    family["MARR"] = married
    family["DIV"] = divorced
    family["MARR_LINE"] = 40
    if divorced != "NA":
        family["DIV_LINE"] = 30
    if child != "NA":
        family["CHIL"] = child #pass in a set
    return family

class TestUS19FirstCousinsCannotMarry(unittest.TestCase):
        
    def setUp(self):
        gedcom.errors.clear()

    def test_first_cousins_married(self):
        families = {
            "F1": makeFamily("I3", "I2", "2000-01-01", "NA", {"I1"}),
            "F2": makeFamily("J3", "J2", "2000-01-01", "NA", {"J1"}),
            "F3": makeFamily("K1", "K2", "2000-01-01", "NA", {"I2", "J2"}),
            "F4": makeFamily("I1", "J1", "2021-01-01", "NA")
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US19: 40: F4: Husband (I1) and wife (J1) are first cousins'
        ])

    def test_first_cousins_married_on_both_sides(self):
        families = {
            "F1": makeFamily("I3", "I2", "2000-01-01", "NA", {"I1", "I4"}),
            "F2": makeFamily("J3", "J2", "2000-01-01", "NA", {"J1"}),
            "F3": makeFamily("K1", "K2", "1969-01-01", "NA", {"I2", "J2"}),
            "F4": makeFamily("I1", "J1", "2021-01-01", "NA"), #first cousins married
            
            "F5": makeFamily("L1", "L2", "2000-01-01", "NA", {"L3"}),
            "F6": makeFamily("M1", "M2", "1969-01-01", "NA", {"L1", "I3"}),
            "F7": makeFamily("I4", "L3", "2022-01-01", "NA"),
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US19: 40: F4: Husband (I1) and wife (J1) are first cousins',
            'ERROR: FAMILY: US19: 40: F7: Husband (I4) and wife (L3) are first cousins'
        ])

    def test_marriage_w_ppl_that_share_a_set_of_first_cousins(self):
        # J1 and L3 are married (different parents, same first cousins)
        families = {
            "F1": makeFamily("I3", "I2", "2000-01-01", "NA", {"I1", "I4"}),
            "F2": makeFamily("J3", "J2", "2000-01-01", "NA", {"J1"}),
            "F3": makeFamily("K1", "K2", "1969-01-01", "NA", {"I2", "J2"}),
            "F4": makeFamily("L3", "J1", "2023-01-01", "NA"), #second cousins married
            
            "F5": makeFamily("L1", "L2", "2000-01-01", "NA", {"L3"}),
            "F6": makeFamily("M1", "M2", "1969-01-01", "NA", {"L1", "I3"}),
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_second_cousins_married(self):
        #J1 and L3 are second cousins
        families = {
            "F7": makeFamily("G1", "G2", "1945-01-01", "NA", {"K1", "M1"}),
            "F3": makeFamily("K1", "K2", "1972-01-01", "NA", {"J2"}),
            "F6": makeFamily("M1", "M2", "1972-01-01", "NA", {"L1"}),
            "F2": makeFamily("J3", "J2", "2000-01-01", "NA", {"J1"}),
            "F5": makeFamily("L1", "L2", "2000-01-01", "NA", {"L3"}),
            "F4": makeFamily("L3", "J1", "2023-01-01", "NA"), #second cousins married
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_siblings_married(self):
        #S1 and S2 are siblings
        families = {
            "F1": makeFamily("I1", "I2", "2000-01-01", "NA", {"S1", "S2"}),
            "F2": makeFamily("S1", "S2", "2024-01-01", "NA"), #siblings married
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_half_siblings_married(self):
        #I3 and I5 are half siblings. This is valid.
        families = {
            "F1": makeFamily("I1", "I2", "1980-01-01", "1985-01-01", {"I3"}),
            "F2": makeFamily("I1", "I4", "1990-01-01", "NA", {"I5"}), 
            "F3": makeFamily("I3", "I5", "2024-01-01", "NA") 
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [])

    def test_half_first_cousins_marry(self):
        # I3 and I5 are half-siblings (same father I1, different mothers).
        # Their children I7 and I9 are first cousins. This is invalid.
        families = {
            "F1": makeFamily("I1", "I2", "1960-01-01", "1968-01-01", {"I3"}),
            "F2": makeFamily("I1", "I4", "1975-01-01", "NA", {"I5"}),
            "F3": makeFamily("I3", "I6", "2000-01-01", "NA",  {"I7"}),
            "F4": makeFamily("I5", "I8", "2001-01-01", "NA", {"I9"}),
            "F5": makeFamily("I7", "I9", "2025-01-01"),
        }
        gedcom.validate_us19_first_cousins_should_not_marry(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US19: 40: F5: Husband (I7) and wife (I9) are half-first cousins'
        ])


class TestUS20AuntsUnclesCannotMarryNiecesNephews(unittest.TestCase):
        
    def setUp(self):
        gedcom.errors.clear()

    def test_aunt_married_to_nephew(self):
        families = {
            "F1": makeFamily("I3", "I2", "2000-01-01", "NA", {"I1"}),
            "F2": makeFamily("I1", "J2", "2022-01-01", "NA", {"J1"}),
            "F3": makeFamily("K1", "K2", "2000-01-01", "NA", {"I2", "J2"}),
        }

        gedcom.validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US20: 40: F2: An aunt (J2) is married to her nephew (I1)'
        ])

    def test_uncle_married_to_niece(self):
        families = {
            "F3": makeFamily("K1", "K2", "1945-01-01", "NA", {"I2", "J1"}),
            "F1": makeFamily("I3", "I2", "1972-01-01", "NA", {"I1"}),
            "F4": makeFamily("J1", "I1", "2000-01-01", "NA"), #uncle married to niece
        }

        gedcom.validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US20: 40: F4: An uncle (J1) is married to his niece (I1)'
        ])

    def test_uncle_married_to_niece(self):
        families = {
            "F3": makeFamily("K1", "K2", "1945-01-01", "NA", {"I2", "J1"}),
            "F1": makeFamily("I3", "I2", "1972-01-01", "NA", {"I1"}),
            "F4": makeFamily("J1", "I1", "2000-01-01", "NA"), #uncle married to niece
        }

        gedcom.validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US20: 40: F4: An uncle (J1) is married to his niece (I1)'
        ])

    #same test as in US19, but this does not return any errors for US20
    def test_first_cousins_married(self):
        families = {
            "F1": makeFamily("I3", "I2", "2000-01-01", "NA", {"I1"}),
            "F2": makeFamily("J3", "J2", "2000-01-01", "NA", {"J1"}),
            "F3": makeFamily("K1", "K2", "2000-01-01", "NA", {"I2", "J2"}),
            "F4": makeFamily("I1", "J1", "2021-01-01", "NA")
        }
        gedcom.validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)
        self.assertEqual(gedcom.errors, [])

    def test_half_uncle_paternal_side_married_to_niece(self):
        families = {
            "F3": makeFamily("K1", "K2", "1945-01-01", "1948-06-01", {"I3"}), #first marriage, ended in divorce
            "F5": makeFamily("K3", "K2", "1949-01-01", "NA", {"J1"}), #second marriage
            "F1": makeFamily("I3", "I2", "1972-01-01", "NA", {"I1"}),
            "F4": makeFamily("J1", "I1", "2000-01-01", "NA"), #half-uncle married to niece
        }
        gedcom.validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)
        self.assertEqual(gedcom.errors, [
            'ERROR: FAMILY: US20: 40: F4: An uncle (J1) is married to his niece (I1)'
        ])

if __name__ == "__main__":
    unittest.main()