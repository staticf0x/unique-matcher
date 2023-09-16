print()
print("----- Checking installation -----")

print("Detecting packages...")

err = False

try:
    from unique_matcher.matcher.matcher import Matcher

    print("Core packages seem to be installed")
except:
    print("ERROR: Core packages not found, are they installed?")
    print("Hint: try running install.bat")

    err = True

print()
print("Detecting Tesseract...")

try:
    import pytesseract

    _ = pytesseract.get_tesseract_version()
    print("Tesseract detected!")
except:
    print("ERROR: Tesseract cannot be found, is it installed and in PATH?")
    print(
        "Hint: follow this guide to install and enable Tesseract: https://github.com/staticf0x/unique-matcher/wiki/Installation#install-tesseract-ocr"
    )

    err = True

print()

if not err:
    print("SUCCESS: All checks passed")
    print("You can now run um.bat to start the main application")
else:
    print("The installation is not complete, the main application will not work :(")

print()
