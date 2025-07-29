import time

import streamlit as st
from query_flow import run_query_pipeline


def streamlit_page():
    """Main RAG application page"""
    st.title("🤖 Recurser - Intelligent Search Assistant")
    st.markdown(
        "Ask complex questions and let our AI-powered RAG pipeline find comprehensive answers from the web."
    )

    # Add some styling
    st.markdown(
        """
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }

        /* Hover effect for Get Answer button only */
    .stButton > button:hover {
        cursor: pointer;
        transform: translateY(-2px);
        transition: transform 0.2s ease;
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Enhanced text area styling */
    .stTextArea > div > div > textarea {
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        transition: border-color 0.3s ease;
    }

    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Progress bar enhancement */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Query input section
    with st.container():
        user_query = st.text_area(
            "",
            placeholder="e.g., What are the latest developments in quantum computing?",
            height=100,
            help="Ask any question and our AI will search the web and provide a comprehensive answer.",
        )

    # Submit button with enhanced styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_button = st.button(
            "🚀 Get Answer",
            type="primary",
            use_container_width=True,
            disabled=not user_query.strip(),
        )

    # Processing section
    if submit_button and user_query.strip():
        # Clear previous results
        if "previous_result" in st.session_state:
            del st.session_state["previous_result"]

        # Create a container for the processing area
        processing_container = st.container()

        with processing_container:
            st.markdown("---")
            st.subheader("🔄 Processing Your Query")

            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Start processing
            start_time = time.time()

            # Update progress
            progress_bar.progress(10)
            status_text.text("Initializing pipeline...")

            # Run the query pipeline
            try:
                result = run_query_pipeline(user_query)

                # Update progress
                progress_bar.progress(100)
                status_text.text("Complete!")

                # Calculate processing time
                processing_time = time.time() - start_time

                # Display results
                st.markdown("---")
                st.subheader("📋 Results")

                # Show processing time
                st.caption(f"⏱️ Processing time: {processing_time:.2f} seconds")

                # Display the answer
                if result.get("error", False):
                    st.error("❌ Error occurred during processing")
                    st.markdown(
                        f"**Error Details:** {result.get('answer', 'Unknown error')}"
                    )
                else:
                    st.success("✅ Answer Generated Successfully!")

                    # Display the answer in a nice format
                    answer = result.get("answer", "No answer was generated.")

                    # Create a styled answer box
                    st.markdown(
                        f"""
                    <div style="
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        padding: 1.5rem;
                        border-radius: 10px;
                        border-left: 5px solid #667eea;
                        margin: 1rem 0;
                    ">
                        <h4 style="margin-top: 0; color: #2c3e50;">Answer:</h4>
                        <p style="margin-bottom: 0; line-height: 1.6; color: #34495e;">{answer}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Store result for potential reuse
                    st.session_state["previous_result"] = result

                    # Add action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(
                            "🔄 Ask Another Question", use_container_width=True
                        ):
                            st.rerun()
                    with col2:
                        if st.button("📋 Copy Answer", use_container_width=True):
                            st.write("Answer copied to clipboard!")
                    with col3:
                        if st.button("📊 View Analytics", use_container_width=True):
                            st.query_params = {"page": "analytics"}
                            st.rerun()

            except Exception as e:
                progress_bar.progress(0)
                status_text.text("Error occurred!")
                st.error(f"❌ An unexpected error occurred: {str(e)}")
                st.info(
                    "Please try again or check if all services are running properly."
                )

    # Show previous result if available
    elif "previous_result" in st.session_state and not submit_button:
        st.markdown("---")
        st.subheader("📋 Previous Result")
        result = st.session_state["previous_result"]

        if not result.get("error", False):
            answer = result.get("answer", "No answer was generated.")
            st.markdown(
                f"""
            <div style="
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 5px solid #667eea;
                margin: 1rem 0;
            ">
                <h4 style="margin-top: 0; color: #2c3e50;">Previous Answer:</h4>
                <p style="margin-bottom: 0; line-height: 1.6; color: #34495e;">{answer}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
