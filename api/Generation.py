import openai
import re
import pandas as pd
import random
import os
from dotenv import load_dotenv

load_dotenv()

random.seed(7180)

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
openai.api_key = OPEN_AI_API_KEY


model = "text-embedding-ada-002"


def normalize_diagnosis(diagnosis):
    return re.sub(r"[-–]", "-", diagnosis.strip().lower())


# introduce agents
def followup_agent(input_text, candidates):
    try:
        # Construct the dynamic prompt
        candidate_list = "\n".join(
            [f"- {topic}: {summary}" for topic, summary in candidates.items()]
        )
        prompt = (
            f"User input:\n{input_text}\n\n"
            f"Candidates:\n{candidate_list}\n\n"
            "Based on the input and candidates, generate clear, concise, and "
            "distinguishable follow-up questions that help refine the selection of the most relevant candidate. "
            "Focus on clinical relevance, behavioral patterns, environmental factors, and distinguishing details. "
            "Do not include statements such as: 'These questions aim to differentiate between potential OCD "
            "characteristics and other disorders like insomnia-related issues or neurodevelopmental conditions such as Tourette syndrome.'"
        )

        # Query the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an independent diagnostic assistant based on DSM-5 principles. "
                        "Your role is to ask clear, concise, and distinguishable follow-up questions "
                        "that help refine the selection of the most relevant psychological answer. "
                        "Hard Limit the questions to five questions. Each question should be ended with a question mark, and no question mark within the questions "
                        "Avoid making references to the purpose of the questions or comparisons with other disorders."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,  # Slight randomness for diverse follow-up questions
            max_tokens=500,  # Adjust based on the expected length of the response
            top_p=1.0,  # Nucleus sampling for high-quality outputs
            frequency_penalty=0.5,  # Reduce redundancy
            presence_penalty=0.0,  # Neutral presence penalty
        )

        # Extract the assistant's message from the response
        followup_questions = response["choices"][0]["message"]["content"]
        # Splitting the block of text into individual questions
        questions = followup_questions.split("?")
        print("questions: ", questions)
        parsed_questions = [q.strip() + "?" for q in questions if q.strip()]
        print(parsed_questions)
        return parsed_questions

    except Exception as e:
        return f"An error occurred: {e}"


def diagnostic_agent(formatted_documents, initial_inputs, formatted_followup, model):
    try:
        # system prompt
        agent_prompt = (
            "You are a DSM-5 diagnostic assistant. Based on the provided input, suggest the top 5 possible diagnoses "
            "for the individual in descending order of likelihood. Do not include reasoning. "
            "Provide the diagnoses as a simple list, and assign a likelihood score of 5 (most likely) to 1 (least likely).\n\n"
            f"Initial Inputs:\n{initial_inputs}\n\n"
            f"Relevant Documents:\n{formatted_documents}\n\n"
            f"Follow-Up Questions and Answers:\n{formatted_followup}\n\n"
            "Return the diagnoses and their likelihood scores in this format:\n"
            "Diagnoses: <diag1>, <diag2>, <diag3>, <diag4>, <diag5>\n"
            "Likelihoods: 5, 4, 3, 2, 1"
        )

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a DSM-5 diagnostic assistant. Your role is to provide the top 5 possible diagnoses "
                        "without reasoning and assign likelihood scores."
                    ),
                },
                {"role": "user", "content": agent_prompt},
            ],
            temperature=0.5,
            max_tokens=300,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Extract raw response text
        response_text = response["choices"][0]["message"]["content"]

        # Parse the response into diagnoses and likelihoods
        diagnoses = []
        likelihoods = []

        # Extract diagnoses
        diag_match = re.search(r"Diagnoses:\s*(.+)", response_text)
        if diag_match:
            diagnoses = [diag.strip() for diag in diag_match.group(1).split(",")]

        # Extract likelihoods
        likelihood_match = re.search(r"Likelihoods:\s*(.+)", response_text)
        if likelihood_match:
            likelihoods = [
                int(score.strip()) for score in likelihood_match.group(1).split(",")
            ]

        return diagnoses, likelihoods

    except Exception as e:
        return ([], [f"An error occurred: {e}"])


