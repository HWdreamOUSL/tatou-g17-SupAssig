"""
Tests for watermarking endpoints.
Testing create-watermark and read-watermark routes.
"""
import pytest
import io


# Register our test methods before running tests
@pytest.fixture(scope="module", autouse=True)
def setup_test_methods():
    import watermarking_utils as WMUtils
    from simple_mock_watermarking import TestWatermarkSuccess, TestWatermarkFails, TestWatermarkNotApplicable

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
    """Make a simple PDF file for testing."""
    pdf = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\nxref\n0 1\ntrailer << /Root 1 0 R >>\n%%EOF\n"
    path = tmp_path / "test.pdf"
    path.write_bytes(pdf)
    return path


class TestCreateWatermark:
    """Tests for POST /api/create-watermark endpoint."""

    def test_basic_success(self, client, auth_headers, test_pdf):
        """Test creating watermark with valid data."""
        # First upload a document
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # Now create watermark
        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'intended_for': 'alice@test.com',
                               'secret': 'my-secret',
                               'key': 'my-key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['documentid'] == doc_id
        assert 'link' in data

    def test_missing_document_id(self, client, auth_headers):
        """Test error when no document ID provided."""
        resp = client.post('/api/create-watermark',
                           json={
                               'method': 'test-success',
                               'intended_for': 'alice@test.com',
                               'secret': 'secret',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_invalid_document_id(self, client, auth_headers):
        """Invalid document ID via query parameter (handled in route)."""
        resp = client.post(
            '/api/create-watermark?id=abc',
            json={
                'method': 'test-success',
                'intended_for': 'alice@test.com',
                'secret': 'secret',
                'key': 'key'
            },
            headers=auth_headers
        )

        assert resp.status_code == 400

    # Same for read-watermark test:
    def test_invalid_document_id(self, client, auth_headers):
        """Invalid document ID in path never reaches handler (Flask routing)."""
        resp = client.post('/api/read-watermark/abc',
                           json={
                               'method': 'test-success',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 405

    def test_missing_method(self, client, auth_headers, test_pdf):
        """Test error when method field missing."""
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'intended_for': 'alice@test.com',
                               'secret': 'secret',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_missing_secret(self, client, auth_headers, test_pdf):
        """Test error when secret field missing."""
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'intended_for': 'alice@test.com',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_method_not_applicable(self, client, auth_headers, test_pdf):
        """Test error when watermark method not applicable."""
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-not-applicable',
                               'intended_for': 'alice@test.com',
                               'secret': 'secret',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_watermarking_fails(self, client, auth_headers, test_pdf):
        """Test error when watermarking process fails."""
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        resp = client.post(f'/api/create-watermark/{doc_id}',
                           json={
                               'method': 'test-fail',
                               'intended_for': 'alice@test.com',
                               'secret': 'secret',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 500

    def test_no_auth(self, client):
        """Test error when not authenticated."""
        resp = client.post('/api/create-watermark/1',
                           json={
                               'method': 'test-success',
                               'intended_for': 'alice@test.com',
                               'secret': 'secret',
                               'key': 'key'
                           })

        assert resp.status_code == 401


class TestReadWatermark:
    """Tests for POST /api/read-watermark endpoint."""

    def test_read_success(self, client, auth_headers, test_pdf):
        """Test reading watermark successfully."""
        # Upload document
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        # Create watermark
        secret = 'test-secret-123'
        client.post(f'/api/create-watermark/{doc_id}',
                    json={
                        'method': 'test-success',
                        'intended_for': 'alice@test.com',
                        'secret': secret,
                        'key': 'test-key'
                    },
                    headers=auth_headers)

        # Read it back
        resp = client.post(f'/api/read-watermark/{doc_id}',
                           json={
                               'method': 'test-success',
                               'key': 'test-key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['secret'] == secret

    def test_missing_document_id(self, client, auth_headers):
        """Test error when no document ID provided."""
        resp = client.post('/api/read-watermark',
                           json={
                               'method': 'test-success',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_invalid_document_id(self, client, auth_headers):
        """Test error with invalid document ID."""
        resp = client.post('/api/read-watermark/abc',
                           json={
                               'method': 'test-success',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_document_not_found(self, client, auth_headers):
        """Test error when document doesn't exist."""
        resp = client.post('/api/read-watermark/99999',
                           json={
                               'method': 'test-success',
                               'key': 'key'
                           },
                           headers=auth_headers)

        assert resp.status_code == 404

    def test_missing_method(self, client, auth_headers, test_pdf):
        """Test error when method field missing."""
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        resp = client.post(f'/api/read-watermark/{doc_id}',
                           json={'key': 'key'},
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_missing_key(self, client, auth_headers, test_pdf):
        """Test error when key field missing."""
        with open(test_pdf, 'rb') as f:
            resp = client.post('/api/upload-document',
                               data={'file': (f, 'test.pdf')},
                               headers=auth_headers,
                               content_type='multipart/form-data')
        doc_id = resp.get_json()['id']

        resp = client.post(f'/api/read-watermark/{doc_id}',
                           json={'method': 'test-success'},
                           headers=auth_headers)

        assert resp.status_code == 400

    def test_no_auth(self, client):
        """Test error when not authenticated."""
        resp = client.post('/api/read-watermark/1',
                           json={
                               'method': 'test-success',
                               'key': 'key'
                           })

        assert resp.status_code == 401
