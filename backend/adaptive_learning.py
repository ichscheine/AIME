import os
import random
from collections import defaultdict
from openai import OpenAI, OpenAIError
from pymongo import MongoClient

# Initialize the OpenAI client using the API key from the environment
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Connect to MongoDB and define collections
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client['amc10_test']
adaptive_collection = db['adaptive_learning']
raw_solutions_collection = db['solutions']
# problems_collection is not used for adaptive generation now

# (Optional) Retain the RLAgent for future use.
class RLAgent:
    def __init__(self, actions, epsilon=0.2, alpha=0.5, gamma=0.9):
        self.q_table = defaultdict(float)  # Default value for non-existent keys
        self.actions = actions
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma

    def get_q(self, state, action):
        return self.q_table[(state, action)]

    def select_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        else:
            q_values = [self.get_q(state, a) for a in self.actions]
            max_q = max(q_values)
            best_actions = [a for a, q in zip(self.actions, q_values) if q == max_q]
            return random.choice(best_actions)

    def update(self, state, action, reward, next_state):
        current_q = self.get_q(state, action)
        next_max = max([self.get_q(next_state, a) for a in self.actions])
        new_q = current_q + self.alpha * (reward + self.gamma * next_max - current_q)
        self.q_table[(state, action)] = new_q

def generate_solution_summary(raw_solution, variant_label):
    """
    Generate a concise, smart, and fast summary of the raw solution.
    variant_label (e.g., "Variant 1") can be used to prompt different stylistic approaches.
    """
    prompt = (
        f"You are an expert AMC 10 math tutor. Summarize the following solution in a concise and clear manner. "
        f"Variant: {variant_label}.\n\n"
        f"Raw Solution:\n{raw_solution}\n\n"
        "Concise Summary:"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert AMC 10 math tutor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except OpenAIError as e:
        print(f"OpenAI API Error in generate_solution_summary: {e}")
        return "Error generating solution summary."

def generate_solution_summaries(raw_solution):
    """
    Generate 3 solution summaries (variants) from the raw solution.
    Returns a list of summaries.
    """
    summaries = []
    variants = ["Variant 1", "Variant 2", "Variant 3"]
    for variant in variants:
        summary = generate_solution_summary(raw_solution, variant)
        summaries.append(summary)
    return summaries

def generate_followup_question(problem_text, difficulty):
    """
    Generate a follow-up AMC 10 problem similar to the original.
    The follow-up problem tests the same concept at the specified difficulty.
    """
    prompt = (
        "You are an expert AMC 10 math tutor who creates clear and visually supported practice problems. "
        "Based solely on the following problem, generate a similar follow-up problem at "
        f"{difficulty} difficulty. The new problem should test the same concept with a slight variation. "
        "Include a diagram (in ASCII or textual format) that clearly illustrates the configuration of the figures. "
        "Be concise.\n\n"
        f"Original Problem:\n{problem_text}\n\n"
        "Follow-up Problem:"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert AMC 10 math tutor who creates clear, detailed problems."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        followup_question = response.choices[0].message.content.strip()
        return followup_question
    except OpenAIError as e:
        print(f"OpenAI API Error in generate_followup_question: {e}")
        return "Error generating follow-up question."

def generate_followup_questions(problem_text):
    """
    Generate 3 follow-up questions with difficulty levels: easy, medium, and hard.
    Returns a dictionary mapping difficulty to follow-up question.
    """
    difficulties = ["easy", "medium", "hard"]
    questions = {}
    for diff in difficulties:
        question = generate_followup_question(problem_text, diff)
        questions[diff] = question
    return questions

def save_adaptive_data(problem_metadata, solution_summaries, followup_questions):
    """
    Save the pre-generated adaptive data (solution summaries and follow-up questions)
    into the adaptive_learning collection.
    """
    adaptive_doc = {
        "year": problem_metadata.get("year"),
        "contest": problem_metadata.get("contest"),
        "problem_number": problem_metadata.get("problem_number"),
        "problem_text": problem_metadata.get("problem_text"),
        "solution_summaries": solution_summaries,
        "followup_questions": followup_questions
    }
    result = adaptive_collection.insert_one(adaptive_doc)
    print(f"Adaptive data saved with ID: {result.inserted_id}")
    return str(result.inserted_id)

def pre_generate_adaptive_data(problem_metadata):
    """
    Given a problem's metadata (including problem_text), pre-generate adaptive learning data.
    Steps:
      1. Fetch the raw solution from the 'solutions' collection using metadata (year, contest, problem_number).
      2. Generate 3 concise solution summaries from the raw solution.
      3. Generate 3 follow-up questions (for easy, medium, and hard difficulty) from the problem text.
      4. Save both in the 'adaptive_learning' collection.
    Returns the adaptive document ID.
    """
    query = {
        "year": problem_metadata.get("year"),
        "contest": problem_metadata.get("contest"),
        "problem_number": problem_metadata.get("problem_number")
    }
    raw_solution_doc = raw_solutions_collection.find_one(query)
    if raw_solution_doc and "solution" in raw_solution_doc:
        raw_solution = raw_solution_doc["solution"]
    else:
        raw_solution = "No raw solution available."

    solution_summaries = generate_solution_summaries(raw_solution)
    followup_questions = generate_followup_questions(problem_metadata.get("problem_text", ""))
    
    adaptive_id = save_adaptive_data(problem_metadata, solution_summaries, followup_questions)
    return adaptive_id

def generate_adaptive_for_all():
    """
    Generate adaptive learning data for every problem in the db['solutions'] collection.
    For each document in db['solutions'], extract the necessary metadata and pre-generate adaptive data.
    Skip any document missing required fields.
    """
    count = 0
    # Iterate over all documents in db['solutions']
    raw_solutions = raw_solutions_collection.find({})
    for sol in raw_solutions:
        # Build metadata using fields from the solutions document.
        metadata = {
            "year": sol.get("year", ""),
            "contest": sol.get("contest", ""),
            "problem_number": sol.get("problem_number", ""),
            "problem_text": sol.get("problem_statement", "")
        }
        if not (metadata["year"] and metadata["contest"] and metadata["problem_number"] and metadata["problem_text"]):
            print(f"Skipping solution with missing metadata: {metadata}")
            continue

        # Check if adaptive data already exists for this problem.
        existing = adaptive_collection.find_one({
            "year": metadata["year"],
            "contest": metadata["contest"],
            "problem_number": metadata["problem_number"]
        })
        if existing:
            print(f"Adaptive data already exists for problem {metadata['problem_number']} ({metadata['year']} {metadata['contest']}). Skipping.")
            continue

        adaptive_id = pre_generate_adaptive_data(metadata)
        print(f"Generated adaptive data for problem {metadata['problem_number']} with ID: {adaptive_id}")
        count += 1
    print(f"Processed {count} new problems.")

# For direct running, generate adaptive data for all problems in db['solutions'].
if __name__ == "__main__":
    generate_adaptive_for_all()
