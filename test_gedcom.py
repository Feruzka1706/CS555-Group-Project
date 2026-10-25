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

# ! allIndividuals and allFamilies are used in US22 to store duplicate families !
# maps individual id -> array of line numbers for the corrresponding individual record(s)
allIndividuals = dict() 
# maps family id -> array of line numbers for the corrresponding family record(s)
allFamilies = dict() 


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
        "spouse": set(),     # FAMS family IDs
        "FAMC_LINES": {},    # FAMC family ID -> line number
        "FAMS_LINES": {}     # FAMS family ID -> line number
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
        "FAM_LINE": "NA",  # line number of the "0 Fxx FAM" line
        "HUSB_LINE": "NA",
        "WIFE_LINE": "NA",
        "CHIL_LINES": {}   # child ID -> line number
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
                    allIndividuals.setdefault(currentInd, []).append(currLineNum) #for US22
                elif tag == 'FAM':
                    currentFam = arguments[0]
                    families[currentFam] = newFamily()
                    families[currentFam]["FAM_LINE"] = currLineNum
                    allFamilies.setdefault(currentFam, []).append(currLineNum) #for US22
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
                        individual["FAMC_LINES"][arguments[0]] = currLineNum

                    case "FAMS":
                        individual["spouse"].add(arguments[0])
                        individual["FAMS_LINES"][arguments[0]] = currLineNum

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
                        family["HUSB_LINE"] = currLineNum

                    case "WIFE":
                        family["WIFE"] = arguments[0]
                        family["WIFE_LINE"] = currLineNum

                    case "CHIL":
                        family["CHIL"].update(arguments)

                        for childId in arguments:
                            family["CHIL_LINES"][childId] = currLineNum

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
    reportTables.append(build_us35_recent_births_table(individuals))
    reportTables.append(build_us36_recent_deaths_table(individuals))
    reportTables.append(build_us31_living_single_table(individuals, families))
    reportTables.append(build_us32_multiple_births_table(families, individuals))
    reportTables.append(build_us37_recent_survivors_table(families, individuals))
    reportTables.append(build_us38_upcoming_birthdays_table(individuals))

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

    # US13: Siblings spacing
    # US14: No more than five multiple births
    validate_us13_siblings_spacing(families, individuals)
    validate_us14_multiple_births_max_five(families, individuals)

    # US17: No marriages to descendants
    # US18: Siblings should not marry
    validate_us17_no_marriages_to_descendants(families)
    validate_us18_siblings_should_not_marry(families)

    # US19: First cousins should not marry
    # US20: Aunts and uncles should not marry their nieces or nephews
    validate_us19_first_cousins_should_not_marry(families)
    validate_us20_aunts_and_uncles_not_married_to_nieces_and_nephews(families)

    # US25: Unique first names in families
    # US26: Corresponding entries
    validate_us25_unique_first_names_in_families(families, individuals)
    validate_us26_corresponding_entries(families, individuals)

    # US21: Correct gender for role
    # US22: Unique IDs
    validate_us21_correct_gender_for_role(families, individuals)
    validate_us22_unique_ids(allFamilies, allIndividuals)

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
                    f"ANOMALY: FAMILY: US08: {childBirthLine}: {familyId}: "
                    f"Child {childId} born {childBirth} before marriage on {married}"
                )

            if divorced != "NA" and compareDates(childBirth, addMonthsToDate(divorced, 9)) > 0:
                errors.append(
                    f"ANOMALY: FAMILY: US08: {childBirthLine}: {familyId}: "
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
                    laterFamily=family2
                    laterMarriage = marriage2
                else:
                    earlierFamilyId = familyId2
                    earlierFamily = family2
                    earlierMarriage = marriage2
                    laterFamilyId = familyId1
                    laterFamily=family1
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
############ USER STORY US13 & US14 ##########

def validate_us13_siblings_spacing(families, individuals):
    """ US13: Siblings should be more than 8 months apart or less than 2 days apart """

    for familyId in sortIds(families.keys()):
        family = families[familyId]
        childrenWithBirthdays = []

        #collect the birth dates of children in this family
        for childId in family.get("CHIL", set()):
            child = individuals.get(childId)

            if child is None:
                continue

            birthday = child.get("birthday", "NA")

            if birthday == "NA":
                continue

            childrenWithBirthdays.append(
                (birthday, childId, child.get("BIRT_LINE", "NA"))
            )

        #sort children by birthday so we compare neighboring births
        childrenWithBirthdays.sort()

        for i in range(1, len(childrenWithBirthdays)):
            earlierBirth, earlierId, earlierLine = childrenWithBirthdays[i - 1]
            laterBirth, laterId, laterLine = childrenWithBirthdays[i]

            #same day births and births one day apart are allowed
            daysApart = (
                date.fromisoformat(laterBirth)
                - date.fromisoformat(earlierBirth)
            ).days

            if daysApart < 2:
                continue

            #births more than 8 calendar months apart are allowed
            eightMonthsLater = addMonthsToDate(earlierBirth, 8)

            if compareDates(laterBirth, eightMonthsLater) > 0:
                continue

            #use the later child's birth-date line for the error
            if laterLine == "NA":
                laterLine = getFamilyLine(family)

            errors.append(
                f"ERROR: FAMILY: US13: {laterLine}: {familyId}: "
                f"Siblings {earlierId} and {laterId} were born "
                f"{daysApart} days apart, which is not allowed"
            )


def validate_us14_multiple_births_max_five(families, individuals):
    """ US14: No more than five siblings should be born at the same time """
    for familyId in sortIds(families.keys()):
        family = families[familyId]
        birthsByDate = {}

        #group the children by their recorded birth date
        for childId in family.get("CHIL", set()):
            child = individuals.get(childId)

            if child is None:
                continue

            birthday = child.get("birthday", "NA")

            if birthday == "NA":
                continue

            birthsByDate.setdefault(birthday, []).append(childId)

        #report any group with more than five children
        for birthday, childIds in sorted(birthsByDate.items()):
            if len(childIds) > 5:
                childIds = sortIds(childIds)

                firstChild = individuals[childIds[0]]
                line = firstChild.get("BIRT_LINE", "NA")

                if line == "NA":
                    line = getFamilyLine(family)

                errors.append(
                    f"ERROR: FAMILY: US14: {line}: {familyId}: "
                    f"{len(childIds)} siblings were born on {birthday}; "
                    f"the maximum allowed is 5. Children: "
                    f"{', '.join(childIds)}"
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


############ USER STORY US25 & US26 VALIDATIONS ##########

def getFirstName(fullName):
    """
    First (given) name from a GEDCOM name, e.g. "Emma /Johnson/" -> "emma".
    Lowercase, so "Emma" and "EMMA" count as the same name.
    Returns "NA" if there is no name.
    """
    if fullName == "NA":
        return "NA"

    givenNames = fullName.split("/")[0].split()

    if len(givenNames) == 0:
        return "NA"

    return givenNames[0].lower()


def validate_us25_unique_first_names_in_families(families, individuals):
    """
    US25: No more than one child with the same first name and birth date
    should appear in a family. Twins with different names are allowed.
    Each repeated child is reported once, naming the first child it matches.
    """
    for familyId in sortIds(families.keys()):
        family = families[familyId]
        firstSeen = {}  # (first name, birthday) -> first child ID with that pair

        for childId in sortIds(family.get("CHIL", set())):
            child = individuals.get(childId)

            if child is None:
                continue

            firstName = getFirstName(child.get("name", "NA"))
            birthday = child.get("birthday", "NA")

            # without both values a child cannot be compared
            if firstName == "NA" or birthday == "NA":
                continue

            key = (firstName, birthday)

            if key not in firstSeen:
                firstSeen[key] = childId
                continue

            line = child.get("BIRT_LINE", "NA")

            if line == "NA":
                line = getFamilyLine(family)

            # show the first name as written in the record, e.g. "Ava"
            displayName = child["name"].split("/")[0].split()[0]

            errors.append(
                f"ERROR: FAMILY: US25: {line}: {familyId}: "
                f"Children {firstSeen[key]} and {childId} have the same first name "
                f"({displayName}) and birth date ({birthday})"
            )


def validate_us26_corresponding_entries(families, individuals):
    """
    US26: Individual and family records must agree.
    - Every FAMS family in an individual record must list them as HUSB or WIFE.
    - Every FAMC family in an individual record must list them as a CHIL.
    - Every HUSB / WIFE in a family record must list that family as FAMS.
    - Every CHIL in a family record must list that family as FAMC.
    A reference to a record that does not exist is also reported.
    """
    # individual records -> family records
    for indId in sortIds(individuals.keys()):
        individual = individuals[indId]

        for familyId in sortIds(individual.get("spouse", set())):
            line = individual.get("FAMS_LINES", {}).get(familyId, "NA")
            family = families.get(familyId)

            if family is None:
                errors.append(
                    f"ERROR: INDIVIDUAL: US26: {line}: {indId}: "
                    f"Spouse in family {familyId} (FAMS), but family {familyId} does not exist"
                )
            elif indId not in (family.get("HUSB", "NA"), family.get("WIFE", "NA")):
                errors.append(
                    f"ERROR: INDIVIDUAL: US26: {line}: {indId}: "
                    f"Spouse in family {familyId} (FAMS), but {familyId} does not list "
                    f"{indId} as husband or wife"
                )

        for familyId in sortIds(individual.get("child", set())):
            line = individual.get("FAMC_LINES", {}).get(familyId, "NA")
            family = families.get(familyId)

            if family is None:
                errors.append(
                    f"ERROR: INDIVIDUAL: US26: {line}: {indId}: "
                    f"Child in family {familyId} (FAMC), but family {familyId} does not exist"
                )
            elif indId not in family.get("CHIL", set()):
                errors.append(
                    f"ERROR: INDIVIDUAL: US26: {line}: {indId}: "
                    f"Child in family {familyId} (FAMC), but {familyId} does not list "
                    f"{indId} as a child"
                )

    # family records -> individual records
    for familyId in sortIds(families.keys()):
        family = families[familyId]

        for role, label in (("HUSB", "husband"), ("WIFE", "wife")):
            spouseId = family.get(role, "NA")

            if spouseId == "NA":
                continue

            line = family.get(f"{role}_LINE", "NA")
            spouse = individuals.get(spouseId)

            if spouse is None:
                errors.append(
                    f"ERROR: FAMILY: US26: {line}: {familyId}: "
                    f"Lists {spouseId} as {label}, but individual {spouseId} does not exist"
                )
            elif familyId not in spouse.get("spouse", set()):
                errors.append(
                    f"ERROR: FAMILY: US26: {line}: {familyId}: "
                    f"Lists {spouseId} as {label}, but {spouseId} does not list "
                    f"{familyId} as a spouse family (FAMS)"
                )

        for childId in sortIds(family.get("CHIL", set())):
            line = family.get("CHIL_LINES", {}).get(childId, "NA")
            child = individuals.get(childId)

            if child is None:
                errors.append(
                    f"ERROR: FAMILY: US26: {line}: {familyId}: "
                    f"Lists {childId} as a child, but individual {childId} does not exist"
                )
            elif familyId not in child.get("child", set()):
                errors.append(
                    f"ERROR: FAMILY: US26: {line}: {familyId}: "
                    f"Lists {childId} as a child, but {childId} does not list "
                    f"{familyId} as a child family (FAMC)"
                )


############ USER STORY US31 & US32 LIST FUNCTIONS ##########

def validate_us31_list_living_single(individuals, families=None, today=None):
    """US31: List living people older than 30 who have never married.

    A person is never married when there are no spouse-family (FAMS) records.
    Calculate age using complete birthdays rather than the approximate age field.
    """
    if today is None:
        today = date.today().isoformat()

    # Reconcile both sides of the relationship: some intentionally invalid US26
    # records omit FAMS even though a family lists the person as a spouse.
    familySpouseIds = set()
    for family in (families or {}).values():
        for field in ("HUSB", "WIFE"):
            spouseId = family.get(field, "NA")
            if spouseId != "NA":
                familySpouseIds.add(spouseId)

    livingSingle = []
    for indId in sortIds(individuals.keys()):
        person = individuals[indId]
        birthday = person.get("birthday", "NA")
        if person.get("death", "NA") != "NA" or person.get("alive", "Y") == "N":
            continue
        if birthday in ("NA", "") or person.get("spouse", set()) or indId in familySpouseIds:
            continue
        if getAgeOnDate(birthday, today) > 30:
            livingSingle.append(indId)

    return livingSingle


def build_us31_living_single_table(individuals, families):
    """Format the US31 report using the project's common PrettyTable helper."""
    rows = [[indId, individuals[indId].get("name", "NA"),
             individuals[indId].get("birthday", "NA")]
            for indId in validate_us31_list_living_single(individuals, families)]
    return build_report_table("US31: Living Single Individuals (Over 30)",
                              ["ID", "Name", "Birth Date"], rows)


def validate_us32_list_multiple_births(families, individuals):
    """US32: List siblings sharing a birth date within the same family.

    Returns sorted (family ID, birth date, tuple of child IDs) groups of size >= 2.
    Shared dates in different families do not imply a multiple birth.
    """
    multipleBirths = []
    for familyId in sortIds(families.keys()):
        birthsByDate = {}
        for childId in families[familyId].get("CHIL", set()):
            person = individuals.get(childId)
            if person is None:
                continue
            birthday = person.get("birthday", "NA")
            if birthday in ("NA", ""):
                continue
            birthsByDate.setdefault(birthday, []).append(childId)

        for birthday, childIds in sorted(birthsByDate.items()):
            if len(childIds) >= 2:
                multipleBirths.append((familyId, birthday, tuple(sortIds(childIds))))

    return multipleBirths


def build_us32_multiple_births_table(families, individuals):
    """Format each multiple-birth group as one row, including its size."""
    rows = [[familyId, birthday, ", ".join(childIds), len(childIds)]
            for familyId, birthday, childIds
            in validate_us32_list_multiple_births(families, individuals)]
    return build_report_table("US32: Multiple Births",
                              ["Family ID", "Birth Date", "Children IDs", "Count"], rows)

############ USER STORY US21 & US22 VALIDATIONS ##########

def validSpouse(individualId, spouse, individuals):
    """
    Returns True if the husband is male / the wife is female
    Returns False if there is a gender mismatch
    Returns None when the individual does not exist
    """
    individual = individuals.get(individualId, {})
    if not individual:
        return None 
    gender = individual.get("gender", "NA")
    if spouse == "HUSB" and gender != "M":
        return False
    elif spouse == "WIFE" and gender != "F":
        return False
    else:
        return True

def validate_us21_correct_gender_for_role(families, individuals):
    """
    US21: Husband in family should be male and wife in family should be female.
    """

    for familyId in sortIds(families.keys()):
        family = families[familyId]
        familyLine = getFamilyLine(family)
        husbLine = family.get(f"HUSB_LINE", "NA")
        wifeLine = family.get(f"WIFE_LINE", "NA")

        husbandId = family.get("HUSB", "NA")
        wifeId = family.get("WIFE", "NA")

        if husbandId != "NA":
            # Corresponding entries are handled in US26. If validSpouse returns None, ignore
            # it to avoid a redundant error.
            if validSpouse(husbandId, "HUSB", individuals) == False:
                husbErrorLine = familyLine if husbLine == "NA" else husbLine
                errors.append(
                    f"ERROR: FAMILY: US21: {husbErrorLine}: {familyId}: "
                    f"Husband ({husbandId}) is not male."
                )

        if wifeId != "NA":
            if validSpouse(wifeId, "WIFE", individuals) == False:
                wifeErrorLine = familyLine if wifeLine == "NA" else wifeLine
                errors.append(
                    f"ERROR: FAMILY: US21: {wifeErrorLine}: {familyId}: "
                    f"Wife ({wifeId}) is not female."
                )

def validate_us22_unique_ids(allFamilies, allIndividuals):
    """
    US22: All individual IDs should be unique and all family IDs should be unique.

    The standard families and individuals dictionaries (used in all other stories) 
    cannot store multiple families/individuals that have the same ID. Standard parsing stores the
    most recent record in family_test.ged.
    
    Therefore, US22 uses allFamilies and allIndividuals to track records with duplicate IDs instead 

    allFamilies maps family ID -> array of line numbers for the corresponding family record(s).
    allIndividuals maps individual ID -> array of line numbers for the corresponding individual record(s).
    """
    for individualId, lineNumbers in allIndividuals.items():
        if (len(lineNumbers) > 1):
                repeatLineNums = ", ".join(map(str, lineNumbers))
                errors.append(
                    f"ERROR: INDIVIDUAL: US22: {repeatLineNums}: "
                    f"{individualId} is not a unique individual ID."
                )

    for familyId, lineNumbers in allFamilies.items():
        if (len(lineNumbers) > 1):
                repeatLineNums = ", ".join(map(str, lineNumbers))
                errors.append(
                    f"ERROR: FAMILY: US22: {repeatLineNums}: "
                    f"{familyId} is not a unique family ID."
                )


############ USER STORY US37 & US38 LIST FUNCTIONS ##########

def isLivingIndividual(indId, individuals):
    """True if indId has an individual record and no death date."""
    individual = individuals.get(indId)

    if individual is None:
        return False

    return individual.get("death", "NA") == "NA"


def validate_us37_list_recent_survivors(families, individuals, today=None):
    """
    US37: List all living spouses and descendants of people in a GEDCOM file
    who died in the last 30 days.

    This is a list/report story, not an error-validation story.
    It returns (deceased ID, survivor ID, relationship) tuples, where the
    relationship is "Spouse" or "Descendant".
    A spouse from a family with a divorce date is an ex-spouse, not a survivor.
    Each survivor is listed once per deceased person.
    `today` can be passed in for testing.
    """
    if today is None:
        today = date.today().isoformat()

    recentSurvivors = []

    # US36 already finds the people who died in the last 30 days
    for deceasedId in validate_us36_list_recent_deaths(individuals, today):
        listed = set()

        for familyId in sortIds(families.keys()):
            family = families[familyId]
            husbandId = family.get("HUSB", "NA")
            wifeId = family.get("WIFE", "NA")

            if husbandId == deceasedId:
                spouseId = wifeId
            elif wifeId == deceasedId:
                spouseId = husbandId
            else:
                continue

            if family.get("DIV", "NA") != "NA":
                continue

            if spouseId not in listed and isLivingIndividual(spouseId, individuals):
                recentSurvivors.append((deceasedId, spouseId, "Spouse"))
                listed.add(spouseId)

        for descendantId in sortIds(getDescendants(deceasedId, families)):
            # skip the deceased person, in case bad data has a cycle back to them
            if descendantId == deceasedId or descendantId in listed:
                continue

            if isLivingIndividual(descendantId, individuals):
                recentSurvivors.append((deceasedId, descendantId, "Descendant"))
                listed.add(descendantId)

    return recentSurvivors


def build_us37_recent_survivors_table(families, individuals, today=None):
    """
    Build output table for US37: List living spouses and descendants of
    people who died in the last 30 days.
    """
    rows = []

    for deceasedId, survivorId, relationship in validate_us37_list_recent_survivors(families, individuals, today):
        deceased = individuals[deceasedId]
        survivor = individuals[survivorId]

        rows.append([
            deceasedId,
            deceased.get("name", "NA"),
            deceased.get("death", "NA"),
            survivorId,
            survivor.get("name", "NA"),
            relationship
        ])

    return build_report_table(
        "US37: Recent Survivors (Deaths in Last 30 Days)",
        ["Deceased ID", "Deceased Name", "Death Date", "Survivor ID", "Survivor Name", "Relationship"],
        rows
    )


def getNextBirthday(birthday, today):
    """
    Date (YYYY-MM-DD) of the first birthday on or after today.
    A 29 FEB birthday falls on 28 FEB in years that are not leap years.
    """
    birthDate = date.fromisoformat(birthday)
    todayDate = date.fromisoformat(today)

    for year in (todayDate.year, todayDate.year + 1):
        try:
            nextBirthday = date(year, birthDate.month, birthDate.day)
        except ValueError:
            nextBirthday = date(year, 2, 28)

        if nextBirthday >= todayDate:
            return nextBirthday.isoformat()


def isWithinNextDays(dateString, today, days=30):
    """
    True if dateString is no more than `days` days after today.
    Today itself counts as upcoming. Past dates are not upcoming.
    """
    daysUntil = (date.fromisoformat(dateString) - date.fromisoformat(today)).days

    return 0 <= daysUntil <= days


def validate_us38_list_upcoming_birthdays(individuals, today=None):
    """
    US38: List all living people in a GEDCOM file whose birthdays occur
    in the next 30 days.

    This is a list/report story, not an error-validation story.
    It returns the IDs of all living individuals with a birthday in the
    next 30 days (today included).
    People born today or in the future have no birthday yet, so they are
    not listed (future births are already reported by US01).
    `today` can be passed in for testing.
    """
    if today is None:
        today = date.today().isoformat()

    upcomingBirthdays = []

    for indId in sortIds(individuals.keys()):
        individual = individuals[indId]
        birthday = individual.get("birthday", "NA")

        if birthday == "NA" or not isLivingIndividual(indId, individuals):
            continue

        if compareDates(birthday, today) >= 0:
            continue

        if isWithinNextDays(getNextBirthday(birthday, today), today, 30):
            upcomingBirthdays.append(indId)

    return upcomingBirthdays


def build_us38_upcoming_birthdays_table(individuals, today=None):
    """
    Build output table for US38: List living individuals with a birthday
    in the next 30 days.
    """
    if today is None:
        today = date.today().isoformat()

    rows = []

    for indId in validate_us38_list_upcoming_birthdays(individuals, today):
        individual = individuals[indId]

        rows.append([
            indId,
            individual.get("name", "NA"),
            individual.get("birthday", "NA"),
            getNextBirthday(individual["birthday"], today)
        ])

    return build_report_table(
        "US38: Upcoming Birthdays (Next 30 Days)",
        ["ID", "Name", "Birthday", "Next Birthday"],
        rows
    )


################

if __name__ == "__main__":
    main()
