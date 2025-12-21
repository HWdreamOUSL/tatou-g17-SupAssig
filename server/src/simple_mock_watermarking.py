from watermarking_method import WatermarkingMethod


class TestWatermarkSuccess(WatermarkingMethod):

    @property
    def name(self):
        """Method name for registration."""
        return "test-success"

    def get_usage(self):
        """Return usage description."""
        return "Test method that succeeds"

    def is_watermark_applicable(self, pdf, position=None):
        """Check if watermarking is applicable."""
        return True

    def add_watermark(self, pdf, secret, key, position=None):
        """Apply watermark to PDF."""
        from watermarking_method import load_pdf_bytes

        # Load the PDF bytes
        data = load_pdf_bytes(pdf)

        # Add a simple marker with the secret
        result = data + b"\n%%TEST_WM:" + secret.encode() + b"\n"
        return result

    def read_secret(self, pdf, key):
        """Read the secret back from watermarked PDF."""
        from watermarking_method import load_pdf_bytes

        data = load_pdf_bytes(pdf)
        marker = b"\n%%TEST_WM:"

        if marker in data:
            start = data.find(marker) + len(marker)
            end = data.find(b"\n", start)
            return data[start:end].decode()

        raise ValueError("No test watermark found in PDF")


class TestWatermarkFails(WatermarkingMethod):
    """Mock that always fails when applying."""

    @property
    def name(self):
        return "test-fail"

    def get_usage(self):
        return "Test method that fails"

    def is_watermark_applicable(self, pdf, position=None):
        """Always applicable, but will fail on apply."""
        return True

    def add_watermark(self, pdf, secret, key, position=None):
        """Simulate a failure during watermarking."""
        raise Exception("Watermarking failed on purpose")

    def read_secret(self, pdf, key):
        """Not used in failure tests."""
        raise Exception("Cannot read from failed watermark")


class TestWatermarkNotApplicable(WatermarkingMethod):
    """Mock that reports not applicable."""

    @property
    def name(self):
        return "test-not-applicable"

    def get_usage(self):
        return "Test method not applicable"

    def is_watermark_applicable(self, pdf, position=None):
        """Always return False to test this branch."""
        return False

    def add_watermark(self, pdf, secret, key, position=None):
        """Should not be called if applicability check works."""
        raise Exception("Should not be called - method not applicable")

    def read_secret(self, pdf, key):
        """Should not be called."""
        raise Exception("Should not be called - method not applicable")