def vote_for_results(documents, initial_inputs, followupQ, followupA):
    # Define agents
    judges = ["gpt-4o", "gpt-3.5-turbo", "gpt-4"]

    formatted_documents = "\n".join(
        [f"- {topic}: {summary}" for topic, summary in documents.items()]
    )
    formatted_followup = "\n".join(
        [f"Q: {q}\nA: {a}" for q, a in zip(followupQ, followupA)]
    )

    # Store diagnostics from each agent
    diagnostics = {}
    for model in judges:
        diagnoses, likelihoods = diagnostic_agent(
            formatted_documents, initial_inputs, formatted_followup, model
        )
        normalized_diagnoses = [normalize_diagnosis(diag) for diag in diagnoses]
        diagnostics[model] = {
            diag: likelihood
            for diag, likelihood in zip(normalized_diagnoses, likelihoods)
        }

    # Collect all unique diagnoses
    all_diagnoses = set(
        diag for result in diagnostics.values() for diag in result.keys()
    )

    # Create a DataFrame with rows as diagnoses and columns as models
    table_data = {
        model: {diag: diagnostics[model].get(diag, 0) for diag in all_diagnoses}
        for model in judges
    }
    df = pd.DataFrame(table_data)
    df["Votes"] = df.sum(axis=1)

    shortlisted_diagnoses = df[df["Votes"] >= 5].index.tolist()

    if not shortlisted_diagnoses:
        return df

    # Second Round Voting
    second_round_diagnostics = {}
    for model in judges:
        # Use the shortlisted diagnoses as the rankable documents
        second_round_diagnoses, second_round_likelihoods = diagnostic_agent(
            shortlisted_diagnoses,  # Replace rankable docs with shortlisted topics
            initial_inputs,
            formatted_followup
            + f"\n\nShortlisted Diagnoses: {', '.join(shortlisted_diagnoses)}",
            model,
        )
        normalized_second_diagnoses = [
            normalize_diagnosis(diag) for diag in second_round_diagnoses
        ]
        second_round_diagnostics[model] = {
            diag: likelihood
            for diag, likelihood in zip(
                normalized_second_diagnoses, second_round_likelihoods
            )
        }

    # Combine second round results into a DataFrame
    second_round_table_data = {
        model: {
            diag: second_round_diagnostics[model].get(diag, 0)
            for diag in shortlisted_diagnoses
        }
        for model in judges
    }
    second_round_df = pd.DataFrame(second_round_table_data)
    second_round_df["Votes"] = second_round_df.sum(axis=1)
    second_round_df.to_csv("./ranktable.csv")

    return second_round_df


def final_agent(
    selected_agent, selected_diagnosis, documents, initial_inputs, followupQ, followupA
):

    # Format documents and follow-up into strings for context
    formatted_documents = "\n".join(
        [f"- {topic}: {summary}" for topic, summary in documents.items()]
    )
    formatted_followup = (
        f"Follow-Up Questions:\n{followupQ}\n\nFollow-Up Answers:\n{followupA}"
    )

    # Initialize conversation history with full context
    conversation_history = [
        {
            "role": "system",
            "content": (
                "You are 'MemeMinds,' a DSM-5 diagnostic assistant. Your role is to first provide reasoning for the diagnosis you selected, "
                "and briefly describe the disorder, offer actionable suggestions for improvement, and ask clarifying questions to refine understanding. Engage in a humor and supportive and conversational tone."
            ),
        },
        {
            "role": "assistant",
            "content": (
                f"Hello, I'm MemeMinds, your meme mental health assistant. Based on the information provided, the suggested diagnosis is '{selected_diagnosis}'. "
                "Let me explain why this diagnosis was considered. Afterward, I’ll share actionable suggestions and ask any questions that can help us understand more."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context:\n"
                f"Initial Inputs: {initial_inputs}\n\n"
                f"Relevant Documents:\n{formatted_documents}\n\n"
                f"{formatted_followup}"
            ),
        },
    ]

    print("\n--- Diagnostic Chat with MemeMinds ---")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    # Start chat loop
    while True:
        # Query the assistant for the next response
        response = openai.ChatCompletion.create(
            model=selected_agent,
            messages=conversation_history,
            temperature=0.7,
            max_tokens=700,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.0,
        )

        # Extract and display the assistant's response
        agent_response = response["choices"][0]["message"]["content"]
        print(f"MemeMinds: {agent_response}")

        # Ask for user input
        user_input = input("You: ").strip()

        # Exit condition
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the diagnostic conversation with MemeMinds. Goodbye!")
            break

        # Append user input to the conversation history
        conversation_history.append({"role": "user", "content": user_input})

        # Append assistant's response to the conversation history
        conversation_history.append({"role": "assistant", "content": agent_response})


def select_agent(vote_df):
    # highest votes
    max_votes = vote_df["Votes"].max()
    top_diagnoses = vote_df[vote_df["Votes"] == max_votes]

    # randomly select a diagnosis if there are ties
    selected_diagnosis = top_diagnoses.sample(1).index[0]

    # select agent
    row = vote_df.loc[selected_diagnosis]
    max_vote_for_diag = row[:-1].max()  # Exclude the "Votes" column
    top_agents = row[row == max_vote_for_diag].index.tolist()
    selected_agent = random.choice(top_agents)

    return selected_agent, selected_diagnosis


def generation(material, input_text, confirm_question, confirm_text):
    prompt = f"""
    The user described their situation as: "{input_text}", 
    and confirmed with the question: "{confirm_question}" that: "{confirm_text}".

    Here is the most relevant summary based on the user's input:

    {material}

    In a humorous tone, provide a diagnosis about the user's psychological state with detailed reasoning.
    Explain the disorder based on user's description.
    Also, suggest **3 practical steps** the user can take to manage the situation, 
    such as lifestyle changes, productivity hacks, mindfulness techniques, or mental health practices.
    *** avoid mentioning the prompt ***
    """
    return query_llm(prompt)
