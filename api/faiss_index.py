import numpy as np
import faiss
from pymongo import MongoClient
import pandas as pd

# Load the CSV
df = pd.read_csv('wiki_raw.csv')

# Ensure embeddings are treated as lists
df['Embeded'] = df['Embeded'].apply(eval)

# Initialize FAISS index
dimension = 1536  # Dimension of the embeddings
index = faiss.IndexFlatL2(dimension)

count = 0  # Track valid entries

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['RetrivalDB']
collection = db['wiki_data']

# Iterate over DataFrame and add embeddings to FAISS index
for idx, row in df.iterrows():
    try:
        embedding = np.array(row['Embeded'], dtype='float32')

        if embedding.shape != (1536,):
            print(f"Skipping index {idx}: Incorrect shape {embedding.shape}.")
            continue

        # Add to FAISS index
        index.add(embedding.reshape(1, -1))
        count += 1

        # Update MongoDB with the row data if not already there
        collection.update_one(
            {'_id': row['_id']},
            {'$set': {
                'Topic': row['Topic'],
                'Summary': row['Summary'],
                'Embeded': row['Embeded']
            }},
            upsert=True
        )

    except Exception as e:
        print(f"Error processing index {idx}: {e}")

# Save the FAISS index
if count > 0:
    faiss.write_index(index, "wiki_faiss.index")
    print(f"FAISS index created with {index.ntotal} entries.")
else:
    print("No valid embeddings found. FAISS index not created.")