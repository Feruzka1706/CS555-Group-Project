"""
Prepared by Group 1 team members:
- Joshua Silva
- Benjamin Wolgang
- Varsha Anumala
- Anuj Patel
- Feruza Jonzokova
"""

from prettytable import PrettyTable
from datetime import date
import sys

# used to validate tags in main()
tags = {
    '0': {'INDI', 'FAM', 'HEAD', 'TRLR', 'NOTE'},
    '1': {'NAME', 'SEX', 'BIRT', 'DEAT', 'FAMC', 'FAMS', 'MARR', 'HUSB', 'WIFE', 'CHIL', 'DIV'},
    '2': {'DATE'}
}

# any errors in the gedcom file will be added to this array.
# these will be printed in the output.txt file.
errors = []


def newIndividual():
    """Default values for an individual record. Missing values are "NA"."""
    return {
        "name": "NA",
        "gender": "NA",
        "birthday": "NA",
        "age": "NA",
        "alive": "Y",
        "death": "NA",
        "BIRT_LINE": "NA",  # line number of the birth DATE
        "DEAT_LINE": "NA",  # line number of the death DATE
        "child": set(),   # FAMC family IDs
        "spouse": set()   # FAMS family IDs
    }


def newFamily():
    """Default values for a family record. Missing values are "NA"."""
    return {
        "HUSB": "NA",
        "WIFE": "NA",
        "CHIL": set(),
        "MARR": "NA",
        "DIV": "NA",
        "MARR_LINE": "NA",
        "DIV_LINE": "NA"
    }


def displayValue(value):
    """Format a stored value for the tables: empty sets are shown as NA."""
    if isinstance(value, set):
        return str(value) if value else "NA"
    return value


def parseGedcom(gedcomFileName, individuals, families):
    """
    Read the GEDCOM file and store every record directly in the
    individuals and families dictionaries.
    """
    with open(gedcomFileName, mode='r', encoding='utf-8-sig') as inputFile:
        currentInd = None   # ID of the individual record being read
        currentFam = None   # ID of the family record being read
        dateToUpdate = ""   # the event tag (BIRT, DEAT, MARR, DIV) the next DATE belongs to
        prevDateLine = -1   # line number of that event tag

        # enumerate gives the actual GEDCOM file line number, including blank lines
        for currLineNum, line in enumerate(inputFile, start=1):
            line = line.strip()

            if line == '':
                continue

            level, tag, *arguments = line.split()

            # "0 I1 INDI" / "0 F1 FAM": the tag is the third token
            if len(arguments) > 0 and level == '0' and (arguments[0] == 'INDI' or arguments[0] == 'FAM'):
                tempTag = tag
                tag = arguments[0]
                arguments[0] = tempTag

            # if this is not a valid tag, ignore this tag
            if level not in tags or tag not in tags[level]:
                continue

            # any level 0 line ends the current record and may start a new one
            if level == '0':
                currentInd = None
                currentFam = None

                if tag == 'INDI':
                    currentInd = arguments[0]
                    individuals[currentInd] = newIndividual()
                elif tag == 'FAM':
                    currentFam = arguments[0]
                    families[currentFam] = newFamily()
                continue

            # tags that belong to an individual record
            if currentInd is not None:
                individual = individuals[currentInd]

                match tag:
                    case "NAME":
                        individual["name"] = " ".join(arguments)

                    case "SEX":
                        individual["gender"] = arguments[0]

                    case "FAMC":
                        individual["child"].add(arguments[0])

                    case "FAMS":
                        individual["spouse"].add(arguments[0])

                    case "BIRT" | "DEAT":
                        dateToUpdate = tag
                        prevDateLine = currLineNum

                    case "DATE":
                        gedcomDate = getDate(arguments)
                        today = date.today().isoformat()
                        isEventDate = prevDateLine == currLineNum - 1

                        match dateToUpdate:
                            case "BIRT":
                                if isEventDate:
                                    individual["birthday"] = gedcomDate
                                    individual["BIRT_LINE"] = currLineNum

                            case "DEAT":
                                if isEventDate:
                                    individual["death"] = gedcomDate
                                    individual["DEAT_LINE"] = currLineNum
                                    individual["alive"] = "N"

            # tags that belong to a family record
            elif currentFam is not None:
                family = families[currentFam]

                match tag:
                    case "HUSB":
                        family["HUSB"] = arguments[0]

                    case "WIFE":
                        family["WIFE"] = arguments[0]

                    case "CHIL":
                        family["CHIL"].update(arguments)

                    case "MARR" | "DIV":
                        dateToUpdate = tag
                        prevDateLine = currLineNum

                    case "DATE":
                        gedcomDate = getDate(arguments)
                        today = date.today().isoformat()

                        # only keep the date if it directly follows MARR / DIV
                        if prevDateLine == currLineNum - 1 and dateToUpdate in ("MARR", "DIV"):
                            family[dateToUpdate] = gedcomDate
                            family[f"{dateToUpdate}_LINE"] = currLineNum

    # ages are calculated once every record has been read
    for individual in individuals.values():
        if individual["birthday"] != "NA":
            individual["age"] = getAge(individual["birthday"], individual["death"])


