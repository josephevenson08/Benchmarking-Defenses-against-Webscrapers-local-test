# Model timing for scraper (c)

Run 2026-11-17T13:32:53 · Ollama 0.40.16 · pages /products/p1, /products/p2, /articles/a1 · 2 timed call(s) per page · reply capped at 400 tokens · temperature 0

## Models

| Model | Parameters | Quantization | Size | Digest | Thinking | Load (s) |
|---|---|---|---|---|---|---|
| `qwen3:4b` | 4.0B | Q4_K_M | 2.50 GB | `359d7dd4bcda` | off | 11.697 |
| `gemma3:1b` | 999.89M | Q4_K_M | 0.81 GB | `97558784bdc9` | model default | 2.353 |
| `llama3.2:3b` | 3.2B | Q4_K_M | 2.02 GB | `a80c4f17acd5` | model default | 8.955 |

## Averages per page (warm model)

| Model | Seconds per page | Prompt tokens | Reply tokens | Reply tokens/s | Values found in reply | Errors |
|---|---|---|---|---|---|---|
| `qwen3:4b` | 36.691 | 166.333 | 400.0 | 11.25 | 49/50 | 0 |
| `gemma3:1b` | 5.707 | 168.0 | 129.333 | 25.633 | 48/50 | 0 |
| `llama3.2:3b` | 6.796 | 173.0 | 89.0 | 14.867 | 50/50 | 0 |

## Every call

| Model | Page | Repeat | Wall (s) | Prompt tokens | Prompt (s) | Reply tokens | Reply (s) | Values found |
|---|---|---|---|---|---|---|---|---|
| `qwen3:4b` | /products/p1 | 1 | 38.407 | 184 | 0.117 | 400 | 38.215 | 10/10 |
| `qwen3:4b` | /products/p1 | 2 | 35.341 | 184 | 0.116 | 400 | 35.166 | 10/10 |
| `qwen3:4b` | /products/p2 | 1 | 37.791 | 176 | 3.04 | 400 | 34.731 | 10/10 |
| `qwen3:4b` | /products/p2 | 2 | 36.831 | 176 | 0.105 | 400 | 36.669 | 9/10 |
| `qwen3:4b` | /articles/a1 | 1 | 36.939 | 139 | 2.66 | 400 | 34.214 | 5/5 |
| `qwen3:4b` | /articles/a1 | 2 | 34.839 | 139 | 0.101 | 400 | 34.685 | 5/5 |
| `gemma3:1b` | /products/p1 | 1 | 6.085 | 186 | 0.106 | 148 | 5.952 | 10/10 |
| `gemma3:1b` | /products/p1 | 2 | 5.338 | 186 | 0.111 | 148 | 5.204 | 10/10 |
| `gemma3:1b` | /products/p2 | 1 | 8.073 | 178 | 1.622 | 149 | 6.421 | 10/10 |
| `gemma3:1b` | /products/p2 | 2 | 6.462 | 178 | 0.17 | 149 | 6.254 | 10/10 |
| `gemma3:1b` | /articles/a1 | 1 | 4.447 | 140 | 1.286 | 91 | 3.136 | 4/5 |
| `gemma3:1b` | /articles/a1 | 2 | 3.834 | 140 | 0.102 | 91 | 3.708 | 4/5 |
| `llama3.2:3b` | /products/p1 | 1 | 7.018 | 188 | 0.084 | 103 | 6.909 | 10/10 |
| `llama3.2:3b` | /products/p1 | 2 | 7.157 | 188 | 0.087 | 103 | 7.051 | 10/10 |
| `llama3.2:3b` | /products/p2 | 1 | 8.748 | 181 | 2.298 | 96 | 6.416 | 10/10 |
| `llama3.2:3b` | /products/p2 | 2 | 6.745 | 181 | 0.087 | 96 | 6.641 | 10/10 |
| `llama3.2:3b` | /articles/a1 | 1 | 6.396 | 150 | 1.954 | 68 | 4.401 | 5/5 |
| `llama3.2:3b` | /articles/a1 | 2 | 4.714 | 150 | 0.088 | 68 | 4.61 | 5/5 |

**Estimated time for scraper (c):** 10 pages × 3 runs × 3 conditions = 90 page calls.

- `qwen3:4b`: about 55.0 minutes.
- `gemma3:1b`: about 8.6 minutes.
- `llama3.2:3b`: about 10.2 minutes.

The timing prompt is a fixed, generic request used only to compare speed; scraper (c)'s own prompt is written separately. "Values found" counts real values that appear anywhere in the reply: a rough quality signal, not a score. Raw replies are in `replies/`.
