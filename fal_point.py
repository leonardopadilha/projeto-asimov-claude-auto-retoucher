import os
import fal_client
from dotenv import load_dotenv
from PIL import Image, ImageDraw

load_dotenv()  # le a FAL_KEY do .env

image_path = "./images/img1.jpeg"

def main(image_path: str, query: str) -> dict:
    # Sobe a imagem local e obtem uma URL publica temporaria
    image_url = fal_client.upload_file(image_path)

    result = fal_client.subscribe(
        "fal-ai/moondream3-preview/point",
        arguments={
            "image_url": image_url,
            "prompt": query,
        },
    )

    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    width, height = image.size

    for point in result["points"]:
        x = point["x"] * width
        y = point["y"] * height
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="red")

    image.show()

    save_image(image, "output.jpg")

    return result

def save_image(image: Image, out_name: str):
    out_name = f"output_{os.path.basename(image_path)}"
    image.save(out_name)

if __name__ == "__main__":
    main("./images/img1.jpeg", "left foot")


