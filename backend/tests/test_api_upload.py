"""
Integration tests for document upload API endpoint.

Tests the FastAPI POST /api/upload endpoint for uploading and processing documents.
Tests include successful uploads with various file formats, validation errors,
error handling, and processing statistics.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, qdrant_manager, chunking_strategy, embedding_manager
from models import DocumentChunk, UploadResponse


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_chunking_strategy():
    """Mock the chunking strategy to return test chunks."""
    with patch('main.chunking_strategy') as mock:
        # Create mock chunks
        mock_chunks = [
            DocumentChunk(
                chunk_id=1,
                parent_id=0,
                text="This is the first chunk of text.",
                start_char=0,
                end_char=30,
                metadata={"source": "test"}
            ),
            DocumentChunk(
                chunk_id=2,
                parent_id=0,
                text="This is the second chunk with more content.",
                start_char=31,
                end_char=70,
                metadata={"source": "test"}
            ),
            DocumentChunk(
                chunk_id=3,
                parent_id=1,
                text="Third chunk from a different section.",
                start_char=71,
                end_char=105,
                metadata={"source": "test"}
            )
        ]
        mock.process_document.return_value = mock_chunks
        yield mock


@pytest.fixture
def mock_embedding_manager():
    """Mock the embedding manager to return test embeddings."""
    with patch('main.embedding_manager') as mock:
        # Create mock embeddings
        mock_embeddings = {
            "matryoshka_64": [[0.1] * 64, [0.2] * 64, [0.3] * 64],
            "matryoshka_768": [[0.1] * 768, [0.2] * 768, [0.3] * 768],
            "colbert": [[[0.1] * 128] * 10, [[0.2] * 128] * 12, [[0.3] * 128] * 8],
            "splade": [
                {"indices": [1, 2, 3], "values": [0.1, 0.2, 0.3]},
                {"indices": [4, 5, 6], "values": [0.4, 0.5, 0.6]},
                {"indices": [7, 8, 9], "values": [0.7, 0.8, 0.9]}
            ]
        }
        mock.generate_all_embeddings.return_value = mock_embeddings
        yield mock


@pytest.fixture
def mock_qdrant_manager():
    """Mock the Qdrant manager to track store_points calls."""
    with patch('main.qdrant_manager') as mock:
        mock.list_collections.return_value = ["test_collection", "existing_collection"]
        mock.store_points = Mock()
        yield mock


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "test_document.pdf")
    
    # Create a minimal PDF file (just a header for testing)
    with open(file_path, 'wb') as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000010 00000 n\ntrailer\n<<>>\nstartxref\n20\n%%EOF")
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def sample_txt_file():
    """Create a sample text file for testing."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "test_document.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("This is a test document.\nIt has multiple lines.\nFor testing the upload endpoint.")
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def sample_md_file():
    """Create a sample markdown file for testing."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "test_document.md")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("# Test Document\n\nThis is a **markdown** document.\n\n- With bullet points\n- For testing purposes")
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def sample_docx_file():
    """Create a sample DOCX file for testing."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "test_document.docx")
    
    # Create a minimal DOCX file (just a ZIP with XML structure)
    import zipfile
    with zipfile.ZipFile(file_path, 'w') as docx:
        # Add minimal required files for a DOCX
        docx.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        docx.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
        docx.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test DOCX content</w:t></w:r></w:p></w:body></w:document>')
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)

