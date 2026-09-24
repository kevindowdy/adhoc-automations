import openpyxl
from openpyxl.drawing.image import Image
from PIL import Image as PILImage
import io

import win32com.client as win32
from PIL import ImageGrab
import time

INPUT_FILE = rf"C:\Users\fbfepde\Documents\Temporary\FIG_P0_Vulnerabilities\report.xlsx"

OUTPUT_FILE = rf"C:\Users\fbfepde\Downloads\image.png"


excel = win32.Dispatch("Excel.Application")
wb = excel.Workbooks.Open(INPUT_FILE)
ws = wb.Worksheets("Vulnerability Report")

rng = ws.Range("A1:L12")

rng.CopyPicture(Appearance=1, Format=2)

time.sleep(1)

img = ImageGrab.grabclipboard()
img.save(OUTPUT_FILE)

wb.Close(False)
excel.Quit()
