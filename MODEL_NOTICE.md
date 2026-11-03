# Model notice

No model weights are downloaded or redistributed by this repository at present. Planned models
will be fetched at pinned revisions after explicit approval and recorded in `models.lock.json`.

For each model we record two separate things and do not assume either determines the other:

1. **Weight license**: the license under which the publisher distributes the weights.
2. **Training-data terms**: the documented terms of the data the model was trained on.
   Whether dataset terms carry over to trained weights is legally unsettled; we do not assert
   an answer. Anyone considering commercial use should review both independently.

| Model (planned role) | Weight license (model card) | Documented training data / terms | Status |
|---|---|---|---|
| BAAI/bge-small-en-v1.5 (embeddings) | MIT | per model card (mixed public datasets) | pending approval |
| cross-encoder/ms-marco-MiniLM-L6-v2 (reranker) | Apache-2.0 | MS MARCO; terms: "intended for non-commercial research purposes only" (<https://microsoft.github.io/msmarco/>) | pending approval |
| BAAI/bge-reranker-v2-m3 (reranker ablation) | Apache-2.0 | per model card | pending approval |
| Qwen/Qwen3-4B-Instruct-2507, GGUF quantization (local adjudicator) | Apache-2.0 | per model card | pending approval |

This project is a non-commercial portfolio project.
