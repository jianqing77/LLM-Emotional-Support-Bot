from flask import Flask, request, jsonify
from Input_pip import Query
from Generation import *
import pandas as pd

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

    user_input = request.json["query"]

    # Generate candidates
    candidates = Query.generate_candidate(user_input, 5)

    # Return a list of questions
    followup = followup_agent(user_input, candidates)

    return jsonify({"followup": followup})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    print("!!!Flask func analyze -- data: " + data)

    query = data["query"]
    print("!!!Flask func analyze -- query: " + query)

    print("************* System Checking *******************")
    print("-------------------------------------------------------------")

    candidates = Query.generate_candidate(query, 5)
    followup = followup_agent(query, candidates)

    print("-------------------------------------------------------------")
    follow = data["follow"]

    votes = vote_for_results(candidates, query, followup, follow)
    agent, diagnosis = select_agent(votes)

    final_response = final_agent(agent, diagnosis, candidates, query, followup, follow)

    print("------------------------- Final Response ---------------------------------")

    return jsonify(
        {
            "followup": followup,
            "agent": agent,
            "diagnosis": diagnosis,
            "final_response": final_response,
        }
    )


if __name__ == "__main__":
    app.run()


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
