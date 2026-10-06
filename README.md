# Writing Assistant

A small FastAPI service that wraps the stages of drafting a document as separate
endpoints around an OpenAI model. The output of one stage is the input of the next: a
premise becomes a synopsis, the synopsis becomes an outline with a target word count per
section, and the outline is written out one section at a time.

| Endpoint | What it does | Returns |
|---|---|---|
| `POST /generate_synopsis` | Turn a premise (genre, audience, characters, conflict, themes) into a synopsis | the synopsis, as a JSON string |
| `POST /synopsis_to_outline` | Expand a synopsis into an outline with per-section target word counts | `{sections: [{header, target_word_count, content}], metadata: {title}}` |
| `POST /outline_to_document` | Write the document section by section from an outline, given what has been written so far | a list of `{header, content}` sections: any `previous_content` passed in, then the new ones |
| `POST /autocomplete` | Continue partial text at sentence, paragraph or document level | the completion, as a JSON string |
| `POST /edit_text` | Rewrite one passage in the context of the text around it | the rewritten passage, as a JSON string |

Every model call passes a Pydantic model as the response format, so the answer comes back
as JSON in a known shape, and the endpoint returns the field or object it needs from it.
`/outline_to_document` makes one call per outline section and gives each call the
sections written so far.

Every request takes a `creativity_level` (0–1, default 0.7), which is used as the sampling
temperature. `/generate_synopsis`, `/autocomplete` and `/edit_text` also send `tone`,
`writing_style` and `writing_level` to the model.

## Run

Python 3.9 or later.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key" > .env
uvicorn app.main:app --reload
```

Interactive docs are at http://127.0.0.1:8000/docs.

The app reads `OPENAI_API_KEY` from the environment or from `.env` and raises at import
if it is missing, so the server does not start without it. Any non-empty value is enough
to load the app and browse the docs; requests need a real key.

An example request:

```bash
curl -s http://127.0.0.1:8000/synopsis_to_outline \
  -H "Content-Type: application/json" \
  -d '{"document_type": "short story", "document_length_in_pages": 4,
       "synopsis": "A night-shift nurse searches for a patient who vanished from a locked ward."}'
```

## Status

A prototype from January 2025.

- There are no automated tests.
- The model (`gpt-4o-mini`) is set in `app/utils.py`.
- `tone`, `writing_style` and `writing_level` are not applied everywhere:
  `/outline_to_document` accepts them but does not send them to the model, and
  `/synopsis_to_outline` does not take them.
- `/edit_text` does not check the range of `creativity_level`; the other endpoints
  return 400 for values outside 0–1.
- The handlers are `async` but call the OpenAI client synchronously, so a worker serves
  one model call at a time.

## Layout

```
app/main.py         FastAPI app and router registration
app/endpoints/      one module per endpoint
app/models.py       request models
app/enums.py        tone, style, reading level, granularity options
app/utils.py        prompt assembly and the OpenAI call
```
