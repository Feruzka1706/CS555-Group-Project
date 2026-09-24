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

# used to validate tags in main()
tags = {
    '0': {'INDI', 'FAM', 'HEAD', 'TRLR', 'NOTE'},
    '1': {'NAME', 'SEX', 'BIRT', 'DEAT', 'FAMC', 'FAMS', 'MARR', 'HUSB', 'WIFE', 'CHIL', 'DIV'},
    '2': {'DATE'}
}

# any errors in the gedcom file will be added to this array.
# these will be printed in the output.txt file.
errors = []

def main():
    #instantiate tables
    individualsTable = PrettyTable(["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"])
    familiesTable = PrettyTable(["ID", "Married", "Divorced", "Husband ID", "Husband Name", "Wife ID", "Wife Name", "Children"])
    individualsTable.title = "Individuals"
    familiesTable.title = "Families"
    individuals = dict() #store all individuals
    families = dict() #store all families

    with open('family_test.ged', mode='r', encoding='utf-8-sig') as inputFile:
        currLineNum = 0 #this is used to make sure dates correspond to the line above it

        #instantiate values
        alive = "Y"
        name = gender = birthday = age = death = child = spouse = "NA" #individual row
        married = divorced = husbandId = husbandName = wifeId = wifeName = children = "NA" #family row

        indRecord = False
        famRecord = False
        currentInd = ""
        currentFam = ""
        dateToUpdate = ""
        prevDateLine = -1

        for line in inputFile:
            line = line.strip()
            if line == '':
                continue
            level, tag, *arguments = line.split()

            if len(arguments) > 0 and level == '0' and (arguments[0] == 'INDI' or arguments[0] == 'FAM'):
                tempTag = tag
                tag = arguments[0]
                arguments[0] = tempTag
            #if this is not a valid tag, ignore this tag
            if level not in tags or tag not in tags[level]:
                currLineNum += 1
                continue

            #at the beginning OR end of an individual record
            if tag == 'INDI' and not indRecord:
                indRecord = True
                currentInd = arguments[0]
                individuals[currentInd] = dict()
            elif level == '0' and indRecord:
                age = getAge(birthday, death)
                #add row to individuals table
                individualsTable.add_row([currentInd, name, gender, birthday, age, alive, death, str(child), str(spouse)])
                #update individuals dict
                individuals[currentInd].update({
                    "age": age,
                    "gender": gender,
                    "birthday": birthday,
                    "alive": alive,
                    "death": death,
                    "child": child,
                    "spouse": spouse
                })
                alive = "Y"
                name = gender = birthday = age = death = child = spouse = "NA"
                if tag != "INDI":
                    #new record is not an individual record
                    indRecord = False
                else:
                    #new individual record found
                    currentInd = arguments[0]
                    individuals[currentInd] = dict()

            #at the beginning OR end of a family record
            if tag == 'FAM' and not famRecord:
                famRecord = True
                currentFam = arguments[0]
                families[currentFam] = {
                    "HUSB": "",
                    "WIFE": "",
                    "CHIL": set(),
                    "MARR": "",
                    "DIV": ""
                }
            elif level == '0' and famRecord:
                familiesTable.add_row([currentFam, married, divorced, husbandId, husbandName, wifeId, wifeName, str(children)])

                #check for errors AFTER looking through whole fam record
                if (compareDates(married, date.today().isoformat()) > 0):
                    errors.append(f"Error US01: Marriage date of {husbandName} ({husbandId}) and {wifeName} ({wifeId}) from Family {currentFam} occurs after current date")
                if (divorced != 'NA' and compareDates(divorced, date.today().isoformat()) > 0):
                    errors.append(f"Error US01: Divorce date of {husbandName} ({husbandId}) and {wifeName} ({wifeId}) from Family {currentFam} occurs after current date")

                married = divorced = husbandId = husbandName = wifeId = wifeName = children = "NA"
                if tag != "FAM":
                    #next record is not a family record
                    famRecord = False
                else:
                    #new family record found
                    currentFam = arguments[0]
                    families[currentFam] = {
                        "HUSB": "",
                        "WIFE": "",
                        "CHIL": set(),
                        "MARR": "",
                        "DIV": ""
                    }

            #tag cases
            match tag:
                case "NAME":
                    name = " ".join(arguments)
                    individuals[currentInd]["name"] = name #name can be accessed in the below checks
                case "SEX":
                    gender = arguments[0]
                case "FAMC":
                    if (child == 'NA'):
                        child = {arguments[0]}
                    else:
                        child.add(arguments[0])
                case "FAMS":
                    if (spouse == 'NA'):
                        spouse = {arguments[0]}
                    else:
                        spouse.add(arguments[0])
                case "BIRT" | "DEAT" | "MARR" | "DIV":
                    dateToUpdate = tag
                    prevDateLine = currLineNum
                case "DATE":
                    gedcomDate = getDate(arguments)
                    today = date.today().isoformat()
                    match dateToUpdate:
                        case "BIRT":
                            if (compareDates(gedcomDate, today) > 0):
                                errors.append(f"Error US01: Birth date of {individuals[currentInd]['name']} ({currentInd}) occurs after current date")
                            if (prevDateLine == currLineNum - 1):
                                birthday = gedcomDate
                        case "DEAT":
                            if (compareDates(gedcomDate, today) > 0):
                                errors.append(f"Error US01: Death date of {individuals[currentInd]['name']} ({currentInd}) occurs after current date")
                            if (prevDateLine == currLineNum - 1):
                                death = gedcomDate
                                alive = "N"
                        case "MARR":
                            families[currentFam]["MARR"] = gedcomDate
                            if (prevDateLine == currLineNum - 1):
                                married = gedcomDate
                        case "DIV":
                            families[currentFam]["DIV"] = gedcomDate
                            if (prevDateLine == currLineNum - 1):
                                divorced = gedcomDate
                case "HUSB":
                    husbandId = arguments[0]
                    husbandName = individuals[husbandId]["name"]
                    families[currentFam]["HUSB"] = husbandId
                case "WIFE":
                    wifeId = arguments[0]
                    wifeName = individuals[wifeId]["name"]
                    families[currentFam]["WIFE"] = wifeId
                case "CHIL":
                    children = set()
                    for child in arguments:
                        children.add(child)
                        families[currentFam]["CHIL"].add(child)

            currLineNum += 1
         
    with open('output.txt', 'w') as outputFile:
        # put husband and wife names in families table (just in case individuals were defined after families in the gedcom file)
        for i in range(len(familiesTable._rows)):
            row = familiesTable._rows[i]
            husbandId = row[3]
            wifeId = row[5]
            familiesTable._rows[i][4] = individuals[husbandId]["name"]
            familiesTable._rows[i][6] = individuals[wifeId]["name"]

        # make long columns wrap so the table is not too wide
        individualsTable.max_width["Name"] = 18
        individualsTable.max_width["Child"] = 12
        individualsTable.max_width["Spouse"] = 15

        familiesTable.max_width["Husband Name"] = 18
        familiesTable.max_width["Wife Name"] = 18
        familiesTable.max_width["Children"] = 12

        # write to output.txt
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
    if (len(day) == 1):
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
    if (days < 0):
        return -1
    elif (days > 0):
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

################

if __name__ == "__main__":
    main()
