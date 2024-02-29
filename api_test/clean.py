# Description: Tests the clean function in the app module.

# Imports sys module and then appends the parent directory to the system path, in order to get the raw function.
import sys

from jinja2 import Undefined
sys.path.append('../')

# Imports clean and re functions from app module.
from app import clean, re

# Init overall feedback.
results = []
cleaned = []

# Test case 1: Literal string.
string = "asdf"

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test case 2: Special characters.
string = "asdf!@#$%^&*()_+"

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test case 3: Letters.

string = "asdf"

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test case 4: Empty string.

string = ""

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test case 5: Undefined string.

string = Undefined

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test case 6: None string.

string = None

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test case 7: Special characters.

string = "asdf!@#$%^&*()_+[][][__--^&?<>,./]|';\":"

cleaned_string = clean(string)

cleaned.append(cleaned_string)

# Test cases done, feedback.

num = 0
for word in cleaned:
    num = num + 1 # Track the numeration.
    if num < 4 or num > 6:
        if word == "asdf":
            print(f"[{num}/7] passed!")
        else:
            print(f"[{num}/7] failed!")
            print(f"Expected: asdf, got: {word}")
    else:
        if word == "":
            print(f"[{num}/7] passed!")
        else:
            print(f"[{num}/7] failed!")
            print(f"Expected: '', got: {word}")