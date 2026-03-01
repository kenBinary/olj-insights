# %% [markdown]
# # Data Processing & JSON Export
# This script performs all data transformations and exports precomputed chart data
# as structured JSON files for consumption by a custom frontend.

# %%
import pandas as pd
import numpy as np
import json
import os
from itertools import combinations
from collections import Counter

OUTPUT_DIR = "../data/chart_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Saved: {path}")


# %%
df = pd.read_csv("../data/transformed_jobs.csv")
print("Total rows: ", len(df))
print("Total columns: ", len(df.columns))


# %% [markdown]
# # Outlier Removal


# %%
def filter_outliers_iqr(group_col):
    Q1 = group_col.quantile(0.25)
    Q3 = group_col.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return (group_col >= lower_bound) & (group_col <= upper_bound)


valid_rows_mask = df.groupby(["currency", "salary_type"])["average_salary"].transform(
    filter_outliers_iqr
)

df_cleaned = df[valid_rows_mask].copy()
outliers_removed = len(df) - len(df_cleaned)
print(f"Removed {outliers_removed} outlier(s) from the dataset.")
df = df_cleaned


# %% [markdown]
# # Metadata / Reference Values

# %%
unique_skills = df["skills"].str.split(";").explode().str.strip().unique()
unique_skills = [skill for skill in unique_skills if str(skill) != "nan"]

metadata = {
    "total_jobs": len(df),
    "unique_work_types": df["work_type"].dropna().unique().tolist(),
    "unique_currencies": df["currency"].dropna().unique().tolist(),
    "unique_salary_types": df["salary_type"].dropna().unique().tolist(),
    "unique_categories": df["category"].dropna().unique().tolist(),
    "unique_subcategories": df["subcategory"].dropna().unique().tolist(),
    "unique_skills": sorted(unique_skills),
    "unique_skills_count": len(unique_skills),
}
save_json("metadata.json", metadata)


# %% [markdown]
# # Salary Landscape

# %% [markdown]
# ## Salary Distribution Histograms
# One entry per (currency, salary_type) combination.
# Each entry contains the raw salary values binned into a histogram.

# %%
df_valid_salary = df.dropna(subset=["average_salary", "currency", "salary_type"]).copy()
df_valid_salary = df_valid_salary[
    ~df_valid_salary["salary_type"].isin(["unknown", "annually", "daily"])
]

currencies = df_valid_salary["currency"].unique()
salary_types = df_valid_salary["salary_type"].unique()

n_bins = int(2 * len(df) ** (1 / 3))

salary_distributions = []

for curr in currencies:
    for sal_type in salary_types:
        subset = df_valid_salary[
            (df_valid_salary["currency"] == curr)
            & (df_valid_salary["salary_type"] == sal_type)
        ]

        if subset.empty:
            continue

        values = subset["average_salary"].dropna().tolist()
        counts, bin_edges = np.histogram(values, bins=n_bins)

        salary_distributions.append(
            {
                "currency": curr,
                "salary_type": sal_type,
                "chart_title": f"Salary Distribution: {curr} - {sal_type.capitalize()}",
                "x_label": f"Average Salary ({curr})",
                "y_label": "Number of Listings",
                "histogram": {
                    "bin_edges": [round(e, 4) for e in bin_edges.tolist()],
                    # bin_starts[i] to bin_starts[i+1] = the i-th bar range
                    "bin_starts": [
                        round(bin_edges[i], 4) for i in range(len(bin_edges) - 1)
                    ],
                    "bin_ends": [
                        round(bin_edges[i + 1], 4) for i in range(len(bin_edges) - 1)
                    ],
                    "counts": counts.tolist(),
                },
                "stats": {
                    "count": len(values),
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "mean": round(np.mean(values), 4),
                    "median": round(np.median(values), 4),
                },
            }
        )

save_json("salary_distributions.json", salary_distributions)


# %% [markdown]
# ## Pay Range by Work Type (Box Plots)
# One entry per (currency, salary_type) combination.
# Each entry contains per-work-type box plot statistics + outlier points.

# %%
pay_range_by_work_type = []

