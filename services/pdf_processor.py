"""PDF processing utilities for extracting text from invoices and policies."""

import PyPDF2
import pdfplumber
import zipfile
import tempfile
import os
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Handles PDF text extraction and ZIP file processing."""
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file using multiple methods for better accuracy.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        
        try:
            # Try pdfplumber first (better for structured documents)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If pdfplumber didn't extract much text, try PyPDF2
            if len(text.strip()) < 50:
                text = ""
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
        
        if not text.strip():
            raise Exception("No text could be extracted from the PDF file")
            
        return text.strip()
    
    def process_zip_file(self, zip_path: str) -> List[Dict[str, str]]:
        """
        Process a ZIP file containing PDF invoices.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            List of dictionaries containing filename and extracted text
        """
        invoices = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Create temporary directory for extraction
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Process all PDF files in the extracted directory
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower().endswith('.pdf'):
                                file_path = os.path.join(root, file)
                                try:
                                    text = self.extract_text_from_pdf(file_path)
                                    invoices.append({
                                        'filename': file,
                                        'content': text,
                                        'file_path': file_path
                                    })
                                    logger.info(f"Successfully processed: {file}")
                                except Exception as e:
                                    logger.error(f"Failed to process {file}: {str(e)}")
                                    # Continue processing other files
                                    continue
                                    
        except zipfile.BadZipFile:
            raise Exception("Invalid ZIP file format")
        except Exception as e:
            logger.error(f"Error processing ZIP file: {str(e)}")
            raise Exception(f"Failed to process ZIP file: {str(e)}")
        
        if not invoices:
            raise Exception("No valid PDF files found in the ZIP archive")
            
        return invoices
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate if a file is a valid PDF.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Try to access the first page to validate
                if len(pdf_reader.pages) > 0:
                    return True
        except Exception:
            pass
        
        return False
    
    def extract_invoice_metadata(self, invoice_text: str) -> Dict[str, any]:
        """
        Extract basic metadata from invoice text using simple pattern matching.
        
        Args:
            invoice_text: Raw text content from invoice
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'date': None,
            'total_amount': None,
            'invoice_number': None
        }
        
        lines = invoice_text.split('\n')
        
        for line in lines:
            line = line.strip().lower()
            
            # Extract total amount (look for patterns like "total: $100", "amount: 500.00", etc.)
            if any(keyword in line for keyword in ['total:', 'amount:', 'total amount:', 'grand total:']):
                # Extract numeric values
                import re
                amounts = re.findall(r'[\d,]+\.?\d*', line)
                if amounts:
                    try:
                        # Take the largest number found (likely the total)
                        metadata['total_amount'] = max([float(amt.replace(',', '')) for amt in amounts])
                    except ValueError:
                        pass
            
            # Extract date patterns
            if any(keyword in line for keyword in ['date:', 'invoice date:', 'bill date:']):
                import re
                # Look for date patterns
                date_patterns = [
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                    r'\d{1,2}\s+\w+\s+\d{2,4}',
                    r'\w+\s+\d{1,2},?\s+\d{2,4}'
                ]
                for pattern in date_patterns:
                    dates = re.findall(pattern, line)
                    if dates:
                        metadata['date'] = dates[0]
                        break
            
            # Extract invoice number
            if any(keyword in line for keyword in ['invoice no:', 'receipt no:', 'bill no:', 'invoice id:']):
                import re
                numbers = re.findall(r'[a-zA-Z0-9]+', line)
                if len(numbers) > 1:  # Skip the keyword itself
                    metadata['invoice_number'] = numbers[-1]
        
        return metadata
