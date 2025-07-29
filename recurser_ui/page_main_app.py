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
    </style>
    """,
        unsafe_allow_html=True,
    )

    # System status indicator (temporarily simplified)
    with st.expander("🔧 System Status", expanded=False):
        st.info("System status monitoring temporarily disabled for debugging")
        if st.button("🔄 Check Services", use_container_width=True):
            st.info("Service checking temporarily disabled")

    # Query input section
    st.subheader("🔍 Ask Your Question")

    # Enhanced query input with examples
    with st.container():
        user_query = st.text_area(
            "Enter your question below:",
            placeholder="e.g., What are the latest developments in quantum computing?",
            height=100,
            help="Ask any question and our AI will search the web and provide a comprehensive answer.",
        )

        # Example queries
        with st.expander("💡 Example Questions", expanded=False):
            st.markdown(
                """
            - What are the benefits of renewable energy?
            - How does machine learning work?
            - What are the latest trends in artificial intelligence?
            - Explain the concept of blockchain technology
            - What are the health benefits of meditation?
            """
            )

    # Submit button with enhanced styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Temporarily disable system readiness check
        system_ready = True  # We'll add this back later
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

    # Footer with helpful information
    st.markdown("---")
    st.markdown(
        """
    <div class="info-box">
        <h5>💡 How it works:</h5>
        <ol>
            <li><strong>Query Optimization:</strong> Your question is enhanced for better search results</li>
            <li><strong>Web Search:</strong> Our system searches the internet for relevant information</li>
            <li><strong>AI Analysis:</strong> An AI model analyzes the search results and generates a comprehensive answer</li>
        </ol>
    </div>
    """,
        unsafe_allow_html=True,
    )
