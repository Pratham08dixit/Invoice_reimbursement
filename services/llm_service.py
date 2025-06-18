"""LLM service using Google Gemini API for invoice analysis and chatbot functionality."""

import google.generativeai as genai
from typing import Dict, List, Optional
import logging
import json
import re
from config import config

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Google Gemini API."""

    def __init__(self):
        """Initialize the Gemini LLM service."""
        api_key = config.GEMINI_API_KEY
        if api_key:
            # Remove quotes if present
            api_key = api_key.strip('"').strip("'")

        if not api_key or api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not properly configured")
            self.model = None
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            logger.info(f"Gemini LLM service initialized successfully with model: {config.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM service: {str(e)}")
            self.model = None

    def analyze_invoice_against_policy(self, invoice_content: str, policy_content: str,
                                     employee_name: str, invoice_filename: str) -> Dict:
        """
        Analyze an invoice against company reimbursement policy using Gemini.

        Args:
            invoice_content: Extracted text from the invoice
            policy_content: Company reimbursement policy text
            employee_name: Name of the employee
            invoice_filename: Name of the invoice file

        Returns:
            Dictionary containing analysis results
        """

        if not self.model:
            return self._create_error_response("Gemini API is not properly configured. Please check your API key.")

        prompt = f"""
You are an expert financial analyst tasked with analyzing employee expense reimbursements against company policy.

**COMPANY REIMBURSEMENT POLICY:**
{policy_content}

**EMPLOYEE INVOICE TO ANALYZE:**
Employee Name: {employee_name}
Invoice File: {invoice_filename}
Invoice Content:
{invoice_content}

**ANALYSIS REQUIREMENTS:**
Please analyze this invoice against the company policy and provide a detailed assessment.

**RESPONSE FORMAT (JSON):**
{{
    "reimbursement_status": "Fully Reimbursed" | "Partially Reimbursed" | "Declined",
    "reimbursement_amount": <numeric_value_or_null>,
    "total_invoice_amount": <numeric_value_or_null>,
    "reason": "<detailed_explanation_of_decision>",
    "policy_violations": ["<list_of_any_policy_violations>"],
    "approved_items": ["<list_of_approved_expense_items>"],
    "rejected_items": ["<list_of_rejected_expense_items>"],
    "invoice_date": "<extracted_date_or_null>",
    "invoice_number": "<extracted_invoice_number_or_null>",
    "expense_category": "<category_like_travel_meal_cab_etc>"
}}

**IMPORTANT GUIDELINES:**
1. Be thorough in your analysis and cite specific policy sections
2. Calculate exact reimbursement amounts based on policy limits
3. Identify all expense items and categorize them
4. Provide clear, actionable reasons for decisions
5. Extract key invoice details (date, number, amounts)
6. Ensure the response is valid JSON format