def buildTables(individuals, families):
    """Build the Individuals and Families tables from the dictionaries."""
    individualsTable = PrettyTable(["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"])
    familiesTable = PrettyTable(["ID", "Married", "Divorced", "Husband ID", "Husband Name", "Wife ID", "Wife Name", "Children"])
    individualsTable.title = "Individuals"
    familiesTable.title = "Families"

    for indId, individual in individuals.items():
        individualsTable.add_row([
            indId,
            individual["name"],
            individual["gender"],
            individual["birthday"],
            individual["age"],
            individual["alive"],
            individual["death"],
            displayValue(individual["child"]),
            displayValue(individual["spouse"])
        ])

    for famId, family in families.items():
        # every record has been read, so spouse names can be looked up directly
        husbandName = individuals.get(family["HUSB"], {}).get("name", "NA")
        wifeName = individuals.get(family["WIFE"], {}).get("name", "NA")

        familiesTable.add_row([
            famId,
            family["MARR"],
            family["DIV"],
            family["HUSB"],
            husbandName,
            family["WIFE"],
            wifeName,
            displayValue(family["CHIL"])
        ])

    # make long columns wrap so the table is not too wide
    individualsTable.max_width["Name"] = 18
    individualsTable.max_width["Child"] = 12
    individualsTable.max_width["Spouse"] = 15

    familiesTable.max_width["Husband Name"] = 18
    familiesTable.max_width["Wife Name"] = 18
    familiesTable.max_width["Children"] = 12

    return individualsTable, familiesTable


def main():
    individuals = dict()  # store all individuals
    families = dict()     # store all families

    # Allows the program to run against any GEDCOM input file.
    # Example: python3 test_gedcom.py family_test.ged
    # If no file is provided, it defaults to family_test.ged.
    if len(sys.argv) > 1:
        gedcomFileName = sys.argv[1]
    else:
        gedcomFileName = "family_test.ged"

    parseGedcom(gedcomFileName, individuals, families)

    # US01: Dates (birth, marriage, divorce, death) before current date
    # US02: Birth before marriage
    validate_us01_dates_before_current_date(families, individuals)
    validate_us02_birth_before_marriage(families, individuals)
    # US05: Marriage before death
    # US10: Marriage after 14
    validate_us05_marriage_before_death(families, individuals)
    validate_us10_marriage_after_14(families, individuals)
    # US06: Divorce before death
    # US07: Less than 150 years old
    validate_us06_divorce_before_death(families, individuals)
    validate_us07_less_than_150_years_old(individuals)

    individualsTable, familiesTable = buildTables(individuals, families)

    with open('output.txt', 'w') as outputFile:
        outputFile.write(individualsTable.get_string())
        outputFile.write("\n\n")
        outputFile.write(familiesTable.get_string())
        outputFile.write("\n\n")

        for error in errors:
            outputFile.write(f"{error}\n")


############ HELPER FUNCTIONS ##########

def getDate(arguments):
    months = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12"
    }

    day, month, year = arguments

    if len(day) == 1:
        day = f"0{day}"

    monthNum = months[month]

    return f"{year}-{monthNum}-{day}"


def compareDates(dateStrA, dateStrB):
    yearA, monthA, dayA = dateStrA.split('-')
    yearB, monthB, dayB = dateStrB.split('-')

    dateA = date(int(yearA), int(monthA), int(dayA))
    dateB = date(int(yearB), int(monthB), int(dayB))

    diff = dateA - dateB
    days = diff.days

    if days < 0:
        return -1
    elif days > 0:
        return 1
    else:
        return 0


