from transformers import AutoTokenizer, RobertaModel
import torch.nn.functional as F
import openai
import faiss
import numpy as np
from pymongo import MongoClient
from rank_bm25 import BM25Okapi

# Set OpenAI API key
import os
from dotenv import load_dotenv

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
openai.api_key = OPEN_AI_API_KEY

model = "text-embedding-ada-002"


class Query:

    # Embed the input
    def Understand(input_text):

        try:
            response = openai.Embedding.create(input=[input_text], model=model)

            return np.array(response["data"][0]["embedding"], dtype="float32").reshape(
                1, -1
            )
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    # Retrive DB by FAISS with top n topics
    def retrieveFAISS(embedding, n):
        """Retrieve top-k relevant documents from FAISS index and MongoDB."""
        try:
            # Load FAISS index
            index = faiss.read_index("wiki_faiss.index")
            distances, indices = index.search(embedding, n)

            # Connect to MongoDB
            client = MongoClient("mongodb://localhost:27017/")
            db = client["RetrivalDB"]
            collection = db["wiki_data"]

            # Collect matching results
            results = []
            for idx in indices[0]:
                result = collection.find_one({"_id": int(idx)})
                if result:
                    filtered_result = {
                        "Topic": result.get("Topic", "No topic available"),
                        "Summary": result.get("Summary", "No summary available"),
                    }
                    results.append(filtered_result)

            return results

        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []

    # Retrive DB by BM25 with top n docs
    def retrieveBM25(input_text, n):

        # Connect to MongoDB and fetch all documents
        client = MongoClient("mongodb://localhost:27017/")
        db = client["RetrivalDB"]
        collection = db["wiki_data"]

        # Fetch documents and filter for valid strings in 'Summary' and presence of 'Topic'
        documents = collection.find({}, {"Topic": 1, "Summary": 1, "_id": 0})
        valid_docs = [
            doc
            for doc in documents
            if isinstance(doc.get("Summary"), str)
            and doc["Summary"].strip()
            and "Topic" in doc
        ]

        # Create corpus and a mapping from Summary to Topic
        corpus = [doc["Summary"] for doc in valid_docs]

        # Check if the corpus is empty
        if not corpus:
            print("Error: No valid summaries found in the database.")
            return []

        # Create a mapping from summaries to topics
        summary_topic_map = {doc["Summary"]: doc["Topic"] for doc in valid_docs}

        # Initialize BM25 with tokenized corpus
        bm25 = BM25Okapi([doc.split() for doc in corpus])

        # Retrieve top-n summaries based on input tokens
        top_n_summaries = bm25.get_top_n(input_text.split(), corpus, n=n)

        # Match summaries to their topics
        results = [
            {"Topic": summary_topic_map[summary], "Summary": summary}
            for summary in top_n_summaries
        ]

        return results

    def generate_candidate(input_text, n_each_method):
        # print("generate_candidate is called in input_pip.py")
        embedding = Query.Understand(input_text)

        # Retrieve documents using FAISS and BM25
        faiss_docs = Query.retrieveFAISS(embedding, n=n_each_method)
        bm25_docs = Query.retrieveBM25(input_text, n=n_each_method)

        # Combine results into a dictionary
        combined_results = {}
        for doc in faiss_docs + bm25_docs:
            topic = doc["Topic"]
            summary = doc["Summary"]
            if topic not in combined_results:
                combined_results[topic] = summary

        return combined_results


def main():
    input_text = "I cannot focus even when I have enough sleep."
    candidates = Query.generate_candidate(input_text, 5)
    for topic, summary in candidates.items():
        print(f"Topic: {topic}")


if __name__ == "__main__":
    main()
