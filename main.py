import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()

# Configure the Google Generative AI API with your API key
genai.configure(api_key=os.environ["API_KEY"])

# Define the root directory for the JSON file
json_file_path = r"C:/Users/hp/Desktop/projects/nm/evaljson.json"

# Load the JSON file from the root directory
with open(json_file_path, "r") as file:
    json_data = json.load(file)

# Extract the relevant data from the JSON
score = json_data.get("mark", None)
answer_eval = json_data.get("answerEval", [])

# Function to generate recommendation based on the model
def generate_recommendation_from_model(score, answer_eval):
    # Create the prompt using the input JSON data
    prompt = f"""
    <Instructions>
    - The following JSON data represents the evaluation of a user's answers to 10 questions in the subject of Biology.
    - Your task is to analyze the data and provide a performance summary, areas of improvement, and suggested intensity levels.
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
