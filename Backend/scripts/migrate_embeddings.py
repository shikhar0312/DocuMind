import os
import io
import time
import traceback
from typing import List
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase import create_client, Client

def main():
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
    
    supabase_url = os.environ.get("VITE_SUPABASE_URL")
    # For a backend admin script, we MUST use the SERVICE_ROLE_KEY to bypass RLS.
    # The user needs to add VITE_SUPABASE_SERVICE_ROLE_KEY to Backend/.env
    supabase_key = os.environ.get("VITE_SUPABASE_SERVICE_ROLE_KEY") 
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not supabase_key:
        print("ERROR: VITE_SUPABASE_SERVICE_ROLE_KEY is required in Backend/.env to bypass RLS for migration.")
        return
    if not gemini_key:
        print("ERROR: GEMINI_API_KEY is required.")
        return

    supabase: Client = create_client(supabase_url, supabase_key)
    
    # 1. Fetch documents that need reprocessing
    # We look for documents marked 'processing' containing the specific error_message set by our migration
    res = supabase.table("documents").select("*").eq("status", "processing").like("error_message", "%Awaiting dimension upgrade%").execute()
    docs = res.data or []
    
    if not docs:
        print("No documents found waiting for dimension upgrade.")
        return
        
    print(f"Found {len(docs)} document(s) to reprocess.")
    
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=gemini_key
    )
    
    for doc in docs:
        doc_id = doc["id"]
        user_id = doc["user_id"]
        file_path = doc["file_path"]
        file_type = doc["file_type"]
        
        print(f"\nProcessing document: {doc['name']} ({doc_id})")
        
        try:
            # Idempotency check: Delete any existing chunks for this document just in case
            supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
            
            # Download file
            file_res = supabase.storage.from_("documents").download(file_path)
            
            # Extract text
            pages = []
            if file_type == "application/pdf":
                pdf_reader = PdfReader(io.BytesIO(file_res))
                for i, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        pages.append({"page_number": i + 1, "text": text})
            else:
                text = file_res.decode("utf-8", errors="ignore")
                if text:
                    pages.append({"page_number": 1, "text": text})
                    
            if not pages:
                raise ValueError("No extractable text found.")
                
            # Chunking
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
                        "document_id": doc_id,
                        "user_id": user_id,
                        "chunk_index": chunk_index,
                        "page_number": page["page_number"],
                        "content": chunk,
                    })
                    chunk_index += 1
            
            if not chunks_data:
                raise ValueError("No chunks after splitting.")
                
            # Embedding
            print(f"  Embedding {len(chunks_data)} chunks...")
            texts = [c["content"] for c in chunks_data]
            embeddings = embeddings_model.embed_documents(texts)
            
            for i, chunk in enumerate(chunks_data):
                chunk["embedding"] = embeddings[i]
                
            # Insert to DB (Batched)
            BATCH_SIZE = 500
            for i in range(0, len(chunks_data), BATCH_SIZE):
                batch = chunks_data[i:i+BATCH_SIZE]
                supabase.table("document_chunks").insert(batch).execute()
            
            # Finalize: Mark as completed ONLY after chunks are safely stored
            supabase.table("documents").update({
                "status": "completed",
                "error_message": None
            }).eq("id", doc_id).execute()
            
            print(f"  Success! Document {doc_id} re-embedded and completed.")
            
        except Exception as e:
            print(f"  Failed processing {doc_id}: {e}")
            traceback.print_exc()
            # Do NOT mark as completed. Either leave as processing or mark failed.
            supabase.table("documents").update({
                "status": "failed",
                "error_message": f"Reprocessing failed: {str(e)}"
            }).eq("id", doc_id).execute()
            
            # Cleanup any partial chunks so we don't have dangling/duplicate state
            supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()

if __name__ == "__main__":
    main()
