from langchain.chains import RetrievalQA

class GeneratorService:
    def __init__(self, qa_chain: RetrievalQA):
        if not qa_chain:
            raise ValueError("QA Chain must be initialized before GeneratorService.")
        self.qa_chain = qa_chain

    def generate_flashcards(self, topic: str):
        """
        Generates professional flashcards based on the document and a given topic.
        Each flashcard includes a clear question on the front and a concise answer on the back.
        """
        prompt = f"""
        Based on the provided document, generate 5 professional flashcards about the topic: '{topic}'.
        Each flashcard should have a 'Front' (question) and a 'Back' (answer).
        Ensure the questions are clear and the answers are concise and directly relevant to the document.
        Format the output as a JSON array of objects, like this:
        [
            {{
                "front": "Question 1",
                "back": "Answer 1"
            }},
            {{
                "front": "Question 2",
                "back": "Answer 2"
            }}
        ]
        """
        try:
            result = self.qa_chain.run(prompt)
            return result
        except Exception as e:
            raise Exception(f"Failed to generate flashcards: {e}")

    def generate_quiz(self, part: int):
        """
        Generates a professional TOEIC-style quiz question for a specific part.
        The question should be relevant to the document, and include four options (A, B, C, D)
        with one correct answer.
        """
        if not (1 <= part <= 7):
            raise ValueError("TOEIC part must be between 1 and 7.")

        prompt = f"""
        Based on the provided document, create one professional TOEIC-style multiple-choice question for Part {part}.
        The question should be challenging but fair, and directly related to the content.
        Provide four distinct answer options (A, B, C, D), only one of which is correct.
        Clearly indicate the correct answer.

        Format the output as a JSON object, like this:
        {{
            "question": "What is the main idea of the passage?",
            "options": {{
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_answer": "B"
        }}
        """
        try:
            result = self.qa_chain.run(prompt)
            return result
        except Exception as e:
            raise Exception(f"Failed to generate quiz: {e}")
