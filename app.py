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
    - The response should be a valid JSON format.
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

# Streamlit UI
st.title('PDF Question Generator')
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

# Define the root directory for the JSON file
json_file_path = r"C:/Users/hp/Desktop/projects/nm/evaljson.json"

# Load the JSON file from the root directory
with open(json_file_path, "r") as file:
    json_data = json.load(file)

# Extract the relevant data from the JSON
score = json_data.get("mark", None)
answer_eval = json_data.get("answerEval", [])


def generate_recommendation_from_model(score, recommendation_data):
    # Create the prompt using the input JSON data
    prompt = f"""
    <Instructions>
    - The following JSON data represents the evaluation of a user's answers to 10 questions in the subject of Biology.
    - Your task is to analyze the data and provide a performance summary, areas of improvement, and suggested intensity levels.
    - The user has scored {score}.
    - Pay CLOSE ATTENTION to the question_text, answer_options, correct_option, explanation, intensity, and expected_response_time for each question, and compare these with selected_option, user_response_time, and is_correct values in the answerEval list.
    </Instructions>

    <AnswerEvaluationJSON>
    {json.dumps(answer_eval, indent=2)}
    </AnswerEvaluationJSON>

    <ExpectedOutput>
    {{
    "performance_summary": "Your detailed performance summary",
    "improvement_topics": ["Topic1", "Topic2", "Topic3"],
    "suggested_intensity_level": [0.5, 0.6, 0.7]
    }}
    </ExpectedOutput>
    """

    # Generate the recommendation using the AI model
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Construct the recommendation from the AI response
    recommendation = {
        "score": score,
        "generated_recommendation": response.text
    }
    
    return recommendation
# Create a button to trigger the suggestion generation
if st.button('Generate Suggestion'):
                    result = generate_recommendation_from_model(score, answer_eval)
                    
                    # Display the result
                    st.write(result)


# Define pdf_text globally
pdf_text = None


with st.sidebar:
    if uploaded_file and pdf_text:
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
               
                
                


    

# Call the ask_pdf function if the PDF is loaded
# Call the ask_pdf function if the PDF is loaded
if pdf_text:
            ask_pdf(pdf_text)

# Main content area for question generation and recommendation
