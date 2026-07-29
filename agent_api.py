from agno.agent import Agent
from agno.media import Image
from agno.models.google import Gemini
from dotenv import load_dotenv

load_dotenv()

agent = Agent(
    model=Gemini(id="gemini-3-flash-preview"),
    #markdown=True,
)

image_path = "./images/img2.jpeg"
agent.print_response(
    "Tell me about this image.",
    images=[Image(filepath=image_path)],
)