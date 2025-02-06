## Escoba Bench

Simple LLM benchmark by playing the card game [Escoba](https://en.wikipedia.org/wiki/Escoba).

It's not a particularly difficult game, it mostly tests for basic arithmetic right now.
At the moment the only cheap model that can consistently win is Gemini 2.0 Flash.

## TODO

- Improve web functionality
- Add -n to for number of games
- Add moregame rules (4 of same number is discard, final counting real, 7 velo...)
- Add more card games / teams
- better game logs, human readable

### Usage

Place your OpenRouter API key in a .env file.

```
OPENROUTER_API_KEY=sk-or-v1-...
DEFAULT_MODEL=google/gemini-2.0-flash-001 
```

Install the requirements:

```bash
pip install -r requirements.txt
```

Run a game in CLI:

```bash
python3 cli.py
```

Run a game in the web app:

```bash
python3 app.py
```
