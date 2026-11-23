# Dataset Audit — Filipino Gen Z Kupal Chatbot Fine-Tuning Overhaul

Working directory: `/home/arjay/Downloads/trainFT/newData`
Originals (untouched): `trainC10.jsonl` (1,000 convos), `validation.jsonl` (100 convos)
Deliverables: `train_v2.jsonl`, `validation_v2.jsonl`, `system_prompt.txt`, this file.

---

## 1. Initial dataset analysis (original files)

### 1.1 Structure (both files clean)
- Every line valid JSON; single shared system prompt (identical in all 1,100 records); roles strictly alternate `system → user → assistant → …`; every conversation ends with an `assistant` message; no empty messages; no extra keys; no exact duplicate user-sequences.
- Conversation lengths (messages per convo): train `{3:200, 5:199, 7:252, 9:284, 11:59, 13:6}`; validation `{3:4, 5:38, 7:50, 9:8}`.

### 1.2 Identified weaknesses
| # | Weakness | Evidence |
|---|---|---|
| 1 | Templated/sycophantic openers | "naiintendihan ko" 195/2821 assistant msgs (6.9%), "salamat sa" 62, "posible, pero/kaya" 66, "ay naku" 46, "magandang plano/hakbang/simula/desisyon" ~60 |
| 2 | Mechanical laughter tic | HAHA-type laughter in 76.5% of train assistant msgs (92.4% in validation) |
| 3 | Question-ending overuse | 37.7% of assistant msgs end with "?" |
| 4 | Language monotony | ~85% heavy-Filipino, ~12% Taglish, ~2% light, ~0.3% English-dominant — almost no real code-switch variety; user msgs very short (median 43 chars) |
| 5 | Kupal energy underpowered | profanity: gaga 49, puta 3, tanga 1 / 2,821 msgs; Gen Z slang (gagi, luh, awit, naur, delulu, kaloka…) almost absent |
| 6 | Length skew | median 122 chars; 64% in 60–150 bucket; only 4 msgs >700 chars; few one-liners (120). Validation median 190 ≠ train 122 (inconsistent) |
| 7 | Topic gaps | per 1,000 train convos: gaming 7, online shopping 13, social media 39, commute 54, school 65; weather 320 (overrepresented) |
| 8 | AI self-reference | one "as an AI" joke (train line 354) |
| 9 | Personality not default-ON in evidence | responses often mirror user tone instead of carrying an 8/10 baseline |

Strengths kept: valid structure, decent scenario variety, some genuinely funny multi-turn banter, correct system-prompt intent.

---

## 2. Workstream contributions (parallel agents)

| Agent | Role | Output |
|---|---|---|
| `architect` | Personality Architect | `system_prompt.txt` (canonical prompt, 263 words), `_spec/persona_spec.md` (voice/language/diversity rules + 8 positive & 8 negative examples), `_spec/gen_rules.md` (JSONL output contract, counts, anti-repetition rules) |
| `gen_casual` | Chaotic casual conversations | 200 convos (180 train / 20 val); 20/20 dead-neutral openers ("hi", "wala lang", "i'm bored"…) answered at 8/10 personality |
| `gen_kupal` | Kupal humor & banter | 200 (180/20); roasting, comebacks, mock outrage, competitive banter; roast-the-situation boundary held |
| `gen_everyday` | Filipino everyday life | 150 (135/15); school, family, commute, food, sari-sari, budget, Shopee/Lazada, load/data, payday, fiestas, brownouts |
| `gen_internet` | Gen Z internet culture | 150 (135/15); MLBB/Valorant/Genshin, TikTok/IG/X, memes, GC drama, slang (capped) |
| `gen_knowledge` | Knowledgeable but chaotic | 150 (135/15); 16 deadpan factual questions still answered with full personality + accuracy (recursion, binary search, photosynthesis, capitals…) |
| `gen_emotional` | Emotional & social | 100 (90/10); ~9 serious/crisis convos handled calmly with NCMH hotline 1553 etc. |
| `gen_hypo` | Hypotheticals, games, creative | 50 (45/5); WYR, debates, tier lists, story games |
| `rw_train_00..04` | Rewrite existing train (200 each) | user messages verbatim (0 mismatches), assistant msgs re-personalized, canonical system prompt applied |
| `rw_val` | Rewrite existing validation (100) | same; kept separate from train |
| `qa_new` | QA — 1,000 new convos | 260 assistant msgs rewritten in 253 convos (slang de-cap: teh 12.46%→2.36%, beh 11.20%→2.36%, grabe 5.89%→2.36%; 1 opener fix); 0 drops; report `qa_report_new.md` |
| `qa_rewrite` | QA — 1,100 rewritten convos | 18 msgs fixed in 16 convos (9 banned "salamat sa pagsabi"→0; 6 opener-collision groups→0); source fidelity 0 mismatches; val/train overlap 0; report `qa_report_rewrite.md` |

## 3. Canonical system prompt

`system_prompt.txt` — 263 words. Core principles: Filipino Gen Z GC friend, personality always ON (~8/10 baseline even for a plain "hello"); dramatic/playful/sarcastic/cheeky voice with natural casual profanity; kupal-but-never-abusive (roast situations, never vulnerable people; zero slurs/harassment/threats); natural Taglish with all mix ratios allowed; slang never forced; factual accuracy on practical/academic/technical questions; serious/safety topics → drop jokes, calm empathy + real-world resources; never claims to be human; never generic-assistant lines or sycophantic praise. The **same prompt is byte-identical in every one of the 2,100 output records** (verified programmatically).

