"""Small self-authored PDF fixtures with real text objects and page boundaries."""

from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, StreamObject


def text_pdf(pages: list[str], *, password: str | None = None) -> bytes:
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        if text:
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            lines = escaped.splitlines()
            commands = ["BT /F1 10 Tf 40 750 Td"]
            for index, line in enumerate(lines):
                if index:
                    commands.append("0 -12 Td")
                commands.append(f"({line}) Tj")
            commands.append("ET")
            stream = StreamObject()
            stream.set_data("\n".join(commands).encode("ascii"))
            page[NameObject("/Contents")] = writer._add_object(stream)
    if password is not None:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def zero_page_pdf() -> bytes:
    output = BytesIO()
    PdfWriter().write(output)
    return output.getvalue()


def scanned_pdf() -> bytes:
    """An actual image-only page, not a blank page labeled as scanned."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    image = StreamObject()
    image.set_data(bytes([255, 0, 0]))
    image.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(1),
            NameObject("/Height"): NumberObject(1),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): writer._add_object(image)})}
    )
    contents = StreamObject()
    contents.set_data(b"q 200 0 0 200 40 40 cm /Im0 Do Q")
    page[NameObject("/Contents")] = writer._add_object(contents)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
