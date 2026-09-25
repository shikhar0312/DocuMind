import os
import io
import traceback
from typing import List
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase import create_client, Client, ClientOptions
from app.core.config import settings

def process_document(
    document_id: str,
    user_id: str,
    file_path: str,
    file_type: str,
    token: str
):
    """
    Background task to extract text, chunk, embed, and store in pgvector.
    We pass the JWT token to ensure we run under the user's RLS context.
    """
    # 1. Initialize Supabase client for this user
    options = ClientOptions(headers={"Authorization": f"Bearer {token}"})
    supabase: Client = create_client(
        settings.VITE_SUPABASE_URL,
        settings.VITE_SUPABASE_ANON_KEY,
        options=options
    )
    
    try:
        # 2. Download the file from Supabase Storage
        res = supabase.storage.from_("documents").download(file_path)
        file_bytes = res
        
        # 3. Extract text while preserving page numbers
        pages = []
        if file_type == "application/pdf":
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            for i, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    pages.append({"page_number": i + 1, "text": text})
        else:
            # For text files, treat the whole file as page 1
            text = file_bytes.decode("utf-8", errors="ignore")
            if text:
                pages.append({"page_number": 1, "text": text})
                
        if not pages:
            raise ValueError("No extractable text found in the document.")
            
        # 4. Chunk the text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks_data = []
        chunk_index = 0
        for page in pages:
            chunks = text_splitter.split_text(page["text"])
            for chunk in chunks:
                chunks_data.append({
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_index": chunk_index,
                    "page_number": page["page_number"],
                    "content": chunk,
                    # embedding will be added next
                })
                chunk_index += 1
                
        if not chunks_data:
            raise ValueError("Document yielded no chunks after splitting.")

        # 5. Generate Embeddings using Gemini
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")
            
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY
        )
        
        texts = [c["content"] for c in chunks_data]
        embeddings = embeddings_model.embed_documents(texts)
        
        for i, chunk in enumerate(chunks_data):
            chunk["embedding"] = embeddings[i]
            
        # 6. Insert chunks into pgvector
        # Supabase Python client handles list of dicts for bulk insert
        # We might need to batch if the document is very large (e.g. >1000 chunks)
        # For a 20MB limit, we can usually insert in batches of 500
        BATCH_SIZE = 500
        for i in range(0, len(chunks_data), BATCH_SIZE):
            batch = chunks_data[i:i+BATCH_SIZE]
            supabase.table("document_chunks").insert(batch).execute()
            
        # 7. Update document status to completed
        supabase.table("documents").update({
            "status": "completed",
            "error_message": None
        }).eq("id", document_id).execute()
        
    except Exception as e:
        # Log the full stack trace securely in the backend
        print(f"Error processing document {document_id}:")
        traceback.print_exc()
        
        # Fallback to update status to failed
        try:
            # We initialize a fresh client in case the previous one is in a bad state, 
            # but reuse the token
            supabase.table("documents").update({
                "status": "failed",
                "error_message": str(e)
            }).eq("id", document_id).execute()
        except Exception as update_err:
            print(f"Critical failure updating document status: {update_err}")
