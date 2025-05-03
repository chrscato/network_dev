# routes/test_api.py
from flask import Blueprint, jsonify, request
from datetime import datetime

test_api_bp = Blueprint("test_api", __name__, url_prefix="/api/test")

@test_api_bp.route("/ping", methods=["GET"])
def ping():
    """Simple ping endpoint for PowerAutomate to test connectivity"""
    return jsonify({
        "status": "success",
        "message": "Connection successful!",
        "timestamp": datetime.utcnow().isoformat(),
        "received_headers": dict(request.headers)
    })

@test_api_bp.route("/sample-documents", methods=["GET"])
def sample_documents():
    """Return sample document data for PowerAutomate testing"""
    return jsonify({
        "status": "success",
        "count": 2,
        "documents": [
            {
                "id": "test-doc-1",
                "provider_id": "test-provider-1",
                "provider_name": "Test Imaging Center",
                "document_type": "contract",
                "docx_url": f"{request.host_url}api/test/sample-file/docx",
                "pdf_url": f"{request.host_url}api/test/sample-file/pdf",
                "is_generated": True,
                "is_ready_for_sending": True,
                "is_sent": False,
                "metadata": {
                    "rate_method": "wcfs",
                    "states": "CA, NY, TX",
                    "generated_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            {
                "id": "test-doc-2",
                "provider_id": "test-provider-2",
                "provider_name": "Another Test Provider",
                "document_type": "contract",
                "docx_url": f"{request.host_url}api/test/sample-file/docx",
                "pdf_url": f"{request.host_url}api/test/sample-file/pdf",
                "is_generated": True,
                "is_ready_for_sending": True,
                "is_sent": False,
                "metadata": {
                    "rate_method": "standard",
                    "states": "FL, GA",
                    "generated_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        ]
    })

@test_api_bp.route("/sample-file/<file_type>", methods=["GET"])
def sample_file(file_type):
    """Return a sample file for testing"""
    from flask import send_file
    import io
    
    # Create a simple text file as a placeholder
    content = f"This is a sample {file_type.upper()} file for testing purposes."
    
    # Return as a file attachment
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"sample.{file_type}"
    )

@test_api_bp.route("/mark-processed/<doc_id>", methods=["POST"])
def mark_processed(doc_id):
    """Test endpoint to mark a document as processed"""
    tracking_id = request.json.get('tracking_id', 'no-tracking-id-provided')
    
    return jsonify({
        "status": "success",
        "message": f"Document {doc_id} marked as processed",
        "tracking_id": tracking_id,
        "timestamp": datetime.utcnow().isoformat()
    })