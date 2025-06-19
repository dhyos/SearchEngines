import re
import sys
import json
import pickle
import math
import io
import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Validasi argumen
if len(sys.argv) != 4:
    print("\nPenggunaan:\n\tpython query.py [indexDB.pkl] [jumlah_output] [query]\n")
    sys.exit(1)

index_file_path = sys.argv[1]
top_n = int(sys.argv[2])
raw_query = sys.argv[3].lower()

# Load index
with open(index_file_path, 'rb') as f:
    tf_idf_index = pickle.load(f)

# Load stopwords
with open("stopword.txt", encoding="utf-8") as f:
    stopwords = f.read().splitlines()

# Setup stemmer
stemmer = StemmerFactory().create_stemmer()

# Preprocessing
def clean_text(text):
    if pd.isna(text):
        return ""
    text = re.sub("&.*?;", "", text)
    text = re.sub(">", "", text)
    text = re.sub(r"[\]\|\[@,$%*&\\()\":]", "", text)
    text = re.sub("-", " ", text)
    text = re.sub(r"\.+", "", text)
    text = re.sub(r"^\s+", "", text)
    text = text.lower()
    return text

cleaned_query = clean_text(raw_query)
query_tokens = cleaned_query.split()
query_words = [stemmer.stem(w) for w in query_tokens if w not in stopwords]

# Hitung TF untuk query
query_tf = {}
for word in query_words:
    query_tf[word] = query_tf.get(word, 0) + 1

# Bangun vektor dokumen lengkap dari index
doc_vectors = {}
doc_meta = {}

for word, posting_list in tf_idf_index.items():
    for entry in posting_list:
        doc_id = entry["doc_id"]
        if doc_id not in doc_vectors:
            doc_vectors[doc_id] = {}
            doc_meta[doc_id] = entry
        doc_vectors[doc_id][word] = entry["score"]

# Cosine similarity
def cosine_similarity(vec1, vec2):
    all_words = set(vec1.keys()).union(set(vec2.keys()))
    dot_product = sum(vec1.get(w, 0) * vec2.get(w, 0) for w in all_words)
    norm1 = math.sqrt(sum(vec1.get(w, 0) ** 2 for w in all_words))
    norm2 = math.sqrt(sum(vec2.get(w, 0) ** 2 for w in all_words))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

# Hitung skor similarity
results = []
for doc_id, doc_vec in doc_vectors.items():
    score = cosine_similarity(query_tf, doc_vec)
    if score > 0:
        doc = doc_meta[doc_id].copy()
        doc["score"] = round(score, 6)
        results.append(doc)

# Urutkan berdasarkan skor
results.sort(key=lambda x: x["score"], reverse=True)

# Cetak hasil top N
for i, doc in enumerate(results[:top_n]):
    print(json.dumps(doc, ensure_ascii=False, indent=2))
    