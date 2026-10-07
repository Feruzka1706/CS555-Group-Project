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
        "child": set(),      # FAMC family IDs
        "spouse": set()      # FAMS family IDs
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
        "DIV_LINE": "NA",
        "FAM_LINE": "NA"  # line number of the "0 Fxx FAM" line
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
                    families[currentFam]["FAM_LINE"] = currLineNum
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


def build_report_table(title, columns, rows):
    """
    Generic report table builder for list/report user stories.
    Example list/report stories: US29, US30, US31, US32, US33, etc.
    """
    reportTable = PrettyTable(columns)
    reportTable.title = title

    for row in rows:
        reportTable.add_row(row)

    for column in columns:
        reportTable.max_width[column] = 18

    return reportTable


def buildReportTables(individuals, families):
    """
    Build all list/report story tables.
    These are not error-validation stories.
    """
    reportTables = []

    reportTables.append(build_us29_deceased_table(individuals))
    reportTables.append(build_us30_living_married_table(families, individuals))

    # Future list/report story examples:
    # reportTables.append(build_us31_living_single_table(individuals))
    # reportTables.append(build_us32_multiple_births_table(families, individuals))
    # reportTables.append(build_us33_orphans_table(families, individuals))
    # reportTables.append(build_us34_large_age_differences_table(families, individuals))
    # reportTables.append(build_us35_recent_births_table(individuals))
    # reportTables.append(build_us36_recent_deaths_table(individuals))
    # reportTables.append(build_us37_recent_survivors_table(families, individuals))
    # reportTables.append(build_us38_upcoming_birthdays_table(individuals))
    # reportTables.append(build_us39_upcoming_anniversaries_table(families, individuals))

    return reportTables


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

    # US03: Birth before death
    # US04: Marriage before divorce
    validate_us03_birth_before_death(individuals)
    validate_us04_marriage_before_divorce(families)

    # US05: Marriage before death
    # US10: Marriage after 14
    validate_us05_marriage_before_death(families, individuals)
    validate_us10_marriage_after_14(families, individuals)

    # US06: Divorce before death
    # US07: Less than 150 years old
    validate_us06_divorce_before_death(families, individuals)
    validate_us07_less_than_150_years_old(individuals)

    # US08: Birth before marriage of parents
    # US09: Birth before death of parents
    validate_us08_birth_before_marriage_of_parents(families, individuals)
    validate_us09_birth_before_death_of_parents(families, individuals)

    # US11: No Bigamy
    # US12: Parents not too old
    validate_us11_no_bigamy(families, individuals)
    validate_us12_parents_not_too_old(families, individuals)

    # US17: No marriages to descendants
    # US18: Siblings should not marry
    validate_us17_no_marriages_to_descendants(families)
    validate_us18_siblings_should_not_marry(families)

    # US19: First cousins should not marry
    # US20: Aunts and uncles should not marry their nieces or nephews
    validate_us19_first_cousins_should_not_marry(families)
    validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)

    individualsTable, familiesTable = buildTables(individuals, families)
    reportTables = buildReportTables(individuals, families)

    with open('output.txt', 'w') as outputFile:
        outputFile.write(individualsTable.get_string())
        outputFile.write("\n\n")
        outputFile.write(familiesTable.get_string())
        outputFile.write("\n\n")

        for reportTable in reportTables:
            outputFile.write(reportTable.get_string())
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
    US01: Dates (birth, marriage, divorce, death) should not be after the current date.
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

        if married != "NA":
            marriageLine = family.get("MARR_LINE", "NA")

            if marriageLine != "NA" and compareDates(married, today) > 0:
                errors.append(
                    f"ERROR: FAMILY: US01: {marriageLine}: {familyId}: "
                    f"Marriage date {married} occurs in the future"
                )

        divorce = family.get("DIV", "NA")

        if divorce != "NA":
            divorceLine = family.get("DIV_LINE", "NA")

            if divorceLine != "NA" and compareDates(divorce, today) > 0:
                errors.append(
                    f"ERROR: FAMILY: US01: {divorceLine}: {familyId}: "
                    f"Divorce date {divorce} occurs in the future"
                )


