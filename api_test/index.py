import os 
a = os.getcwd()

if(("\\youtube-downloader\\api_test") in a):
    ""
else:
    raise ValueError("Wrong Directory - You are not in the correct directory. Please run this script from the api_test directory.")

print("Running clean.py tests...")
import clean
print("\n")

# EOF

#import api