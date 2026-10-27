"""Self-authored ASCII text PDFs for reproducible software acceptance corpora."""

from io import BytesIO
from textwrap import wrap

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject


def corpus_pdf(pages):
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
        lines = ["BT /F1 10 Tf 40 750 Td"]
        for index, line in enumerate(wrap(text, width=85)):
            if index:
                lines.append("0 -14 Td")
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            lines.append(f"({escaped}) Tj")
        lines.append("ET")
        stream = StreamObject()
        stream.set_data("\n".join(lines).encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    result = BytesIO()
    writer.write(result)
    return result.getvalue()
