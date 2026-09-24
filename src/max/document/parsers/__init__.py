"""Parsers package for Module 24 — Document Intelligence."""

from max.document.parsers.base import BaseDocumentParser
from max.document.parsers.csv_parser import CsvDocumentParser
from max.document.parsers.docx_parser import DocxDocumentParser
from max.document.parsers.json_parser import JsonDocumentParser
from max.document.parsers.markdown_parser import MarkdownDocumentParser
from max.document.parsers.pdf_parser import PdfDocumentParser
from max.document.parsers.pptx_parser import PptxDocumentParser
from max.document.parsers.registry import DocumentParserRegistry
from max.document.parsers.text_parser import TextDocumentParser
from max.document.parsers.xlsx_parser import XlsxDocumentParser
from max.document.parsers.xml_parser import XmlDocumentParser

__all__ = [
    "BaseDocumentParser",
    "TextDocumentParser",
    "MarkdownDocumentParser",
    "CsvDocumentParser",
    "JsonDocumentParser",
    "XmlDocumentParser",
    "PdfDocumentParser",
    "DocxDocumentParser",
    "XlsxDocumentParser",
    "PptxDocumentParser",
    "DocumentParserRegistry",
]