Analyze the invoice now:
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis_result = json.loads(json_str)
            else:
                # Fallback parsing if JSON is not properly formatted
                analysis_result = self._parse_fallback_response(response_text)

            # Validate required fields
            required_fields = ['reimbursement_status', 'reason']
            for field in required_fields:
                if field not in analysis_result:
                    analysis_result[field] = "Analysis incomplete"

            # Ensure status is valid
            valid_statuses = ["Fully Reimbursed", "Partially Reimbursed", "Declined"]
            if analysis_result.get('reimbursement_status') not in valid_statuses:
                analysis_result['reimbursement_status'] = "Declined"
                analysis_result['reason'] = "Unable to determine reimbursement status"

            logger.info(f"Successfully analyzed invoice: {invoice_filename}")
            return analysis_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for {invoice_filename}: {str(e)}")
            return self._create_error_response("Failed to parse analysis response")
        except Exception as e:
            logger.error(f"Error analyzing invoice {invoice_filename}: {str(e)}")
            return self._create_error_response(f"Analysis failed: {str(e)}")

    def generate_chatbot_response(self, user_query: str, search_results: List[Dict],
                                conversation_history: List[Dict] = None) -> str:
        """
        Generate a chatbot response based on user query and search results.

        Args:
            user_query: User's question
            search_results: Relevant invoice analyses from vector search
            conversation_history: Previous conversation messages

        Returns:
            Formatted response in markdown
        """

        if not self.model:
            return "I apologize, but the Gemini API is not properly configured. Please check the API key configuration."

        # Format search results for context
        context = ""
        if search_results:
            context = "**RELEVANT INVOICE ANALYSES:**\n\n"
            for i, result in enumerate(search_results[:5], 1):
                metadata = result.get('metadata', {})
                context += f"**Invoice {i}:**\n"
                context += f"- Employee: {metadata.get('employee_name', 'N/A')}\n"
                context += f"- Status: {metadata.get('reimbursement_status', 'N/A')}\n"
                context += f"- Amount: ${metadata.get('reimbursement_amount', 'N/A')}\n"
                context += f"- Date: {metadata.get('invoice_date', 'N/A')}\n"
                context += f"- Reason: {metadata.get('reason', 'N/A')}\n\n"

        # Format conversation history
        history_context = ""
        if conversation_history:
            history_context = "**CONVERSATION HISTORY:**\n"
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                history_context += f"- {msg.get('role', 'user')}: {msg.get('content', '')}\n"
            history_context += "\n"

        prompt = f"""
You are an intelligent assistant for an Invoice Reimbursement System. Your role is to help users query and understand invoice reimbursement data.

{history_context}

{context}

**USER QUERY:** {user_query}

**INSTRUCTIONS:**
1. Answer the user's question based on the provided invoice analysis data
2. If no relevant data is found, explain that clearly
3. Provide specific details from the analyses when available
4. Format your response in clear, readable markdown
5. Be helpful and professional
6. If the user asks for summaries, provide organized information
7. Include relevant statistics or patterns if applicable

**RESPONSE FORMAT:**
- Use markdown formatting (headers, lists, tables where appropriate)
- Be concise but comprehensive
- Highlight important information
- Provide actionable insights when possible

Generate your response:
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error generating chatbot response: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    def _parse_fallback_response(self, response_text: str) -> Dict:
        """
        Fallback method to parse response when JSON extraction fails.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Dictionary with parsed information
        """
        result = {
            'reimbursement_status': 'Declined',
            'reimbursement_amount': None,
            'total_invoice_amount': None,
            'reason': 'Unable to parse analysis response',
            'policy_violations': [],
            'approved_items': [],
            'rejected_items': [],
            'invoice_date': None,
            'invoice_number': None,
            'expense_category': 'Unknown'
        }

        # Try to extract status
        if 'fully reimbursed' in response_text.lower():
            result['reimbursement_status'] = 'Fully Reimbursed'
        elif 'partially reimbursed' in response_text.lower():
            result['reimbursement_status'] = 'Partially Reimbursed'

        # Try to extract amounts
        import re
        amounts = re.findall(r'\$?(\d+\.?\d*)', response_text)
        if amounts:
            try:
                result['total_invoice_amount'] = float(amounts[0])
                if len(amounts) > 1:
                    result['reimbursement_amount'] = float(amounts[1])
            except ValueError:
                pass

        # Use the full response as reason if no specific reason found
        if len(response_text) > 50:
            result['reason'] = response_text[:500] + "..." if len(response_text) > 500 else response_text

        return result

    def _create_error_response(self, error_message: str) -> Dict:
        """
        Create a standardized error response.

        Args:
            error_message: Error description

        Returns:
            Dictionary with error information
        """
        return {
            'reimbursement_status': 'Declined',
            'reimbursement_amount': None,
            'total_invoice_amount': None,
            'reason': error_message,
            'policy_violations': [],
            'approved_items': [],
            'rejected_items': [],
            'invoice_date': None,
            'invoice_number': None,
            'expense_category': 'Error'
        }