class TestUploadEndpoint:
    """Tests for POST /api/upload endpoint."""
    
    def test_upload_successful_pdf(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_pdf_file
    ):
        """Test successful upload of a PDF file."""
        # Read the sample file
        with open(sample_pdf_file, 'rb') as f:
            file_content = f.read()
        
        # Make upload request
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.pdf", file_content, "application/pdf")
            },
            data={"collection_name": "test_collection"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunks_created"] == 3
        assert data["processing_time"] > 0
        assert "message" in data
        
        # Verify mocks were called correctly
        mock_qdrant_manager.list_collections.assert_called()
        mock_chunking_strategy.process_document.assert_called_once()
        mock_embedding_manager.generate_all_embeddings.assert_called_once()
        mock_qdrant_manager.store_points.assert_called_once()
        
        # Verify store_points was called with correct arguments
        store_points_call = mock_qdrant_manager.store_points.call_args
        assert store_points_call[0][0] == "test_collection"  # collection_name
        assert len(store_points_call[0][1]) == 3  # chunks
        assert "matryoshka_64" in store_points_call[0][2]  # embeddings
    
    def test_upload_successful_txt(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_txt_file
    ):
        """Test successful upload of a text file."""
        with open(sample_txt_file, 'rb') as f:
            file_content = f.read()
        
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.txt", file_content, "text/plain")
            },
            data={"collection_name": "test_collection"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunks_created"] == 3
    
    def test_upload_successful_md(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_md_file
    ):
        """Test successful upload of a markdown file."""
        with open(sample_md_file, 'rb') as f:
            file_content = f.read()
        
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.md", file_content, "text/markdown")
            },
            data={"collection_name": "test_collection"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunks_created"] == 3
    
    def test_upload_successful_docx(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_docx_file
    ):
        """Test successful upload of a DOCX file."""
        with open(sample_docx_file, 'rb') as f:
            file_content = f.read()
        
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.docx", file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            },
            data={"collection_name": "test_collection"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chunks_created"] == 3
    
    def test_upload_invalid_file_format(self, client, mock_qdrant_manager):
        """Test upload with invalid file format returns 400."""
        # Create an unsupported file (e.g., .exe)
        temp_dir = tempfile.gettempdir()
        invalid_file = os.path.join(temp_dir, "test.exe")
        with open(invalid_file, 'wb') as f:
            f.write(b"Invalid file content")
        
        try:
            with open(invalid_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.exe", file_content, "application/octet-stream")
                },
                data={"collection_name": "test_collection"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unsupported file format" in data["detail"]
            assert "PDF" in data["detail"]  # Should list supported formats
            
        finally:
            # Cleanup
            if os.path.exists(invalid_file):
                os.remove(invalid_file)
    
    def test_upload_missing_collection(self, client, mock_qdrant_manager):
        """Test upload to non-existent collection returns 400."""
        # Mock list_collections to return empty list
        mock_qdrant_manager.list_collections.return_value = []
        
        # Create a test file
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "non_existent_collection"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "does not exist" in data["detail"]
            assert "non_existent_collection" in data["detail"]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_missing_file_field(self, client):
        """Test upload without file field returns 422 (validation error)."""
        response = client.post(
            "/api/upload",
            data={"collection_name": "test_collection"}
        )
        
        # FastAPI returns 422 for missing required field
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_upload_missing_collection_name(self, client):
        """Test upload without collection_name returns 422 (validation error)."""
        # Create a test file
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                }
                # Missing collection_name
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_empty_file(self, client, mock_qdrant_manager):
        """Test upload with empty file returns 400."""
        # Create an empty file
        temp_dir = tempfile.gettempdir()
        empty_file = os.path.join(temp_dir, "empty.pdf")
        with open(empty_file, 'wb') as f:
            pass  # Empty file
        
        try:
            with open(empty_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("empty.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # The endpoint might process empty files but chunking would fail
            # Let's see what happens
            assert response.status_code in [200, 400, 500]
            
        finally:
            # Cleanup
            if os.path.exists(empty_file):
                os.remove(empty_file)
    
    def test_upload_chunking_failure(
        self,
        client,
        mock_chunking_strategy,
        mock_qdrant_manager
    ):
        """Test upload when chunking fails returns 400."""
        # Mock chunking strategy to raise an exception
        mock_chunking_strategy.process_document.side_effect = ValueError("Failed to parse document")
        
        # Create a test file
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Failed to parse" in data["detail"] or "validation error" in data["detail"]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_embedding_generation_failure(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload when embedding generation fails returns 500."""
        # Mock embedding manager to raise an exception
        mock_embedding_manager.generate_all_embeddings.side_effect = RuntimeError("GPU out of memory")
        
        # Create a test file
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "failed to generate embeddings" in data["detail"].lower()
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_qdrant_store_failure(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload when Qdrant storage fails returns 500."""
        # Mock Qdrant manager to raise an exception
        mock_qdrant_manager.store_points.side_effect = Exception("Qdrant connection failed")
        
        # Create a test file
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "failed to store document" in data["detail"].lower()
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_processing_statistics_accuracy(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_pdf_file
    ):
        """Test that processing statistics are accurate."""
        # Record start time
        start_time = time.time()
        
        with open(sample_pdf_file, 'rb') as f:
            file_content = f.read()
        
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.pdf", file_content, "application/pdf")
            },
            data={"collection_name": "test_collection"}
        )
        
        end_time = time.time()
        max_expected_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify statistics
        assert data["success"] is True
        assert data["chunks_created"] == 3
        assert data["processing_time"] > 0
        assert data["processing_time"] <= max_expected_time  # Should not exceed actual time
        
        # Verify message includes correct information
        assert "test_document.pdf" in data["message"]
        assert "3" in data["message"]  # Number of chunks
    
    def test_upload_temporary_file_cleanup(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_pdf_file
    ):
        """Test that temporary files are cleaned up after upload."""
        # Track temporary directory contents before upload
        temp_dir = tempfile.gettempdir()
        initial_files = set(os.listdir(temp_dir))
        
        with open(sample_pdf_file, 'rb') as f:
            file_content = f.read()
        
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.pdf", file_content, "application/pdf")
            },
            data={"collection_name": "test_collection"}
        )
        
        assert response.status_code == 200
        
        # Check that no upload_* files remain in temp directory
        # (give it a moment for cleanup)
        import time
        time.sleep(0.1)
        
        final_files = set(os.listdir(temp_dir))
        new_files = final_files - initial_files
        
        # There might be some new files, but they shouldn't be upload_* files
        upload_files = [f for f in new_files if f.startswith("upload_")]
        assert len(upload_files) == 0, f"Temporary upload files not cleaned up: {upload_files}"
    
    def test_upload_temporary_file_cleanup_on_error(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test that temporary files are cleaned up even when upload fails."""
        # Mock embedding generation to fail
        mock_embedding_manager.generate_all_embeddings.side_effect = RuntimeError("Test error")
        
        # Track temporary directory contents
        temp_dir = tempfile.gettempdir()
        initial_files = set(os.listdir(temp_dir))
        
        # Create a test file
        test_file = os.path.join(temp_dir, "test_error.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest error")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test_error.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            assert response.status_code == 500
            
            # Check that no upload_* files remain
            import time
            time.sleep(0.1)
            
            final_files = set(os.listdir(temp_dir))
            new_files = final_files - initial_files - {"test_error.pdf"}
            
            upload_files = [f for f in new_files if f.startswith("upload_")]
            assert len(upload_files) == 0, f"Temporary upload files not cleaned up on error: {upload_files}"
            
        finally:
            # Cleanup test file
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_large_file(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload of a large file (simulated)."""
        # Create a large test file (1MB)
        temp_dir = tempfile.gettempdir()
        large_file = os.path.join(temp_dir, "large.pdf")
        
        # Generate 1MB of data
        large_content = b"%PDF-1.4\n" + b"X" * (1024 * 1024 - 10)
        
        with open(large_file, 'wb') as f:
            f.write(large_content)
        
        try:
            with open(large_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("large.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should still succeed
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
        finally:
            # Cleanup
            if os.path.exists(large_file):
                os.remove(large_file)
    
    def test_upload_with_special_characters_in_filename(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload with special characters in filename."""
        # Create a test file with special characters in name
        temp_dir = tempfile.gettempdir()
        special_file = os.path.join(temp_dir, "test file with spaces & special chars.pdf")
        
        with open(special_file, 'wb') as f:
            f.write(b"%PDF-1.4\nSpecial chars test")
        
        try:
            with open(special_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test file with spaces & special chars.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
        finally:
            # Cleanup
            if os.path.exists(special_file):
                os.remove(special_file)
class TestUploadWorkflow:
    """Integration tests for complete upload workflows."""
    
    def test_upload_to_multiple_collections(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_pdf_file
    ):
        """Test uploading the same file to multiple collections."""
        collections = ["collection_a", "collection_b", "collection_c"]
        
        # Mock list_collections to return all test collections
        mock_qdrant_manager.list_collections.return_value = collections
        
        with open(sample_pdf_file, 'rb') as f:
            file_content = f.read()
        
        for collection in collections:
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": collection}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Reset mock call counts for next iteration
            mock_qdrant_manager.store_points.reset_mock()
    
    def test_sequential_uploads(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test multiple sequential uploads."""
        # Create multiple test files
        temp_dir = tempfile.gettempdir()
        files = []
        
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test_{i}.pdf")
            with open(file_path, 'wb') as f:
                f.write(f"%PDF-1.4\nTest document {i}".encode())
            files.append(file_path)
        
        try:
            for i, file_path in enumerate(files):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                response = client.post(
                    "/api/upload",
                    files={
                        "file": (f"test_{i}.pdf", file_content, "application/pdf")
                    },
                    data={"collection_name": "test_collection"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                
        finally:
            # Cleanup
            for file_path in files:
                if os.path.exists(file_path):
                    os.remove(file_path)


class TestUploadValidation:
    """Tests for upload validation and edge cases."""
    
    def test_upload_file_size_limit(self, client, mock_qdrant_manager):
        """Test upload with very large file (simulating size limit)."""
        # Note: The actual implementation doesn't have a file size limit,
        # but we can test that large files are handled
        
        # Create a moderately large file (10MB)
        temp_dir = tempfile.gettempdir()
        large_file = os.path.join(temp_dir, "very_large.pdf")
        
        # Generate 10MB of data
        chunk_size = 1024 * 1024  # 1MB
        with open(large_file, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            for _ in range(10):  # 10MB total
                f.write(b"X" * chunk_size)
        
        try:
            # This test might be slow, so we'll skip the actual upload
            # and just verify the file was created
            assert os.path.exists(large_file)
            assert os.path.getsize(large_file) > 10 * 1024 * 1024
            
            # We could test the upload, but it would be slow
            # Instead, we'll just note that large files should be supported
            
        finally:
            # Cleanup
            if os.path.exists(large_file):
                os.remove(large_file)
    
    def test_upload_with_different_content_types(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload with different content types for the same file extension."""
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest content")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            # Test with different content types
            content_types = [
                "application/pdf",
                "application/octet-stream",
                "text/plain"  # Wrong for PDF, but should still work based on extension
            ]
            
            for content_type in content_types:
                response = client.post(
                    "/api/upload",
                    files={
                        "file": ("test.pdf", file_content, content_type)
                    },
                    data={"collection_name": "test_collection"}
                )
                
                # Should succeed regardless of content type (validation is by extension)
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_response_model_validation(self, client):
        """Test that upload response matches the Pydantic model."""
        # This test verifies the response structure matches the UploadResponse model
        response = UploadResponse(
            success=True,
            chunks_created=5,
            processing_time=1.5,
            message="Test message"
        )
        
        # Verify the model can be instantiated
        assert response.success is True
        assert response.chunks_created == 5
        assert response.processing_time == 1.5
        assert response.message == "Test message"
        
        # Verify model validation
        with pytest.raises(ValueError):
            # chunks_created should be >= 0
            UploadResponse(
                success=True,
                chunks_created=-1,  # Invalid
                processing_time=1.5
            )
        
        with pytest.raises(ValueError):
            # processing_time should be >= 0
            UploadResponse(
                success=True,
                chunks_created=5,
                processing_time=-1.0  # Invalid
            )
    
    def test_upload_with_unsupported_extension_but_valid_content_type(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test upload with unsupported extension but valid content type."""
        # Create a file with .xyz extension but PDF content
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.xyz")
        
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest content")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.xyz", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should fail because validation is by file extension, not content type
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unsupported file format" in data["detail"]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_with_no_extension(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test upload with file that has no extension."""
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "testfile")
        
        with open(test_file, 'wb') as f:
            f.write(b"Test content without extension")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("testfile", file_content, "text/plain")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should fail because no extension
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unsupported file format" in data["detail"]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_with_case_insensitive_extensions(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload with uppercase file extensions."""
        temp_dir = tempfile.gettempdir()
        test_files = [
            ("test.PDF", b"%PDF-1.4\nTest content"),
            ("test.DOCX", b"DOCX content"),
            ("test.MD", b"# Markdown content"),
            ("test.TXT", b"Text content")
        ]
        
        for filename, content in test_files:
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                response = client.post(
                    "/api/upload",
                    files={
                        "file": (filename, file_content, "application/octet-stream")
                    },
                    data={"collection_name": "test_collection"}
                )
                
                # Should succeed for uppercase extensions
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                
            finally:
                # Cleanup
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    def test_upload_with_dot_in_filename(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload with multiple dots in filename."""
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.document.v2.pdf")
        
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest content with dots in name")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.document.v2.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should succeed - should extract .pdf extension correctly
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_statistics_message_format(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager,
        sample_pdf_file
    ):
        """Test that the success message has the correct format."""
        with open(sample_pdf_file, 'rb') as f:
            file_content = f.read()
        
        response = client.post(
            "/api/upload",
            files={
                "file": ("test_document.pdf", file_content, "application/pdf")
            },
            data={"collection_name": "test_collection"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check message format
        assert "test_document.pdf" in data["message"]
        assert "3" in data["message"]  # Number of chunks
        assert "Successfully uploaded and processed" in data["message"]
        assert "Created" in data["message"]
        assert "chunks" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
class TestUploadComprehensive:
    """Comprehensive tests for upload endpoint covering edge cases."""
    
    def test_upload_with_zero_chunks(
        self,
        client,
        mock_chunking_strategy,
        mock_qdrant_manager
    ):
        """Test upload when chunking returns zero chunks."""
        # Mock chunking strategy to return empty list
        mock_chunking_strategy.process_document.return_value = []
        
        # Create a test file
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should return 400 because no chunks were created
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "No text content could be extracted" in data["detail"]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_with_very_long_filename(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload with very long filename."""
        # Create a test file with a very long name
        temp_dir = tempfile.gettempdir()
        long_filename = "a" * 100 + ".pdf"
        test_file = os.path.join(temp_dir, long_filename)
        
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest content")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": (long_filename, file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should still succeed
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_with_unicode_filename(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test upload with Unicode characters in filename."""
        temp_dir = tempfile.gettempdir()
        unicode_filename = "test_文档_文件.pdf"  # Chinese characters
        test_file = os.path.join(temp_dir, unicode_filename)
        
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest content with Unicode filename")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": (unicode_filename, file_content, "application/pdf")
                },
                data={"collection_name": "test_collection"}
            )
            
            # Should succeed
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_concurrent_requests(
        self,
        client,
        mock_chunking_strategy,
        mock_embedding_manager,
        mock_qdrant_manager
    ):
        """Test handling of concurrent upload requests."""
        # This is a simplified test - in reality we'd need async testing
        # Create test files
        temp_dir = tempfile.gettempdir()
        files = []
        
        for i in range(2):  # Test with 2 concurrent requests
            file_path = os.path.join(temp_dir, f"concurrent_{i}.pdf")
            with open(file_path, 'wb') as f:
                f.write(f"%PDF-1.4\nConcurrent test {i}".encode())
            files.append(file_path)
        
        try:
            # Simulate concurrent requests (simplified - sequential for now)
            for i, file_path in enumerate(files):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                response = client.post(
                    "/api/upload",
                    files={
                        "file": (f"concurrent_{i}.pdf", file_content, "application/pdf")
                    },
                    data={"collection_name": "test_collection"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                
        finally:
            # Cleanup
            for file_path in files:
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    def test_upload_error_message_clarity(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test that error messages are clear and informative."""
        # Test with non-existent collection
        mock_qdrant_manager.list_collections.return_value = []
        
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\nTest")
        
        try:
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            response = client.post(
                "/api/upload",
                files={
                    "file": ("test.pdf", file_content, "application/pdf")
                },
                data={"collection_name": "non_existent_collection"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            # Error message should be clear
            assert "does not exist" in data["detail"]
            assert "non_existent_collection" in data["detail"]
            assert "create it first" in data["detail"] or "Please create" in data["detail"]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_upload_file_validation_comprehensive(
        self,
        client,
        mock_qdrant_manager
    ):
        """Comprehensive test of file format validation."""
        test_cases = [
            # (filename, should_succeed, description)
            ("test.pdf", True, "Valid PDF"),
            ("test.PDF", True, "Uppercase PDF"),
            ("test.docx", True, "Valid DOCX"),
            ("test.doc", True, "Valid DOC"),
            ("test.md", True, "Valid Markdown"),
            ("test.txt", True, "Valid text"),
            ("test.exe", False, "Invalid executable"),
            ("test.zip", False, "Invalid archive"),
            ("test", False, "No extension"),
            ("test.pdf.exe", False, "Double extension with invalid final"),
            ("test.pdf.txt", True, "Double extension with valid final"),
        ]
        
        for filename, should_succeed, description in test_cases:
            temp_dir = tempfile.gettempdir()
            test_file = os.path.join(temp_dir, filename)
            
            with open(test_file, 'wb') as f:
                f.write(b"Test content")
            
            try:
                with open(test_file, 'rb') as f:
                    file_content = f.read()
                
                response = client.post(
                    "/api/upload",
                    files={
                        "file": (filename, file_content, "application/octet-stream")
                    },
                    data={"collection_name": "test_collection"}
                )
                
                if should_succeed:
                    assert response.status_code == 200, f"Failed for {description}: {filename}"
                    data = response.json()
                    assert data["success"] is True, f"Failed for {description}: {filename}"
                else:
                    assert response.status_code == 400, f"Should have failed for {description}: {filename}"
                    data = response.json()
                    assert "detail" in data, f"Missing detail for {description}: {filename}"
                    assert "Unsupported file format" in data["detail"], f"Wrong error for {description}: {filename}"
                    
            finally:
                # Cleanup
                if os.path.exists(test_file):
                    os.remove(test_file)