def validate_us02_birth_before_marriage(families, individuals):
    """
    US02: Birth should occur before marriage of an individual.
    """
    for indId, individual in individuals.items():
        birthday = individual.get("birthday", "NA")

        if birthday == "NA":
            continue

        birthdayLine = individual.get("BIRT_LINE", "NA")
        spouseFamilies = individual.get("spouse", set())

        if len(spouseFamilies) == 0:
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

    If a spouse was born on or after the marriage date, that is already handled by US02.
    US10 skips that spouse to avoid duplicate errors or negative-age messages.
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
                if compareDates(husbandBirth, married) >= 0:
                    continue

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
                if compareDates(wifeBirth, married) >= 0:
                    continue

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


############ USER STORY US03 & US04 VALIDATIONS ##########

def validate_us04_marriage_before_divorce(families):
    """US04: Marriage should occur before divorce of spouses, and divorce can only occur after marriage."""
    for familyId, family in families.items():
        married = family.get("MARR", "NA")
        divorced = family.get("DIV", "NA")

        # Skip families that do not have both marriage and divorce dates.
        if married == "NA" or divorced == "NA":
            continue

        # Marriage must occur before divorce.
        if compareDates(married, divorced) >= 0:
            errors.append(
                f"ERROR: FAMILY: US04: {family.get('DIV_LINE', 'NA')}: "
                f"{familyId}: Divorce {divorced} occurs on or before marriage {married}"
            )


def validate_us03_birth_before_death(individuals):
    """US03: Birth should occur before death of an individual."""
    for indId, individual in individuals.items():
        birthday = individual.get("birthday", "NA")
        death = individual.get("death", "NA")

        # Skip individuals who do not have both dates.
        if birthday == "NA" or death == "NA":
            continue

        # Birth must occur before death.
        if compareDates(birthday, death) >= 0:
            errors.append(
                f"ERROR: INDIVIDUAL: US03: {individual.get('DEAT_LINE', 'NA')}: "
                f"{indId}: Birth {birthday} occurs on or after death {death}"
            )


############ USER STORY US08 & US09 VALIDATIONS ##########

def addMonthsToDate(dateString, months):
    year, month, day = dateString.split('-')
    year, month, day = int(year), int(month), int(day)

    monthIndex = month - 1 + months
    year = year + monthIndex // 12
    month = monthIndex % 12 + 1

    # if the new month is shorter (e.g. May 31 + 9 months), use its last day
    while True:
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            day -= 1


def validate_us08_birth_before_marriage_of_parents(families, individuals):
    for familyId, family in families.items():
        married = family.get("MARR", "NA")
        divorced = family.get("DIV", "NA")

        for childId in sorted(family.get("CHIL", set()), key=lambda x: (len(x), x)):
            child = individuals.get(childId)

            if child is None:
                continue

            childBirth = child.get("birthday", "NA")

            if childBirth == "NA":
                continue

            childBirthLine = child.get("BIRT_LINE", "NA")

            if married != "NA" and compareDates(childBirth, married) < 0:
                errors.append(
                    f"ERROR: FAMILY: US08: {childBirthLine}: {familyId}: "
                    f"Child {childId} born {childBirth} before marriage on {married}"
                )

            if divorced != "NA" and compareDates(childBirth, addMonthsToDate(divorced, 9)) > 0:
                errors.append(
                    f"ERROR: FAMILY: US08: {childBirthLine}: {familyId}: "
                    f"Child {childId} born {childBirth} more than 9 months after divorce on {divorced}"
                )


