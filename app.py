import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
from dotenv import load_dotenv
import warnings
import json

load_dotenv()

genai.configure(api_key=os.environ["API_KEY"])


# Function to extract text from PDf
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    extracted_text = ""
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text
    return extracted_text

# Function to converse with the PDF
def ask_pdf(pdf_text):
    # Initialize session state for the conversation history if not already initialized
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    # Use static keys for both text_input and button
    user_query = st.text_input("Ask a question about the PDF:", key="pdf_ask_input")

    if st.button("Submit", key="submit_btn"):
        if user_query:
            # Append the user query to the conversation history
            st.session_state.conversation.append({"role": "user", "text": user_query})

            # Prepare the prompt for the AI model
            prompt = f"""
            {pdf_text}

            Based on the text above, answer the following question: {user_query}
            Your answers should be only based on the provided PDF file.
            """

            with st.spinner("Generating response..."):
                    # Generate response from the AI model
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                    response = model.generate_content(prompt)

                    # Append the AI's response to the conversation history
                    st.session_state.conversation.append({"role": "ai", "text": response.text})
    # Display the conversation history
    for exchange in reversed(st.session_state.conversation):
        if exchange["role"] == "user":
            st.markdown(f"**You:** {exchange['text']}")
        else:
            st.markdown(f"**AI:** {exchange['text']}")


        
# Function to generate content and format it in markdown
def generate_questions(pdf_text):
    # Define the prompt with the extracted text
    prompt = f"""
    <Instructions>
    - Use the provided pdf file only to create questions.
    - The response should be a JSON list.
    </Instructions>
    <Question>
    Generate 15 questions for the subject  based on the provided text. Each question should follow this schema:
    {{
    subject: "",
    question_text: "question",
    topic: "topic_name",
    subtopic: "sub_topic_name",
    answer_options: {{
    "A": "answer 1",
    "B": "answer 2",
    "C": "answer 3",
    "D": "answer 4"
    }},
    correct_option: "answer 2",
    explanation: "explanation for the correct answer",
    intensity: 0.8,
    expected_response_time: 30,
    normalized_response_time: 0.5
    }}
    </Question>
    """
    
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([prompt, pdf_text])
    
    questions = response.text

    return questions

# Function to generate a recommendation based on score
def generate_recommendation(score, pdf_text):
    prompt = f"""
    The user has a score of {score}/5 on their evaluation. 
    Based on the score provided, generate a personalized recommendation using only the contents of the uploaded PDF file. 
    The recommendation should include a detailed roadmap for the user to follow. 
    Display the recommendation only after the PDF file is uploaded and the score has been entered
    If the score is:
    - 0-3: Very low performance, provide a detailed plan for improvement.
    - 4-6: Below average performance, suggest some improvements.
    - 7-9: Good performance, suggest ways to enhance further.
    - 10: Excellent performance, provide encouragement and advanced tips.
    Text: {pdf_text}

    Response:
    """
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(prompt)

    recommendation = response.text
    return recommendation


# Define pdf_text globally
pdf_text = None

# Streamlit UI
st.title('PDF Question Generator')
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
with st.sidebar:
    if uploaded_file and pdf_text:
        st.info('Please upload a PDF file to begin.')

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success('Text extracted successfully!')
        score = st.number_input("Enter your score (0-10):", max_value=10, step=1)
        # Button to generate questions
        if st.button('Generate Questions'):
            with st.spinner('Generating questions...'):
                questions = generate_questions(pdf_text)

                # Display the generated questions in a neat format
                st.markdown("### Generated Questions")
                st.write(questions)  # You can parse and display JSON as needed

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
               

                if score is not None:
                    recommendation = generate_recommendation(score, pdf_text)
                    st.markdown("### Recommendation")
                    st.write(recommendation)

                

    

# Call the ask_pdf function if the PDF is loaded
# Call the ask_pdf function if the PDF is loaded
if pdf_text:
            ask_pdf(pdf_text)

# Main content area for question generation and recommendation
