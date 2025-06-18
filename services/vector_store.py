"""FAISS-based vector store for storing and retrieving invoice analysis embeddings."""

import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import logging
import uuid
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    """FAISS-based vector store for invoice reimbursement analysis."""
    
    def __init__(self):
        """Initialize the FAISS vector store."""
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.metadata = []  # Store metadata for each vector
        self.id_to_index = {}  # Map document IDs to index positions
        
        # Ensure vector DB directory exists
        os.makedirs(config.VECTOR_DB_PATH, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def add_invoice_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """
        Add an invoice analysis to the vector store.
        
        Args:
            analysis_data: Dictionary containing invoice analysis results
            
        Returns:
            Document ID for the stored analysis
        """
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Create text content for embedding
            content_parts = [
                f"Employee: {analysis_data.get('employee_name', '')}",
                f"Status: {analysis_data.get('reimbursement_status', '')}",
                f"Amount: {analysis_data.get('reimbursement_amount', '')}",
                f"Reason: {analysis_data.get('reason', '')}",
                f"Invoice Content: {analysis_data.get('invoice_content', '')[:500]}",  # Truncate for embedding
                f"Category: {analysis_data.get('expense_category', '')}",
                f"Date: {analysis_data.get('invoice_date', '')}"
            ]
            
            content_text = " ".join(content_parts)
            
            # Generate embedding
            embedding = self.embedding_model.encode([content_text])
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding)
            
            # Add to index
            self.index.add(embedding)
            
            # Store metadata
            metadata = {
                'doc_id': doc_id,
                'employee_name': analysis_data.get('employee_name'),
                'invoice_filename': analysis_data.get('invoice_filename'),
                'reimbursement_status': analysis_data.get('reimbursement_status'),
                'reimbursement_amount': analysis_data.get('reimbursement_amount'),
                'total_invoice_amount': analysis_data.get('total_invoice_amount'),
                'reason': analysis_data.get('reason'),
                'invoice_date': analysis_data.get('invoice_date'),
                'invoice_number': analysis_data.get('invoice_number'),
                'expense_category': analysis_data.get('expense_category'),
                'policy_violations': analysis_data.get('policy_violations', []),
                'approved_items': analysis_data.get('approved_items', []),
                'rejected_items': analysis_data.get('rejected_items', []),
                'content_text': content_text,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metadata.append(metadata)
            self.id_to_index[doc_id] = len(self.metadata) - 1
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Added invoice analysis to vector store: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding invoice analysis to vector store: {str(e)}")
            raise
    
    def search(self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar invoice analyses.
        
        Args:
            query: Search query text
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching documents with metadata and scores
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("Vector store is empty")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding, min(k * 2, self.index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                metadata = self.metadata[idx].copy()
                metadata['similarity_score'] = float(score)
                
                # Apply filters if provided
                if filters and not self._matches_filters(metadata, filters):
                    continue
                
                results.append({
                    'metadata': metadata,
                    'score': float(score)
                })
            
            # Sort by score and return top k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def get_all_analyses(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all invoice analyses, optionally filtered.
        
        Args:
            filters: Optional metadata filters
            
        Returns:
            List of all matching analyses
        """
        results = []
        
        for metadata in self.metadata:
            if filters and not self._matches_filters(metadata, filters):
                continue
            
            results.append({
                'metadata': metadata,
                'score': 1.0  # No similarity score for direct retrieval
            })
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the stored analyses.
        
        Returns:
            Dictionary containing various statistics
        """
        if not self.metadata:
            return {
                'total_analyses': 0,
                'employees': [],
                'status_distribution': {},
                'total_reimbursed': 0,
                'average_reimbursement': 0
            }
        
        # Calculate statistics
        employees = list(set(m.get('employee_name') for m in self.metadata if m.get('employee_name')))
        
        status_counts = {}
        total_reimbursed = 0
        reimbursement_amounts = []
        
        for metadata in self.metadata:
            status = metadata.get('reimbursement_status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            amount = metadata.get('reimbursement_amount')
            if amount and isinstance(amount, (int, float)):
                total_reimbursed += amount
                reimbursement_amounts.append(amount)
        
        avg_reimbursement = sum(reimbursement_amounts) / len(reimbursement_amounts) if reimbursement_amounts else 0
        
        return {
            'total_analyses': len(self.metadata),
            'employees': employees,
            'status_distribution': status_counts,
            'total_reimbursed': total_reimbursed,
            'average_reimbursement': avg_reimbursement,
            'reimbursement_count': len(reimbursement_amounts)
        }
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if metadata matches the provided filters.
        
        Args:
            metadata: Document metadata
            filters: Filter criteria
            
        Returns:
            True if metadata matches all filters
        """
        for key, value in filters.items():
            if key not in metadata:
                continue
            
            metadata_value = metadata[key]
            
            # Handle different filter types
            if isinstance(value, str):
                if isinstance(metadata_value, str):
                    if value.lower() not in metadata_value.lower():
                        return False
                else:
                    if str(metadata_value).lower() != value.lower():
                        return False
            elif isinstance(value, (int, float)):
                if metadata_value != value:
                    return False
            elif isinstance(value, list):
                if metadata_value not in value:
                    return False
        
        return True
    
    def _save_index(self):
        """Save the FAISS index and metadata to disk."""
        try:
            index_path = os.path.join(config.VECTOR_DB_PATH, config.INDEX_FILE)
            metadata_path = os.path.join(config.VECTOR_DB_PATH, config.METADATA_FILE)
            
            # Save FAISS index
            faiss.write_index(self.index, index_path)
            
            # Save metadata
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'id_to_index': self.id_to_index
                }, f)
            
            logger.info("Vector store saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
    
    def _load_index(self):
        """Load existing FAISS index and metadata from disk."""
        try:
            index_path = os.path.join(config.VECTOR_DB_PATH, config.INDEX_FILE)
            metadata_path = os.path.join(config.VECTOR_DB_PATH, config.METADATA_FILE)
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(index_path)
                
                # Load metadata
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata = data.get('metadata', [])
                    self.id_to_index = data.get('id_to_index', {})
                
                logger.info(f"Loaded vector store with {len(self.metadata)} documents")
            else:
                logger.info("No existing vector store found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            # Reset to empty state on error
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
            self.id_to_index = {}

# Global instance
vector_store = FAISSVectorStore()