def validate_us09_birth_before_death_of_parents(families, individuals):
    for familyId, family in families.items():
        husbandId = family.get("HUSB", "NA")
        wifeId = family.get("WIFE", "NA")

        husband = individuals.get(husbandId)
        wife = individuals.get(wifeId)

        fatherDeath = husband.get("death", "NA") if husband is not None else "NA"
        motherDeath = wife.get("death", "NA") if wife is not None else "NA"

        for childId in sorted(family.get("CHIL", set()), key=lambda x: (len(x), x)):
            child = individuals.get(childId)

            if child is None:
                continue

            childBirth = child.get("birthday", "NA")

            if childBirth == "NA":
                continue

            childBirthLine = child.get("BIRT_LINE", "NA")

            if motherDeath != "NA" and compareDates(childBirth, motherDeath) > 0:
                errors.append(
                    f"ERROR: FAMILY: US09: {childBirthLine}: {familyId}: "
                    f"Child {childId} born {childBirth} after mother's ({wifeId}) death on {motherDeath}"
                )

            if fatherDeath != "NA" and compareDates(childBirth, addMonthsToDate(fatherDeath, 9)) > 0:
                errors.append(
                    f"ERROR: FAMILY: US09: {childBirthLine}: {familyId}: "
                    f"Child {childId} born {childBirth} more than 9 months after father's ({husbandId}) death on {fatherDeath}"
                )

############ USER STORY US11 & US12 VALIDATIONS ##########

def validate_us11_no_bigamy(families, individuals):
    """
    US11: Marriage should not occur during marriage to another spouse
    """

    #store every marriage for each person
    marriages = {}

    for familyId, family in families.items():
        married = family.get("MARR", "NA")

        if married == "NA":
            continue

        for spouseId in (family.get("HUSB", "NA"), family.get("WIFE", "NA")):
            if spouseId == "NA":
                continue

            marriages.setdefault(spouseId, []).append((familyId, family))

    #compare each persons marriages to identify overlaps
    for spouseId, spouseMarriages in marriages.items():
        for i in range(len(spouseMarriages)):
            familyId1, family1 = spouseMarriages[i]
            marriage1 = family1.get("MARR", "NA")

            for j in range(i + 1, len(spouseMarriages)):
                familyId2, family2 = spouseMarriages[j]
                marriage2 = family2.get("MARR", "NA")

                #determine which marriage happened first
                if compareDates(marriage1, marriage2) <= 0:
                    earlierFamilyId = familyId1
                    earlierFamily = family1
                    earlierMarriage = marriage1
                    laterFamilyId = familyId2
                    laterMarriage = marriage2
                else:
                    earlierFamilyId = familyId2
                    earlierFamily = family2
                    earlierMarriage = marriage2
                    laterFamilyId = familyId1
                    laterMarriage = marriage1

                #find the other spouse in the earlier marriage
                if earlierFamily.get("HUSB", "NA") == spouseId:
                    otherSpouseId = earlierFamily.get("WIFE", "NA")
                else:
                    otherSpouseId = earlierFamily.get("HUSB", "NA")

                #get the divorce date
                divorceDate = earlierFamily.get("DIV", "NA")

                #get the other spouse's death date
                deathDate = "NA"

                if otherSpouseId != "NA" and otherSpouseId in individuals:
                    deathDate = individuals[otherSpouseId].get("death", "NA")

                #determine when the earlier marriage actually ended
                #divorce or death
                marriageEnd = "NA"

                if divorceDate != "NA" and deathDate != "NA":
                    if compareDates(divorceDate, deathDate) <= 0:
                        marriageEnd = divorceDate
                    else:
                        marriageEnd = deathDate

                elif divorceDate != "NA":
                    marriageEnd = divorceDate

                elif deathDate != "NA":
                    marriageEnd = deathDate

                #if the earlier marriage has no ending date it is still active
                if marriageEnd == "NA":
                    errors.append(
                        f"ERROR: INDIVIDUAL: US11: "
                        f"{laterFamily.get('MARR_LINE', 'NA')}: {spouseId}: "
                        f"Marriage in {laterFamilyId} on {laterMarriage} "
                        f"occurs while marriage in {earlierFamilyId} "
                        f"on {earlierMarriage} is still active"
                    )

                #ff the later marriage occurs before or on the date then bigamy
               
                elif compareDates(laterMarriage, marriageEnd) <= 0:
                    errors.append(
                        f"ERROR: INDIVIDUAL: US11: "
                        f"{laterFamily.get('MARR_LINE', 'NA')}: {spouseId}: "
                        f"Marriage in {laterFamilyId} on {laterMarriage} "
                        f"occurs during marriage in {earlierFamilyId} "
                        f"on {earlierMarriage}, which ended on {marriageEnd}"
                    )


