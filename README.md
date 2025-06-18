# Invoice Reimbursement System

An intelligent AI-powered system for analyzing employee invoice reimbursements against company policies using Google Gemini API and FAISS vector database. This system automates the reimbursement process by leveraging Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to provide accurate analysis and conversational querying capabilities.

## 🎯 Project Overview

The Invoice Reimbursement System addresses the challenge of manually processing employee expense reimbursements by providing:

1. **Automated Invoice Analysis**: AI-powered analysis of invoices against company reimbursement policies
2. **Intelligent Classification**: Categorizes reimbursements as "Fully Reimbursed", "Partially Reimbursed", or "Declined"
3. **RAG-Powered Chatbot**: Conversational interface for querying processed invoice data using natural language
4. **Vector Search Integration**: Semantic search with metadata filtering for precise data retrieval
5. **Simple Web Interface**: Clean Streamlit UI for easy interaction

## 🏗️ Technical Stack

### Core Technologies
- **Programming Language**: Python 3.8+
- **Backend Framework**: FastAPI
- **Frontend**: Streamlit (Clean UI)
- **Large Language Model**: Google Gemini API (gemini-1.5-flash)
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Embedding Model**: Sentence Transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDF2

### Key Libraries
- `fastapi` - Modern web framework for building APIs
- `uvicorn` - ASGI server for FastAPI
- `streamlit` - Web app framework for the UI
- `google-generativeai` - Google Gemini API client
- `sentence-transformers` - Embedding model for vector search
- `faiss-cpu` - Vector similarity search
- `PyPDF2` - PDF text extraction
- `python-multipart` - File upload handling
- `python-dotenv` - Environment variable management

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Edit `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### 3. Start the System
```bash
# Terminal 1: Start backend
python main.py

# Terminal 2: Start UI
streamlit run final_ui.py --server.port 8507
```

### 4. Access the Application
- **UI**: http://localhost:8507
- **API Docs**: http://localhost:8000/docs

## 📝 How to Use

### 1. Analyze Invoices
1. Go to "Analyze Invoices" tab
2. Enter employee name
3. Upload policy PDF file
4. Upload ZIP file containing invoice PDFs
5. Click "Start Analysis"

### 2. Ask Questions
1. Go to "Ask Questions" tab
2. Type your question about the analyzed invoices
3. Click "Ask" or use sample questions
4. View AI responses

## 📁 Project Structure
```
invoice-reimbursement-system/
├── main.py                 # FastAPI backend
├── final_ui.py             # Streamlit frontend
├── config.py               # Configuration
├── models.py               # Data models
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
└── services/               # Core services
    ├── pdf_processor.py    # PDF handling
    ├── llm_service.py      # Gemini API
    ├── vector_store.py     # FAISS database
    └── conversation_manager.py # Chat context
```


### Overall Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI    │    │   FastAPI Server  │    │  Gemini LLM      │
│                 │◄──►│                  │◄──►│  Service         │
│  - File Upload   │    │  - Invoice API    │    │                 │
│  - Chat Interface│    │  - Chat API       │    │  - Analysis      │
│  - Results View  │    │  - Health Check   │    │  - Responses     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  FAISS Vector    │    │  PDF Processor    │    │ Conversation    │
│  Database        │    │                  │    │ Manager         │
│                 │    │  - Text Extract   │    │                 │
│  - Embeddings    │    │  - ZIP Handler    │    │  - Context       │
│  - Metadata      │    │  - Validation     │    │  - Sessions      │
│  - Search        │    │  - Cleanup        │    │  - History       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📝 Prompt Design

### Invoice Analysis Prompt Engineering

The system uses carefully crafted prompts to ensure accurate and consistent invoice analysis:

#### Key Design Principles:
1. **Structured Output**: Forces JSON format for reliable parsing
2. **Policy Context**: Provides complete policy text for accurate interpretation
3. **Detailed Requirements**: Specifies exact analysis criteria and output format
4. **Error Prevention**: Includes validation guidelines and fallback instructions

#### Prompt Structure:
```
1. System Role Definition
2. Company Policy Context (Full Text)
3. Invoice Details (Employee, File, Content)
4. Analysis Requirements
5. JSON Response Format Specification
6. Decision Guidelines and Validation Rules
```

### Chatbot Prompt Engineering

The RAG chatbot uses context-aware prompts for intelligent responses:

#### Response Strategy:
- Semantic search retrieval from vector database
- Context-aware response generation
- Markdown formatting for readability
- Source attribution for transparency

## 🔧 API Endpoints

### 1. Invoice Analysis Endpoint
**POST** `/analyze-invoices`

**Purpose**: Analyze employee invoices against company reimbursement policy

**Parameters**:
- `employee_name` (form field): Name of the employee
- `policy_file` (file): Company reimbursement policy PDF
- `invoices_zip` (file): ZIP file containing invoice PDFs

**Response Format**:
```json
{
  "success": true,
  "message": "Successfully processed 5 invoices",
  "processed_invoices": 5,
  "errors": []
}
```

### 2. RAG Chatbot Endpoint
**POST** `/chat`

**Purpose**: Query invoice reimbursement data using natural language

**Request Body**:
```json
{
  "query": "Show me all declined reimbursements",
  "session_id": "optional-session-id"
}
```

**Response Format**:
```json
{
  "response": "## Analysis Results\n\nBased on the data...",
  "session_id": "uuid-session-id",
  "sources": [
    {
      "employee_name": "John Doe",
      "invoice_filename": "receipt.pdf",
      "reimbursement_status": "Declined",
      "similarity_score": 0.95
    }
  ]
}




---

