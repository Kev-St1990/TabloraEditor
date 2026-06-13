from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
REQUIREMENTS = [
    line.strip()
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]


setup(
    name="csv-xlsx-editor",
    version="2.0",
    description="Desktop editor for CSV, XLSX, and XLSM spreadsheets",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    entry_points={
        "gui_scripts": [
            "csv-xlsx-editor=main:main",
        ],
    },
    python_requires=">=3.12",
)
