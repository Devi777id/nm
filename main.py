
import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
from dotenv import load_dotenv
import warnings
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


def generate_questions(pdf_text, output_file='questions.json'):
    # Define the prompt with the extracted text
    prompt = f"""
    
    Based on the provided text, generate 15 multiple-choice questions. 
    - The response should be a valid JSON list.
    Each question should be in the following format:
    1. **Question text**
       - A) Answer option A
       - B) Answer option B
       - C) Answer option C
       - D) Answer option D
    
    Provide the questions as a JSON list where each question is an object with the following structure:
    {{
        "question_text": "Question text",
        "answer_options": {{
            "A": "Answer option A",
            "B": "Answer option B",
            "C": "Answer option C",
            "D": "Answer option D"
        }},
        "correct_option": "A",
        "explanation": "Explanation for the correct answer"
    }}
    """

    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([prompt, pdf_text])
    
    # Retrieve and print the raw response for debugging
    raw_response = response.text
    print("Raw Response:", raw_response)  # For debugging purposes

    # Attempt to clean and parse the JSON response
    try:
        # Clean up the response if it contains extra information
        clean_response = raw_response.strip()
        if clean_response.startswith("<Instructions>"):
            clean_response = clean_response.split("</Instructions>")[1].strip()
        if clean_response.startswith("<Question>"):
            clean_response = clean_response.split("</Question>")[0].strip()
        
        question_list = json.loads(clean_response)
    except json.JSONDecodeError as e:
        return f"Error decoding JSON from the response: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

    # # Save questions to a JSON file
    # try:
    #     with open(output_file, 'w') as f:
    #         json.dump(question_list, f, indent=4)
    #     return f"Questions successfully saved to {output_file}."
    # except IOError as e:
    #     return f"Error saving questions to file: {e}"

# Example usage
pdf_text = "Your PDF text goes here."
result = generate_questions(pdf_text)
print(result)

# Define pdf_text globally
pdf_text = None

# Streamlit UI
st.title('PDF Question Generator')
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf") 
st.info('Please upload a PDF file to begin.')   




if uploaded_file:
            pdf_text = extract_text_from_pdf(uploaded_file)
            st.success('Text extracted successfully!')
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
                