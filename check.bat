@echo off

echo ---- Running basic checks ----
echo Detecting Python...

python --version 2>NUL

if errorlevel 1 (
	echo Python not installed!
) else (
	echo Python detected successfully!

	python check.py
)
pause