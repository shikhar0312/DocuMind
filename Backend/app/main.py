from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DocuMind API",
    description="Document-based AI question-answering API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to DocuMind API"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "app": "DocuMind"}