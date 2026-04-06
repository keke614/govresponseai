# GovResponseAI (SIADS 699 Capstone)

This project is a computational political science "text-as-data" analysis of AI governance policy documents.

Current pipeline (US pilot):
- document index: `metadata/doc_index.csv`
- download + parse PDFs into chunks: `notebooks/01_fetch_and_parse.ipynb`
- baseline keyword tagging for 5 responsiveness mechanism categories

## How to run
1) Install dependencies: `pip install -r requirements.txt`
2) Update `metadata/doc_index.csv` with document URLs
3) Run `notebooks/01_fetch_and_parse.ipynb` to generate chunks locally (not committed)
4) Run tagging/analysis cells to reproduce figures

## Data access
Raw PDFs are not redistributed in this repo. See `DATA_ACCESS.md` for source links and collection notes.
