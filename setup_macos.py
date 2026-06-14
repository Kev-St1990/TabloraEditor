from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).resolve().parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
APP_BUNDLE_NAME = "Tablora Editor"
APP_DISPLAY_NAME = "Tablora Editor"
APP_VERSION = "2.0.0"

APP = ["main.py"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "CFBundleName": APP_BUNDLE_NAME,
        "CFBundleDisplayName": APP_DISPLAY_NAME,
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "CFBundleIdentifier": "com.tablora.editor",
    },
    "packages": [
        "tablora",
        "tksheet",
        "openpyxl",
        "pandas",
        "tkinterdnd2",
        "darkdetect",
    ],
}


setup(
    name="tablora-macos",
    version=APP_VERSION,
    description="macOS app bundle build for Tablora",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    app=APP,
    options={"py2app": OPTIONS},
)
