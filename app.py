import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
from dotenv import load_dotenv
from fpdf import FPDF
import json

load_dotenv()
genai.configure(api_key=os.environ["API_KEY"])

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    extracted_text = ""
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text
    return extracted_text

# Function to converse with the PDF (moved to sidebar)
def ask_pdf(pdf_text):
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
        
    # Ensure session state for the text input is set up correctly
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""

    # Use session state to handle the input field
    user_query = st.sidebar.text_input("Ask a question about the PDF:", key="pdf_ask_input_sidebar", value=st.session_state.user_query)

    if st.sidebar.button("Submit Question", key="submit_btn_sidebar"):
        if user_query:
            # Append user's query to the conversation
            st.session_state.conversation.append({"role": "user", "text": user_query})

            prompt = f"""
            {pdf_text}

            Based on the text above, answer the following question: {user_query}
            Your answers should be only based on the provided PDF file.
            """
            
            with st.spinner("Generating response..."):
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                response = model.generate_content(prompt)
                # Append AI's response to the conversation
                st.session_state.conversation.append({"role": "ai", "text": response.text})
            
            # Clear the user query in session state after submitting
            st.session_state.user_query = ""

    # Display the conversation history
    for exchange in reversed(st.session_state.conversation):
        if exchange["role"] == "user":
            st.sidebar.markdown(f"**You:** {exchange['text']}")
        else:
            st.sidebar.markdown(f"**AI:** {exchange['text']}")


# Function to generate content and format it in plain text
def generate_questions(pdf_text):
    prompt = f"""
    <Instructions>
    - Use the provided PDF file only to create questions.
    - The response should be a plain text format.
    </Instructions>
    <Question>
    Generate 15 questions for the subject based on the provided text. Each question should follow this schema:
    1. Question: "question"
    2. Topic: "topic_name"
    3. Subtopic: "sub_topic_name" 
    
    4. Answer Options:
       - A: "answer 1"
       - B: "answer 2"
       - C: "answer 3"
       - D: "answer 4"
    5. Correct Option: "answer 2"
    6. Explanation: "explanation for the correct answer"
    7. Intensity: 0.8
    </Question>
    """

    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([prompt, pdf_text])

    questions_text = response.text
    return questions_text

# Streamlit UI
st.title('PDF Question Generator')
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success('Text extracted successfully!')
        # Add the ask_pdf function to the sidebar
        with st.sidebar:
            if uploaded_file:
                ask_pdf(pdf_text)

        # Button to generate questions
        if st.button('Generate Questions'):
            with st.spinner('Generating questions...'):
                questions = generate_questions(pdf_text)

                # Display the generated questions in a neat format
                st.markdown("### Generated Questions")
                st.write(questions)  # You can parse and display JSON as needed
                # score = st.number_input("Enter your score (0-10):", max_value=10, step=1)

                try:
                        question_list = json.loads(questions)  # Use json.loads to parse JSON
                        for idx, question in enumerate(question_list):
                            st.markdown(f"**Question {idx+1}: {question['question_text']}**")
                            st.markdown(f"**Topic:** {question['topic']} | **Subtopic:** {question['subtopic']}")
                            st.markdown("Options:")
                            for option, answer in question['answer_options'].items():
                                st.markdown(f"- **{option}:** {answer}")

                            st.markdown(f"**Correct Answer:** {question['correct_option']}")

                            st.markdown(f"**Explanation:** {question['explanation']}")
                            st.markdown("---")

                        
                except json.JSONDecodeError:
                        st.error("Invalid JSON format. Please check the output from the Gemini model.")