def getAge(birth, curr):
    birthYear, birthMonth, birthDay = birth.split('-')
    birthDate = date(int(birthYear), int(birthMonth), int(birthDay))

    currDate = date.today()

    if curr != "NA":
        deathYear, deathMonth, deathDay = curr.split('-')
        currDate = date(int(deathYear), int(deathMonth), int(deathDay))

    diff = currDate - birthDate
    days = diff.days
    age = int(days / 365)

    return age


def getAgeOnDate(birthDateString, compareDateString):
    birthYear, birthMonth, birthDay = birthDateString.split('-')
    compareYear, compareMonth, compareDay = compareDateString.split('-')

    birthDate = date(int(birthYear), int(birthMonth), int(birthDay))
    compareDate = date(int(compareYear), int(compareMonth), int(compareDay))

    age = compareDate.year - birthDate.year

    # If birthday has not happened yet in the marriage year, subtract 1.
    if (compareDate.month, compareDate.day) < (birthDate.month, birthDate.day):
        age -= 1

    return age

############ USER STORY US01 & US02 VALIDATIONS ##########

def validate_us01_dates_before_current_date(families, individuals):
    """
    US01: Dates (birth, marriage, divorce, death) should not be after the current date
    """
    today = date.today().isoformat()

    # Check birthday and death date for every individual
    for indId, individual in individuals.items():
        birthday = individual.get("birthday", "NA")

        if birthday != "NA":
            birthdayLine = individual.get("BIRT_LINE", "NA")

            if birthdayLine != "NA" and compareDates(birthday, today) > 0:
                errors.append(
                    f"ERROR: INDIVIDUAL: US01: {birthdayLine}: {indId}: "
                    f"Birthday {birthday} occurs in the future"
                )
        
        death = individual.get("death", "NA")
        if death == "NA":
            continue

        deathLine = individual.get("DEAT_LINE", "NA")

        if deathLine != "NA" and compareDates(death, today) > 0:
            errors.append(
                f"ERROR: INDIVIDUAL: US01: {deathLine}: {indId}: "
                f"Death {death} occurs in the future"
            )

    # Check marriage and divorce date for every family
    for familyId, family in families.items():
        married = family.get("MARR", "NA")

        if married == "NA":
            continue

        marriageLine = family.get("MARR_LINE", "NA")
        if marriageLine != "NA" and compareDates(married, today) > 0:
            errors.append(
                f"ERROR: FAMILY: US01: {marriageLine}: {familyId}: "
                f"Marriage date {married} occurs in the future"
            )

        divorce = family.get("DIV", "NA")

        if divorce == "NA":
            continue

        divorceLine = family.get("DIV_LINE", "NA")
        if divorceLine != "NA" and compareDates(divorce, today) > 0:
            errors.append(
                f"ERROR: FAMILY: US01: {divorceLine}: {familyId}: "
                f"Divorce date {divorce} occurs in the future"
            )

def validate_us02_birth_before_marriage(families, individuals):
    """
    US02: Birth should occur before marriage of an individual
    """
    for indId, individual in individuals.items():
        birthday = individual.get("birthday", "NA")
        birthdayLine = "NA"

        if birthday != "NA":
            birthdayLine = individual.get("BIRT_LINE", "NA")

        spouseFamilies = individual.get("spouse", set())
        if (len(spouseFamilies) == 0):
            continue

        for familyId in spouseFamilies:
            family = families.get(familyId, None)
            if family is None:
                continue
            married = family.get("MARR", "NA")
            if married != "NA" and compareDates(birthday, married) >= 0:
                errors.append(
                    f"ERROR: INDIVIDUAL: US02: {birthdayLine}: {indId}: "
                    f"Birth date {birthday} occurs on or after marriage date {married}"
                )


############ USER STORY US05 & US10 VALIDATIONS ##########

