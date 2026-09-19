from prettytable import PrettyTable
from datetime import date

# used to validate tags in main()
tags = {
    '0': {'INDI', 'FAM', 'HEAD', 'TRLR', 'NOTE'},
    '1': {'NAME', 'SEX', 'BIRT', 'DEAT', 'FAMC', 'FAMS', 'MARR', 'HUSB', 'WIFE', 'CHIL', 'DIV'},
    '2': {'DATE'}
}

def main():
    #instantiate tables
    individualsTable = PrettyTable(["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"])
    familiesTable = PrettyTable(["ID", "Married", "Divorced", "Husband ID", "Husband Name", "Wife ID", "Wife Name", "Children"])
    individualsTable.title = "Individuals"
    familiesTable.title = "Families"
    individuals = dict()

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
            elif level == '0' and indRecord:
                age = getAge(birthday, death)
                individualsTable.add_row([currentInd, name, gender, birthday, age, alive, death, str(child), str(spouse)])
                individuals[currentInd] = name
                alive = "Y"
                name = gender = birthday = age = death = child = spouse = "NA"
                if tag != "INDI":
                    indRecord = False
                else:
                    currentInd = arguments[0]

            #at the beginning OR end of a family record
            if tag == 'FAM' and not famRecord:
                famRecord = True
                currentFam = arguments[0]
            elif level == '0' and famRecord:
                familiesTable.add_row([currentFam, married, divorced, husbandId, husbandName, wifeId, wifeName, str(children)])
                married = divorced = husbandId = husbandName = wifeId = wifeName = children = "NA"
                if tag != "FAM":
                    famRecord = False
                else:
                    currentFam = arguments[0]

            #tag cases
            match tag:
                case "NAME":
                    name = " ".join(arguments)
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
                    match dateToUpdate:
                        case "BIRT":
                            if (prevDateLine == currLineNum - 1):
                                birthday = getDate(arguments)
                        case "DEAT":
                            if (prevDateLine == currLineNum - 1):
                                death = getDate(arguments)
                                alive = "N"
                        case "MARR":
                            if (prevDateLine == currLineNum - 1):
                                married = getDate(arguments)
                        case "DIV":
                            if (prevDateLine == currLineNum - 1):
                                divorced = getDate(arguments)
                case "HUSB":
                    husbandId = arguments[0]
                case "WIFE":
                    wifeId = arguments[0]
                case "CHIL":
                    children = set()
                    for child in arguments:
                        children.add(child)

            currLineNum += 1
         
    with open('output.txt', 'w') as outputFile:
        #put husband and wife names in families table
        for i in range(len(familiesTable._rows)):
            row = familiesTable._rows[i]
            husbandId = row[3]
            wifeId = row[5]
            familiesTable._rows[i][4] = individuals[husbandId]
            familiesTable._rows[i][6] = individuals[wifeId]

        outputFile.write(individualsTable.get_string())
        outputFile.write(familiesTable.get_string())

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
