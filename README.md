# OLJ Market Insights

A data analysis and visualization project using [OnlineJobs.ph Job Listings dataset](https://www.kaggle.com/datasets/kennethjoshuabecaro/onlinejobs-ph-job-listings) on Kaggle.

The project takes raw job listing data scraped from OnlineJobs.ph, cleans and transforms it through a series of Jupyter notebooks.

---

## Exploration Secions

- **Salary Landscape** — Salary distribution histograms, pay-range box plots by work type, and average pay rankings by category and subcategory (in USD and PHP).
- **Market Demands** — Top 10 and Top 50 required skills, skills broken down by work type, and skill co-occurrence heatmaps (Top 15 and Top 25).
- **Work Types & Trends** — Job distribution by work type (donut chart), monthly job posting volume over time, and weekly hours distribution.
- **Pay vs. Hours** — Scatter plot correlating hours per week with average monthly salary, segmented by work type and currency.

---

## Project Structure

```
olj-market-insights/
├── data/
│   ├── reamde # link to the data
│
├── notebooks/
│   ├── 1_cleaning.ipynb         # Salary filtering, fuzzy deduplication, export
│   ├── 2_transformation.ipynb   # Salary parsing, normalization, categorization
│   └── 3_exploration.ipynb      # Exploratory data analysis and visualizations
│
├── scripts/
│   ├── convert_to_csv.py        # Exports cleaned DB to CSV (extracts skills + dates)
│   └── csv_sampler.py           # Utility to draw a random sample from any CSV
│
├── utils/
│   ├── date_extract.py          # Parses "DATE UPDATED" from raw HTML job pages
│   └── skill_extract.py         # Parses "SKILL REQUIREMENT" tags from raw HTML
│
├── results/                     # Exported HTML renders of the notebooks
├── index.html                   # Standalone frontend dashboard
├── pyproject.toml
└── uv.lock
```

---

## Data Pipeline

```
olj-jobs.db  (raw)
     │
     ▼
notebooks/1_cleaning.ipynb
  • Drop rows where salary currency cannot be identified (USD/PHP only)
  • Remove exact and near-duplicate listings (TF-IDF cosine similarity ≥ 0.80)
  • Export → olj-jobs-cleaned.db
     │
     ▼
scripts/convert_to_csv.py
  • Read olj_jobs table from cleaned DB
  • Extract skills and date_updated from raw HTML via BeautifulSoup
  • Export → data/olj-jobs-cleaned.csv
     │
     ▼
notebooks/2_transformation.ipynb
  • Parse and normalize salary strings (ranges, hourly, monthly, etc.)
  • Classify currency (USD / PHP) and salary type (hourly/monthly/weekly)
  • Add USD-normalized salary column
  • Classify job categories and subcategories
  • Export → data/transformed_jobs.csv
```

---

## Setup

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency management and requires **Python 3.13+**.

**1. Install dependencies**

```bash
uv sync
```

**2. Activate the virtual environment**

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Download the dataset**

Download the raw dataset from Kaggle and place the SQLite database at `data/olj-jobs.db`:

> https://www.kaggle.com/datasets/kennethjoshuabecaro/onlinejobs-ph-job-listings

---

## Usage

### Run the full pipeline
**NOTE** when I was doing the pipline it crashed my pc because it used around 30GB of ram, make sure your pc can handle this, if not use google colab to run the notebooks.

Execute the notebooks in order using Jupyter:

```
notebooks/1_cleaning.ipynb       → produces data/olj-jobs-cleaned.db
notebooks/2_transformation.ipynb → produces data/transformed_jobs.csv
```

Then run the extraction and analysis scripts:

```bash
py -m scripts.convert_to_csv
```

### Utility scripts

**Sample rows from a CSV for quick inspection:**

```bash
# Sample 10 records (default)
py -m scripts.csv_sampler data/transformed_jobs.csv

# Sample 50 records with a fixed seed and a custom output file
py -m scripts.csv_sampler data/transformed_jobs.csv -n 50 -o data/sample/sample_50.csv --seed 42
```
---

## Dependencies

| Package | Purpose |
|---|---|
| `pandas` | Data loading, cleaning, and transformation |
| `numpy` | Statistical computations and binning |
| `scikit-learn` | TF-IDF vectorization for fuzzy deduplication |
| `beautifulsoup4` | HTML parsing for skill and date extraction |
| `plotly` | Interactive chart rendering (exploration notebooks) |
| `seaborn` | Statistical visualizations (exploration notebooks) |

---

## Dataset

The raw data was collected from [OnlineJobs.ph](https://www.onlinejobs.ph/), a platform for hiring Filipino remote workers. The Kaggle dataset used as the source is:

> https://www.kaggle.com/datasets/kennethjoshuabecaro/onlinejobs-ph-job-listings
