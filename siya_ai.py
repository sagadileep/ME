# Siya - her AI connection (the public study app keeps using ai.py)
# With ANTHROPIC_API_KEY in the secrets, Siya uses Claude: Sonnet for her replies (warm, careful writing)
# and Haiku for quick background jobs (picking verses, updating notes). Without it, she uses Gemini.
# Replies are streamed: the words appear while she is still writing.
# If Claude fails (key expired, no credit, outage), Siya quietly falls back to Gemini.

import os

from dotenv import load_dotenv

load_dotenv()

REPLY_MODEL = "claude-sonnet-5-5"   # change to "claude-haiku-5-5" for the cheapest Siya
FAST_MODEL = "claude-haiku-5-5"
GEMINI_MODEL = "gemini-3.6-flash"
MAX_TOKENS = 700

_claude = None
_gemini = None


def using_claude():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def claude():
    global _claude
    if _claude is None:
        import anthropic
        _claude = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY itself
    return _claude


def gemini():
    global _gemini
    if _gemini is None:
        from google import genai
        _gemini = genai.Client()                 # reads GEMINI_API_KEY itself
    return _gemini


def ask_fast(prompt):
    # A quick background answer, all at once.
    if using_claude():
        try:
            message = claude().messages.create(model=FAST_MODEL, max_tokens=MAX_TOKENS,
                                               messages=[{"role": "user", "content": prompt}])
            return "".join(block.text for block in message.content if block.type == "text")
        except Exception as error:
            print(f"Claude failed, using Gemini: {type(error).__name__}", flush=True)
    return gemini().models.generate_content(model=GEMINI_MODEL, contents=prompt).text


def stream_reply(prompt):
    # Siya's reply, piece by piece, so it can appear on screen while she writes.
    started = False
    if using_claude():
        try:
            with claude().messages.stream(model=REPLY_MODEL, max_tokens=MAX_TOKENS,
                                          messages=[{"role": "user", "content": prompt}]) as stream:
                for text in stream.text_stream:
                    started = True
                    yield text
            return
        except Exception as error:
            print(f"Claude failed, using Gemini: {type(error).__name__}", flush=True)
            if started:
                return            # half a reply is already on screen; don't add a second one
    for chunk in gemini().models.generate_content_stream(model=GEMINI_MODEL, contents=prompt):
        if chunk.text:
            yield chunk.text
