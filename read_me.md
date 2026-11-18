# Error Propagation in Multi-Step Agentic AI Workflows

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Dataset: HotpotQA](https://img.shields.io/badge/Dataset-HotpotQA-green.svg)](https://hotpotqa.github.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 Overview

As Large Language Models (LLMs) transition into autonomous **Deep Research Agents (DRAs)**, they increasingly rely on multi-step reasoning loops. However, these systems exhibit a severe vulnerability: **trajectory drift**. An initial logical error or factual hallucination early in the execution chain compounds across sequential steps, eventually causing the agent to synthesize completely fabricated conclusions.

This repository contains the experimental code, datasets, and evaluation protocols for an M.Tech research study investigating whether explicit self-reflection can mitigate this drift. 

The study compares:
1. **Baseline (Single-Pass CoT):** A standard Chain-of-Thought reasoning prompt.
2. **Experimental (Metacognitive Monitor):** A dual-pass "draft-and-verify" loop where the model is explicitly instructed to review its own draft against the source text before finalizing its answer.

### 🎯 Key Research Focus
This project rigorously tracks the transition states of paired samples to measure:
* **Genuine Recoveries:** Instances where the monitor successfully fixes a flawed initial draft.
* **Over-Corrections:** Instances where the monitor erroneously degrades a perfectly valid draft due to adversarial distractor noise (a phenomenon identified as *Distractor Hallucination* and *Over-Cautious Hedging*).

---

## 📊 Dataset: HotpotQA (Distractor Setting)

This experiment utilizes the **HotpotQA** dataset, specifically the Validation Split (`hotpot_dev_distractor_v1.json`). 

* **Why this dataset?** It requires complex, multi-hop reasoning across multiple paragraphs to find the correct answer.
* **The "Distractor" Setting:** Every query is provided with 2 "gold" (relevant) paragraphs and 8 "distractor" (irrelevant but semantically similar) paragraphs. This adversarial noise is crucial for testing whether the Metacognitive Monitor can stay grounded or if it gets confused and hallucinates.

---

## 🏗️ Repository Structure

```text
hotpot-metacognition-study/
├── README.md                           # Comprehensive study overview and execution guide
├── requirements.txt                    # Frozen dependency versions for reproducibility
├── research_decisions.md               # Log of protocol deviations (e.g., API fallbacks, rate limits)
├── data/                               # Raw and processed JSON datasets
│   └── hotpot_dev_distractor_v1.json   # Downloaded dataset (n=7405)
├── notebooks/                          # Jupyter/Colab execution environments
│   └── main_experiment.ipynb           # Interactive notebook containing the full pipeline
├── src/                                # Reusable Python modules
│   ├── api_client.py                   # Robust Gemini API wrapper with exponential backoff & jitter
│   └── evaluator.py                    # Custom string normalization, Exact Match (EM), & F1 scoring
└── results/                            # Output artifacts and analytical logs
    ├── baseline_results.csv            # Predictions from the Single-Pass CoT
    ├── experimental_results.csv        # Predictions from the Dual-Pass Monitor
    ├── paired_analysis_valid.csv       # Subset of successfully matched question pairs
    ├── paired_analysis_failed.csv      # Log of incomplete API responses (crashes/timeouts)
    └── over_corrections_analysis.csv   # Filtered log of instances where the monitor degraded the draft
```

---

## ⚙️ Methodology & Architecture

### 1. The API Client (`api_client.py`)
Evaluating hundreds of multi-hop prompts triggers severe rate-limiting (HTTP 429) and capacity constraints (HTTP 503) from standard LLM APIs. The custom `GeminiAPIClient` implements a robust **exponential backoff algorithm with jitter**. If a generation fails, the script pauses, doubles the wait time (starting at a base delay of 15s), and retries up to 5 times to guarantee a 100% execution success rate.

### 2. The Evaluator (`evaluator.py`)
Standard substring matching is notoriously brittle (e.g., scoring an exact match failure if the prediction is "rolling stones" but the ground truth is "The Rolling Stones"). The evaluator module applies a **stringent text normalization pipeline**:
* Converts all text to lowercase.
* Strips all punctuation.
* Removes common articles ("a", "an", "the").
* Standardizes whitespace before computing **Exact Match (EM)** and **Token F1** scores.

---

## 💻 Prerequisites & Installation

1. **Python Environment:** Ensure you have Python 3.10+ installed. It is recommended to use a virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Configuration:** 
   You must possess a valid Google Gemini API key. 
   * **Local Execution:** Set it as an environment variable: `export GEMINI_API_KEY="your_api_key_here"`
   * **Google Colab:** Configure it in your Colab Secrets tab with the name `GEMINI_API_KEY` and grant notebook access.

---

## 🚀 Usage & Execution Order

To guarantee scientific reproducibility, the experiment must be executed in the following strict order. You can run these step-by-step via the `notebooks/main_experiment.ipynb` file.

### Step 1: Data Ingestion
Run the dataset loader cell to fetch the `hotpot_qa` distractor dataset from HuggingFace and slice it into the local `data/` directory.

### Step 2: Baseline Generation
Execute the Single-Pass CoT loop. The agent will read the context and question, provide step-by-step reasoning, and output a `FINAL ANSWER`. This establishes the baseline zero-shot accuracy.
* *Output:* `results/baseline_results.csv`

### Step 3: Experimental Generation (Metacognitive Monitor)
Execute the Dual-Pass loop. 
* **Phase 1:** The agent generates a `DRAFT ANSWER`.
* **Phase 2:** The script injects the context, the query, and the draft into a secondary verification prompt, forcing the agent to evaluate its own work.
* *Note: Due to rate-limit pacing (sleep timers), a 200-sample execution will take several hours. Leave the session active.*
* *Output:* `results/experimental_results.csv`

### Step 4: Variance Evaluation
Run `evaluator.py` against the generated CSVs. This script aligns the IDs, normalizes the text, calculates the transitions (e.g., Correct $\rightarrow$ Wrong), and isolates the Over-Correction rate.

---

## 👨‍🎓 Author
**Chandra Shekhar Sahu** (MNS2026003)  
Indian Institute of Information Technology, Allahabad, India  
*M.Tech Research Project Thesis Repository*