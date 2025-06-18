"""
Invoice Reimbursement System - Main FastAPI Application

This system provides two main endpoints:
1. Invoice Analysis: Analyze employee invoices against company policy
2. RAG Chatbot: Query and retrieve information about processed invoices
"""

import os
import tempfile
import logging
from typing import List
import uuid
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import InvoiceAnalysisResponse, ChatRequest, ChatResponse
from services import PDFProcessor, LLMService, vector_store, conversation_manager
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Invoice Reimbursement System",
    description="AI-powered system for analyzing employee invoice reimbursements against company policy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_processor = PDFProcessor()
llm_service = LLMService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Invoice Reimbursement System...")
    logger.info(f"Vector store initialized with {len(vector_store.metadata)} existing analyses")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Invoice Reimbursement System...")
    conversation_manager.cleanup_expired_sessions()

@app.get("/")
async def root():
    """Root endpoint with system information."""
    stats = vector_store.get_statistics()
    session_stats = conversation_manager.get_session_stats()
    
    return {
        "message": "Invoice Reimbursement System API",
        "version": "1.0.0",
        "status": "running",
        "statistics": {
            "total_analyses": stats.get("total_analyses", 0),
            "active_sessions": session_stats.get("active_sessions", 0),
            "employees_processed": len(stats.get("employees", [])),
            "total_reimbursed": stats.get("total_reimbursed", 0)
        }
    }

