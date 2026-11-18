# Research Decisions & Protocol Log
Project: Error Propagation in Multi-Step Agentic AI Workflows
Author: Chandra Shekhar Sahu (MNS2026003)

This log documents all critical runtime decisions, protocol deviations, and engineering adaptations made during the execution of the experimental phase, as mandated by the Frozen Evaluation Protocol.

## 1. Model Availability & Fallback Routing
*   **Target Model:** `gemini-3.8-flash`
*   **Encountered Issue:** During initial execution, the API returned HTTP `503 UNAVAILABLE` for `gemini-3.8-flash`, indicating the model was experiencing temporary high demand and capacity constraints.
*   **Resolution:** To ensure the experiment proceeded without delaying the 1-2 week timeline, the execution automatically fell back to the `gemini-3.5-flash-lite` model. This model possesses sufficient zero-shot reasoning capabilities to act as a valid testbed for the metacognitive monitor prompt structure.

## 2. Handling Rate Limits & Execution Stability
*   **Encountered Issue:** Executing a dual-pass prompt on 200 samples requires 400 distinct API calls. Using a free-tier or standard API key introduces severe rate limiting (`HTTP 429 Too Many Requests`).
*   **Resolution:** An exponential backoff algorithm with jitter was implemented within the `api_client.py` and generation scripts. If a `429` or `503` error occurred, the script paused execution, doubled the wait time (starting at a base delay of 15 seconds), and retried up to 5 times.
*   **Outcome:** This ensured a 100% execution success rate across the 200-sample partition, resulting in zero incomplete pairs and an empty `paired_analysis_failed.csv` log.

## 3. Evaluation Metric Normalization
*   **Encountered Issue:** The standard substring matching technique used in early baselines proved excessively brittle (e.g., scoring an exact match failure when the prediction was "animorphs" but the ground truth was "Animorphs").
*   **Resolution:** A stringent text normalization module was engineered in `evaluator.py`. Prior to EM and F1 scoring, both the prediction and the ground truth were converted to lowercase, stripped of all punctuation, and stripped of common articles ("a", "an", "the"). 
