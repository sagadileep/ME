# ME - AI connection
# One function for the whole project: ask_ai(prompt) returns the AI's answer.
# To switch AI provider or model, change only PROVIDER and MODEL below.

from dotenv import load_dotenv
from google import genai

load_dotenv()

PROVIDER = "gemini"
MODEL = "gemini-3.6-flash"
THINKING = "low"   # how long the model "thinks" before answering; lower = faster (default is high)

_gemini_client = genai.Client()


def ask_ai(prompt):
    if PROVIDER == "gemini":
        try:
            interaction = _gemini_client.interactions.create(
                model=MODEL, input=prompt, generation_config={"thinking_level": THINKING}
            )
        except Exception:
            # Some models do not accept this setting: ask again with the default.
            interaction = _gemini_client.interactions.create(model=MODEL, input=prompt)
        return interaction.output_text
    else:
        raise ValueError(f"Unknown AI provider: {PROVIDER}")