for curr in currencies:
    for sal_type in salary_types:
        subset = df_valid_salary[
            (df_valid_salary["currency"] == curr)
            & (df_valid_salary["salary_type"] == sal_type)
        ]

        if subset.empty:
            continue

        work_type_boxes = []
        for wt, group in subset.groupby("work_type"):
            vals = group["average_salary"].dropna()
            if vals.empty:
                continue

            q1 = float(vals.quantile(0.25))
            q3 = float(vals.quantile(0.75))
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            non_outliers = vals[(vals >= lower_fence) & (vals <= upper_fence)]
            outlier_vals = vals[(vals < lower_fence) | (vals > upper_fence)]

            work_type_boxes.append(
                {
                    "work_type": wt,
                    "stats": {
                        "min": (
                            round(float(non_outliers.min()), 4)
                            if not non_outliers.empty
                            else None
                        ),
                        "q1": round(q1, 4),
                        "median": round(float(vals.median()), 4),
                        "q3": round(q3, 4),
                        "max": (
                            round(float(non_outliers.max()), 4)
                            if not non_outliers.empty
                            else None
                        ),
                        "mean": round(float(vals.mean()), 4),
                        "count": int(len(vals)),
                        "lower_fence": round(lower_fence, 4),
                        "upper_fence": round(upper_fence, 4),
                    },
                    "outliers": [round(v, 4) for v in outlier_vals.tolist()],
                }
            )

        pay_range_by_work_type.append(
            {
                "currency": curr,
                "salary_type": sal_type,
                "chart_title": f"Pay Range by Work Type: {curr} - {sal_type.capitalize()}",
                "x_label": "Work Type",
                "y_label": f"Average Salary ({curr})",
                "series": work_type_boxes,
            }
        )

save_json("pay_range_by_work_type.json", pay_range_by_work_type)


# %% [markdown]
# ## Average Pay by Category (Top 10, Monthly, USD)

# %%
cat_df = df.dropna(subset=["category"])
cat_df = cat_df[cat_df["salary_type"] == "monthly"]

cat_group = cat_df.groupby("category").agg(avg_usd=("usd_salary", "mean")).reset_index()
top10_cat = cat_group.nlargest(10, "avg_usd").sort_values("avg_usd", ascending=True)

avg_pay_by_category = {
    "chart_title": "Average Monthly Pay by Category (Top 10) — USD",
    "x_label": "Average Monthly Salary (USD)",
    "y_label": "Category",
    "orientation": "horizontal",
    "series": [
        {"category": row["category"], "avg_usd": round(row["avg_usd"], 4)}
        for _, row in top10_cat.iterrows()
    ],
}
save_json("avg_pay_by_category_top10.json", avg_pay_by_category)


# %% [markdown]
# ## Average Pay by Subcategory (Top 10, Monthly, Full Time, USD)

# %%
sub_df = df.dropna(subset=["subcategory"])
sub_df = sub_df[
    (sub_df["salary_type"] == "monthly") & (sub_df["work_type"] == "Full Time")
]

sub_group = (
    sub_df.groupby("subcategory").agg(avg_usd=("usd_salary", "mean")).reset_index()
)
top10_sub = sub_group.nlargest(10, "avg_usd").sort_values("avg_usd", ascending=True)

avg_pay_by_subcategory = {
    "chart_title": "Average Monthly Pay by Subcategory (Top 10) — USD",
    "x_label": "Average Monthly Salary (USD)",
    "y_label": "Subcategory",
    "orientation": "horizontal",
    "filters": {"salary_type": "monthly", "work_type": "Full Time"},
    "series": [
        {"subcategory": row["subcategory"], "avg_usd": round(row["avg_usd"], 4)}
        for _, row in top10_sub.iterrows()
    ],
}
save_json("avg_pay_by_subcategory_top10.json", avg_pay_by_subcategory)


# %% [markdown]
# # Market Demands


# %%
def parse_skills(series):
    return series.dropna().str.split(";").explode().str.strip().str.lower()


# %% [markdown]
# ## Top 10 Required Skills

# %%
skill_counts = parse_skills(df["skills"]).value_counts().head(10).reset_index()
skill_counts.columns = ["skill", "count"]

top10_skills = {
    "chart_title": "Top 10 Most Required Skills",
    "x_label": "Number of Job Listings",
    "y_label": "Skill",
    "orientation": "horizontal",
    "series": [
        {"skill": row["skill"], "count": int(row["count"])}
        for _, row in skill_counts.iterrows()
    ],
}
save_json("top10_skills.json", top10_skills)


