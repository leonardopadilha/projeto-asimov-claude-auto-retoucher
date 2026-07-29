from transformers import AutoModelForCausalLM
from PIL import Image
from PIL import ImageDraw
import torch

# Load the model
model = AutoModelForCausalLM.from_pretrained(
    "moondream/moondream3-preview",
    trust_remote_code=True,
    dtype=torch.bfloat16,
    device_map="cuda"
)
model.compile()

image = Image.open("./images/img1.jpeg")

result = model.query(
    image=image,
    question="What's in this image?"
)

# Point
result = model.point(image, "left eye")

draw = ImageDraw.Draw(image)
width, height = image.size
x = int[result['points'][0]['x'] * width]
y = int[result['points'][0]['y'] * height]
draw.ellipse((x-5, y-5, x+5, y+5), fill="red")
image.show()



