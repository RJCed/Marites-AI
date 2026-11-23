"""MARITES inference engine.

Owns everything model-related for the chat app:

* base-model loading (Qwen3-14B, NF4 4-bit via bitsandbytes),
* MARITES LoRA adapter loading (peft),
* chat-template formatting (Qwen3 chat template, non-thinking mode),
* response generation (streaming via TextIteratorStreamer).

The Gradio interface lives in the root ``app.py`` and only imports
``SYSTEM_PROMPT`` and the ZeroGPU-decorated ``respond`` handler from here.

ZeroGPU note: ``import spaces`` MUST happen before torch / transformers are
imported anywhere in the process, so it sits at the very top of this module
(and of ``app.py``). Model weights are loaded once at module scope so ZeroGPU
packs and reuses them across requests.
"""

import os

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

import spaces  # noqa: F401 — MUST be imported before torch / transformers (ZeroGPU requirement)
import threading

import gradio as gr
import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
)

# --- Model wiring -----------------------------------------------------------
# Adapter repo: RJCed/MARITES-v1 (public). Its adapter_config.json declares
# base_model_name_or_path = "unsloth/Qwen3-14B-unsloth-bnb-4bit" (verified),
# peft_type=LORA, r=32, lora_alpha=32, task_type=CAUSAL_LM, Qwen3ForCausalLM.
BASE_MODEL = "unsloth/Qwen3-14B-unsloth-bnb-4bit"
ADAPTER = "RJCed/MARITES-v1"

# Canonical MARITES system prompt (default ON; users can edit/override in the UI).
SYSTEM_PROMPT = """You are a Filipino Gen Z friend hanging out in a group chat — not a formal assistant. Your personality is always ON: even a plain "hello" gets a lively, expressive reply at your own high energy (around 8/10 in casual chats), without waiting for the user to joke first.

Voice: dramatic, playful, sarcastic, cheeky. React big to stories and chika, roast your friends playfully (roast the situation, never vulnerable people), exaggerate for comedy, and use casual profanity (gagi, teh, etc.) when it comes naturally. Never use slurs, harassment, threats, or cruelty.

Language: speak natural Taglish — mix Filipino and English the way real Filipinos do online. Sometimes Taglish-heavy, sometimes mostly Filipino, sometimes mostly English with Filipino expressions; all mixes are fine. use some emojis and slang words,  don't end every message with a question. Vary your length: a one-liner, a short reply, or a longer explanation when the topic warrants it.

Helpfulness: on practical, academic, or technical questions, give the correct, clear answer first — but don't forget to add humor around it — but the info must always be factually accurate and useful. You stay the same chaotic friend while doing it.

Serious or safety-sensitive topics (distress, crisis, harm): drop the jokes. Be calm, empathetic, and genuinely supportive — still the same friend, not a customer-service bot.

Never use generic assistant lines ("How can I help you today?", "As an AI...") or sycophantic praise like "magandang tanong/plano/hakbang!". Be honest, warm, and real."""

# Keep only the last N messages of history so prefill stays bounded on long
# chats (old context is dropped; chika quality is unaffected in practice).
MAX_HISTORY_MESSAGES = 10


# --- Model loading (once, at module scope — ZeroGPU packs & reuses it) -------
def load_quantization_config() -> BitsAndBytesConfig:
    """NF4 4-bit quantization config for the base model."""
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )


def load_tokenizer() -> AutoTokenizer:
    """Tokenizer + chat template come from the adapter repo."""
    return AutoTokenizer.from_pretrained(ADAPTER)


def load_base_model(quantization_config: BitsAndBytesConfig) -> AutoModelForCausalLM:
    # bitsandbytes' loader is ZeroGPU-aware, so device_map="cuda" is safe here
    # (for non-bnb loads the rule would be .to("cuda"); never a hardcoded device index).
    return AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map="cuda",
        attn_implementation="sdpa",
    )


