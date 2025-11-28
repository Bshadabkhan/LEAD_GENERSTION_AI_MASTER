import streamlit as st
import os


def render_sidebar():
    """Render the sidebar and handle configuration options.
    
    Returns:
        dict: Contains user configuration options
    """
      
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        #st.markdown("<h2 class='sub-header'>Advanced Options</h2>", unsafe_allow_html=True)
        
        # Add API key configurations
        with st.expander("🔑 API Keys", expanded=True):
            st.info("API keys are stored temporarily in memory and cleared when you close the browser.")
            
            # OpenAI API Key input
            openai_api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="Enter your OpenAI API key",
                help="Enter your OpenAI API key"
            )
            if openai_api_key:
                os.environ["OPENAI_API_KEY"] = openai_api_key
                
            # Exa API Key input
            serp_api_key = st.text_input(
                "Serper API Key",
                type="password",
                placeholder="Enter your Serper API key",
                help="Enter your Serper API key for web search capabilities"
            )
            if serp_api_key:
                os.environ["SERPER_API_KEY"] = serp_api_key
        
                
        # Add information expander
        with st.expander("ℹ️ About", expanded=False):
            st.markdown("""
                This lead generation tool uses OpenAI models and Serper API to help you:
                - Research market opportunities
                - Generate potential leads
                - Qualify leads
                - Research contact information
                        
                Enter your OpenAI API key to get started. The Serper API key enables 
                web search for more up-to-date market information.
            """)
            
        # Add a cost tracking section at the bottom of sidebar
        st.divider()
        with st.expander("💰 Usage Metrics", expanded=True):
            # Add a small note about the model used
            st.info("Using gpt-4o-mini pricing")
        
        
    return {
        "has_openai_key": bool(openai_api_key),
        "has_serp_key": bool(serp_api_key)
    } 