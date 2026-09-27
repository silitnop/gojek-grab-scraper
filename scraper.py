"""
Scraper otomatis buat review Gojek & Grab dari Play Store.
Beda sama versi notebook: script ini AMAN dijalanin berkali-kali,
karena otomatis buang data yang reviewId-nya udah ada (gak dobel).
"""
import os
import pandas as pd
from google_play_scraper import Sort, reviews

APPS = {
    "Gojek": "com.gojek.app",
    "Grab": "com.grabtaxi.passenger",
}

DATA_PATH = "data/gojek_grab_raw.csv"
# Tiap run cukup ambil beberapa ratus review terbaru aja, bukan 5000 -
# yang lama udah kesimpen, kita cuma nambahin yang baru muncul sejak run terakhir.
TARGET_PER_RUN = 200


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

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    if os.path.exists(DATA_PATH):
        old_df = pd.read_csv(DATA_PATH)
        before = len(old_df)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset="reviewId", keep="first")
        print(f"Data lama: {before} baris, data baru unik ditambahin: {len(combined) - before} baris")
    else:
        combined = new_df.drop_duplicates(subset="reviewId", keep="first")
        print(f"Belum ada data lama, mulai dari nol: {len(combined)} baris")

    combined.to_csv(DATA_PATH, index=False, encoding="utf-8")
    print(f"Total data sekarang: {len(combined)} baris. Disimpan ke {DATA_PATH}")


if __name__ == "__main__":
    main()
