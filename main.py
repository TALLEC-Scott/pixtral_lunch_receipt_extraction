#!/usr/bin/env python3

import argparse
import base64
import json
import os
import re
from mistralai import Mistral


def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # General exception handling
        print(f"Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Extract total price and date from a restaurant bill image.")
    parser.add_argument("image_path", help="Path to the image to be processed.")
    args = parser.parse_args()

    image_path = args.image_path
    if not os.path.exists(image_path):
        print(f"Error: The file {image_path} was not found.")
        return

    # Encode the image to base64
    base64_image = encode_image(image_path)
    if not base64_image:
        print("Image encoding failed; exiting.")
        return

    # Retrieve the API key from environment variables, need to set the API key ofc
    api_key = os.environ["MISTRAL_API_KEY"]
    # Initialize the Mistral client
    client = Mistral(api_key=api_key)

    # Define the messages for the chat
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Extract the text elements described by the user from the picture, "
                        "and return the result formatted as JSON in the following format: "
                        "{ 'total_price': 'XXX.XX', 'date': 'DD-MM-YYYY' }"
                    )
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "From this restaurant bill, extract the total price and date. "
                        "For the price, use XXX.XX format, and for the date use the DD-MM-YYYY format."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]

    # Send request to Mistral model
    chat_response = client.chat.complete(
        model="pixtral-12b-2409",
        messages=messages,
        response_format={
            "type": "json_object",
        }
    )

    # The Mistral API should return a JSON string in chat_response.choices[0].message.content
    response_content = chat_response.choices[0].message.content.strip()
    print("Raw response content:\n", response_content)

    # Attempt to parse the JSON from the response
    try:
        parsed_data = json.loads(response_content)
        # e.g. {"total_price": "5.08", "date": "23-04-2012"}

        # Get the date from the JSON (expected format: DD-MM-YYYY)
        date_str = parsed_data.get("date", "")
        # Regex to capture day, month, and year from the format DD-MM-YYYY
        match = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", date_str)
        if match:
            day, month, year = match.groups()
            # Build the filename in the format lunch_receipt_{month}_{day}_{year}.json
            filename = f"lunch_receipt_{month}_{day}_{year}.json"
        else:
            print("Date format not recognized. Using a fallback filename.")
            filename = "lunch_receipt_unknown_date.json"

        # Write the JSON to a file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2)

        print(f"JSON saved to {filename}")

        # Now rename the image to match our JSON filename (but keep extension)
        base_dir = os.path.dirname(image_path)  # Directory of the original image
        original_ext = os.path.splitext(image_path)[1]  # The file extension (e.g., .jpg or .png)

        # Construct a new image filename with the same base name (minus .json) plus original extension
        image_basename_no_ext = os.path.splitext(filename)[0]  # e.g. lunch_receipt_04_23_2012
        new_image_name = image_basename_no_ext + original_ext  # e.g. lunch_receipt_04_23_2012.jpg
        new_image_path = os.path.join(base_dir, new_image_name)

        # Perform the rename
        os.rename(image_path, new_image_path)

        print(f"Image renamed to {new_image_path}")

    except json.JSONDecodeError:
        print("Error: The response is not valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
