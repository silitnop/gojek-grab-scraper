import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "gojek-grab-analytics"
TABLE_ID = "gojek-grab-analytics.review_analytics.fact_reviews"
CSV_PATH = "gojek_grab_final.csv"

COLUMNS = [
    "reviewId",
    "userName",
    "userImage",
    "content",
    "score",
    "thumbsUpCount",
    "reviewCreatedVersion",
    "at",
    "replyContent",
    "repliedAt",
    "appVersion",
    "app_name",
    "cleaned_content",
    "sentiment",
]

SCHEMA = [
    bigquery.SchemaField("reviewId", "STRING"),
    bigquery.SchemaField("userName", "STRING"),
    bigquery.SchemaField("userImage", "STRING"),
    bigquery.SchemaField("content", "STRING"),
    bigquery.SchemaField("score", "INT64"),
    bigquery.SchemaField("thumbsUpCount", "INT64"),
    bigquery.SchemaField("reviewCreatedVersion", "STRING"),
    bigquery.SchemaField("at", "TIMESTAMP"),
    bigquery.SchemaField("replyContent", "STRING"),
    bigquery.SchemaField("repliedAt", "TIMESTAMP"),
    bigquery.SchemaField("appVersion", "STRING"),
    bigquery.SchemaField("app_name", "STRING"),
    bigquery.SchemaField("cleaned_content", "STRING"),
    bigquery.SchemaField("sentiment", "STRING"),
]


def main():
    client = bigquery.Client(project=PROJECT_ID)

    print("Membaca CSV...")
    df = pd.read_csv(CSV_PATH)

    # Pastikan hanya kolom yang sesuai schema yang digunakan
    df = df[COLUMNS].copy()

    # Hindari duplikasi dalam CSV
    df = df.drop_duplicates(
        subset=["app_name", "reviewId"],
        keep="last"
    )

    # Sesuaikan tipe data dengan BigQuery
    string_columns = [
        "reviewId", "userName", "userImage", "content",
        "reviewCreatedVersion", "replyContent", "appVersion",
        "app_name", "cleaned_content", "sentiment"
    ]

    for col in string_columns:
        df[col] = df[col].astype("string")

    for col in ["score", "thumbsUpCount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ["at", "repliedAt"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # Ambil ID review yang sudah ada di BigQuery
    print("Memeriksa review yang sudah tersimpan...")

    query = f"""
        SELECT app_name, reviewId
        FROM `{TABLE_ID}`
    """

    existing_keys = {
        (row.app_name, row.reviewId)
        for row in client.query(query).result()
    }

    # Filter hanya review baru
    new_mask = [
        (app, review_id) not in existing_keys
        for app, review_id in zip(df["app_name"], df["reviewId"])
    ]

    new_df = df.loc[new_mask].copy()

    if new_df.empty:
        print("Tidak ada review baru untuk di-upload.")
        return

    print(f"Menemukan {len(new_df)} review baru.")

    # Upload ke BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition="WRITE_APPEND"
    )

    job = client.load_table_from_dataframe(
        new_df,
        TABLE_ID,
        job_config=job_config
    )

    job.result()

    print(f"Berhasil upload {len(new_df)} review baru ke BigQuery.")


if __name__ == "__main__":
    main()
