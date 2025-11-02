"""
File Transfer Module
Handles file upload/download operations with progress tracking and security
"""
import os
import base64
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
TRANSFER_DIR = Path("file_transfers")
UPLOAD_DIR = TRANSFER_DIR / "uploads"
DOWNLOAD_DIR = TRANSFER_DIR / "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default
CHUNK_SIZE = 64 * 1024  # 64KB chunks

# Transfer tracking
active_transfers = {}
transfer_history = []

def ensure_transfer_directories():
    """Create necessary directories for file transfers"""
    TRANSFER_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    DOWNLOAD_DIR.mkdir(exist_ok=True)

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file"""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def start_upload(filename: str, file_size: int, client_hash: str = None) -> Dict:
    """Initiate a file upload session"""
    ensure_transfer_directories()
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        return {
            "success": False,
            "error": f"File size ({file_size}) exceeds maximum allowed ({MAX_FILE_SIZE})"
        }
    
    # Generate transfer ID
    transfer_id = hashlib.md5(f"{filename}_{datetime.now().isoformat()}".encode()).hexdigest()
    
    # Clean filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_filename:
        safe_filename = f"upload_{transfer_id[:8]}"
    
    filepath = UPLOAD_DIR / f"{transfer_id}_{safe_filename}"
    
    # Initialize transfer tracking
    active_transfers[transfer_id] = {
        "type": "upload",
        "filename": safe_filename,
        "original_filename": filename,
        "filepath": str(filepath),
        "file_size": file_size,
        "bytes_transferred": 0,
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "client_hash": client_hash,
        "chunks_received": 0,
        "last_activity": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "transfer_id": transfer_id,
        "chunk_size": CHUNK_SIZE,
        "max_file_size": MAX_FILE_SIZE
    }

def upload_chunk(transfer_id: str, chunk_index: int, chunk_data: str, is_final: bool = False) -> Dict:
    """Upload a file chunk"""
    if transfer_id not in active_transfers:
        return {"success": False, "error": "Invalid transfer ID"}
    
    transfer = active_transfers[transfer_id]
    
    if transfer["status"] != "active":
        return {"success": False, "error": "Transfer is not active"}
    
    try:
        # Decode base64 chunk
        chunk_bytes = base64.b64decode(chunk_data)
        
        # Write chunk to file
        with open(transfer["filepath"], "ab") as f:
            f.write(chunk_bytes)
        
        # Update progress
        transfer["bytes_transferred"] += len(chunk_bytes)
        transfer["chunks_received"] += 1
        transfer["last_activity"] = datetime.now().isoformat()
        
        # Calculate progress
        progress = (transfer["bytes_transferred"] / transfer["file_size"]) * 100
        
        # Check if upload is complete
        if is_final or transfer["bytes_transferred"] >= transfer["file_size"]:
            transfer["status"] = "completed"
            transfer["end_time"] = datetime.now().isoformat()
            
            # Verify file integrity if hash provided
            if transfer.get("client_hash"):
                server_hash = get_file_hash(transfer["filepath"])
                if server_hash != transfer["client_hash"]:
                    transfer["status"] = "error"
                    transfer["error"] = "File integrity check failed"
                    return {
                        "success": False,
                        "error": "File integrity check failed",
                        "expected_hash": transfer["client_hash"],
                        "actual_hash": server_hash
                    }
            
            # Add to history
            transfer_history.append(transfer.copy())
            
            return {
                "success": True,
                "status": "completed",
                "progress": 100.0,
                "bytes_transferred": transfer["bytes_transferred"],
                "filename": transfer["filename"]
            }
        
        return {
            "success": True,
            "status": "active",
            "progress": progress,
            "bytes_transferred": transfer["bytes_transferred"],
            "chunk_index": chunk_index
        }
        
    except Exception as e:
        transfer["status"] = "error"
        transfer["error"] = str(e)
        return {"success": False, "error": str(e)}

def start_download(filepath: str) -> Dict:
    """Initiate a file download session"""
    ensure_transfer_directories()
    
    # Validate file path and existence
    file_path = Path(filepath)
    if not file_path.exists():
        return {"success": False, "error": "File not found"}
    
    if not file_path.is_file():
        return {"success": False, "error": "Path is not a file"}
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        return {
            "success": False,
            "error": f"File size ({file_size}) exceeds maximum allowed ({MAX_FILE_SIZE})"
        }
    
    # Generate transfer ID
    transfer_id = hashlib.md5(f"{filepath}_{datetime.now().isoformat()}".encode()).hexdigest()
    
    # Calculate file hash
    file_hash = get_file_hash(file_path)
    
    # Initialize transfer tracking
    active_transfers[transfer_id] = {
        "type": "download",
        "filename": file_path.name,
        "filepath": str(file_path),
        "file_size": file_size,
        "bytes_transferred": 0,
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "file_hash": file_hash,
        "chunks_sent": 0,
        "total_chunks": (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE,
        "last_activity": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "transfer_id": transfer_id,
        "filename": file_path.name,
        "file_size": file_size,
        "file_hash": file_hash,
        "chunk_size": CHUNK_SIZE,
        "total_chunks": active_transfers[transfer_id]["total_chunks"]
    }

def download_chunk(transfer_id: str, chunk_index: int) -> Dict:
    """Download a file chunk"""
    if transfer_id not in active_transfers:
        return {"success": False, "error": "Invalid transfer ID"}
    
    transfer = active_transfers[transfer_id]
    
    if transfer["status"] != "active":
        return {"success": False, "error": "Transfer is not active"}
    
    try:
        # Calculate chunk position
        start_pos = chunk_index * CHUNK_SIZE
        
        # Read chunk from file
        with open(transfer["filepath"], "rb") as f:
            f.seek(start_pos)
            chunk_data = f.read(CHUNK_SIZE)
        
        if not chunk_data:
            return {"success": False, "error": "No data at chunk index"}
        
        # Encode chunk as base64
        chunk_b64 = base64.b64encode(chunk_data).decode('utf-8')
        
        # Update progress
        transfer["bytes_transferred"] = min(
            transfer["bytes_transferred"] + len(chunk_data),
            transfer["file_size"]
        )
        transfer["chunks_sent"] += 1
        transfer["last_activity"] = datetime.now().isoformat()
        
        # Calculate progress
        progress = (transfer["bytes_transferred"] / transfer["file_size"]) * 100
        
        # Check if download is complete
        is_final = chunk_index >= transfer["total_chunks"] - 1
        if is_final:
            transfer["status"] = "completed"
            transfer["end_time"] = datetime.now().isoformat()
            transfer_history.append(transfer.copy())
        
        return {
            "success": True,
            "chunk_data": chunk_b64,
            "chunk_index": chunk_index,
            "chunk_size": len(chunk_data),
            "is_final": is_final,
            "progress": progress,
            "bytes_transferred": transfer["bytes_transferred"]
        }
        
    except Exception as e:
        transfer["status"] = "error"
        transfer["error"] = str(e)
        return {"success": False, "error": str(e)}

def get_transfer_status(transfer_id: str) -> Dict:
    """Get status of a transfer"""
    if transfer_id not in active_transfers:
        return {"success": False, "error": "Transfer not found"}
    
    transfer = active_transfers[transfer_id]
    progress = (transfer["bytes_transferred"] / transfer["file_size"]) * 100 if transfer["file_size"] > 0 else 0
    
    return {
        "success": True,
        "transfer_id": transfer_id,
        "type": transfer["type"],
        "filename": transfer["filename"],
        "file_size": transfer["file_size"],
        "bytes_transferred": transfer["bytes_transferred"],
        "progress": progress,
        "status": transfer["status"],
        "start_time": transfer["start_time"],
        "last_activity": transfer["last_activity"]
    }

def cancel_transfer(transfer_id: str) -> Dict:
    """Cancel an active transfer"""
    if transfer_id not in active_transfers:
        return {"success": False, "error": "Transfer not found"}
    
    transfer = active_transfers[transfer_id]
    transfer["status"] = "cancelled"
    transfer["end_time"] = datetime.now().isoformat()
    
    # Clean up partial upload file
    if transfer["type"] == "upload":
        try:
            os.remove(transfer["filepath"])
        except:
            pass
    
    return {"success": True, "message": "Transfer cancelled"}

def list_transfers(active_only: bool = False) -> Dict:
    """List all transfers or only active ones"""
    if active_only:
        transfers = [t for t in active_transfers.values() if t["status"] == "active"]
    else:
        transfers = list(active_transfers.values()) + transfer_history
    
    return {
        "success": True,
        "transfers": transfers,
        "count": len(transfers)
    }

def list_uploaded_files() -> Dict:
    """List all uploaded files"""
    ensure_transfer_directories()
    
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(file_path)
            })
    
    return {
        "success": True,
        "files": files,
        "count": len(files)
    }

def cleanup_old_transfers(max_age_hours: int = 24):
    """Clean up old completed transfers and files"""
    cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
    
    # Clean up transfer history
    global transfer_history
    transfer_history = [
        t for t in transfer_history
        if datetime.fromisoformat(t["start_time"]).timestamp() > cutoff_time
    ]
    
    # Clean up completed active transfers
    completed_transfers = [
        tid for tid, t in active_transfers.items()
        if t["status"] in ["completed", "error", "cancelled"]
        and datetime.fromisoformat(t["start_time"]).timestamp() < cutoff_time
    ]
    
    for tid in completed_transfers:
        del active_transfers[tid]

# Initialize directories on import
ensure_transfer_directories()