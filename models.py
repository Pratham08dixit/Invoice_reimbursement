"""Pydantic models for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class InvoiceAnalysisRequest(BaseModel):
    """Request model for invoice analysis."""
    employee_name: str = Field(..., description="Name of the employee")

class InvoiceAnalysisResponse(BaseModel):
    """Response model for invoice analysis."""
    success: bool = Field(..., description="Whether the analysis was successful")
    message: str = Field(..., description="Status message")
    processed_invoices: int = Field(default=0, description="Number of invoices processed")
    errors: List[str] = Field(default_factory=list, description="List of errors if any")

class ChatRequest(BaseModel):
    """Request model for chatbot queries."""
    query: str = Field(..., description="User's search query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")

class ChatResponse(BaseModel):
    """Response model for chatbot queries."""
    response: str = Field(..., description="Chatbot response in markdown format")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")

class InvoiceAnalysis(BaseModel):
    """Model for individual invoice analysis results."""
    invoice_id: str = Field(..., description="Unique identifier for the invoice")
    employee_name: str = Field(..., description="Employee name")
    invoice_date: Optional[str] = Field(None, description="Date from the invoice")
    total_amount: Optional[float] = Field(None, description="Total amount from invoice")
    reimbursement_status: str = Field(..., description="Reimbursement status category")
    reimbursement_amount: Optional[float] = Field(None, description="Amount to be reimbursed")
    reason: str = Field(..., description="Detailed reason for the reimbursement decision")
    invoice_content: str = Field(..., description="Extracted text content from invoice")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")

class ConversationContext(BaseModel):
    """Model for storing conversation context."""
    session_id: str
    messages: List[Dict[str, str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