# %% [markdown]
# ## Top 50 Required Skills

# %%
skill_counts_50 = parse_skills(df["skills"]).value_counts().head(50).reset_index()
skill_counts_50.columns = ["skill", "count"]

top50_skills = {
    "chart_title": "Top 50 Most Required Skills",
    "x_label": "Number of Job Listings",
    "y_label": "Skill",
    "orientation": "horizontal",
    "series": [
        {"skill": row["skill"], "count": int(row["count"])}
        for _, row in skill_counts_50.iterrows()
    ],
}
save_json("top50_skills.json", top50_skills)


# %% [markdown]
# ## Top 10 Skills by Work Type

# %%
work_types = df["work_type"].dropna().unique()
skills_by_work_type = []

for wt in work_types:
    subset = df[df["work_type"] == wt]
    skill_wt_counts = (
        parse_skills(subset["skills"]).value_counts().head(10).reset_index()
    )
    skill_wt_counts.columns = ["skill", "count"]

    if skill_wt_counts.empty:
        continue

    skills_by_work_type.append(
        {
            "work_type": wt,
            "chart_title": f"Top 10 Skills — {wt}",
            "x_label": "Number of Job Listings",
            "y_label": "Skill",
            "orientation": "horizontal",
            "series": [
                {"skill": row["skill"], "count": int(row["count"])}
                for _, row in skill_wt_counts.iterrows()
            ],
        }
    )

save_json("skills_by_work_type.json", skills_by_work_type)


# %% [markdown]
# ## Skill Co-occurrence Heatmap (Top 15 Skills)

# %%
TOP_N = 15
top_skills = parse_skills(df["skills"]).value_counts().head(TOP_N).index.tolist()

pair_counts = Counter()
for skill_list in df["skills"].dropna():
    skills_in_row = list(
        {
            s.strip().lower()
            for s in skill_list.split(";")
            if s.strip().lower() in top_skills
        }
    )
    for pair in combinations(sorted(skills_in_row), 2):
        pair_counts[pair] += 1

matrix = pd.DataFrame(0, index=top_skills, columns=top_skills)
for (s1, s2), count in pair_counts.items():
    matrix.loc[s1, s2] = count
    matrix.loc[s2, s1] = count

skill_heatmap_15 = {
    "chart_title": f"Skill Co-occurrence Heatmap (Top {TOP_N} Skills)",
    "x_label": "Skill",
    "y_label": "Skill",
    "skills": top_skills,
    # matrix[i][j] = co-occurrence count of skills[i] and skills[j]
    "matrix": matrix.values.tolist(),
    # flat list of {skill_a, skill_b, count} for easier lookup
    "pairs": [
        {"skill_a": s1, "skill_b": s2, "count": int(count)}
        for (s1, s2), count in pair_counts.items()
    ],
}
save_json("skill_cooccurrence_heatmap_top15.json", skill_heatmap_15)


# %% [markdown]
# ## Skill Co-occurrence Heatmap (Top 25 Skills)

# %%
TOP_N_25 = 25
top_skills_25 = parse_skills(df["skills"]).value_counts().head(TOP_N_25).index.tolist()

pair_counts_25 = Counter()
for skill_list in df["skills"].dropna():
    skills_in_row = list(
        {
            s.strip().lower()
            for s in skill_list.split(";")
            if s.strip().lower() in top_skills_25
        }
    )
    for pair in combinations(sorted(skills_in_row), 2):
        pair_counts_25[pair] += 1

matrix_25 = pd.DataFrame(0, index=top_skills_25, columns=top_skills_25)
for (s1, s2), count in pair_counts_25.items():
    matrix_25.loc[s1, s2] = count
    matrix_25.loc[s2, s1] = count

skill_heatmap_25 = {
    "chart_title": f"Skill Co-occurrence Heatmap (Top {TOP_N_25} Skills)",
    "x_label": "Skill",
    "y_label": "Skill",
    "skills": top_skills_25,
    "matrix": matrix_25.values.tolist(),
    "pairs": [
        {"skill_a": s1, "skill_b": s2, "count": int(count)}
        for (s1, s2), count in pair_counts_25.items()
    ],
}
save_json("skill_cooccurrence_heatmap_top25.json", skill_heatmap_25)


# %% [markdown]
# # Work Types & Trends

# %% [markdown]
# ## Jobs per Work Type (Pie / Donut)

