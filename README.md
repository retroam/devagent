# /dev/color FAQ Agent

A command-line retrieval augmented generation (RAG) agent that answers questions about /dev/color using a FAQ knowledge base, with optional fallback to web search.

## Architecture

![System diagram](system_diagram.png)

**Components:**
- *agent* — LLM (Claude Opus 4.7 via OpenRouter by default) with function calling
- *search_faq* — semantic similarity search via `sentence-transformers` embeddings (`all-MiniLM-L6-v2`)
- *web_search* — DuckDuckGo fallback for questions outside FAQ scope

**Project layout:**
```
devcolor-agent/
├── agent.py            # CLI loop, agent definition, tool wiring
├── index.py            # FAQ parser + semantic index
├── models.py           # Pydantic models (FAQEntry, SearchResult, ...)
├── tools.py            # Web search helper
├── data/
│   └── devcolorfaq.txt # FAQ corpus (one Q/A per entry)
├── requirements.txt
├── pyproject.toml      # uv / build config
└── .env.example
```

## Setup

Requires Python ≥ 3.10.

1. Install [uv](https://docs.astral.sh/uv/) if you haven't:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. From the project root, install dependencies:
   ```bash
   uv sync
   ```
3. Copy `.env.example` to `.env` and provide your OpenRouter key:
   ```bash
   cp .env.example .env
   # then edit .env and set OPENROUTER_API_KEY=...
   ```
   An OpenRouter API key is required. You may optionally override `MODEL`
   in `.env` to select a different model available on OpenRouter.
4. Run the agent:
   ```bash
   uv run agent.py
   uv run agent.py --verbose   # also show tool-call trace
   ```
   Type `exit` (or `quit`) to leave the chat.

> **Note:** On first run, `sentence-transformers` downloads the `all-MiniLM-L6-v2` model (~80 MB). Subsequent runs are instant.

## Example output

The agent returns a structured `Answer` object (`answer`, `sources`, `could_answer`).
The `sources` list contains the FAQ entry IDs the model actually used, and is shown in
the panel title so user can see which corpus entries grounded each response.

Example queries and response:

### 1. How can /dev/color help me develop my career?

```
╭────────────────── 💬 Answer  (sources: [1, 3, 6]) ───────────────────╮
│ /dev/color offers several ways to help you develop your career as a  │
│ Black technologist:                                                  │
│                                                                      │
│  • The A* Program (flagship initiative): Designed for Black software │
│    engineers and managers, this program helps you set and achieve    │
│    ambitious career goals through peer support and mentorship.       │
│    You'll join a small, year-round squad to collaborate on career    │
│    development, problem-solving, skill-building, networking, and     │
│    leadership development.                                           │
│  • Mentorship & Community: /dev/color fosters a strong community of  │
│    Black technologists where you can connect with peers, mentors,    │
│    founders, and leaders who can help you navigate career challenges │
│    and advance professionally.                                       │
│  • Professional Development Events: Through partnerships with        │
│    companies like Pinterest, Grammarly, and Concrete Rose Capital —  │
│    and organizations like the Black Product Managers Network,        │
│    ColorStack, and Goodie Nation — /dev/color hosts panels,          │
│    networking events, and professional development sessions that     │
│    connect members directly with industry opportunities.             │
╰──────────────────────────────────────────────────────────────────────╯
```

### 2. How can I contribute to /dev/color?

```
╭─────────────────── 💬 Answer  (sources: [10, 6]) ────────────────────╮
│ There are several ways to contribute to /dev/color's mission of      │
│ empowering Black technologists:                                      │
│                                                                      │
│ As an individual:                                                    │
│  • 💰 Make a financial contribution to help sustain programs and     │
│    resources                                                         │
│  • 🤝 Participate in mentorship programs by sharing your experience  │
│  • 📣 Advocate for diversity in tech within your network/workplace   │
│                                                                      │
│ As a company:                                                        │
│  • 🎤 Sponsor events such as panels, networking nights, and          │
│    professional development sessions                                 │
│  • 💵 Provide funding to support /dev/color's programs and           │
│    operations                                                        │
│  • 🚀 Offer professional development opportunities for Black         │
│    technologists (similar to past collaborations with Pinterest,     │
│    Grammarly, and Concrete Rose Capital)                             │
╰──────────────────────────────────────────────────────────────────────╯
⚠ Conversation history reached 10 messages — clearing context to keep
responses focused.
```

> Note: the agent caps conversation history at 10 messages and resets it
> with the warning above, so each new question starts fresh.

### 3. In which cities is /dev/color located?

```
╭───────────────────── 💬 Answer  (sources: [5]) ──────────────────────╮
│ Based on the /dev/color FAQ, the organization has hosted in-person   │
│ events in several major U.S. cities, including:                      │
│                                                                      │
│  • San Francisco                                                     │
│  • New York                                                          │
│  • Atlanta                                                           │
│  • Seattle                                                           │
│                                                                      │
│ These events were supported by corporate partners like LinkedIn and  │
│ Intuit and serve as hubs where Black technologists can connect,      │
│ learn, and grow.                                                     │
╰──────────────────────────────────────────────────────────────────────╯
```

### Verbose mode

Running with `--verbose` additionally prints a structured `Trace` for each
tool call (tool name, args, FAQ entry IDs returned, similarity scores, and
elapsed time), e.g.:

```
  🔧 search_faq_tool({'query': 'cities /dev/color located', 'top_k': 3})
     → ids=[5] scores=[0.612] (8ms)
```
