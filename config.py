"""Configuration settings for the Invoice Reimbursement System."""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""

    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # LLM Configuration
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Vector Database Configuration (FAISS)
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./faiss_db")
    INDEX_FILE = os.getenv("INDEX_FILE", "invoice_index.faiss")
    METADATA_FILE = os.getenv("METADATA_FILE", "invoice_metadata.pkl")

    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # File Upload Settings
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {".pdf", ".zip"}

    # Reimbursement Categories
    REIMBURSEMENT_CATEGORIES = [
        "Fully Reimbursed",
        "Partially Reimbursed",
        "Declined"
    ]

config = Config()
