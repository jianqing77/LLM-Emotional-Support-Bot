import wikipediaapi
import pandas as pd
from tqdm import tqdm
import os
from pymongo import MongoClient
from nltk.corpus import stopwords
import openai
import time
import faiss_index
import faiss
import numpy as np
from pymongo import MongoClient
import os
from dotenv import load_dotenv


# Declare the identity of requestor
wiki_wiki = wikipediaapi.Wikipedia(
    "Psychology_LLM_Agent (fan.qih@northeastern.edu)", "en"
)


load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
openai.api_key = OPEN_AI_API_KEY

model = "text-embedding-ada-002"


def print_sections(sections, level=0):
    for s in sections:
        print("%s: %s - %s" % ("*" * (level + 1), s.title, s.text[0:40]))
        print_sections(s.sections, level + 1)


def get_list(page_name):
    page_py = wiki_wiki.page(page_name)
    list = []
    for link in page_py.links:
        list.append(link)
    return list


def get_summary(page_title):
    page = wiki_wiki.page(page_title)
    if page.exists():
        return page.summary  # Fetches the summary of the page
    else:
        return "Page not found"


def remove_duplicates(list1, list2):
    """Remove topics that appear in both lists and return a combined list of unique topics."""
    set1 = set(list1)
    set2 = set(list2)
    common = set1.intersection(set2)
    unique_set1 = set1 - common
    unique_set2 = set2 - common
    result = list(unique_set1) + list(unique_set2) + list(common)
    return result


def mongoDB(csv_file, db_name, collection_name, host):
    client = MongoClient(f"mongodb://localhost:{host}/")
    db = client[db_name]
    collection = db[collection_name]
    collection.insert_many(pd.read_csv(csv_file).to_dict("records"))
    print(f"Retrival Database [{db_name}] has been created!")


def textEmbed(text):
    try:
        # Ensure the input is passed as a list
        response = openai.Embedding.create(
            input=[text], model=model  # Wrap input in a list
        )
        # Extract the embedding from the API response
        return response["data"][0]["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def main():
    csv_file = "./wiki_raw.csv"

    # Step 1: Check if the CSV file exists
    if not os.path.isfile(csv_file):
        # Fetch and combine lists of topics
        Mental_Disorder = get_list("List_of_mental_disorders")
        Neuro_Disorder = get_list("List of neurological conditions and disorders")
        all_topics = remove_duplicates(Mental_Disorder, Neuro_Disorder)

        data_list = []
        for idx, topic in tqdm(enumerate(all_topics), total=len(all_topics)):
            summary = get_summary(topic)
            embeded = textEmbed(summary)
            data_list.append(
                {"_id": idx, "Topic": topic, "Summary": summary, "Embeded": embeded}
            )
            time.sleep(1)

        # Save data to CSV
        data = pd.DataFrame(data_list)
        data.dropna(subset=["Summary", "Embeded"], inplace=True)
        data.to_csv(csv_file, index=False)
        print(f"CSV file saved to {csv_file}")

    # Step 2: Check if embeddings are already in the CSV
    data = pd.read_csv(csv_file)
    if "Embeded" in data.columns and not data["Embeded"].isnull().all():
        print("Embeddings found in CSV. Processing directly from CSV.")

        # Convert string embeddings back to NumPy arrays (if needed)
        data["Embeded"] = data["Embeded"].apply(
            lambda x: np.fromstring(x.strip("[]"), sep=",") if isinstance(x, str) else x
        )

        # Initialize FAISS index
        dimension = 1536  # Size of embeddings
        index = faiss.IndexFlatL2(dimension)

        count = 0
        for _, row in data.iterrows():
            embedding = np.array(row["Embeded"], dtype="float32")
            if embedding.shape == (dimension,):
                index.add(embedding.reshape(1, -1))
                count += 1
            else:
                print(f"Skipping row {_}: Incorrect embedding shape {embedding.shape}.")

        # Save FAISS index
        if count > 0:
            faiss.write_index(index, "wiki_faiss.index")
            print(f"FAISS index created with {index.ntotal} entries.")
        else:
            print("No valid embeddings found. FAISS index not created.")
    else:
        print("Embeddings not found in CSV. Fetching from MongoDB.")

        # Step 3: Insert data into MongoDB (if needed)
        mongoDB(csv_file, "RetrivalDB", "wiki_data", "27017")

        # Step 4: Set up MongoDB connection
        client = MongoClient("mongodb://localhost:27017/")
        db = client["RetrivalDB"]
        collection = db["wiki_data"]

        # Step 5: Initialize FAISS index
        dimension = 1536  # Size of embeddings
        index = faiss.IndexFlatL2(dimension)
        count = 0

        # Fetch and process embeddings from MongoDB
        for doc in collection.find({}, {"_id": 1, "Embeded": 1}):
            try:
                if "Embeded" not in doc or not doc["Embeded"]:
                    print(
                        f"Skipping document {doc['_id']}: No 'Embeded' field or empty embedding."
                    )
                    continue

                embedding = np.array(doc["Embeded"], dtype="float32")
                if embedding.shape != (dimension,):
                    print(
                        f"Skipping document {doc['_id']}: Incorrect shape {embedding.shape}."
                    )
                    continue

                index.add(embedding.reshape(1, -1))
                count += 1
            except Exception as e:
                print(f"Error processing document {doc['_id']}: {e}")

        # Step 6: Save the FAISS index if valid entries were added
        if count > 0:
            faiss.write_index(index, "wiki_faiss.index")
            print(f"FAISS index created with {index.ntotal} entries.")
        else:
            print("No valid embeddings found. FAISS index not created.")


if __name__ == "__main__":
    main()
