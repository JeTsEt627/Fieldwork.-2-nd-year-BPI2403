"""Юнит-тесты валидации загружаемых файлов (BE-02)."""

import pytest

from app.core.config import settings
from app.core.exceptions import EmptyFileError, FileTooLargeError, UnsupportedFormatError
from app.services.file_validation import (
    get_file_extension,
    validate_extension,
    validate_size,
    validate_upload,
)


class TestGetFileExtension:
    def test_returns_extension_lowercase(self):
        assert get_file_extension("report.PDF") == "pdf"

    def test_returns_extension_docx(self):
        assert get_file_extension("document.docx") == "docx"

    def test_returns_empty_string_for_no_extension(self):
        assert get_file_extension("noextfile") == ""

    def test_handles_empty_name(self):
        assert get_file_extension("") == ""

    def test_handles_multiple_dots(self):
        assert get_file_extension("my.archive.file.pdf") == "pdf"


class TestValidateExtension:
    def test_accepts_pdf(self):
        assert validate_extension("report.pdf") == "pdf"

    def test_accepts_PDF_uppercase(self):
        assert validate_extension("REPORT.PDF") == "pdf"

    def test_accepts_docx(self):
        assert validate_extension("thesis.docx") == "docx"

    def test_rejects_txt(self):
        with pytest.raises(UnsupportedFormatError):
            validate_extension("notes.txt")

    def test_rejects_png(self):
        with pytest.raises(UnsupportedFormatError):
            validate_extension("image.png")

    def test_rejects_no_extension(self):
        with pytest.raises(UnsupportedFormatError):
            validate_extension("noextension")

    def test_rejects_exe(self):
        with pytest.raises(UnsupportedFormatError):
            validate_extension("malware.exe")


class TestValidateSize:
    def test_accepts_normal_size(self):
        validate_size(1024)  # 1 KB — не должна бросать исключений

    def test_accepts_exactly_max_size(self):
        validate_size(settings.max_upload_size_bytes)

    def test_rejects_empty_file(self):
        with pytest.raises(EmptyFileError):
            validate_size(0)

    def test_rejects_negative_size(self):
        with pytest.raises(EmptyFileError):
            validate_size(-1)

    def test_rejects_oversized_file(self):
        with pytest.raises(FileTooLargeError):
            validate_size(settings.max_upload_size_bytes + 1)

    def test_rejects_very_large_file(self):
        with pytest.raises(FileTooLargeError):
            validate_size(100 * 1024 * 1024)  # 100 МБ


class TestValidateUpload:
    def test_valid_pdf(self):
        ext = validate_upload("report.pdf", 1024, "application/pdf")
        assert ext == "pdf"

    def test_valid_docx(self):
        ext = validate_upload(
            "doc.docx",
            1024,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert ext == "docx"

    def test_none_content_type_is_accepted(self):
        ext = validate_upload("report.pdf", 1024, None)
        assert ext == "pdf"

    def test_octet_stream_accepted_for_docx(self):
        ext = validate_upload("doc.docx", 1024, "application/octet-stream")
        assert ext == "docx"

    def test_rejects_mismatched_content_type(self):
        with pytest.raises(UnsupportedFormatError):
            validate_upload("report.pdf", 1024, "image/png")

    def test_rejects_wrong_extension(self):
        with pytest.raises(UnsupportedFormatError):
            validate_upload("virus.exe", 1024, "application/octet-stream")

    def test_rejects_empty_file(self):
        with pytest.raises(EmptyFileError):
            validate_upload("report.pdf", 0, "application/pdf")

    def test_rejects_too_large_file(self):
        with pytest.raises(FileTooLargeError):
            validate_upload("report.pdf", 50 * 1024 * 1024, "application/pdf")
