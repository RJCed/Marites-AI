# GENERATION OUTPUT CONTRACT — all generation/rewrite agents MUST follow this exactly

Working dir: `/home/arjay/Downloads/trainFT/newData`
Canonical system prompt: `system_prompt.txt` (read it from disk; do not retype it — copy it verbatim into every record's `system` message).
Shared persona spec: `_spec/persona_spec.md`.

---

## 1. EXACT JSONL FORMAT

- One JSON object per line, OpenAI chat format:
  ```json
  {"messages": [{"role": "system", "content": "<CANONICAL PROMPT from system_prompt.txt>"}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
  ```
- First message is ALWAYS `system` with the canonical prompt from `system_prompt.txt`, byte-for-byte identical.
- After `system`, roles strictly alternate `user` → `assistant` → `user` → ...
- **Every conversation MUST end with an `assistant` message.**
- Valid UTF-8. Escape quotes, backslashes, and newlines properly — **build each conversation as a Python dict / JS object and serialize with `json.dumps` / `JSON.stringify` per line. NEVER hand-write JSON.**
- No markdown fences, no comments, no blank lines, no extra keys (only `messages`, and inside messages only `role` + `content`).
- If you have code execution, **re-parse every line with a JSON parser before writing** and assert: valid JSON, first role == system, alternating roles, last role == assistant, no empty content.

## 2. HOW TO WRITE BATCHES

- Write new generated batches to:
  - `/home/arjay/Downloads/trainFT/newData/_work/batches/<name>_train.jsonl`
  - `/home/arjay/Downloads/trainFT/newData/_work/batches/<name>_val.jsonl`
  - (create directories as needed)
- Pattern per batch: build a list of conversation objects in code, serialize each with `json.dumps(conv, ensure_ascii=False)` (or `JSON.stringify`), join with `\n`, write once. Then validate by re-reading and re-parsing every line.

## 3. COUNTS CONTRACT PER CATEGORY (new data = 1000 total: 900 train + 100 val)

| Category            | Total | Train | Val |
|---------------------|-------|-------|-----|
| casual              | 200   | 180   | 20  |
| kupal               | 200   | 180   | 20  |
| everyday            | 150   | 135   | 15  |
| internet            | 150   | 135   | 15  |
| knowledge           | 150   | 135   | 15  |
| emotional           | 100   | 90    | 10  |
| hypotheticals/games | 50    | 45    | 5   |

Split each category's conversations into its `_train.jsonl` / `_val.jsonl` files exactly per the table. Aggregate per-category train files later into the final train set; same for val.

## 4. REWRITE CONTRACT (for rewriting existing trainC10.jsonl / validation.jsonl)

- **Preserve original user messages verbatim** and the conversational intent.
- Rewrite assistant messages to match the persona spec; keep any factual content correct.
- Keep multi-turn continuity (each assistant reply must make sense after the previous turns).
- Replace the old system prompt with the canonical one from `system_prompt.txt`.
- Write rewritten output to `/home/arjay/Downloads/trainFT/newData/_work/rewrite/<name>.jsonl` (e.g. `trainC10_rewritten.jsonl`), same JSONL rules as §1, validated line-by-line.

## 5. ANTI-REPETITION RULES

- No duplicate conversations (hash the user-message sequence; reject dupes).
- No two assistant messages (in a batch) with the same opener (first 2–3 words).
- Cap any single slang term at a small % of messages (e.g. ≤2–3%); scan output for repeated phrases before writing.
- Target diversity metrics to beat the old audit: laughter (HAHA-type) well below 76.5%, question-endings well below 37.7%, a real mix of heavy-Filipino / Taglish / light-Taglish / mostly-English messages, response lengths spread across one-liner → long (not median 122 chars), varied openers, zero "as an AI".

## 6. QUALITY BAR

Every assistant message must pass the test: **"Would a real Filipino Gen Z friend in a group chat actually say this?"** If it sounds like an AI assistant, a customer-service bot, or a motivational poster, rewrite it. Follow `_spec/persona_spec.md` for voice, language, diversity, serious-topic, and factual-accuracy rules.
