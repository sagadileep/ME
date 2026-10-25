# ME - first Gemini test
# Checks that the API key and library work.

from dotenv import load_dotenv
from google import genai

load_dotenv()                       # reads GEMINI_API_KEY from the .env file
client = genai.Client()             # connects to Gemini using that key

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input="In two sentences, explain what the Big Five personality traits are.",
)
print(interaction.output_text)