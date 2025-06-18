# Invoice Reimbursement System

An intelligent AI-powered system for analyzing employee invoice reimbursements against company policies using Google Gemini API and FAISS vector database.

## 🎯 Features

- **Automated Invoice Analysis**: AI-powered analysis of invoices against company reimbursement policies
- **Intelligent Classification**: Categorizes reimbursements as "Fully Reimbursed", "Partially Reimbursed", or "Declined"
- **RAG-Powered Chatbot**: Conversational interface for querying processed invoice data using natural language
- **Vector Search Integration**: Semantic search with metadata filtering for precise data retrieval
- **Simple Web Interface**: Clean Streamlit UI for easy interaction

## 🏗️ Technical Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit (Clean UI)
- **LLM**: Google Gemini API (gemini-1.5-flash)
- **Vector Database**: FAISS
- **Embedding Model**: Sentence Transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDF2

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- Google Gemini API key
- 2GB+ RAM

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/invoice_reimbursement.git
   cd invoice_reimbursement
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Start the system**
   ```bash
   # Terminal 1: Start backend
   python main.py
   
   # Terminal 2: Start UI
   streamlit run final_ui.py --server.port 8507
   ```

5. **Access the application**
   - **UI**: http://localhost:8507
   - **API Docs**: http://localhost:8000/docs

## 📝 Usage

### Analyze Invoices
1. Go to "Analyze Invoices" tab
2. Enter employee name
3. Upload policy PDF file
4. Upload ZIP file containing invoice PDFs
5. Click "Start Analysis"

### Ask Questions
1. Go to "Ask Questions" tab
2. Type questions like:
   - "Show me all declined reimbursements"
   - "What's the total reimbursement amount?"
   - "List expenses by employee"

## 🔧 API Endpoints

### POST /analyze-invoices
Analyze employee invoices against company policy

**Parameters:**
- `employee_name`: Employee name
- `policy_file`: Policy PDF file
- `invoices_zip`: ZIP file with invoices

### POST /chat
Query invoice data using natural language

**Body:**
```json
{
  "query": "Show me all analyses",
  "session_id": "optional"
}
```

### GET /health
Check system health status

## 📁 Project Structure

```
invoice_reimbursement/
├── main.py                 # FastAPI backend
├── final_ui.py             # Streamlit frontend
├── config.py               # Configuration
├── models.py               # Data models
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── services/              # Core services
    ├── pdf_processor.py   # PDF handling
    ├── llm_service.py     # Gemini API
    ├── vector_store.py    # FAISS database
    └── conversation_manager.py # Chat context
```

## 🧠 Technical Implementation

### LLM Integration
- **Google Gemini (gemini-1.5-flash)**: Fast, accurate text analysis
- **Structured Prompts**: Consistent JSON output for reliable parsing
- **Error Handling**: Graceful fallbacks for API failures

### Vector Search
- **FAISS Database**: Fast similarity search for large datasets
- **Sentence Transformers**: 384-dimensional embeddings
- **Hybrid Search**: Vector similarity + metadata filtering

### Architecture
- **Modular Design**: Clean separation of concerns
- **Async Processing**: FastAPI's async capabilities
- **Error Recovery**: Comprehensive error handling
- **Security**: Input validation and file type restrictions

## ⚠️ Troubleshooting

**Backend API not running**
- Start with `python main.py`
- Check port 8000 availability

**Gemini API errors**
- Verify API key in `.env` file
- Check API permissions

**File upload issues**
- Ensure PDFs are valid
- Check file size limits (50MB max)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Google Gemini API for powerful language processing
- FAISS for efficient vector search
- Streamlit for simple UI development
- FastAPI for modern API framework

---

**Built with ❤️ using modern AI technologies**
