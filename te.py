import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.environ["API_KEY"])

# Store LLM generated responses
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

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

    if response.candidate.safety_ratings and not response.candidate.safety_ratings.is_safe:
        raise ValueError("Response was blocked due to safety ratings.")

    if hasattr(response, 'text'):
        return response.text
    else:
        raise ValueError("Response does not contain valid text.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# User-provided PDF upload
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file:
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.success('Text extracted successfully!')

    # Button to generate questions
    if st.sidebar.button('Generate Questions'):
        with st.spinner('Generating questions...'):
            try:
                questions = generate_questions(pdf_text)
                questions_list = json.loads(questions)

                # Format and display questions
                question_display = "### Generated Questions\n"
                for idx, question in enumerate(questions_list):
                    question_display += f"**Question {idx + 1}:** {question['question_text']}\n"
                    question_display += f"**Topic:** {question['topic']} | **Subtopic:** {question['subtopic']}\n"
                    question_display += "Options:\n"
                    for option, answer in question['answer_options'].items():
                        question_display += f"- **{option}:** {answer}\n"
                    question_display += f"**Correct Answer:** {question['correct_option']}\n"
                    question_display += f"**Explanation:** {question['explanation']}\n---\n"
                st.markdown(question_display)
                
                st.session_state.messages.append({"role": "assistant", "content": question_display})

            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check the output from the Gemini model.")
            except ValueError as e:
                st.error(str(e))

# User input for additional questions
if prompt := st.chat_input("Ask a question about the PDF:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Handle user query here
    # (You can implement the ask_pdf functionality if needed)
