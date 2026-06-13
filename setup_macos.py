from pathlib import Path

from setuptools import find_packages, setup

from csv_xlsx_editor.config import APP_NAME, VERSION


ROOT = Path(__file__).resolve().parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

APP = ["main.py"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "CFBundleIdentifier": "com.csvxlsxeditor.app",
    },
    "packages": [
        "csv_xlsx_editor",
        "tksheet",
        "openpyxl",
        "pandas",
        "tkinterdnd2",
        "darkdetect",
    ],
}


setup(
    name="csv-xlsx-editor-macos",
    version=VERSION,
    description="macOS app bundle build for the CSV/XLSX editor",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    app=APP,
    options={"py2app": OPTIONS},
)
