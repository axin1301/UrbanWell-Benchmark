import os


# Configure your Google Street View API key before running these scripts.
# PowerShell example:
#   $env:GOOGLE_KEY_MY = "your_api_key"
GOOGLE_KEY_MY = os.getenv("GOOGLE_KEY_MY", "")

if not GOOGLE_KEY_MY:
    print("Warning: GOOGLE_KEY_MY is not set. Street View download scripts will not run until you configure it.")
