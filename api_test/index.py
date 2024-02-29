import os 
a = os.getcwd()
string = ""

if(("\\youtube-downloader\\api_test") in a):
    ""
else:
    print("Wrn: Either triggered by workflow (can safely ignore) or your not in the correct directory.")

print("Running clean.py tests...")
print("\n")
import clean
error_string = string + clean.string
print("\n")

if error_string == "":
    print("All test cases passed!")
else:
    raise ValueError(f"Test case failed: {error_string}")
# EOF

#import api