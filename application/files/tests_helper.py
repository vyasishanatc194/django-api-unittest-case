# python imports
import io
import json
from PIL import Image
from django.http.request import validate_host
from reportlab.pdfgen import canvas


def create_test_file(fmt="png"):
    file = io.BytesIO()
    if fmt == "png":
        image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
        image.save(file, "png")
        file.name = "test.png"
        file.seek(0)
    elif fmt == "json":
        data = b'{"hello":"World"}'
        file.write(data)
        file.name = "test.json"
        file.seek(0)
    elif fmt == "csv":
        data = b"file_test\r\nhello\r\nworld"
        file.write(data)
        file.name = "test.csv"
        file.seek(0)
    elif fmt == "pdf":
        file = io.BytesIO()
        pdf = canvas.Canvas(file)
        pdf.drawString(100, 100, "Hello world.")
        pdf.showPage()
        pdf.save()
        file.name = "test.pdf"
        file.seek(0)
    return file


def create_file_with_bytes(data, filename):
    file = io.BytesIO(data)
    file.name = filename
    file.seek(0)
    return file
