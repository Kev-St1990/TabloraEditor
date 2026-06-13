import csv
from openpyxl import load_workbook

class FileManager:
    def load_csv(self, path, delimiter=";"):
        with open(path, encoding="utf-8-sig", newline="") as f:
            return list(csv.reader(f, delimiter=delimiter))

    def load_xlsx(self, path):
        wb = load_workbook(path)
        return wb