@app.post("/analyze-invoices", response_model=InvoiceAnalysisResponse)
async def analyze_invoices(
    background_tasks: BackgroundTasks,
    employee_name: str = Form(..., description="Name of the employee"),
    policy_file: UploadFile = File(..., description="HR reimbursement policy PDF file"),
    invoices_zip: UploadFile = File(..., description="ZIP file containing invoice PDFs")
):
    """
    Analyze employee invoices against company reimbursement policy.
    
    This endpoint:
    1. Extracts text from the policy PDF
    2. Processes all invoice PDFs from the ZIP file
    3. Uses Gemini LLM to analyze each invoice against the policy
    4. Stores analysis results in FAISS vector database
    5. Returns summary of processing results
    """
    
    logger.info(f"Starting invoice analysis for employee: {employee_name}")
    
    # Validate file types
    if not policy_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Policy file must be a PDF")
    
    if not invoices_zip.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invoices file must be a ZIP archive")
    
    # Validate file sizes
    if policy_file.size > config.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Policy file too large")
    
    if invoices_zip.size > config.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invoices ZIP file too large")
    
    processed_invoices = 0
    errors = []
    
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as policy_temp:
            policy_content = await policy_file.read()
            policy_temp.write(policy_content)
            policy_temp_path = policy_temp.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as invoices_temp:
            invoices_content = await invoices_zip.read()
            invoices_temp.write(invoices_content)
            invoices_temp_path = invoices_temp.name
        
        # Extract policy text
        try:
            policy_text = pdf_processor.extract_text_from_pdf(policy_temp_path)
            logger.info("Successfully extracted policy text")
        except Exception as e:
            logger.error(f"Failed to extract policy text: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to process policy PDF: {str(e)}")
        
        # Process invoices ZIP
        try:
            invoices_data = pdf_processor.process_zip_file(invoices_temp_path)
            logger.info(f"Found {len(invoices_data)} invoice PDFs in ZIP file")
        except Exception as e:
            logger.error(f"Failed to process invoices ZIP: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to process invoices ZIP: {str(e)}")
        
        # Process each invoice
        for invoice_data in invoices_data:
            try:
                # Analyze invoice against policy
                analysis_result = llm_service.analyze_invoice_against_policy(
                    invoice_content=invoice_data['content'],
                    policy_content=policy_text,
                    employee_name=employee_name,
                    invoice_filename=invoice_data['filename']
                )
                
                # Add additional metadata
                analysis_result.update({
                    'employee_name': employee_name,
                    'invoice_filename': invoice_data['filename'],
                    'invoice_content': invoice_data['content'],
                    'analysis_timestamp': datetime.now().isoformat()
                })
                
                # Store in vector database
                doc_id = vector_store.add_invoice_analysis(analysis_result)
                logger.info(f"Stored analysis for {invoice_data['filename']} with ID: {doc_id}")
                
                processed_invoices += 1
                
            except Exception as e:
                error_msg = f"Failed to process {invoice_data['filename']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Cleanup temporary files
        background_tasks.add_task(cleanup_temp_files, [policy_temp_path, invoices_temp_path])
        
        # Prepare response
        success = processed_invoices > 0
        message = f"Successfully processed {processed_invoices} invoices"
        if errors:
            message += f" with {len(errors)} errors"
        
        logger.info(f"Completed invoice analysis: {processed_invoices} processed, {len(errors)} errors")
        
        return InvoiceAnalysisResponse(
            success=success,
            message=message,
            processed_invoices=processed_invoices,
            errors=errors
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during invoice analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_system(request: ChatRequest):
    """
    Chat with the RAG-enabled assistant about invoice reimbursements.
    
    This endpoint:
    1. Maintains conversation context across requests
    2. Uses vector search to find relevant invoice analyses
    3. Generates contextual responses using Gemini LLM
    4. Returns responses in markdown format
    """
    
    logger.info(f"Processing chat request: {request.query[:100]}...")
    
    try:
        # Get or create conversation session
        session_id = conversation_manager.get_or_create_session(request.session_id)
        
        # Add user message to conversation history
        conversation_manager.add_message(session_id, "user", request.query)
        
        # Get conversation history for context
        conversation_history = conversation_manager.get_conversation_history(session_id)
        
        # Perform vector search to find relevant invoice analyses
        search_results = vector_store.search(
            query=request.query,
            k=5  # Get top 5 most relevant results
        )
        
        # Generate response using LLM
        response_text = llm_service.generate_chatbot_response(
            user_query=request.query,
            search_results=search_results,
            conversation_history=conversation_history
        )
        
        # Add assistant response to conversation history
        conversation_manager.add_message(session_id, "assistant", response_text)
        
        # Prepare sources information
        sources = []
        for result in search_results[:3]:  # Include top 3 sources
            metadata = result.get('metadata', {})
            sources.append({
                'employee_name': metadata.get('employee_name'),
                'invoice_filename': metadata.get('invoice_filename'),
                'reimbursement_status': metadata.get('reimbursement_status'),
                'similarity_score': result.get('score', 0)
            })
        
        logger.info(f"Generated chat response for session: {session_id}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        
        # Create error session if needed
        if not request.session_id:
            session_id = conversation_manager.get_or_create_session()
        else:
            session_id = request.session_id
        
        error_response = f"I apologize, but I encountered an error while processing your request: {str(e)}"
        
        return ChatResponse(
            response=error_response,
            session_id=session_id,
            sources=[]
        )

@app.get("/statistics")
async def get_system_statistics():
    """Get comprehensive system statistics."""
    
    try:
        vector_stats = vector_store.get_statistics()
        session_stats = conversation_manager.get_session_stats()
        
        return {
            "vector_store": vector_stats,
            "conversations": session_stats,
            "system": {
                "total_analyses": vector_stats.get("total_analyses", 0),
                "unique_employees": len(vector_stats.get("employees", [])),
                "active_chat_sessions": session_stats.get("active_sessions", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "vector_store": "operational",
            "llm_service": "operational",
            "conversation_manager": "operational"
        }
    }

@app.delete("/conversations/{session_id}")
async def clear_conversation(session_id: str):
    """Clear a specific conversation session."""
    
    try:
        conversation_manager.clear_session(session_id)
        return {"message": f"Conversation session {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

def cleanup_temp_files(file_paths: List[str]):
    """Background task to cleanup temporary files."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
