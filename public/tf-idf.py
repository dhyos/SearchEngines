import re
import sys
import math
import pickle
import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Validasi argumen
if len(sys.argv) != 3:
    print("\nGunakan:\n\t python tf-idf.py [input.csv] [output]\n")
    sys.exit(1)

input_csv = sys.argv[1]
output_file = sys.argv[2]

# Load stopword
stopwords = open("stopword.txt", encoding='utf-8').read().splitlines()

# Setup stemmer bahasa Indonesia
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Preprocessing
def clean_str(text):
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

# Load data CSV
df = pd.read_csv(input_csv)

# Kolom teks yang akan digabung
text_columns = [
    "surah_no", "surah_name_en", "surah_name_ar", "surah_name_roman",
    "ayah_no_surah", "ayah_no_quran", "ayah_ar", "ayah_en", "ayah_in",
    "ruko_no", "juz_no", "manzil_no", "hizb_quarter",
    "total_ayah_surah", "total_ayah_quran", "place_of_revelation",
    "sajah_ayah", "sajdah_no", "no_of_word_ayah", "list_of_words"
]

tf_data = {}
df_data = {}

for idx, row in df.iterrows():
    combined_text = " ".join(str(row[col]) for col in text_columns if col in row and pd.notna(row[col]))
    clean_text = clean_str(combined_text)

    # Tokenisasi + stemming + stopword removal
    words = clean_text.split()
    stemmed_words = [stemmer.stem(w) for w in words if w not in stopwords]

    # TF
    tf = {}
    for word in stemmed_words:
        tf[word] = tf.get(word, 0) + 1
        df_data[word] = df_data.get(word, 0) + 1

    url_key = f"{row.get('surah_no', '')}:{row.get('ayah_en', '')}:{row.get('ayah_in', '')}"
    tf_data[url_key] = {
        "meta": {
            "surah_no": row.get("surah_no"),
            "surah_name_en": row.get("surah_name_en"),
            "surah_name_ar": row.get("surah_name_ar"),
            "surah_name_roman": row.get("surah_name_roman"),

            "ayah_no_surah": row.get("ayah_no_surah"),
            "ayah_no_quran": row.get("ayah_no_quran"),
            "ayah_ar": row.get("ayah_ar"),
            "ayah_en": row.get("ayah_en"),
            "ayah_in": row.get("ayah_in"),

            "ruko_no": row.get("ruko_no"),
            "juz_no": row.get("juz_no"),
            "manzil_no": row.get("manzil_no"),
            "hizb_quarter": row.get("hizb_quarter"),

            "total_ayah_surah": row.get("total_ayah_surah"),
            "total_ayah_quran": row.get("total_ayah_quran"),
            "place_of_revelation": row.get("place_of_revelation"),

            "sajah_ayah": row.get("sajah_ayah"),
            "sajdah_no": str(row.get("sajdah_no", "")),
            "no_of_word_ayah": row.get("no_of_word_ayah"),
            "list_of_words" : row.get("list_of_words", "").strip("[]").split(",")
        },
        "tf": tf
    }

# Hitung IDF
idf_data = {}
total_docs = len(tf_data)
for word in df_data:
    idf_data[word] = 1 + math.log10(total_docs / df_data[word])

# Buat TF-IDF index
tf_idf = {}
for word in df_data:
    doc_list = []
    for doc_id, data in tf_data.items():
        tf_val = data["tf"].get(word, 0)
        score = tf_val * idf_data[word]
        if score > 0:
            doc_list.append({
                "doc_id": doc_id,
                "score": score,
                **data["meta"]
            })
    tf_idf[word] = doc_list

# Simpan ke file
with open(output_file, "wb") as f:
    pickle.dump(tf_idf, f)

print(f"Sukses menyimpan TF-IDF ke {output_file}")
