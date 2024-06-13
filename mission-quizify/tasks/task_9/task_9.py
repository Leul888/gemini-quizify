import streamlit as st
import os
import sys
import json
sys.path.append(os.path.abspath('../../'))
from tasks.task_3.task_3 import DocumentProcessor
from tasks.task_4.task_4 import EmbeddingClient
from tasks.task_5.task_5 import ChromaCollectionCreator
from tasks.task_8.task_8 import QuizGenerator

class QuizManager:
    def __init__(self, questions: list):
        self.questions = questions
        self.total_questions = len(questions)

    def get_question_at_index(self, index: int):
        if self.total_questions == 0:
            return None
        valid_index = index % self.total_questions
        return self.questions[valid_index]

    def next_question_index(self, direction=1):
        if self.total_questions == 0:
            return
        current_index = st.session_state["question_index"]
        current_index += direction
        current_index = current_index % self.total_questions
        st.session_state["question_index"] = current_index

if __name__ == "__main__":
    embed_config = {
        "model_name": "textembedding-gecko@003",
        "project": "myradicalai",
        "location": "us-central1"
    }

    # Initialize session state variables if they do not exist
    if "question_bank" not in st.session_state:
        st.session_state.question_bank = []
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0

    screen = st.empty()
    with screen.container():
        st.header("Quiz Builder")
        processor = DocumentProcessor()
        processor.ingest_documents()

        embed_client = EmbeddingClient(**embed_config)

        chroma_creator = ChromaCollectionCreator(processor, embed_client)

        question = None
        question_bank = None

        with st.form("Load Data to Chroma"):
            st.subheader("Quiz Builder")
            st.write("Select PDFs for Ingestion, the topic for the quiz, and click Generate!")

            topic_input = st.text_input("Topic for Generative Quiz", placeholder="Enter the topic of the document")
            questions = st.slider("Number of Questions", min_value=1, max_value=10, value=1)

            submitted = st.form_submit_button("Submit")
            if submitted:
                chroma_creator.create_chroma_collection()
                st.write(topic_input)

                # Test the Quiz Generator
                generator = QuizGenerator(topic_input, questions, chroma_creator)
                question_bank = generator.generate_quiz()
                st.session_state.question_bank = question_bank

    if st.session_state.question_bank:
        screen.empty()
        with st.container():
            st.header("Generated Quiz Question: ")

            quiz_manager = QuizManager(st.session_state.question_bank)
            index_question = quiz_manager.get_question_at_index(st.session_state.question_index)

            if index_question:
                with st.form("Multiple Choice Question"):
                    choices = [choice['value'] for choice in index_question['choices']]
                    st.write(index_question["question"])

                    answer = st.radio('Choose the correct answer', choices, key="radio_select")

                    submit_button = st.form_submit_button("Submit")
                    if submit_button:
                        correct_answer_key = index_question['answer']
                        if answer.startswith(correct_answer_key):
                            st.success("Correct!")
                        else:
                            st.error("Incorrect!")

                next_button = st.button("Next")
                if next_button:
                    quiz_manager.next_question_index(1)
                    st.experimental_rerun()
    else:
        st.write("No questions generated yet.")
