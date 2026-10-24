"""Real LangChain PyPDFLoader / splitter tests using self-authored PDFs."""

import pytest
from casepilot.knowledge.errors import KnowledgeError
from casepilot.knowledge.pdf import chunk_pages, parse_pages
from pdf_fixtures import scanned_pdf, text_pdf, zero_page_pdf


def test_real_loader_retains_multiple_pages_and_cross_page_clause_boundaries():
    document = text_pdf(
        [
            "Article 1. Insurance liability begins on the effective date.\nA continued clause starts here.",
            "The same clause continues on page two.\nArticle 2. Repair invoice is required.",
        ]
    )
    pages = parse_pages(document)
    assert [page for page, _ in pages] == [1, 2]
    assert "liability" in pages[0][1]
    assert "invoice" in pages[1][1]
    chunks = chunk_pages(pages)
    assert [chunk["ordinal"] for chunk in chunks] == list(range(len(chunks)))
    assert any(chunk["page"] == 1 and "starts here" in chunk["content"] for chunk in chunks)
    assert any(chunk["page"] == 2 and "continues" in chunk["content"] for chunk in chunks)
    assert all(chunk["content"] in dict(pages)[chunk["page"]] for chunk in chunks)


def test_blank_page_does_not_fabricate_text_or_shift_page_numbers():
    pages = parse_pages(text_pdf(["", "Actual clause on second page."]))
    assert pages[0] == (1, "")
    chunks = chunk_pages(pages)
    assert chunks
    assert all(chunk["page"] == 2 for chunk in chunks)


@pytest.mark.parametrize(
    "content,code",
    [
        (b"", "INVALID_PDF"),
        (b"not a pdf", "INVALID_PDF"),
        (b"%PDF-1.7\nmalformed", "PDF_PARSE_FAILED"),
    ],
)
def test_invalid_pdf_errors_are_explicit(content, code):
    with pytest.raises(KnowledgeError) as caught:
        parse_pages(content)
    assert caught.value.code == code


@pytest.mark.parametrize(
    "kind,code",
    [
        ("empty", "PDF_NO_TEXT"),
        ("scanned", "PDF_NO_TEXT"),
        ("encrypted", "ENCRYPTED_PDF"),
        ("zero-pages", "PDF_PAGE_LIMIT"),
        ("too-many-pages", "PDF_PAGE_LIMIT"),
    ],
)
def test_unsupported_pdf_never_fakes_extraction(kind, code):
    content = {
        "empty": lambda: text_pdf([""]),
        "scanned": scanned_pdf,
        "encrypted": lambda: text_pdf(["Secret text"], password="private-password"),
        "zero-pages": zero_page_pdf,
        "too-many-pages": lambda: text_pdf(["Clause"] * 101),
    }[kind]()
    with pytest.raises(KnowledgeError) as caught:
        parse_pages(content)
    assert caught.value.code == code


def test_long_page_chunks_have_bounded_content_and_real_provenance():
    pages = parse_pages(text_pdf(["Invoice documents support repair cost. " * 100]))
    chunks = chunk_pages(pages)
    assert len(chunks) > 1
    assert all(0 < len(chunk["content"]) <= 800 for chunk in chunks)
    assert all(chunk["page"] == 1 for chunk in chunks)
    assert all(chunk["content"] in pages[0][1] for chunk in chunks)


def test_exactly_one_hundred_pages_is_supported():
    pages = parse_pages(text_pdf([f"Clause on page {index + 1}." for index in range(100)]))
    assert [page for page, _ in pages] == list(range(1, 101))
    assert "100" in pages[-1][1]
