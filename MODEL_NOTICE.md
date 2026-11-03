# Model notice

Weights are **never committed or redistributed** by this repository. With the owner's
approval (2026-11-03), they were fetched by `scripts/fetch_models.py` into `./models/`
(git-ignored), and every file was verified against `models.lock.json`:
- large (LFS) files by SHA-256;
- small files by the git blob SHA-1 that Hugging Face publishes.

Each model has two separate kinds of terms:

1. **Weight license:** the license the publisher states for the weights (from the model
   card or repository metadata).
2. **Training-data terms:** the terms of the documented training data.

We do **not** assume either one determines the other. Whether dataset terms carry over to
trained weights is legally unsettled, and we draw no conclusion. Anyone considering commercial
use should review both independently. This is a non-commercial portfolio project.

| Role | Repository @ full revision | Weight file (bytes, SHA-256) | Weight license (as stated) | Training-data terms (documented) |
|---|---|---|---|---|
| Embeddings | `BAAI/bge-small-en-v1.5` @ `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` | `model.safetensors` (133,466,304; `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`) | MIT | Not reviewed in detail here; see the model card |
| Reranker | `cross-encoder/ms-marco-MiniLM-L6-v2` @ `233902d25c440f23af6f7d6e94d2946bac0bee0a` | `model.safetensors` (90,870,598; `821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae`) | Apache-2.0 | Trained on MS MARCO passage ranking (model card). The MS MARCO terms state the datasets are "intended for non-commercial research purposes only" (<https://microsoft.github.io/msmarco/>) |
| Adjudicator (local, advisory) | `unsloth/Qwen3-4B-Instruct-2507-GGUF` @ `a06e946bb6b655725eafa393f4a9745d460374c9` | `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (2,497,281,120; `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`) | Apache-2.0 (repository metadata; the base model `Qwen/Qwen3-4B-Instruct-2507` is also Apache-2.0 per its card) | Not reviewed in detail here; see the base model card |

## Third-party quantization provenance

The GGUF file was produced by **unsloth**, a third party, not by Qwen. Its repository
metadata names `Qwen/Qwen3-4B-Instruct-2507` as the base model (`base_model:quantized`). No
official Qwen GGUF repository was found on 2026-11-03. We have **not** independently verified
that this quantization faithfully reproduces the base weights; we verified only that the file
matches the published hash.

## Runtime

`llama-server` is built inside the project (`.tools/llama.cpp`, git-ignored) from llama.cpp
commit `8fc0376721e9662d498a5706d7ee8e7574ce99f4` (tag `b12081`), with Metal enabled. It
binds to 127.0.0.1 only, and the adapter refuses non-loopback endpoints. Models load with
`HF_HUB_OFFLINE=1`, so nothing is fetched at runtime.

```bash
.tools/llama.cpp/build/bin/llama-server -m models/unsloth__Qwen3-4B-Instruct-2507-GGUF/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 8192 -ngl 99 --alias qwen3-4b-instruct-2507-q4km --no-webui
```
