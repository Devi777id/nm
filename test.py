import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
from dotenv import load_dotenv
import json

# Load environment variables
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

# Function to generate questions
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

# Streamlit UI Configuration
st.set_page_config(page_title='PDF Question Generator', layout='wide', initial_sidebar_state='expanded')

# Set Theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;  /* Light background */
    }
    .css-1d391kg {  /* Header style */
        background-color: #1E90FF;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('PDF Question Generator')
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file:
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.success('Text extracted successfully!')

    # Button to generate questions
    if st.button('Generate Questions'):
        with st.spinner('Generating questions...'):
            questions = generate_questions(pdf_text)

            # Display the generated questions in a neat format
            st.markdown("### Generated Questions")
            try:
                question_list = json.loads(questions)
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