def load_adapter(model: AutoModelForCausalLM) -> PeftModel:
    # torch_device="cpu": peft's infer_device() would pick "cuda" (ZeroGPU fakes
    # torch.cuda.is_available() in the main process) and safetensors would try to
    # allocate real CUDA memory. Loading on CPU avoids that; peft then moves the
    # adapter onto the base model's (virtual) device via hijack-safe .to() calls.
    return PeftModel.from_pretrained(model, ADAPTER, torch_device="cpu")


tokenizer = load_tokenizer()
model = load_adapter(load_base_model(load_quantization_config()))
model.eval()

_peft_cfg = model.peft_config["default"]
print(
    f"[MARITES] base={BASE_MODEL} adapter={ADAPTER} "
    f"peft_type={_peft_cfg.peft_type} r={_peft_cfg.r} alpha={_peft_cfg.lora_alpha}"
)


# --- Chat-template formatting -------------------------------------------------
def content_to_text(content) -> str:
    """Gradio 6 Chatbot message content may arrive as a list of content blocks
    ([{"type": "text", "text": "..."}]); the chat template needs plain strings."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
        return "\n".join(p for p in parts if p)
    return str(content)


def build_messages(message, history, system_prompt) -> list[dict[str, str]]:
    """Assemble the full message list (system + bounded history + new user turn)."""
    history = [
        {"role": m.get("role", "user"), "content": content_to_text(m.get("content", ""))}
        for m in (history or [])
    ][-MAX_HISTORY_MESSAGES:]
    prompt = (system_prompt or SYSTEM_PROMPT).strip()
    messages = ([{"role": "system", "content": prompt}] if prompt else []) + history + [
        {"role": "user", "content": message}
    ]
    return messages


def encode_messages(messages: list[dict[str, str]]):
    """Apply the Qwen3 chat template (non-thinking mode) and tokenize."""
    return tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        enable_thinking=False,  # non-thinking mode for ordinary conversation
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
    )


# --- Response generation ------------------------------------------------------
def estimate_duration(message, history, system_prompt, temperature, top_p, repetition_penalty, max_new_tokens, *args, **kwargs):
    """GPU seconds to CAP per request (ZeroGPU charges ~1.5x the actual runtime).

    Qwen3-14B NF4 on an A10G decodes at roughly 15-30 tok/s, so 0.10 s/token is
    a safe ceiling. Most replies stop at EOS long before the cap, so the
    typical charge is far below it — the cap only truncates runaway
    generations, and shorter caps also improve queue priority.
    """
    return min(90, 12 + int(max_new_tokens) * 0.10)


@spaces.GPU(duration=estimate_duration)
def respond(message, history, system_prompt, temperature, top_p, repetition_penalty, max_new_tokens):
    """Chat with MARITES (RJCed/MARITES-v1 LoRA on Qwen3-14B). Streams the reply token by token.

    Yields (updated message history, "") so the chatbot streams and the input clears.
    """
    message = content_to_text(message)
    if not message.strip():
        raise gr.Error("Mag-send ka muna ng message 😄")

    messages = build_messages(message, history, system_prompt)

    enc = encode_messages(messages)
    input_ids = enc["input_ids"].to("cuda")
    attention_mask = enc["attention_mask"].to("cuda") if "attention_mask" in enc else None

    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    gen_kwargs = dict(
        input_ids=input_ids,
        attention_mask=attention_mask,
        streamer=streamer,
        max_new_tokens=int(max_new_tokens),
        do_sample=float(temperature) > 0,
        temperature=max(float(temperature), 1e-5),
        top_p=float(top_p),
        repetition_penalty=float(repetition_penalty),
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )

    err = None

    def _run():
        nonlocal err
        try:
            model.generate(**gen_kwargs)
        except Exception as e:  # surface worker errors instead of hanging the stream
            err = e
        finally:
            streamer.end()

    thread = threading.Thread(target=_run)
    thread.start()

    history = [
        {"role": m.get("role", "user"), "content": content_to_text(m.get("content", ""))}
        for m in (history or [])
    ][-MAX_HISTORY_MESSAGES:]
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})
    for new_text in streamer:
        history[-1]["content"] += new_text
        yield history, ""
    thread.join()
    if err is not None:
        raise err
