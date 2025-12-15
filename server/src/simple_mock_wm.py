from watermarking_method import WatermarkingMethod


class TestWatermarkSuccess(WatermarkingMethod):
    
    @staticmethod
    def get_name():
        return "test-success"
    
    @staticmethod
    def get_usage():
        return "Test method that succeeds"
    
    @staticmethod
    def is_applicable(pdf, position=None):
        return True
    
    @staticmethod
    def apply(pdf, secret, key, position=None):
        #Read the PDF and add our secret at the end
        with open(pdf, 'rb') as f:
            data = f.read()
        # Add a simple marker with the secret
        result = data + b"\n%%TEST_WM:" + secret.encode() + b"\n"
        return result
    
    @staticmethod
    def read(pdf, key):
        # Read the secret back
        with open(pdf, 'rb') as f:
            data = f.read()
        marker = b"\n%%TEST_WM:"
        if marker in data:
            start = data.find(marker) + len(marker)
            end = data.find(b"\n", start)
            return data[start:end].decode()
        return None


class TestWatermarkFails(WatermarkingMethod):
    """Mock that always fails when applying."""
    
    @staticmethod
    def get_name():
        return "test-fail"
    
    @staticmethod
    def get_usage():
        return "Test method that fails"
    
    @staticmethod
    def is_applicable(pdf, position=None):
        return True
    
    @staticmethod
    def apply(pdf, secret, key, position=None):
        # Simulate a failure
        raise Exception("Watermarking failed on purpose")
    
    @staticmethod
    def read(pdf, key):
        return None


class TestWatermarkNotApplicable(WatermarkingMethod):
    """Mock that reports not applicable."""
    
    @staticmethod
    def get_name():
        return "test-not-applicable"
    
    @staticmethod
    def get_usage():
        return "Test method not applicable"
    
    @staticmethod
    def is_applicable(pdf, position=None):
        # Always return False to test this branch
        return False
    
    @staticmethod
    def apply(pdf, secret, key, position=None):
        raise Exception("Should not be called")
    
    @staticmethod
    def read(pdf, key):
        return None
