import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from supabase import Client
from app.core.dependencies import get_supabase_client, security
from app.services.rag import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_TYPES = ["application/pdf", "text/plain"]

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    supabase: Client = Depends(get_supabase_client),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # 1. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_TYPES)}"
        )
    
    # 2. Validate file size (reading into memory)
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds the maximum limit of 20MB."
        )
    
    # 3. Generate Document ID and Setup Paths
    user = supabase.auth_user
    document_id = str(uuid.uuid4())
    
    # Extract extension securely
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "pdf"
    if file.content_type == "text/plain":
        ext = "txt"
    elif file.content_type == "application/pdf":
        ext = "pdf"
        
    storage_path = f"{user.id}/{document_id}.{ext}"
    
    # 4. Upload to Supabase Storage
    try:
        res = supabase.storage.from_("documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document to storage: {str(e)}"
        )
        
    # 5. Insert Record into PostgreSQL
    try:
        db_res = supabase.table("documents").insert({
            "id": document_id,
            "user_id": user.id,
            "name": file.filename,
            "file_path": storage_path,
            "file_type": file.content_type,
            "size_bytes": len(file_bytes),
            "status": "processing"
        }).execute()
        
        # 6. Trigger Background Task
        background_tasks.add_task(
            process_document,
            document_id=document_id,
            user_id=user.id,
            file_path=storage_path,
            file_type=file.content_type,
            token=credentials.credentials
        )
        
        return {
            "message": "Document uploaded successfully",
            "document": db_res.data[0]
        }
    except Exception as e:
        # If DB insert fails, attempt to delete the uploaded file
        try:
            supabase.storage.from_("documents").remove([storage_path])
        except:
            pass # ignore cleanup errors
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {str(e)}"
        )

@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    supabase: Client = Depends(get_supabase_client)
):
    try:
        res = supabase.table("documents").select("id, status, error_message").eq("id", document_id).single().execute()
        return res.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
