import os
import random
from collections import defaultdict
from openai import OpenAI, OpenAIError

# Initialize the OpenAI client using the API key from the environment
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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

def generate_explanation(problem_text):
    """
    Generate a detailed, step-by-step explanation for the given AMC 10 problem.
    The explanation should be specific to the problem text, include fully resolved numerical expressions,
    and avoid raw LaTeX code.
    """
    prompt = (
        "You are an expert AMC 10 math tutor who explains concepts clearly and precisely. "
        "Please provide a necessary step-by-step explanation for solving the following problem in the most optimal way. "
        "Make sure that all math expressions are fully resolved (showing evaluated numbers) and avoid using raw LaTeX. "
        "Focus solely on the details of the problem provided. Limit in 300 words. \n\n"
        f"Problem:\n{problem_text}\n\n"
        "Concise Explanation:"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert AMC 10 math tutor who explains concepts clearly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        explanation = response.choices[0].message.content.strip()
        return explanation
    except OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return "An error occurred while generating the explanation."

def generate_followup_question(problem_text, difficulty):
    """
    Generate a follow-up AMC 10 problem similar to the original.
    The follow-up problem should test the same concept at the specified difficulty,
    include a user-friendly statement, and provide a diagram (in ASCII or textual format)
    that shows the configuration of the relevant figures.
    """
    prompt = (
        "You are an expert AMC 10 math tutor who creates clear and visually supported practice problems. "
        "Based solely on the following problem, generate a similar follow-up problem at "
        f"{difficulty} difficulty. The new problem should test the same concept with a slight variation. "
        "Include a diagram (in ASCII or textual format) that clearly illustrates the configuration of the figures. "
        "Do not include any generic examples; base your problem solely on the details provided."
        "Be concise. \n\n"
        f"Original Problem:\n{problem_text}\n\n"
        "Follow-up Problem:"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert AMC 10 math tutor who creates clear, detailed problems with diagrams when needed."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.7,
    )
    followup_question = response.choices[0].message.content.strip()
    return followup_question

def explain_and_generate(problem_text, student_answer, correct_answer, agent, state=None):
    """
    Compare the student's answer to the correct answer.
    If correct, return a confirmation.
    If incorrect, generate a detailed, user-friendly explanation specific to the problem,
    and then generate a follow-up problem (with a diagram) at a difficulty selected by the RL agent.
    """
    if student_answer.strip().lower() == correct_answer.strip().lower():
        state = "correct"
        return {
            "explanation": "Correct! Great job.",
            "followup": None,
            "selected_difficulty": None
        }
    else:
        state = "incorrect"
        explanation = generate_explanation(problem_text)
        selected_difficulty = agent.select_action(state)
        followup_question = generate_followup_question(problem_text, selected_difficulty)
        return {
            "explanation": explanation,
            "followup": followup_question,
            "selected_difficulty": selected_difficulty
        }
