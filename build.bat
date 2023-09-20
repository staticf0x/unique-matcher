rmdir /s /q build
rmdir /s /q dist
rmdir /s /q Output
python -m PyInstaller main.py --name UniqueMatcher -i um.ico