## 4. Final dataset statistics

| File | Conversations | Composition | Assistant msgs |
|---|---:|---|---:|
| `train_v2.jsonl` | **1,900** | 1,000 rewritten original + 900 new | 3,886 |
| `validation_v2.jsonl` | **200** | 100 rewritten original + 100 new (zero overlap with train) | 385 |

### 4.1 Category distribution (new 1,000)
| Category | Train | Val | Total |
|---|---:|---:|---:|
| Casual / small talk | 180 | 20 | 200 |
| Kupal humor & banter | 180 | 20 | 200 |
| Filipino everyday life | 135 | 15 | 150 |
| Gen Z internet culture | 135 | 15 | 150 |
| Knowledge / academic / technical | 135 | 15 | 150 |
| Emotional & social | 90 | 10 | 100 |
| Hypotheticals / games / creative | 45 | 5 | 50 |
| **Total** | **900** | **100** | **1,000** |

### 4.2 Language & style distribution (train_v2, 3,886 assistant msgs)
- Language mix (Filipino-marker ratio): Taglish 51.0%, light Taglish 24.2%, heavy Filipino 16.9%, mostly-English 7.9% — vs. old ~85% heavy-Filipino only.
- Response length: min 15 / median 117 / mean 134 / max 531 chars; buckets `<60: 269, 60–150: 2,419, 150–350: 1,080, 350–700: 118, >700: 0` — one-liners through long explanations all present (old: 64% in one bucket, only 4 msgs >700).
- Conversation length: `{3:950, 5:339, 7:257, 9:289, 11:59, 13:6}` messages — single-turn through 6 exchanges.
- HAHA-type laughter ≈ 6–23% (old 76.5%; QA-measured 23.0% new / 21.4% rewritten, target <40%).
- Question-endings 14.5% (old 37.7%).
- Emoji in 37.1% of msgs; top slang: beh 2.8%, eme 2.6%, amp 2.4%, grabe 2.3%, teh 1.1% — all ≤3% cap; gagi/puta/tanga/hayop/ulol present in kupal contexts only, no slurs or targeted harassment.
- Banned/robotic phrases ("as an ai", "how can i help", "magandang tanong/plano/hakbang", "naiintendihan ko", "posible, pero", "salamat sa pagsabi", …): **0 hits** (old: openers like "naiintendihan ko" at 6.9% + 1 "as an AI").
- Opener collisions (>1 use of same first-3-words) across 3,886 msgs: 90, max frequency 4 — natural phrases, no template openers.

### 4.3 Duplicate & overlap analysis
- Exact duplicate conversations within train_v2: **0**; near-dupes (same first user+assistant pair or Jaccard > 0.85): **0**.
- Train/validation overlap: **0** at every level — exact conversation hashes, user-sequence hashes, individual message texts, first user+assistant pairs, and Jaccard ≥ 0.6 near-dupes. (One 30-char user line, "nag-aalala ako sa exam bukas", had coincidentally been generated into both a new train convo and a new val convo — full conversations differed, but the colliding val convo was replaced with a fresh one and the check re-run: fully clean.)
- Rewritten validation never copied into training; validation user-sequences originating from old `trainC10.jsonl`: **0**.

### 4.4 Validation results (automated, run on the final files from disk)
- Every line re-parsed with Python `json.loads`: **2,100/2,100 valid**.
- Every record: only `messages` key; first role `system` with content byte-identical to `system_prompt.txt`; strict user/assistant alternation after system; ends with `assistant`; no empty content; only `role`/`content` inside messages.
- Files written with `json.dumps(ensure_ascii=False)`, one object per line, UTF-8, no markdown fences/comments/blank lines.
- Original files `trainC10.jsonl` / `validation.jsonl` **unmodified**.

### 4.5 Personality check (neutral prompts)
Sampled neutral/boring first messages from the final files — "hi", "hello", "good morning", "good evening", "wala lang", "kamusta", "What is photosynthesis?", "Explain binary search.", "hindi ko gets 'yung lesson" — **every sampled assistant reply shows the expressive Filipino Gen Z personality** (e.g. `"hi" → "helloooo beh!! bakit parang ang lungkot ng chat na 'to, spill mo na kung ano meron"`; `"What is photosynthesis?" → "Deadpan pa eh HAHA sige. Photosynthesis = …"`). QA agents independently confirmed 30/30 neutral-first convos (new) and 30/30 (rewritten) pass the personality test without the user initiating a joking tone.

### 4.6 Accuracy & safety spot-checks
- 20 knowledge/technical answers per QA stream verified factually correct (binary search, quadratic formula, DNS, PH OT pay, 13th-month pay, git, Big O, physics constants…); hedged disclaimers kept where appropriate.
- 21 (new) + 49 (rewritten) serious/crisis/safety convos reviewed: jokes absent/minimal, empathy present, real-world resources included (NCMH Crisis Hotline 1553, 911, DOLE/CSC, barangay VAW desk, school counselor, licensed professionals).
- Multi-turn continuity: 15/15 sampled per stream — each assistant turn follows from previous turns.

---

## 5. How to use
- Fine-tune with `train_v2.jsonl`; evaluate with `validation_v2.jsonl`.
- At inference, prepend the exact contents of `system_prompt.txt` as the `system` message of every conversation — identical to training.
