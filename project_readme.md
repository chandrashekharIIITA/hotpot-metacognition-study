# Error Propagation in Multi-Step Agentic AI Workflows

## Overview
This repository contains the experimental code and evaluation protocol for investigating **trajectory drift** and compounding errors in autonomous AI agents. The study compares a standard single-pass Chain-of-Thought (CoT) baseline against a **Metacognitive Monitor** intervention (a draft-and-verify loop) to measure its impact on multi-hop reasoning tasks. 

Specifically, this project tracks the rate of **genuine corrections** versus **over-corrections** (where the monitor erroneously degrades a valid draft due to distractor noise).

## Dataset
* **Primary Dataset:** HotpotQA (Distractor Setting)
* **Partition:** Validation Split (`hotpot_dev_distractor_v1.json`)
* **Task:** Multi-hop Question Answering

## Repository Structure
```text
hotpot-metacognition-study/
├── README.md               # Study overview and execution instructions
├── requirements.txt        # Frozen dependency versions
├── data/                   # Raw and processed JSON datasets (gitignored)
├── notebooks/              # Jupyter/Colab execution environments
│   └── main_experiment.ipynb
├── src/                    # Reusable Python modules
│   ├── api_client.py       # Robust retry/backoff logic for Gemini API
│   └── evaluator.py        # String normalization & EM/F1 scoring
└── results/                # Output artifacts
    ├── logs_baseline.csv
    └── logs_experimental.csv
```

## Prerequisites & Installation
1. Ensure you have Python 3.10+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. You will need a valid Google Gemini API key. Set it as an environment variable or configure it in your Colab Secrets tab as `GEMINI_API_KEY`.

## Usage
The primary experiment is designed to be executed via Google Colab. 
1. Open `notebooks/main_experiment.ipynb`.
2. Run the environment configuration and dataset download cells.
3. Execute the baseline and experimental loops. The script includes automated exponential backoff to handle HTTP 503/429 rate limits.

## Author
* **Chandra Shekhar Sahu** (MNS2026003) - Indian Institute of Information Technology, Allahabad