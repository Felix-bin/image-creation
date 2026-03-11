#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
#     "pillow>=10.0.0",
#     "python-dotenv>=1.0.0",
#     "requests",
# ]
# ///
"""
Generate images via Paratera API (model selected by env).

Usage:
    uv run generate_image.py --prompt "your image description" --filename "output.png" [--resolution 1K|2K|4K]
"""

import argparse
import base64
import os
import sys
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv

# Resolution mapping
RESOLUTION_MAP = {
    "1K": "1024x1024",
    "2K": "1280x720",
    "4K": "1216x896",
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate images via Paratera API"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Image description/prompt"
    )
    parser.add_argument(
        "--filename", "-f",
        required=True,
        help="Output filename (e.g., sunset-mountains.png)"
    )
    parser.add_argument(
        "--resolution", "-r",
        choices=["1K", "2K", "4K"],
        default="1K",
        help="Output resolution: 1K (default), 2K, or 4K"
    )

    args = parser.parse_args()

    from openai import OpenAI
    from PIL import Image as PILImage

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("IMAGE_MODEL") or "Doubao-Seedream-4.0"

    missing = []
    if not api_key:
        missing.append("OPENAI_API_KEY")
    if not base_url:
        missing.append("OPENAI_BASE_URL")
    if missing:
        missing_list = ", ".join(missing)
        print(
            f"Missing required environment variables: {missing_list}. "
            "Set them in your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialise OpenAI-compatible client
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    # Set up output path
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    size = RESOLUTION_MAP[args.resolution]
    print(f"Generating image with size {size}...")

    try:
        response = client.images.generate(
            model=model,
            prompt=args.prompt,
            size=size,
        )

        # Extract and save image from URL
        image_url = response.data[0].url
        if not image_url:
            print("Error: No image URL found in response.", file=sys.stderr)
            sys.exit(1)

        print(f"Downloading image from: {image_url}")
        import requests
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        image_data = img_response.content

        image = PILImage.open(BytesIO(image_data))
        image.convert("RGB").save(str(output_path), "PNG")
        image_saved = True

        if not image_saved:
            print("Error: No image data found in response.", file=sys.stderr)
            sys.exit(1)

        full_path = output_path.resolve()
        print(f"\nImage saved: {full_path}")
        print(f"MEDIA: {full_path}")

    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
