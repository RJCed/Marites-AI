"""MARITES — Gradio chat interface (Hugging Face Space entrypoint).

This module only builds the UI and wires it to the inference engine in
``src.inference`` (model loading, LoRA adapter, chat template, generation).

ZeroGPU note: ``import spaces`` MUST happen before torch / transformers are
imported anywhere in the process, so it comes first — before
``src.inference`` (which imports torch) is loaded.
"""

import os

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

import spaces  # noqa: F401 — MUST be imported before torch / transformers (ZeroGPU requirement)

import gradio as gr

from src.inference import SYSTEM_PROMPT, respond

# --- UI ----------------------------------------------------------------------
# Layout order for new/non-expert users: header → chat box → example chips →
# input + send → clear → advanced settings (collapsed accordion at the bottom).
CSS = """
#col-container { max-width: 920px; margin: 0 auto; padding: 0 10px; }
.dark .gradio-container { color: var(--body-text-color); }
.gradio-container, #col-container { overflow-x: hidden; }
.marites-header { text-align: center; padding: 20px 16px; border-radius: 18px; margin-bottom: 14px;
  background: linear-gradient(135deg, #ffb03a 0%, #ff4d8d 50%, #8b5cf6 100%);
  color: #ffffff; box-shadow: 0 8px 28px rgba(255, 77, 141, 0.28); }
.marites-header h1 { margin: 0 0 6px 0; font-size: 2.1rem; letter-spacing: 0.5px; }
.marites-header p { margin: 0; font-size: 0.95rem; opacity: 0.97; overflow-wrap: break-word; }
.marites-header .quota { font-size: 0.78rem; opacity: 0.85; margin-top: 6px; }
.chip { border-radius: 999px !important; white-space: normal !important; height: auto !important; }
#chip-row { flex-wrap: wrap; gap: 8px; }
/* never let chat content overflow horizontally */
#chatbot .message, #chatbot .wrap { overflow-wrap: break-word; max-width: 100%; }
#chatbot pre { overflow-x: auto; max-width: 100%; }
#chatbot code { overflow-wrap: break-word; }
@media (max-width: 640px) {
  .marites-header { padding: 14px 12px; border-radius: 14px; }
  .marites-header h1 { font-size: 1.5rem; }
  .marites-header p { font-size: 0.85rem; }
  .marites-header .quota { font-size: 0.72rem; }
  .chip { font-size: 0.8rem; }
  #input-row { flex-direction: column !important; align-items: stretch !important; gap: 8px; }
  #input-row > * { width: 100% !important; }
  #input-row .gr-button { width: 100% !important; }
  #chatbot { height: 52vh !important; }
}
"""

HEADER = """
<div class="marites-header">
  <h1>💬 MARITES</h1>
  <p>Your chaotic Filipino Gen Z friend — chat in <b>Taglish or English</b>. Powered by
  <b>MARITES-v1</b> (Qwen3-14B + LoRA) running on this Space's own ZeroGPU. No sign-up, no API keys.</p>
  <p class="quota">⏳ Free ZeroGPU time per visitor each day (2 min logged-out · 5 min with a free HF account) — if it runs out, just come back after the daily reset.</p>
</div>
"""

with gr.Blocks() as demo:
    gr.Markdown(HEADER)

    chatbot = gr.Chatbot(
        height=440,
        autoscroll=True,
        elem_id="chatbot",
        placeholder="👋 <b>Hi! Ako si MARITES.</b> Magkwento ka — chika, rant, o tanong, tara!",
    )

    gr.Markdown("✨ **Try one of these:**")
    with gr.Row(elem_id="chip-row"):
        chip1 = gr.Button("💬 Uy, anong ganap?", elem_classes=["chip"], size="sm", variant="secondary")
        chip2 = gr.Button("👯 Huy bess, Meron akong chika!", elem_classes=["chip"], size="sm", variant="secondary")
        chip3 = gr.Button("☀️ Magandang umaga!", elem_classes=["chip"], size="sm", variant="secondary")

    with gr.Row(elem_id="input-row"):
        msg = gr.Textbox(
            show_label=False,
            placeholder="I-type mo dito… Taglish or English, go!",
            lines=1,
            autofocus=True,
            scale=9,
        )
        send = gr.Button("Send ➤", variant="primary", scale=1)

    with gr.Row():
        clear = gr.Button("🗑️ Clear chat", size="sm", variant="secondary")

    with gr.Accordion("⚙️ Advanced settings", open=False):
        system_prompt = gr.Textbox(
            label="System prompt (default: MARITES persona)",
            value=SYSTEM_PROMPT,
            lines=5,
        )
        temperature = gr.Slider(0.0, 1.5, value=0.85, step=0.05, label="Temperature")
        top_p = gr.Slider(0.1, 1.0, value=0.90, step=0.05, label="Top-p")
        repetition_penalty = gr.Slider(0.8, 1.5, value=1.05, step=0.05, label="Repetition penalty")
        max_new_tokens = gr.Slider(32, 1024, value=256, step=32, label="Max new tokens")

    inputs = [msg, chatbot, system_prompt, temperature, top_p, repetition_penalty, max_new_tokens]
    send.click(respond, inputs=inputs, outputs=[chatbot, msg], api_name="respond")
    msg.submit(respond, inputs=inputs, outputs=[chatbot, msg], api_name=False)
    clear.click(lambda: ([], ""), inputs=None, outputs=[chatbot, msg], queue=False, api_name=False)
    for chip, text in [
        (chip1, "Uy, anong ganap?"),
        (chip2, "Huy bess, Meron akong chika!"),
        (chip3, "Magandang umaga!"),
    ]:
        chip.click(lambda t=text: t, inputs=None, outputs=msg, api_name=False)

# Gradio 6: theme/css are passed to launch(), not Blocks(). show_error defaults to
# False, so visitors never see internal stack traces (they stay in the Space logs).
demo.launch(mcp_server=True, theme=gr.themes.Citrus(), css=CSS)
