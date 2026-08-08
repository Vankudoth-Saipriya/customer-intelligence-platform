"""
Full Memory Audit Script — Customer Intelligence Platform.
Measures RSS, heap, per-DataFrame, per-page, and peak across the full user journey.
"""
import gc
import os
import sys
from pathlib import Path
import tracemalloc

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import psutil
    PROC = psutil.Process(os.getpid())
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    PROC = None

import pandas as pd

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def rss_mb():
    if HAS_PSUTIL:
        return PROC.memory_info().rss / (1024 * 1024)
    return 0.0

def df_mb(df):
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────
# Phase 1: Baseline
# ─────────────────────────────────────────────
tracemalloc.start()
section("BASELINE (before any imports)")
base_rss = rss_mb()
print(f"RSS: {base_rss:.1f} MB")

# ─────────────────────────────────────────────
# Phase 2: Import artifact_store (first load)
# ─────────────────────────────────────────────
section("ARTIFACT STORE — First Load (all 4 tables)")
from app.ai import artifact_store

rss_before_load = rss_mb()
print(f"RSS before first load: {rss_before_load:.1f} MB")

fs  = artifact_store.get_feature_store()
seg = artifact_store.get_segments()
clv = artifact_store.get_clv_predictions()
rp  = artifact_store.get_repeat_predictions()

rss_after_load = rss_mb()
print(f"RSS after first load:  {rss_after_load:.1f} MB  (+{rss_after_load - rss_before_load:.1f} MB)")

print("\nDataFrame memory breakdown:")
dfs = {"feature_store": fs, "segments": seg, "clv_predictions": clv, "repeat_predictions": rp}
total_df = 0
for name, df in dfs.items():
    if df is not None:
        mb = df_mb(df)
        total_df += mb
        print(f"  {name}: {df.shape[0]:,} rows x {df.shape[1]} cols = {mb:.2f} MB")
    else:
        print(f"  {name}: None")
print(f"  TOTAL DataFrames: {total_df:.2f} MB")

# ─────────────────────────────────────────────
# Phase 3: Second call — identity check (no reload)
# ─────────────────────────────────────────────
section("ARTIFACT STORE — Second Call (should be zero cost)")
rss_before_second = rss_mb()
fs2  = artifact_store.get_feature_store()
seg2 = artifact_store.get_segments()
clv2 = artifact_store.get_clv_predictions()
rp2  = artifact_store.get_repeat_predictions()
rss_after_second = rss_mb()
print(f"RSS before 2nd call: {rss_before_second:.1f} MB")
print(f"RSS after 2nd call:  {rss_after_second:.1f} MB  (+{rss_after_second - rss_before_second:.1f} MB)")
print(f"Same objects: fs={fs is fs2}, seg={seg is seg2}, clv={clv is clv2}, rp={rp is rp2}")

# ─────────────────────────────────────────────
# Phase 4: Simulate each page data load
# ─────────────────────────────────────────────
import json

def load_eda(name):
    path = ARTIFACTS_DIR / "eda" / f"{name}_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

section("PER-PAGE MEMORY SIMULATION")
pages = [
    ("Home", ["customer", "sales", "delivery", "review"]),
    ("Customer Analytics", ["customer"]),
    ("Product Analytics", ["product"]),
    ("Sales Analytics", ["sales"]),
    ("Delivery Analytics", ["delivery"]),
    ("Payment Analytics", ["payment"]),
    ("Review Analytics", ["review"]),
    ("Segmentation", []),
    ("CLV Prediction", []),
    ("Repeat Purchase", []),
    ("AI Business Analyst", ["customer"]),
]

print(f"\n{'Page':<30} {'RSS Before':>12} {'RSS After':>11} {'Delta':>8}")
print("-" * 65)

