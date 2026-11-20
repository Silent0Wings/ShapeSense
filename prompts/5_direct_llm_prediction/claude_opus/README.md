# Direct LLM prediction - Claude Opus 5.5

Blind direct visual classification run completed on **2026-11-19** using `claude-opus-5-5-medium` against the 50 seed-0 labeled training examples (`results/direct_llm_prediction/fewshot_example_ids.csv`) and the 200 seed-0 held-out test images (`results/direct_llm_prediction/sample_ids.csv`).

- **Score:** **92.55 Macro F1** (`185/200`, `92.50%` accuracy) vs. `97.50` Macro F1 for trained CNN `A2_0`
- **Predictions CSV:** [`results/direct_llm_prediction/claude_opus_predictions.csv`](../../../results/direct_llm_prediction/claude_opus_predictions.csv)
- **Blind ID mapping:** [`results/direct_llm_prediction/blind_id_map.csv`](../../../results/direct_llm_prediction/blind_id_map.csv)
- **Error comparison:** [`01_direct-prediction-error-comparison.md`](../cross_critique/01_direct-prediction-error-comparison.md)

## Batch Exchanges (10 batches × 20 images)

- [Batch 01 (T001-T020)](01_batch-01.md)
- [Batch 02 (T021-T040)](02_batch-02.md)
- [Batch 03 (T041-T060)](03_batch-03.md)
- [Batch 04 (T061-T080)](04_batch-04.md)
- [Batch 05 (T081-T100)](05_batch-05.md)
- [Batch 06 (T101-T120)](06_batch-06.md)
- [Batch 07 (T121-T140)](07_batch-07.md)
- [Batch 08 (T141-T160)](08_batch-08.md)
- [Batch 09 (T161-T180)](09_batch-09.md)
- [Batch 10 (T181-T200)](10_batch-10.md)