def validate_us12_parents_not_too_old(families, individuals):
    """
    US12: Mother should be less than 60 years older than her child
    and father should be less than 80 years older than his child
    """
    for familyId, family in families.items():
        motherId = family.get("WIFE", "NA")
        fatherId = family.get("HUSB", "NA")

        mother = individuals.get(motherId)
        father = individuals.get(fatherId)

        for childId in sorted(
            family.get("CHIL", set()),
            key=lambda x: (len(x), x)
        ):
            child = individuals.get(childId)

            if child is None:
                continue

            childBirth = child.get("birthday", "NA")
            childBirthLine = child.get("BIRT_LINE", "NA")

            if childBirth == "NA":
                continue

            #check the moms age when the kid was born
            if mother is not None:
                motherBirth = mother.get("birthday", "NA")

                if motherBirth != "NA":
                    motherAge = getAgeOnDate(motherBirth, childBirth)

                    if motherAge >= 60:
                        errors.append(
                            f"ERROR: FAMILY: US12: {childBirthLine}: {familyId}: "
                            f"Mother ({motherId}) was {motherAge} years old when "
                            f"child ({childId}) was born on {childBirth}"
                        )

            #check the dads age when the kid was born
            if father is not None:
                fatherBirth = father.get("birthday", "NA")

                if fatherBirth != "NA":
                    fatherAge = getAgeOnDate(fatherBirth, childBirth)

                    if fatherAge >= 80:
                        errors.append(
                            f"ERROR: FAMILY: US12: {childBirthLine}: {familyId}: "
                            f"Father ({fatherId}) was {fatherAge} years old when "
                            f"child ({childId}) was born on {childBirth}"
                        )



############ USER STORY US29 & US30 LIST FUNCTIONS ##########

def sortIds(ids):
    """
    Sort GEDCOM IDs in readable order.
    Example: I2 comes before I10.
    """
    return sorted(ids, key=lambda value: (len(value), value))


def validate_us29_list_deceased(individuals):
    """
    US29: List all deceased individuals in a GEDCOM file.

    This is a list/report story, not an error-validation story.
    It returns the IDs of all individuals with a death date.
    """
    deceasedIndividuals = []

    for indId in sortIds(individuals.keys()):
        individual = individuals[indId]

        if individual.get("death", "NA") != "NA":
            deceasedIndividuals.append(indId)

    return deceasedIndividuals


def validate_us30_list_living_married(families, individuals):
    """
    US30: List all living married people in a GEDCOM file.

    This is a list/report story, not an error-validation story.
    It returns the IDs of all living people who are currently married.
    Divorced people and widowed people are not included.
    """
    livingMarriedPeople = []

    for indId in sortIds(individuals.keys()):
        currentFamilyIds = get_current_married_family_ids(indId, families, individuals)

        if len(currentFamilyIds) > 0:
            livingMarriedPeople.append(indId)

    return livingMarriedPeople


def build_us29_deceased_table(individuals):
    """
    Build output table for US29: List all deceased individuals.
    """
    rows = []

    for indId in validate_us29_list_deceased(individuals):
        individual = individuals[indId]

        rows.append([
            indId,
            individual.get("name", "NA"),
            individual.get("death", "NA")
        ])

    return build_report_table(
        "US29: Deceased Individuals",
        ["ID", "Name", "Death Date"],
        rows
    )