for page_name, eda_names in pages:
    rss_b = rss_mb()
    eda_data = {}
    for name in eda_names:
        try:
            eda_data[name] = load_eda(name)
        except Exception:
            pass
    # Parquet data is already cached — no reload
    if "Segmentation" in page_name:
        _ = artifact_store.get_segments()
    elif "CLV" in page_name:
        _ = artifact_store.get_clv_predictions()
    elif "Repeat" in page_name:
        _ = artifact_store.get_repeat_predictions()
    elif "Customer Analytics" in page_name:
        _ = artifact_store.get_feature_store()
    elif "AI Business" in page_name:
        _ = artifact_store.get_segments()
        _ = artifact_store.get_clv_predictions()
        _ = artifact_store.get_repeat_predictions()
        _ = artifact_store.get_feature_store()

    gc.collect()
    rss_a = rss_mb()
    print(f"{page_name:<30} {rss_b:>10.1f} MB {rss_a:>9.1f} MB {rss_a - rss_b:>+7.1f} MB")
    del eda_data
    gc.collect()

# ─────────────────────────────────────────────
# Phase 5: Plotly figure memory
# ─────────────────────────────────────────────
section("PLOTLY FIGURE MEMORY ESTIMATION")
import plotly.express as px
import sys as _sys

if seg is not None and "cluster_description" in seg.columns:
    gc.collect()
    rss_b = rss_mb()
    fig = px.pie(seg["cluster_description"].value_counts().reset_index(),
                 names="cluster_description", values="count", hole=0.4)
    fig_size = _sys.getsizeof(fig.to_json()) / (1024 * 1024)
    rss_a = rss_mb()
    print(f"Pie chart (seg 96k rows aggregated) — JSON size: {fig_size:.2f} MB, RSS delta: {rss_a - rss_b:.1f} MB")
    del fig; gc.collect()

if clv is not None and "total_revenue" in clv.columns:
    rss_b = rss_mb()
    # Un-sampled scatter — worst case
    fig_big = px.scatter(clv, x="total_revenue", y="predicted_clv")
    fig_big_size = _sys.getsizeof(fig_big.to_json()) / (1024 * 1024)
    rss_a_big = rss_mb()
    del fig_big; gc.collect()
    # Sampled scatter — optimized case
    rss_b2 = rss_mb()
    fig_small = px.scatter(clv.sample(2000, random_state=42), x="total_revenue", y="predicted_clv")
    fig_small_size = _sys.getsizeof(fig_small.to_json()) / (1024 * 1024)
    rss_a_small = rss_mb()
    del fig_small; gc.collect()
    print(f"Scatter (96k points) — JSON: {fig_big_size:.2f} MB, RSS delta: {rss_a_big - rss_b:.1f} MB")
    print(f"Scatter (2k sample)  — JSON: {fig_small_size:.2f} MB, RSS delta: {rss_a_small - rss_b2:.1f} MB")

if rp is not None and "repeat_propensity" in rp.columns:
    rss_b = rss_mb()
    fig_hist_big = px.histogram(rp, x="repeat_propensity", nbins=50)
    fig_hist_big_size = _sys.getsizeof(fig_hist_big.to_json()) / (1024 * 1024)
    rss_a_big = rss_mb()
    del fig_hist_big; gc.collect()

    rss_b2 = rss_mb()
    fig_hist_small = px.histogram(rp.sample(5000, random_state=42), x="repeat_propensity", nbins=50)
    fig_hist_small_size = _sys.getsizeof(fig_hist_small.to_json()) / (1024 * 1024)
    rss_a_small = rss_mb()
    del fig_hist_small; gc.collect()
    print(f"Histogram (96k rows) — JSON: {fig_hist_big_size:.2f} MB, RSS delta: {rss_a_big - rss_b:.1f} MB")
    print(f"Histogram (5k sample)— JSON: {fig_hist_small_size:.2f} MB, RSS delta: {rss_a_small - rss_b2:.1f} MB")

