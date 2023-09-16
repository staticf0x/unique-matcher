"""Installation script."""
import os

from jinja2 import BaseLoader, Environment

from unique_matcher.constants import ITEM_DIR, ROOT_DIR

TEMPLATE = """#s::{
    Run screen.exe, {{ root }}
}"""

print("Creating AHK script...")

template = Environment(loader=BaseLoader).from_string(TEMPLATE)
rendered = template.render(root=ROOT_DIR)

with open("screenshot.ahk", "w") as fwrite:
    fwrite.write(rendered)

print("Checking for assets...")

if not os.path.exists(ITEM_DIR):
    print("Downloading assets...")

    import zipfile

    import gdown

    gdown.download(
        url="https://drive.google.com/uc?id=1AXhY537lV6BZeYjvPT3b6o-U9Cq-eqhC",
        output="items.zip",
    )

    with zipfile.ZipFile("items.zip", "r") as zf:
        zf.extractall()
else:
    print("Assets already downloaded")
