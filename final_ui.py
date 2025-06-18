"""
Final Clean Streamlit UI for Invoice Reimbursement System
NO SIDEBAR - NO SAMPLE DATA OPTIONS - Only essential features
"""

import streamlit as st
import requests
import json

# Page configuration - disable sidebar
st.set_page_config(
    page_title="Invoice Reimbursement System", 
    page_icon="💰",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely
st.markdown("""
<style>
    .css-1d391kg {display: none}
    .css-1rs6os {display: none}
    .css-17eq0hr {display: none}
    section[data-testid="stSidebar"] {display: none}
    .css-1lcbmhc {display: none}
    .css-1outpf7 {display: none}
    .css-1y4p8pa {display: none}
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_connection():
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main application."""
    
    st.title("💰 Invoice Reimbursement System")
    
    # Check API connection
    if not check_api_connection():
        st.error("🚨 Backend API is not running!")
        st.info("Please start the FastAPI server first:")
        st.code("python main.py")
        st.stop()
    
    # Only 2 tabs - no sidebar, no sample data
    tab1, tab2 = st.tabs(["📁 Analyze Invoices", "💬 Ask Questions"])
    
    with tab1:
        show_analysis_page()
    
    with tab2:
        show_questions_page()

def show_analysis_page():
    """Show invoice analysis page."""
    st.header("Analyze Invoices")
    
    # Employee name
    employee_name = st.text_input("Employee Name:")
    
    # File uploads
    policy_file = st.file_uploader("Upload Policy PDF:", type=['pdf'])
    invoices_zip = st.file_uploader("Upload Invoices ZIP:", type=['zip'])
    
    # Analyze button
    if st.button("Start Analysis", type="primary"):
        if employee_name and policy_file and invoices_zip:
            with st.spinner("Analyzing invoices..."):
                try:
                    # Prepare files
                    files = {
                        'policy_file': ('policy.pdf', policy_file.getvalue(), 'application/pdf'),
                        'invoices_zip': ('invoices.zip', invoices_zip.getvalue(), 'application/zip')
                    }
                    data = {'employee_name': employee_name}
                    
                    # Make API request
                    response = requests.post(f"{API_BASE_URL}/analyze-invoices", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Analysis completed!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Processed Invoices", result.get('processed_invoices', 0))
                        with col2:
                            st.metric("Errors", len(result.get('errors', [])))
                        
                        st.info(result.get('message', 'Analysis completed'))
                        
                        if result.get('errors'):
                            st.subheader("Errors:")
                            for error in result['errors']:
                                st.error(error)
                                
                        st.success("💡 Now go to 'Ask Questions' tab to query your data!")
                        
                    else:
                        st.error(f"❌ Analysis failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.error("Please provide employee name, policy PDF, and invoices ZIP")

def show_questions_page():
    """Show questions/chat page."""
    st.header("Ask Questions")
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Chat input
    user_question = st.text_input("Ask a question about the analyzed invoices:")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        ask_button = st.button("Ask", type="primary")
    with col2:
        if st.button("Clear Chat"):
            st.session_state.messages = []
            if 'session_id' in st.session_state:
                del st.session_state.session_id
            st.rerun()
    
    # Process question
    if ask_button and user_question:
        process_question(user_question)
    
    # Sample questions
    st.subheader("Sample Questions")
    sample_questions = [
        "Show me all invoice analyses",
        "What's the total reimbursement amount?",
        "List all declined reimbursements",
        "Show expenses by employee",
        "What are the policy violations?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(question, key=f"sample_{i}"):
                process_question(question)
    
    # Display chat history
    if st.session_state.messages:
        st.markdown("---")
        st.subheader("Conversation")
        
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.write(f"**👤 You:** {message['content']}")
            else:
                st.write(f"**🤖 Assistant:** {message['content']}")
            st.write("")

def process_question(question):
    """Process a user question."""
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    
    with st.spinner("🤔 Getting answer..."):
        try:
            payload = {
                'query': question,
                'session_id': st.session_state.get('session_id')
            }
            
            response = requests.post(f"{API_BASE_URL}/chat", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.session_id = result.get('session_id')
                
                # Add assistant response
                assistant_response = result.get('response', 'No response received')
                
                # Add sources info if available
                sources = result.get('sources', [])
                if sources:
                    assistant_response += f"\n\n📚 **Sources:** {len(sources)} documents referenced"
                
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            else:
                error_msg = f"❌ Error: {response.status_code} - {response.text}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Rerun to update display
    st.rerun()

if __name__ == "__main__":
    main()