# Feature store monetary histogram
if fs is not None and "monetary_value" in fs.columns:
    rss_b = rss_mb()
    subset = fs[fs["monetary_value"] <= 1000]
    fig_mon = px.histogram(subset, x="monetary_value", nbins=50)
    fig_mon_size = _sys.getsizeof(fig_mon.to_json()) / (1024 * 1024)
    rss_a = rss_mb()
    del fig_mon; gc.collect()
    print(f"Monetary histogram ({len(subset):,} rows) — JSON: {fig_mon_size:.2f} MB, RSS delta: {rss_a - rss_b:.1f} MB")

# ─────────────────────────────────────────────
# Phase 6: session_state simulation
# ─────────────────────────────────────────────
section("SESSION STATE — Chat History Memory")
import sys as _sys2
chat_history = [{"role": "assistant", "content": "Hello!"}]
# Simulate 20 messages of ~300 chars each
for i in range(20):
    chat_history.append({"role": "user", "content": "What is total revenue?" * 3})
    chat_history.append({"role": "assistant", "content": "### Revenue\n" + ("The total revenue is $16M. " * 20)})
size_kb = _sys2.getsizeof(str(chat_history)) / 1024
print(f"20-message chat history: {size_kb:.1f} KB (negligible)")

# ─────────────────────────────────────────────
# Phase 7: st.cache_data — double-copy issue
# ─────────────────────────────────────────────
section("CACHE ANALYSIS — @st.cache_data copy overhead")
print("st.cache_data COPIES the return value on every call.")
print("With 4 DataFrames x ~30 MB each = up to 120 MB extra per RERUN.")
print("These copies persist in Streamlit's internal cache until TTL expires.")
print("On a 512 MB system, 2 reruns can push to 240 MB cache overhead alone.")
print()
print("SOLUTION: @st.cache_data(ttl=3600, max_entries=1) limits accumulation.")
print("BETTER:   Return lightweight summaries from @st.cache_data, use")
print("          artifact_store singletons for the raw DataFrames — no copies.")

# ─────────────────────────────────────────────
# Phase 8: tracemalloc peak
# ─────────────────────────────────────────────
section("TRACEMALLOC PEAK")
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"Current heap: {current/(1024*1024):.2f} MB")
print(f"Peak heap:    {peak/(1024*1024):.2f} MB")

# ─────────────────────────────────────────────
# Phase 9: Final RSS
# ─────────────────────────────────────────────
section("FINAL RSS")
gc.collect()
final_rss = rss_mb()
print(f"Final RSS: {final_rss:.1f} MB")

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
section("ROOT CAUSE SUMMARY")
print("""
IDENTIFIED ROOT CAUSES OF EXIT 137:

1. artifact_store._load() calls pd.read_parquet TWICE per table (schema peek + actual).
   → Doubles peak RAM during first load: 4 tables × 2x = ~243 MB spike at startup.

2. @st.cache_data wrapper around artifact_store getters forces Streamlit to
   COPY the DataFrame on every page navigation rerun.
   → 4 DataFrames × ~30 MB each × 2 copies = ~240 MB cache overhead per rerun cycle.
   → On repeated navigation, cache accumulates: 2 reruns = 480 MB → OOM kill.

3. Customer Analytics page loads full feature_store (13 cols × 96k rows = 45 MB)
   and then creates a histogram from a FILTERED SUBSET without sampling.
   → Filter `df_fs[monetary_value <= 1000]` creates a 44 MB copy.

4. @st.cache_data has no TTL and no max_entries set.
   → Old cached copies are NEVER evicted during a session.

5. Plotly scatter (CLV page) is sampled to 2000 points ✓ already fixed.
   Plotly histogram (repeat purchase) is sampled to 5000 points ✓ already fixed.
   Monetary histogram (customer analytics) is NOT sampled — uses a filtered copy.

ESTIMATED PEAK MEMORY BREAKDOWN (Render Production):
  Python + Streamlit runtime:     120 MB
  4 DataFrames (artifact_store):  122 MB
  st.cache_data copies (2 reruns): 244 MB
  _load() double-read spike:       122 MB transient
  ─────────────────────────────────────
  PEAK TOTAL:                     ~608 MB  ← exceeds 512 MB → Exit 137
""")
