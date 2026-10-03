# Group 1 GEDCOM Project

## Development and Testing Instructions

### 1. Create a separate branch before making code changes

Before working on any user story, bug fix, or code update, create a new branch from the latest `main`.

```bash
git checkout main
git pull origin main
git checkout -b sprint2-yourname-usXX-usYY
```

Example:

```bash
git checkout -b sprint2-fj-us29-us30
```

Do not make changes directly on `main`.

---

### 2. Update the main GEDCOM code

All main GEDCOM parsing and user story logic should be added to:

```text
test_gedcom.py
```

For validation stories, the function should add an error message to the global `errors` list only when invalid GEDCOM data is found.

Example error formats:

```text
ERROR: INDIVIDUAL: US01: lineNumber: individualId: error details
ERROR: FAMILY: US05: lineNumber: familyId: error details
```

For list/report stories the function should return the expected list of individuals and should not add listing messages on Error lines to `output.txt`.

---

### 3. Update GEDCOM test data if needed

The main GEDCOM test input file is:

```text
family_test.ged
```

Use existing GEDCOM test data when possible.

Add new GEDCOM records only if the current file does not already contain enough data to test the new user story.

The GEDCOM file should continue to demonstrate all current and previous sprint stories.

---

### 4. Add or update unit tests

Each user story should have unit tests.

Recommended structure:

```text
test_us01_us02.py
test_us03_us04.py
test_us05_us10.py
test_us06_us07.py
test_us08_us09.py
test_us29_us30.py
```

Each test file should import the main GEDCOM code:

```python
import test_gedcom as gedcom
```

Before each test, clear the global `errors` list:

```python
def setUp(self):
    gedcom.errors.clear()
```

Unit tests should directly call the user story function and verify the expected result.

---

### 5. Run all unit tests before committing

After making any code change, run all unit tests from the project root:

```bash
python3 -m unittest discover -v
```

This command discovers and runs all test files that start with `test`.

You can also run one specific test file:

```bash
python3 -m unittest test_us29_us30.py -v
```

All tests should pass before pushing code or creating a Pull Request.

---

### 6. Run the GEDCOM program and regenerate `output.txt`

After unit tests pass, run the main GEDCOM program:

```bash
python3 test_gedcom.py family_test.ged
```

This generates or updates:

```text
output.txt
```

Review `output.txt` and make sure it includes:

```text
1. Individuals table
2. Families table
3. Expected ERROR or ANOMALY lines for validation stories
```

For list/report stories, verify the logic through unit tests unless the team agrees to include a separate report section in `output.txt`.

---

### 7. Check Git status before committing

Before committing, check which files changed:

```bash
git status
```

Do not commit generated Python cache files.

These files/folders should not be committed:

```text
__pycache__/
*.pyc
```

Make sure `.gitignore` includes:

```gitignore
__pycache__/
*.pyc
```

---

### 8. Commit only related changes

Stage only the files related to the user story or fix:

```bash
git add test_gedcom.py family_test.ged output.txt test_usXX_usYY.py
```

Example:

```bash
git add test_gedcom.py family_test.ged output.txt test_us29_us30.py
```

Then commit with a clear message:

```bash
git commit -m "Implement USXX and USYY validations"
```

Example:

```bash
git commit -m "Implement US29 and US30 list stories"
```

---

### 9. Push the branch and create a Pull Request

Push your branch:

```bash
git push origin sprint2-yourname-usXX-usYY
```

Example:

```bash
git push origin sprint2-fj-us29-us30
```

Create a Pull Request into `main`.

Before requesting review, make sure:

```text
1. All unit tests pass.
2. output.txt was regenerated.
3. The PR only includes relevant files.
4. The PR description explains what user stories were implemented.
5. The PR does not include __pycache__ or .pyc files.
```

---

### 10. Pull latest `main` before starting new work

Before starting another story or bug fix, always update local `main`:

```bash
git checkout main
git pull origin main
```

Then create a new branch for the next work item.

---

## Quick Commands

Run all unit tests:

```bash
python3 -m unittest discover -v
```

Run one specific test file:

```bash
python3 -m unittest test_us29_us30.py -v
```

Run the GEDCOM program:

```bash
python3 test_gedcom.py family_test.ged
```

Check changed files:

```bash
git status
```

Stage files for a story:

```bash
git add test_gedcom.py family_test.ged output.txt test_usXX_usYY.py
```

Commit changes:

```bash
git commit -m "Implement USXX and USYY validations"
```

Push branch:

```bash
git push origin branch-name
```