def get_current_married_family_ids(indId, families, individuals):
    """
    Return current married family IDs for one living individual.
    A current married family has a marriage date, no divorce date,
    and the other spouse is also living.
    """
    currentFamilyIds = []
    individual = individuals.get(indId)

    if individual is None:
        return currentFamilyIds

    if individual.get("death", "NA") != "NA":
        return currentFamilyIds

    spouseFamilies = individual.get("spouse", set())

    for familyId in sortIds(spouseFamilies):
        family = families.get(familyId)

        if family is None:
            continue

        married = family.get("MARR", "NA")
        divorced = family.get("DIV", "NA")

        if married == "NA" or divorced != "NA":
            continue

        otherSpouseId = "NA"

        if family.get("HUSB", "NA") == indId:
            otherSpouseId = family.get("WIFE", "NA")
        elif family.get("WIFE", "NA") == indId:
            otherSpouseId = family.get("HUSB", "NA")

        otherSpouse = individuals.get(otherSpouseId)

        if otherSpouse is None:
            continue

        if otherSpouse.get("death", "NA") != "NA":
            continue

        currentFamilyIds.append(familyId)

    return currentFamilyIds


def build_us30_living_married_table(families, individuals):
    """
    Build output table for US30: List all living married individuals.
    """
    rows = []

    for indId in validate_us30_list_living_married(families, individuals):
        individual = individuals[indId]
        currentFamilyIds = get_current_married_family_ids(indId, families, individuals)

        rows.append([
            indId,
            individual.get("name", "NA"),
            ", ".join(currentFamilyIds)
        ])

    return build_report_table(
        "US30: Living Married Individuals",
        ["ID", "Name", "Family ID"],
        rows
    )


############ USER STORY US17 & US18 VALIDATIONS ##########

def getFamilyLine(family):
    """Line number to report for a family error: the marriage DATE line,
    or the "0 Fxx FAM" line if the family has no marriage date."""
    marriageLine = family.get("MARR_LINE", "NA")

    if marriageLine != "NA":
        return marriageLine

    return family.get("FAM_LINE", "NA")


def getChildren(personId, families):
    """All children of personId, from every family where they are a spouse."""
    children = set()

    for family in families.values():
        if personId != "NA" and personId in (family.get("HUSB"), family.get("WIFE")):
            children.update(family.get("CHIL", set()))

    return children


def getDescendants(personId, families):
    """All descendants of personId (children, grandchildren, ...)."""
    descendants = set()
    toVisit = list(getChildren(personId, families))

    while toVisit:
        currentId = toVisit.pop()

        # skip anyone already seen, so bad data with a cycle can't loop forever
        if currentId in descendants:
            continue

        descendants.add(currentId)
        toVisit.extend(getChildren(currentId, families))

    return descendants


def getParents(personId, families):
    """The family IDs and parent IDs for personId, from the families' CHIL lists."""
    parentFamilies = set()
    parents = set()

    for familyId, family in families.items():
        if personId in family.get("CHIL", set()):
            parentFamilies.add(familyId)

            for role in ("HUSB", "WIFE"):
                parentId = family.get(role, "NA")

                if parentId != "NA":
                    parents.add(parentId)

    return parentFamilies, parents


def validate_us17_no_marriages_to_descendants(families):
    """
    US17: Parents should not marry any of their descendants.
    Checks children, grandchildren and further generations.
    """
    for familyId, family in families.items():
        husbandId = family.get("HUSB", "NA")
        wifeId = family.get("WIFE", "NA")

        if husbandId == "NA" or wifeId == "NA":
            continue

        familyLine = getFamilyLine(family)

        if wifeId in getDescendants(husbandId, families):
            errors.append(
                f"ERROR: FAMILY: US17: {familyLine}: {familyId}: "
                f"Husband ({husbandId}) is married to his descendant, wife ({wifeId})"
            )

        if husbandId in getDescendants(wifeId, families):
            errors.append(
                f"ERROR: FAMILY: US17: {familyLine}: {familyId}: "
                f"Wife ({wifeId}) is married to her descendant, husband ({husbandId})"
            )


