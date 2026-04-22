from pathlib import Path
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"

st.set_page_config(
    page_title="AI Governance Document Explorer",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    path = RESULTS / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

country_summary = load_csv("table_country_summary.csv")
doc_summary = load_csv("table_doc_summary.csv")
top_docs = load_csv("table_top_documents_by_category.csv")
snippets = load_csv("table_representative_snippets.csv")
corpus_overview = load_csv("table_corpus_overview.csv")
corpus_country = load_csv("table_country_corpus_summary.csv")
report_summary = load_csv("table_report_summary_numbers.csv")
failed_docs = load_csv("table_failed_docs.csv")

CATEGORY_LABELS = {
    "TRANSPARENCY": "Transparency",
    "OVERSIGHT_AUDIT": "Oversight/Audit",
    "ACCOUNTABILITY_LIABILITY": "Accountability/Liability",
    "PUBLIC_PARTICIPATION": "Public Participation",
    "APPEALS_REMEDY": "Appeals/Remedy",
}

st.title("AI Governance Document Explorer")
st.caption("Prototype local interface for comparing U.S. and Chinese AI governance documents.")

st.markdown(
    """
    This local explorer organizes outputs from a comparative text analysis of U.S. and Chinese AI governance documents.
    It helps users move between country-level summaries, document-level patterns, and supporting evidence.
    """
)

if report_summary.empty:
    st.error(
        "Could not find result files. Run your analysis notebook first so the CSV and PNG files are saved in the results/ folder."
    )
    st.stop()

with st.sidebar:
    st.header("Filters")

    country_options = ["All"]
    if not doc_summary.empty and "country" in doc_summary.columns:
        country_options += sorted(doc_summary["country"].dropna().unique().tolist())
    selected_country = st.selectbox("Country", country_options)

    category_options = ["All"] + list(CATEGORY_LABELS.keys())
    selected_category = st.selectbox(
        "Governance category",
        category_options,
        format_func=lambda x: "All" if x == "All" else CATEGORY_LABELS.get(x, x),
    )

    doc_options = ["All"]
    if not doc_summary.empty and "doc_id" in doc_summary.columns:
        temp = doc_summary.copy()
        if selected_country != "All":
            temp = temp[temp["country"] == selected_country]
        doc_options += sorted(temp["doc_id"].dropna().unique().tolist())
    selected_doc = st.selectbox("Document", doc_options)

    st.markdown("---")
    st.markdown("**Current selection**")
    pretty_category = "All" if selected_category == "All" else CATEGORY_LABELS.get(selected_category, selected_category)
    st.write(f"Country: {selected_country}")
    st.write(f"Category: {pretty_category}")
    st.write(f"Document: {selected_doc}")

st.markdown("### Corpus snapshot")
summary_cols = st.columns(5)
row = report_summary.iloc[0]
summary_cols[0].metric("US documents", int(row.get("n_us_documents", 0)))
summary_cols[1].metric("CN documents", int(row.get("n_cn_documents", 0)))
summary_cols[2].metric("US chunks", int(row.get("n_us_chunks", 0)))
summary_cols[3].metric("CN chunks", int(row.get("n_cn_chunks", 0)))
summary_cols[4].metric("Failed docs", int(row.get("n_failed_docs", 0)))

if not corpus_country.empty:
    with st.expander("Corpus summary table", expanded=False):
        st.dataframe(corpus_country, width="stretch")

country_tab, doc_tab, evidence_tab, corpus_tab = st.tabs([
    "Country Overview",
    "Document Explorer",
    "Evidence",
    "Corpus & Pipeline",
])

with country_tab:
    st.subheader("Country-level comparison")
    st.markdown(
        """
        This section compares the average tagged share of each governance category across the U.S. and Chinese corpora.
        The dumbbell plot highlights the gap for each category, while the radar chart gives a profile view of the two country-level patterns.
        """
    )

    left, right = st.columns([1.05, 1.2])

    with left:
        display_df = country_summary.copy()
        rename_map = {k: v for k, v in CATEGORY_LABELS.items() if k in display_df.columns}
        display_df = display_df.rename(columns=rename_map)
        st.dataframe(display_df, width="stretch", height=220)

    with right:
        dumbbell_path = RESULTS / "fig_country_dumbbell.png"
        if dumbbell_path.exists():
            st.image(str(dumbbell_path), caption="Country comparison by governance category")

    st.divider()

    radar_path = RESULTS / "fig_country_radar.png"
    if radar_path.exists():
        st.image(str(radar_path), caption="Country-level governance profile")

with doc_tab:
    st.subheader("Document-level exploration")

    filtered_docs = doc_summary.copy()
    if selected_country != "All" and "country" in filtered_docs.columns:
        filtered_docs = filtered_docs[filtered_docs["country"] == selected_country]
    if selected_doc != "All" and "doc_id" in filtered_docs.columns:
        filtered_docs = filtered_docs[filtered_docs["doc_id"] == selected_doc]

    if selected_category != "All" and selected_category in filtered_docs.columns:
        filtered_docs = filtered_docs.sort_values(selected_category, ascending=False)

    if selected_doc != "All" and not doc_summary.empty:
        match = doc_summary[doc_summary["doc_id"] == selected_doc]
        if not match.empty:
            st.markdown("### Selected document")
            st.dataframe(match, width="stretch", height=140)

    st.markdown("### Filtered document table")
    rename_map = {k: v for k, v in CATEGORY_LABELS.items() if k in filtered_docs.columns}
    filtered_docs_display = filtered_docs.rename(columns=rename_map)
    st.dataframe(filtered_docs_display, width="stretch", height=300)

    st.divider()
    st.markdown("### Heatmap view")
    st.markdown(
        "The heatmap helps compare category profiles across documents and shows whether patterns are broad-based or concentrated in a few texts."
    )

    heatmap_path = RESULTS / "fig_doc_category_heatmap.png"
    if heatmap_path.exists():
        st.image(str(heatmap_path), caption="Document-by-category heatmap")

with evidence_tab:
    st.subheader("Evidence and supporting outputs")
    st.markdown(
        """
        This section combines two forms of evidence: ranked document-level outputs and representative example chunks.
        The ranking helps identify which documents drive the strongest patterns, while the snippets give a limited but concrete view of matched text.
        """
    )

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("### Document ranking")
        ranking_df = top_docs.copy()

        if selected_country != "All" and "country" in ranking_df.columns:
            ranking_df = ranking_df[ranking_df["country"] == selected_country]
        if selected_doc != "All" and "doc_id" in ranking_df.columns:
            ranking_df = ranking_df[ranking_df["doc_id"] == selected_doc]
        if selected_category != "All" and selected_category in ranking_df.columns:
            ranking_df = ranking_df.sort_values(selected_category, ascending=False)

        ranking_display = ranking_df.rename(
            columns={k: v for k, v in CATEGORY_LABELS.items() if k in ranking_df.columns}
        )
        st.dataframe(ranking_display, width="stretch", height=320)

        top_path = RESULTS / "fig_top_docs_oversight.png"
        if top_path.exists() and selected_category in ("All", "OVERSIGHT_AUDIT"):
            st.image(str(top_path), caption="Document ranking by Oversight/Audit share")

    with right:
        st.markdown("### Representative snippets")
        snippet_df = snippets.copy()

        if selected_country != "All" and "country" in snippet_df.columns:
            snippet_df = snippet_df[snippet_df["country"] == selected_country]
        if selected_category != "All" and "category" in snippet_df.columns:
            snippet_df = snippet_df[snippet_df["category"] == selected_category]
        if selected_doc != "All" and "doc_id" in snippet_df.columns:
            snippet_df = snippet_df[snippet_df["doc_id"] == selected_doc]

        if not snippet_df.empty:
            for _, r in snippet_df.head(8).iterrows():
                label = CATEGORY_LABELS.get(r.get("category", ""), r.get("category", ""))
                with st.container(border=True):
                    st.markdown(f"**{label}** · {r.get('country', '')} · `{r.get('doc_id', '')}`")
                    st.caption(f"Chunk: {r.get('chunk_id', '')}")
                    snippet = str(r.get("text_snippet", ""))
                    if len(snippet) > 350:
                        snippet = snippet[:350] + "..."
                    st.write(snippet)
        else:
            st.info("No snippets match the current filters.")

with corpus_tab:
    st.subheader("Corpus and preprocessing pipeline")
    st.markdown(
        """
        This section shows how the corpus was constructed, how document length varies across the corpus,
        and how preprocessing decisions shape the analytical dataset.
        """
    )

    pipeline_path = RESULTS / "fig_method_pipeline.png"
    lollipop_path = RESULTS / "fig_doc_chunk_lollipop.png"
    chunks_path = RESULTS / "fig_chunks_by_country.png"

    img_cols = st.columns(3)
    if pipeline_path.exists():
        img_cols[0].image(str(pipeline_path), caption="Method pipeline")
    if lollipop_path.exists():
        img_cols[1].image(str(lollipop_path), caption="Document chunk counts")
    if chunks_path.exists():
        img_cols[2].image(str(chunks_path), caption="Chunks by country")

    with st.expander("Corpus overview table", expanded=False):
        st.dataframe(corpus_overview, width="stretch")

    if not failed_docs.empty:
        with st.expander("Failed documents", expanded=False):
            st.dataframe(failed_docs, width="stretch")