def validate_us05_marriage_before_death(families, individuals):
    """
    US05: Marriage should occur before death of either spouse.
    """
    for familyId, family in families.items():
        married = family.get("MARR", "")

        if married == "" or married == "NA":
            continue

        marriageLine = family.get("MARR_LINE", "")
        husbandId = family.get("HUSB", "")
        wifeId = family.get("WIFE", "")

        husband = individuals.get(husbandId)
        wife = individuals.get(wifeId)

        if husband is not None:
            husbandDeath = husband.get("death", "NA")

            if husbandDeath != "NA" and compareDates(married, husbandDeath) > 0:
                errors.append(
                    f"ERROR: FAMILY: US05: {marriageLine}: {familyId}: "
                    f"Married {married} after husband's ({husbandId}) death on {husbandDeath}"
                )

        if wife is not None:
            wifeDeath = wife.get("death", "NA")

            if wifeDeath != "NA" and compareDates(married, wifeDeath) > 0:
                errors.append(
                    f"ERROR: FAMILY: US05: {marriageLine}: {familyId}: "
                    f"Married {married} after wife's ({wifeId}) death on {wifeDeath}"
                )


def validate_us10_marriage_after_14(families, individuals):
    """
    US10: Marriage should be at least 14 years after birth of both spouses.
    """
    for familyId, family in families.items():
        married = family.get("MARR", "")

        if married == "" or married == "NA":
            continue

        marriageLine = family.get("MARR_LINE", "")
        husbandId = family.get("HUSB", "")
        wifeId = family.get("WIFE", "")

        husband = individuals.get(husbandId)
        wife = individuals.get(wifeId)

        if husband is not None:
            husbandBirth = husband.get("birthday", "NA")

            if husbandBirth != "NA":
                husbandAgeAtMarriage = getAgeOnDate(husbandBirth, married)

                if husbandAgeAtMarriage < 14:
                    errors.append(
                        f"ERROR: FAMILY: US10: {marriageLine}: {familyId}: "
                        f"Husband's ({husbandId}) age {husbandAgeAtMarriage} is less than 14 "
                        f"at marriage on {married}"
                    )

        if wife is not None:
            wifeBirth = wife.get("birthday", "NA")

            if wifeBirth != "NA":
                wifeAgeAtMarriage = getAgeOnDate(wifeBirth, married)

                if wifeAgeAtMarriage < 14:
                    errors.append(
                        f"ERROR: FAMILY: US10: {marriageLine}: {familyId}: "
                        f"Wife's ({wifeId}) age {wifeAgeAtMarriage} is less than 14 "
                        f"at marriage on {married}"
                    )


############ USER STORY US06 & US07 VALIDATIONS ##########

def validate_us06_divorce_before_death(families, individuals):
    """
    US06: Divorce can only occur before death of both spouses.
    A divorce on the same day as a death is allowed (same rule as US05).
    """
    for familyId, family in families.items():
        divorced = family.get("DIV", "NA")

        if divorced == "" or divorced == "NA":
            continue

        divorceLine = family.get("DIV_LINE", "NA")

        for role, label in (("HUSB", "husband"), ("WIFE", "wife")):
            spouseId = family.get(role, "NA")
            spouse = individuals.get(spouseId)

            if spouse is None:
                continue

            spouseDeath = spouse.get("death", "NA")

            if spouseDeath != "NA" and compareDates(divorced, spouseDeath) > 0:
                errors.append(
                    f"ERROR: FAMILY: US06: {divorceLine}: {familyId}: "
                    f"Divorced {divorced} after {label}'s ({spouseId}) death on {spouseDeath}"
                )


def validate_us07_less_than_150_years_old(individuals, today=None):
    """
    US07: Death should be less than 150 years after birth for dead people,
    and the current date should be less than 150 years after birth for
    living people. `today` can be passed in for testing.
    """
    if today is None:
        today = date.today().isoformat()

    for indId, individual in individuals.items():
        birthday = individual.get("birthday", "NA")

        if birthday == "NA":
            continue

        death = individual.get("death", "NA")

        if death != "NA":
            age = getAgeOnDate(birthday, death)

            if age >= 150:
                errors.append(
                    f"ERROR: INDIVIDUAL: US07: {individual.get('DEAT_LINE', 'NA')}: {indId}: "
                    f"More than 150 years old at death - Birth {birthday}: Death {death}"
                )
        else:
            age = getAgeOnDate(birthday, today)

            if age >= 150:
                errors.append(
                    f"ERROR: INDIVIDUAL: US07: {individual.get('BIRT_LINE', 'NA')}: {indId}: "
                    f"More than 150 years old - Birth {birthday}"
                )


################

if __name__ == "__main__":
    main()