def validate_us18_siblings_should_not_marry(families):
    """
    US18: Siblings should not marry one another.
    Siblings are children of the same family. Half-siblings (one shared
    parent, different families) are also reported.
    """
    for familyId, family in families.items():
        husbandId = family.get("HUSB", "NA")
        wifeId = family.get("WIFE", "NA")

        if husbandId == "NA" or wifeId == "NA":
            continue

        husbandFamilies, husbandParents = getParents(husbandId, families)
        wifeFamilies, wifeParents = getParents(wifeId, families)

        if husbandFamilies & wifeFamilies:
            relationship = "siblings"
        elif husbandParents & wifeParents:
            relationship = "half-siblings"
        else:
            continue

        errors.append(
            f"ERROR: FAMILY: US18: {getFamilyLine(family)}: {familyId}: "
            f"Husband ({husbandId}) and wife ({wifeId}) are {relationship}"
        )

############ USER STORY US19 & US20 VALIDATIONS ##########

def getGrandparents(personId, families):
    """IDs of all grandparents of personId (parents of their parents)."""
    _, parentIds = getParents(personId, families)
    grandparentIds = set()

    for parentId in parentIds:
        _, parentParentIds = getParents(parentId, families)
        grandparentIds |= parentParentIds

    return grandparentIds

def validate_us19_first_cousins_should_not_marry(families):
    """
    US19: First cousins should not marry one another.
    First cousins each have one parent with the same family id.
    Half-first cousins don't have parents that share the same id, they each have a parent that share one parent.
    """
    for familyId, family in families.items():

        husbandId = family.get("HUSB", "NA")
        wifeId = family.get("WIFE", "NA")
        if husbandId == "NA" or wifeId == "NA":
            continue

        husbandFamilyIds, husbandParentIds = getParents(husbandId, families)
        wifeFamilyIds, wifeParentIds = getParents(wifeId, families)
        husbandGrandparentIds = getGrandparents(husbandId, families)
        wifeGrandparentIds = getGrandparents(wifeId, families)

        #if siblings
        if husbandFamilyIds & wifeFamilyIds or husbandParentIds & wifeParentIds:
            continue

        husbandParentFamilyIds = set()
        wifeParentFamilyIds = set()

        for husbandParentId in husbandParentIds:
            parentFamilyIds, _ = getParents(husbandParentId, families)
            husbandParentFamilyIds |= parentFamilyIds

        for wifeParentId in wifeParentIds:
            parentFamilyIds, _ = getParents(wifeParentId, families)
            wifeParentFamilyIds |= parentFamilyIds

        familyIntersect = husbandParentFamilyIds & wifeParentFamilyIds
        grandparentsIntersect = wifeGrandparentIds & husbandGrandparentIds

        if (len(familyIntersect) != 0):
            errors.append(
                f"ERROR: FAMILY: US19: {getFamilyLine(family)}: {familyId}: "
                f"Husband ({husbandId}) and wife ({wifeId}) are first cousins"
            )
        elif (len(familyIntersect) == 0 and len(grandparentsIntersect) != 0):
            errors.append(
                f"ERROR: FAMILY: US19: {getFamilyLine(family)}: {familyId}: "
                f"Husband ({husbandId}) and wife ({wifeId}) are half-first cousins"
            )

def isAuntOrUncleOf(candidateId, personId, families):
    """
    Checks if candidateId is a sibling or half-sibling of one of personId's parents
    """
    _, candidateParentIds = getParents(candidateId, families)
    _, parentIds = getParents(personId, families)

    for parentId in parentIds:
        if parentId == candidateId: #candidate is the parent, skip
            continue
        _, parentParentIds = getParents(parentId, families)
        if parentParentIds & candidateParentIds: #share at least one parent
            return True

    return False

def getAuntUncleRelation(personAId, personBId, families):
    """
    Returns aunt/nephew, uncle/niece, or None (if no such relation exists)
    """
    if isAuntOrUncleOf(personAId, personBId, families):
        return personAId, personBId
    if isAuntOrUncleOf(personBId, personAId, families):
        return personBId, personAId
    return None

def validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families):
    """
    US20: Aunts and uncles should not marry their nieces or nephews.
    """
    for familyId, family in families.items():

        husbandId = family.get("HUSB", "NA")
        wifeId = family.get("WIFE", "NA")
        if husbandId == "NA" or wifeId == "NA":
            continue

        auntUncleRelation = getAuntUncleRelation(husbandId, wifeId, families)

        if auntUncleRelation:
            personAId = auntUncleRelation[0]
            personBId = auntUncleRelation[1]

            #make error string
            startString =  f"ERROR: FAMILY: US20: {getFamilyLine(family)}: {familyId}: "
            personAString = f"An aunt or uncle ({personAId}) is married to his/her " #default string
            personBString = f"niece or nephew ({personBId})" #default string

            if (personAId == husbandId):
                personAString = f"An uncle ({personAId}) is married to his "
            elif (personAId == wifeId):
                personAString = f"An aunt ({personAId}) is married to her "

            if (personBId == husbandId):
                personBString = f"nephew ({personBId})"
            elif (personBId == wifeId):
                personBString = f"niece ({personBId})"

            resultString = startString + personAString + personBString
            errors.append(resultString)


################

############ USER STORY US35 & US36 LIST FUNCTIONS ##########

def isWithinLastDays(dateString, today, days=30):
    """
    True if dateString is no more than `days` days before today.
    Today itself counts as recent. Future dates are not recent
    (those are already reported by US01).
    """
    if dateString == "NA":
        return False

    eventYear, eventMonth, eventDay = dateString.split('-')
    todayYear, todayMonth, todayDay = today.split('-')

    eventDate = date(int(eventYear), int(eventMonth), int(eventDay))
    todayDate = date(int(todayYear), int(todayMonth), int(todayDay))

    daysAgo = (todayDate - eventDate).days

    return 0 <= daysAgo <= days


def validate_us35_list_recent_births(individuals, today=None):
    """
    US35: List all people in a GEDCOM file who were born in the last 30 days.

    This is a list/report story, not an error-validation story.
    It returns the IDs of all individuals born in the last 30 days.
    `today` can be passed in for testing.
    """
    if today is None:
        today = date.today().isoformat()

    recentBirths = []

    for indId in sortIds(individuals.keys()):
        individual = individuals[indId]

        if isWithinLastDays(individual.get("birthday", "NA"), today, 30):
            recentBirths.append(indId)

    return recentBirths


def validate_us36_list_recent_deaths(individuals, today=None):
    """
    US36: List all people in a GEDCOM file who died in the last 30 days.

    This is a list/report story, not an error-validation story.
    It returns the IDs of all individuals who died in the last 30 days.
    `today` can be passed in for testing.
    """
    if today is None:
        today = date.today().isoformat()

    recentDeaths = []

    for indId in sortIds(individuals.keys()):
        individual = individuals[indId]

        if isWithinLastDays(individual.get("death", "NA"), today, 30):
            recentDeaths.append(indId)

    return recentDeaths


def build_us35_recent_births_table(individuals, today=None):
    """
    Build output table for US35: List all individuals born in the last 30 days.
    """
    rows = []

    for indId in validate_us35_list_recent_births(individuals, today):
        individual = individuals[indId]

        rows.append([
            indId,
            individual.get("name", "NA"),
            individual.get("birthday", "NA")
        ])

    return build_report_table(
        "US35: Recent Births (Last 30 Days)",
        ["ID", "Name", "Birthday"],
        rows
    )


def build_us36_recent_deaths_table(individuals, today=None):
    """
    Build output table for US36: List all individuals who died in the last 30 days.
    """
    rows = []

    for indId in validate_us36_list_recent_deaths(individuals, today):
        individual = individuals[indId]

        rows.append([
            indId,
            individual.get("name", "NA"),
            individual.get("death", "NA")
        ])

    return build_report_table(
        "US36: Recent Deaths (Last 30 Days)",
        ["ID", "Name", "Death Date"],
        rows
    )
###################

if __name__ == "__main__":
    main()
