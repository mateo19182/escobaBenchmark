## Escoba Benchmark

Simple LLM benchmark by playing the card game [Escoba](https://en.wikipedia.org/wiki/Escoba).

It's not a particularly difficult game, it mostly tests for basic arithmetic right now.

google/gemini-2.0-flash-001
mistralai/ministral-8b

### Usage

Place your OpenRouter API key in the .env file.


```
OPENROUTER_API_KEY=sk-or-v1-...
DEFAULT_MODEL=google/gemini-2.0-flash-001 
```

Run a game in CLI:

```bash
python3 cli.py
```

Run a game in the web app:

```bash
python3 app.py
```
