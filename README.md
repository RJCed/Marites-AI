# 💬 MARITES

<p align="center">
  <a href="https://huggingface.co/spaces/RJCed/MARITES-v1-chat"><img src="https://img.shields.io/badge/💬%20Live%20Demo-HF%20Space-ffb03a?style=for-the-badge" alt="Live demo on Hugging Face Spaces"></a>
  <a href="https://huggingface.co/RJCed/MARITES-v1"><img src="https://img.shields.io/badge/🤗%20Model-RJCed%2FMARITES--v1-blue?style=for-the-badge" alt="MARITES-v1 on Hugging Face"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776ab?style=for-the-badge" alt="Python 3.12"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-green?style=for-the-badge" alt="Apache 2.0 License"></a>
</p>


**MARITES** is a Filipino conversational AI fine-tuned to talk like your funny, expressive friend from the group chat — natural **Taglish**, playful sarcasm, slang, and chika — while still being able to answer everyday, academic, and technical questions.

## ✨ Features

- 🗣️ **Natural Taglish** — Filipino + English mixed the way real Filipinos chat online (English & Filipino)
- 😏 **Gen Z personality** — playful sarcasm, humor, casual banter, Filipino internet slang, and some emojis
- 📚 **Still answers questions correctly** — academic, technical, and everyday topics, with humor woven around it
- 💬 **Conversational** — remembers the chat and replies like a friend, not a bot
- 🪶 **Lightweight** — a small LoRA adapter on top of a big base model (see below)

## 🚀 Demo & Model

| | Link |
|---|---|
| 💬 **Live Chat Demo** (free, runs on ZeroGPU) | https://huggingface.co/spaces/RJCed/MARITES-v1-chat |
| 🤗 **Hugging Face Model** | https://huggingface.co/RJCed/MARITES-v1 |

Try it with a quick "Uy, anong ganap?" — no sign-up needed. 😄

> ⚠️ **MARITES-v1 is a LoRA adapter, not a standalone model.** It contains only the trained adapter weights — you must load it on top of the compatible base model: [`unsloth/Qwen3-14B-unsloth-bnb-4bit`](https://huggingface.co/unsloth/Qwen3-14B-unsloth-bnb-4bit) (Qwen3-14B, 4-bit quantized).
>
> ```python
> import torch
> from peft import PeftModel
> from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
>
> BASE_MODEL = "unsloth/Qwen3-14B-unsloth-bnb-4bit"  # required base model
> ADAPTER = "RJCed/MARITES-v1"                        # the LoRA adapter
>
> tokenizer = AutoTokenizer.from_pretrained(ADAPTER)
> bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
>                          bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
> model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=bnb, device_map="auto")
> model = PeftModel.from_pretrained(model, ADAPTER)
> ```

## 📁 Project Structure

```text
MARITES/
├── app.py                  # Gradio chat app (Hugging Face Space entry point)
├── requirements.txt        # Python dependencies for running the app
├── src/
│   ├── __init__.py
│   └── inference.py        # Model + LoRA loading, chat template, streaming replies
├── data/                   # Chat datasets (JSONL): v2 files = training set; older originals kept for reference
├── prompts/
│   └── system_prompt.txt   # The system prompt that gives MARITES its personality
├── training/
│   ├── initial_config.yaml # LoRA training config (first run)
│   └── continuation_config.yaml  # LoRA training config (continuation run)
├── docs/                   # Dataset audit + generation rules and persona spec
├── LICENSE                 # Apache 2.0
└── README.md
```

## 🏋️ Training

- **Base model:** [`unsloth/Qwen3-14B-unsloth-bnb-4bit`](https://huggingface.co/unsloth/Qwen3-14B-unsloth-bnb-4bit) (Qwen3-14B, 4-bit quantized)
- **Method:** Supervised fine-tuning (SFT) with a **LoRA adapter** (`peft_type: LORA`, r=32, alpha=32, QLoRA-style on the 4-bit base) for conversational text generation
- **Data:** ~2,100 Taglish conversations (1,900 train / 200 validation) — the `train_v2.jsonl` / `validation_v2.jsonl` files in `data/` (the older `trainC10` / `validation` files are kept as untouched originals)
- **License:** Apache-2.0
- **Configs:** see `training/` for the exact hyperparameters used

## ⚠️ Limitations

- MARITES can occasionally be **inaccurate or make things up** — always double-check important facts.
- It works best in **Taglish and English**; in other languages it may not respond as well or stay in character.
- It's a personality-first chatbot, **not a substitute for professional advice** (medical, legal, financial, etc.).
- As a LoRA adapter, its output depends on the **base model, chat template, and system prompt** — load it with the base model above for best results.
- The personality can get very casual (slang, playful teasing, occasional mild profanity) — it's a friend, not a search engine 😄

---

<p align="center"><i>Fine-tuned from Qwen3-14B with LoRA using <a href="https://github.com/unslothai/unsloth">Unsloth</a>.<br>
Developed by <a href="https://huggingface.co/RJCed">RJCed</a>.</i></p>
