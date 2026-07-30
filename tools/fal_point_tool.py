import os
import json
import fal_client
from PIL import Image, ImageDraw
from agno.tools import Toolkit

class FalPointTool(Toolkit):
    def __init__(self):
        super().__init__(name="fal_point_tool")
        self.register(self.find_points_in_image)

    def find_points_in_image(self, image_path: str, prompt: str) -> str:
        """
        Detects specific elements in an image using Fal AI (moondream3-preview/point) and returns their coordinates.
        It also saves a debug image with the points marked.

        Args:
            image_path (str): The local path to the image file.
            prompt (str): The description of the element to find (e.g., "eyes", "blemishes", "lips").

        Returns:
            str: A JSON string containing the list of detected points with 'x' and 'y' coordinates.
        """
        if not os.path.exists(image_path):
            return json.dumps({"error": f"Image file not found at {image_path}"})

        try:
            # Upload image to Fal AI
            image_url = fal_client.upload_file(image_path)
            
            # Submit request to the model
            handler = fal_client.submit(
                "fal-ai/moondream3-preview/point",
                arguments={
                    "image_url": image_url,
                    "prompt": prompt
                },
            )
            
            # Get result
            result = handler.get()
            
            if "points" in result:
                points = result["points"]
                
                # Draw points on a debug image
                try:
                    with Image.open(image_path) as img:
                        img = img.convert("RGB")
                        draw = ImageDraw.Draw(img)
                        width, height = img.size
                        
                        for point in points:
                            x = point['x'] * width
                            y = point['y'] * height
                            draw.ellipse([(x-5, y-5), (x+5, y+5)], fill="red", outline="white")
                        
                        # Save debug image
                        filename = os.path.basename(image_path)
                        debug_path = os.path.join(os.path.dirname(image_path), f"debug_{prompt.replace(' ', '_')}_{filename}")
                        # img.save(debug_path)
                except Exception as e:
                    print(f"Error creating debug image: {e}")

                return json.dumps(points)
            else:
                return json.dumps({"error": "No points found", "raw_result": result})

        except Exception as e:
            return json.dumps({"error": str(e)})



if __name__ == "__main__":
    fal = FalPointTool()
    fal.find_points_in_image("img2.jpeg", "left eye")