import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import create_client, Client, ClientOptions
from app.core.config import settings

# Langchain imports for RAG
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

router = APIRouter(
    prefix="/api/chats",
    tags=["chats"],
)

def get_supabase(request: Request) -> Client:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth_header.split(" ")[1]
    
    options = ClientOptions(headers={"Authorization": f"Bearer {token}"})
    return create_client(
        settings.VITE_SUPABASE_URL,
        settings.VITE_SUPABASE_ANON_KEY,
        options=options
    )

def get_user_id(request: Request) -> str:
    # A simple mock to extract user_id from token if needed, but since RLS handles it, 
    # we can query supabase auth.
    supabase = get_supabase(request)
    user_res = supabase.auth.get_user()
    if not user_res or not user_res.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_res.user.id


class CreateChatRequest(BaseModel):
    document_id: str
    title: str

class SendMessageRequest(BaseModel):
    content: str

@router.get("")
def get_chats(document_id: str, supabase: Client = Depends(get_supabase)):
    res = supabase.table("chats").select("*").eq("document_id", document_id).order("created_at", desc=True).execute()
    return res.data

@router.post("")
def create_chat(req: CreateChatRequest, supabase: Client = Depends(get_supabase), user_id: str = Depends(get_user_id)):
    # Verify document ownership and status
    doc_res = supabase.table("documents").select("status").eq("id", req.document_id).execute()
    if not doc_res.data:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
    if doc_res.data[0]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    chat_res = supabase.table("chats").insert({
        "user_id": user_id,
        "document_id": req.document_id,
        "title": req.title
    }).execute()
    
    return chat_res.data[0]

@router.get("/{chat_id}/messages")
def get_messages(chat_id: str, supabase: Client = Depends(get_supabase)):
    res = supabase.table("messages").select("*").eq("chat_id", chat_id).order("created_at", desc=False).execute()
    return res.data

@router.post("/{chat_id}/messages")
def send_message(chat_id: str, req: SendMessageRequest, supabase: Client = Depends(get_supabase), user_id: str = Depends(get_user_id)):
    # 1. Verify chat ownership and get document_id
    chat_res = supabase.table("chats").select("document_id").eq("id", chat_id).execute()
    if not chat_res.data:
        raise HTTPException(status_code=404, detail="Chat not found or unauthorized")
    document_id = chat_res.data[0]["document_id"]
    
    # Verify document status
    doc_res = supabase.table("documents").select("status").eq("id", document_id).execute()
    if not doc_res.data or doc_res.data[0]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Document not ready")

    # 2. Save User Message
    user_msg_res = supabase.table("messages").insert({
        "chat_id": chat_id,
        "role": "user",
        "content": req.content,
        "sources": []
    }).execute()

    # 3. Retrieve Context from pgvector
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured")
        
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY
    )
    query_embedding = embeddings_model.embed_query(req.content)
    
    # We use a raw sql RPC function to perform the vector search securely, or if not available, we can try using supabase rpc
    # Wait, supabase client doesn't support vector search directly in .select() without RPC.
    # Let's write the RPC function call.
    search_res = supabase.rpc("match_document_chunks", {
        "query_embedding": query_embedding,
        "match_threshold": 0.5,
        "match_count": 5,
        "p_document_id": document_id,
        "p_user_id": user_id
    }).execute()
    
    chunks = search_res.data or []
    
    # 4. Construct context and sources array
    context_text = ""
    sources = []
    for i, chunk in enumerate(chunks):
        marker = i + 1
        page_num = chunk.get("page_number")
        page_ref = f"Page {page_num}" if page_num else "Snippet"
        
        context_text += f"\n--- Chunk [{marker}] ({page_ref}) ---\n{chunk.get('content')}\n"
        
        sources.append({
            "chunk_id": chunk.get("id"),
            "page_number": page_num,
            "content_snippet": chunk.get("content")[:150] + "..." # Snippet for UI
        })

    # 5. Get chat history
    history_res = supabase.table("messages").select("role, content").eq("chat_id", chat_id).order("created_at", desc=False).limit(10).execute()
    history = history_res.data or []
    
    # 6. Generate Answer using Gemini
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3
    )
    
    sys_prompt = f"""You are a helpful assistant answering questions about a document. 
Use ONLY the provided context chunks to answer. 
If the answer is not contained in the context, say "The document does not contain this information." 
Cite your sources exactly using the chunk markers, for example: [1], [2]. Do not invent sources.

Context:
{context_text}
"""
    
    langchain_msgs = [SystemMessage(content=sys_prompt)]
    for m in history:
        if m["role"] == "user":
            langchain_msgs.append(HumanMessage(content=m["content"]))
        else:
            langchain_msgs.append(AIMessage(content=m["content"]))
            
    # Add current question (already added if history fetched it? history includes the one we just inserted! )
    # Wait, the history query fetches the newly inserted user message. So we don't need to append it again!
    
    response = llm.invoke(langchain_msgs)
    answer_text = response.content
    
    # 7. Save Assistant Message
    assistant_msg_res = supabase.table("messages").insert({
        "chat_id": chat_id,
        "role": "assistant",
        "content": answer_text,
        "sources": sources
    }).execute()
    
    return assistant_msg_res.data[0]
