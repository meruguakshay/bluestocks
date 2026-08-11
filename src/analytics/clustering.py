import os
import sqlite3

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # Headless chart generation
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = os.getenv("DB_PATH", "db/nifty100.db")


def main():
    print("=" * 60)
    print("STARTING KMEANS CLUSTERING (DAY 36 & 37)")
    print("=" * 60)

    # 1. Connect to DB
    conn = sqlite3.connect(DB_PATH)

    # 2. Extract latest conformed financial ratios for each company
    df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

    # Prefer latest record with non-null return_on_equity_pct
    df_not_null = df_ratios.dropna(subset=["return_on_equity_pct"])
    latest_not_null = (
        df_not_null.sort_values("year").groupby("company_id").last().reset_index()
    )

    # Fallback to absolute latest for companies with all null ROE (e.g. SBIN)
    missing_ids = set(df_ratios["company_id"]) - set(latest_not_null["company_id"])
    df_missing = df_ratios[df_ratios["company_id"].isin(missing_ids)]
    latest_missing = (
        df_missing.sort_values("year").groupby("company_id").last().reset_index()
    )

    df_combined = pd.concat([latest_not_null, latest_missing], ignore_index=True)

    # Merge with companies and sectors to get broad sector
    df_comps = pd.read_sql_query(
        "SELECT c.company_id, s.broad_sector as sector FROM companies c JOIN sectors s ON c.sector_id = s.sector_id",
        conn,
    )
    df_data = pd.merge(df_combined, df_comps, on="company_id", how="left")

    # Load FCF CAGR 5yr from cashflow_intelligence.xlsx
    cf_intel = pd.read_excel("output/cashflow_intelligence.xlsx")
    df_data = pd.merge(
        df_data, cf_intel[["company_id", "fcf_cagr_5yr"]], on="company_id", how="left"
    )

    # Define the 5 features
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]
    df_features = df_data[["company_id", "sector"] + features].copy()

    # Before scaling: impute missing values with sector median for each metric
    for col in features:
        sector_medians = df_features.groupby("sector")[col].transform("median")
        df_features[col] = df_features[col].fillna(sector_medians)
        # Global fallback if still missing
        global_median = df_features[col].median()
        df_features[col] = df_features[col].fillna(global_median)

    # Apply StandardScaler to normalise features to zero mean and unit variance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_features[features])

    # Generate elbow plot (inertia vs k from 2 to 10)
    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    os.makedirs("reports", exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.plot(k_range, inertias, marker="o", color="#002B49")
    plt.xlabel("Number of Clusters (k)", fontweight="bold")
    plt.ylabel("Inertia (Within-cluster Sum of Squares)", fontweight="bold")
    plt.title("KMeans Elbow Plot", fontweight="bold", pad=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig("reports/elbow_plot.png", dpi=300)
    plt.close()
    print("[OK] Saved elbow plot to reports/elbow_plot.png")

    # Run KMeans with n_clusters=5, random_state=42
    kmeans = KMeans(n_clusters=5, random_state=42)
    df_features["cluster_id"] = kmeans.fit_predict(X_scaled)

    # Calculate distance from centroid (Euclidean distance to assigned cluster centroid)
    distances = kmeans.transform(X_scaled)
    df_features["distance_from_centroid"] = [
        distances[i, df_features.loc[i, "cluster_id"]] for i in range(len(df_features))
    ]

    # Map cluster IDs to descriptive names based on their financial profile characteristics
    # Cluster Naming Map:
    # 0 -> High-Quality Compounders
    # 1 -> Defensive Dividend Payers
    # 2 -> Value Cyclicals
    # 3 -> Distressed or Turnaround
    # 4 -> Emerging Growth
    cluster_names_map = {
        0: "High-Quality Compounders",
        1: "Defensive Dividend Payers",
        2: "Value Cyclicals",
        3: "Distressed or Turnaround",
        4: "Emerging Growth",
    }

    df_features["cluster_name"] = df_features["cluster_id"].map(cluster_names_map)

    # Save output/cluster_labels.csv
    os.makedirs("output", exist_ok=True)
    cluster_labels_df = df_features[
        ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    ]
    cluster_labels_df.to_csv("output/cluster_labels.csv", index=False)
    print(
        f"[OK] Saved {len(cluster_labels_df)} cluster labels to output/cluster_labels.csv"
    )

    conn.close()


if __name__ == "__main__":
    main()
