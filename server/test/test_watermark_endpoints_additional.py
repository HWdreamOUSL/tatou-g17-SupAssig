"""
Additional tests for watermarking endpoints to improve branch coverage.
These tests focus on input validation and authorization checks.
"""
import pytest


# Register test methods (same as main test file)
@pytest.fixture(scope="module", autouse=True)
def setup_test_methods():
    """Register mock watermarking methods for testing."""
    import watermarking_utils as WMUtils
    from simple_mock_watermarking import (
        TestWatermarkSuccess,
        TestWatermarkFails,
        TestWatermarkNotApplicable
    )

    # Add our test methods
    WMUtils.METHODS["test-success"] = TestWatermarkSuccess()
    WMUtils.METHODS["test-fail"] = TestWatermarkFails()
    WMUtils.METHODS["test-not-applicable"] = TestWatermarkNotApplicable()

    yield

    # Clean up
    WMUtils.METHODS.pop("test-success", None)
    WMUtils.METHODS.pop("test-fail", None)
    WMUtils.METHODS.pop("test-not-applicable", None)


@pytest.fixture
def test_pdf(tmp_path):
    """Create a simple test PDF file."""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\nxref\n0 1\ntrailer << /Root 1 0 R >>\n%%EOF\n"
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(pdf_content)
    return pdf_file


class TestCreateWatermarkAdditional:
    """Additional tests for create-watermark endpoint."""

    def test_missing_intended_for(self, client, auth_headers, test_pdf):
        """Test behavior when intended_for field is missing.

        Checks: Server validates that intended_for is a required field.
        """
        # Upload a document
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # Try to create watermark without intended_for field
        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               # Missing 'intended_for' field!
                               'secret': 'my-secret',
                               'key': 'my-key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_invalid_key_type(self, client, auth_headers, test_pdf):
        """Test what happens when key is wrong data type.

        Checks: Server validates that key must be string, not number or other type.
        """
        # Upload a document
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # Try with key as integer instead of string
        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'intended_for': 'alice@example.com',
                               'secret': 'my-secret',
                               'key': 12345  # Wrong type - should be string
                           },
                           headers=auth_headers)

        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_unauthorized_create_watermark(self, client, create_test_user, test_pdf):
        """Test what happens when user tries to watermark someone else's document.

        Checks: Users can only watermark their own documents, not other users' files.
        """
        # User 1 uploads a document
        user1 = create_test_user("_user1")
        login1 = client.post('/api/login', json={
            'email': user1['email'],
            'password': user1['password']
        })
        token1 = login1.get_json()['token']
        auth1 = {'Authorization': f'Bearer {token1}'}

        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth1,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # User 2 tries to watermark User 1's document
        user2 = create_test_user("_user2")
        login2 = client.post('/api/login', json={
            'email': user2['email'],
            'password': user2['password']
        })
        token2 = login2.get_json()['token']
        auth2 = {'Authorization': f'Bearer {token2}'}

        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'intended_for': 'alice@example.com',
                               'secret': 'secret',
                               'key': 'key'
                           },
                           headers=auth2)

        # Should return 404 (not 403) to avoid revealing document exists
        assert resp.status_code == 404


class TestReadWatermarkAdditional:
    """Additional tests for read-watermark endpoint."""

    def test_unauthorized_read_watermark(self, client, create_test_user, test_pdf):
        """Test what happens when user tries to read someone else's watermark.

        Checks: Users can only read watermarks from their own documents.
        """
        # User 1 creates and watermarks a document
        user1 = create_test_user("_user1")
        login1 = client.post('/api/login', json={
            'email': user1['email'],
            'password': user1['password']
        })
        token1 = login1.get_json()['token']
        auth1 = {'Authorization': f'Bearer {token1}'}

        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth1,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # Create watermark
        client.post(f'/api/create-watermark/{doc_id}',
                    json={
                        'method': 'test-success',
                        'intended_for': 'alice@example.com',
                        'secret': 'user1-secret',
                        'key': 'user1-key'
                    },
                    headers=auth1)

        # User 2 tries to read User 1's watermark
        user2 = create_test_user("_user2")
        login2 = client.post('/api/login', json={
            'email': user2['email'],
            'password': user2['password']
        })
        token2 = login2.get_json()['token']
        auth2 = {'Authorization': f'Bearer {token2}'}

        resp = client.post(f'/api/read-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'key': 'user1-key'
                           },
                           headers=auth2)

        # Should return 404 to not reveal document exists
        assert resp.status_code == 404

    def test_read_watermark_from_unwatermarked_file(self, client, auth_headers, test_pdf):
        """Test reading watermark from file that never had one added.

        Checks: Server handles case where we try to read watermark that doesn't exist.
        """
        # Upload document WITHOUT creating a watermark
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # Try to read watermark that doesn't exist
        resp = client.post(f'/api/read-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'key': 'any-key'
                           },
                           headers=auth_headers)

        # Should fail because no watermark was ever created
        assert resp.status_code == 400
        assert 'error' in resp.get_json()