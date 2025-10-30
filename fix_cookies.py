import json

COOKIE_FILE = "linkedin_cookies.json"

print(f"Attempting to clean {COOKIE_FILE}...")

try:
    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    cleaned_cookies = 0
    for cookie in cookies:
        # Check if sameSite is missing, null, or not one of the valid values
        if "sameSite" not in cookie or cookie.get("sameSite") not in ["Strict", "Lax", "None"]:
            # Set a safe default. "Lax" is the most common.
            cookie["sameSite"] = "Lax"
            cleaned_cookies += 1

    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2)

    if cleaned_cookies > 0:
        print(f"Success! Cleaned and fixed {cleaned_cookies} cookie entries.")
    else:
        print("Cookies already look good. No changes made.")

except FileNotFoundError:
    print(f"Error: {COOKIE_FILE} not found. Make sure it's in the same directory.")
except Exception as e:
    print(f"An error occurred: {e}")