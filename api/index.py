from flask import Flask, request, jsonify
from Input_pip import Query
from Generation import *
import pandas as pd
from RetrievalDB import main as retrieval_main

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, World!"


@app.route("/api/generate", methods=["POST"])
def generate_followup():
    # Extracting the query from the request
    if not request.json or "query" not in request.json:
        return (
            jsonify({"error": "No query provided"}),
            400,
        )  # TODO: maybe not an error but something else

    # Get user initial question
    user_initial_query = request.json["query"]

    # Generate candidates
    candidates = Query.generate_candidate(user_initial_query, 5)

    # Return a list of questions
    bot_followup_questions = followup_agent(user_initial_query, candidates)

    return jsonify(
        {
            "initialQuery": user_initial_query,
            "candidates": candidates,
            "followupQuestions": bot_followup_questions,
        }
    )


@app.route("/api/analyze", methods=["POST"])
def analyze():
    # Get necessary data to be passed to the functions
    data = request.get_json()
    user_initial_query = data.get("initialQuery", "")
    candidates = data.get("candidates", [])
    # print("==== candidate in index.py: ", candidates)
    bot_followup_questions = data.get("followUpQuestions", [])
    user_followup_response = data.get("userFollowupResponse", [])

    # Concatenate lists into a single string
    bot_followup_questions_str = " ".join(bot_followup_questions)
    user_followup_response_str = ". ".join(user_followup_response)
    # print("bot_followup_questions_str in function analyze", bot_followup_questions_str)
    # print("user_followup_response_str in function analyze", user_followup_response_str)

    # Call predefined methods to vote
    votes = vote_for_results(
        candidates,
        user_initial_query,
        bot_followup_questions_str,
        user_followup_response_str,
    )

    # select the ideal agent
    agent, diagnosis = select_agent(votes)

    # print(f"{agent} steps in!")
    result = final_agent(
        agent,
        diagnosis,
        candidates,
        user_initial_query,
        bot_followup_questions_str,
        user_followup_response_str,
    )

    return jsonify({"result": result})


if __name__ == "__main__":
    retrieval_main()
    app.run()