# %%
work_type_counts = df["work_type"].value_counts().reset_index()
work_type_counts.columns = ["work_type", "job_count"]

jobs_by_work_type = {
    "chart_title": "Number of Jobs per Work Type",
    "series": [
        {"work_type": row["work_type"], "job_count": int(row["job_count"])}
        for _, row in work_type_counts.iterrows()
    ],
}
save_json("jobs_by_work_type.json", jobs_by_work_type)


# %% [markdown]
# ## Job Posting Volume Over Time (Monthly)

# %%
df["date_updated_parsed"] = pd.to_datetime(df["date_updated"], errors="coerce")
df["year_month"] = df["date_updated_parsed"].dt.to_period("M")

monthly_volume = (
    df.dropna(subset=["date_updated_parsed"])
    .groupby("year_month")
    .size()
    .reset_index(name="job_count")
    .sort_values("year_month")
)
monthly_volume["year_month_str"] = monthly_volume["year_month"].dt.strftime("%Y-%m")

posting_volume_over_time = {
    "chart_title": "Job Posting Volume Over Time (Monthly)",
    "x_label": "Month",
    "y_label": "Number of Job Postings",
    "series": [
        {"year_month": row["year_month_str"], "job_count": int(row["job_count"])}
        for _, row in monthly_volume.iterrows()
    ],
}
save_json("posting_volume_over_time.json", posting_volume_over_time)


# %% [markdown]
# ## Weekly Hours Distribution

# %%
hours_clean = pd.to_numeric(df["hours_per_week"], errors="coerce").dropna()
hours_clean = hours_clean[hours_clean > 0]

bins = [0, 10, 20, 30, 40, 50, 60, 80, float("inf")]
labels = ["1-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-80", "80+"]
hours_binned = pd.cut(hours_clean, bins=bins, labels=labels)
hours_dist = (
    hours_binned.value_counts().reindex(labels).fillna(0).astype(int).reset_index()
)
hours_dist.columns = ["range", "count"]

weekly_hours_distribution = {
    "chart_title": "Weekly Hours Distribution",
    "subtitle": "TBD & missing values excluded",
    "x_label": "Hours per Week",
    "y_label": "Number of Job Postings",
    "highlight_range": "31-40",
    "highlight_note": "31-40 hrs = standard full-time",
    "valid_records": int(len(hours_clean)),
    "total_records": int(len(df)),
    "series": [
        {"range": row["range"], "count": int(row["count"])}
        for _, row in hours_dist.iterrows()
    ],
}
save_json("weekly_hours_distribution.json", weekly_hours_distribution)


# %% [markdown]
# # Pay vs Hours (Scatter)
# Monthly salary jobs only, integer hours only.

# %%
df["hours_per_week"] = pd.to_numeric(df["hours_per_week"], errors="coerce")
df = df.dropna(subset=["hours_per_week", "average_salary"])
df = df[
    df["hours_per_week"]
    == df["hours_per_week"].apply(lambda x: int(x) if pd.notna(x) else x)
]
df = df[df["salary_type"] == "monthly"]

pay_vs_hours = []

for currency in ["USD", "PHP"]:
    subset = df[df["currency"] == currency]
    work_type_series = []

    for wt, group in subset.groupby("work_type"):
        work_type_series.append(
            {
                "work_type": wt,
                "points": [
                    {
                        "hours_per_week": int(row["hours_per_week"]),
                        "average_salary": round(float(row["average_salary"]), 4),
                        "title": str(row["title"])[:60],
                        "job_id": str(row["job_id"]) if "job_id" in row else None,
                    }
                    for _, row in group.iterrows()
                ],
            }
        )

    pay_vs_hours.append(
        {
            "currency": currency,
            "chart_title": f"Pay vs Hours — {currency}",
            "x_label": "Hours per Week",
            "y_label": f"Average Salary ({currency})",
            "filters": {"salary_type": "monthly"},
            "series": work_type_series,
        }
    )

save_json("pay_vs_hours.json", pay_vs_hours)


# %% [markdown]
# # Export Complete

# %%
print("\n✅ All chart data exported to:", OUTPUT_DIR)
print("\nFiles generated:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    path = os.path.join(OUTPUT_DIR, f)
    size_kb = os.path.getsize(path) / 1024
    print(f"  {f:55s} {size_kb:7.1f} KB")
