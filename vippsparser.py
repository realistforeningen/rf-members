from collections import namedtuple
from openpyxl import load_workbook
from datetime import date
import sys

Transaction = namedtuple('Transaction', ['date', 'id', 'last_name', 'first_name', 'order_id', 'message', 'amount'])

def to_infinity(start=0):
    while True:
        yield start
        start += 1

def transactions(wb):
    sheet = wb['Salgsrapport']
    for i in to_infinity(9):
        row = sheet[i]
        if row[0].value == "Sum":
            break

        d, m, y = map(int, row[0].value.split("."))

        yield Transaction(
            date=date(y, m, d),
            id=str(int(row[1].value)),
            last_name=row[2].value,
            first_name=row[3].value,
            order_id=row[4].value,
            message=row[5].value,
            amount=int(row[6].value),
        )

def load_transactions(filename):
    wb = load_workbook(filename)
    return transactions(wb)

