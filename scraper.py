import os
import re
import pandas as pd
from google_play_scraper import Sort, reviews

APPS = {
    "Gojek": "com.gojek.app",
    "Grab": "com.grabtaxi.passenger",
}

RAW_DATA_PATH = "data/gojek_grab_raw.csv"
CLEAN_DATA_PATH = "gojek_grab_final.csv"  
TARGET_PER_RUN = 1000

# Kamus normalisasi bahasa gaul
KAMUS_NORMALISASI = {
    'gk': 'tidak', 'gak': 'tidak', 'nggak': 'tidak',
    'bgt': 'banget', 'bgd': 'banget', 'yg': 'yang',
    'tp': 'tapi', 'utk': 'untuk', 'dgn': 'dengan',
    'driverny': 'driver', 'drivernya': 'driver',
    'abg': 'abang', 'jg': 'juga', 'org': 'orang',
    'tlp': 'telepon', 'trs': 'terus', 'bikin': 'buat',
    'lemot': 'lambat', 'lelet': 'lambat'
}

def full_cleaning(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split()
    normalized_words = [KAMUS_NORMALISASI.get(word, word) for word in words]
    return ' '.join(normalized_words)

def categorize_sentiment(score):
    if score in [1, 2]:
        return 'Negatif'
    elif score == 3:
        return 'Netral'
    elif score in [4, 5]:
        return 'Positif'
    else:
        return 'Unknown'

def scrape_app(app_id: str, target_count: int) -> pd.DataFrame:
    all_reviews = []
    continuation_token = None

    while len(all_reviews) < target_count:
        fetch_count = min(200, target_count - len(all_reviews))
        result, continuation_token = reviews(
            app_id,
            lang="id",
            country="id",
            sort=Sort.NEWEST,
            count=fetch_count,
            continuation_token=continuation_token,
        )
        if not result:
            break
        all_reviews.extend(result)
        if not continuation_token:
            break

    return pd.DataFrame(all_reviews)

def main():
    frames = []
    for name, app_id in APPS.items():
        print(f"Scraping {name} ({app_id})...")
        df = scrape_app(app_id, TARGET_PER_RUN)
        df["app_name"] = name
        frames.append(df)
        print(f"  -> dapet {len(df)} review terbaru")

    new_df = pd.concat(frames, ignore_index=True)

    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)

    
    if os.path.exists(RAW_DATA_PATH):
        old_df = pd.read_csv(RAW_DATA_PATH)
        combined_raw = pd.concat([old_df, new_df], ignore_index=True)
        combined_raw = combined_raw.drop_duplicates(subset="reviewId", keep="first")
    else:
        combined_raw = new_df.drop_duplicates(subset="reviewId", keep="first")

    
    combined_raw.to_csv(RAW_DATA_PATH, index=False, encoding="utf-8")
    print(f"Raw data total: {len(combined_raw)} baris tersimpan.")

   
    print("Menjalankan proses cleaning dan pelabelan sentimen...")
    combined_raw['cleaned_content'] = combined_raw['content'].apply(full_cleaning)
    combined_raw = combined_raw[combined_raw['cleaned_content'] != '']
    combined_raw['sentiment'] = combined_raw['score'].apply(categorize_sentiment)

   
    combined_raw.to_csv(CLEAN_DATA_PATH, index=False, encoding="utf-8")
    print(f"File bersih berhasil diperbarui ke '{CLEAN_DATA_PATH}' ({len(combined_raw)} baris).")

if __name__ == "__main__":
    main()
