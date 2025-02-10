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
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file {image_path} was not found.")
    except Exception as e:
        raise RuntimeError(f"Error encoding image: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract total price and date from a restaurant bill image."
    )
    parser.add_argument("image_path", help="Path to the image to be processed.")
    return parser.parse_args()


def get_api_key():
    """Retrieve the API key from environment variables."""
    try:
        return os.environ["MISTRAL_API_KEY"]
    except KeyError:
        raise KeyError("Error: MISTRAL_API_KEY environment variable not set.")


def build_messages(base64_image):
    """Construct the messages for the Mistral chat request."""
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
                    ),
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "From this restaurant bill, extract the total price and date. "
                        "For the price, use XXX.XX format, and for the date use the DD-MM-YYYY format."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        },
    ]
    return messages


def extract_filename_from_date(parsed_data):
    """
    Extract the date from parsed JSON data and generate a JSON filename.
    Expected date format in parsed_data: DD-MM-YYYY.
    """
    date_str = parsed_data.get("date", "")
    match = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", date_str)
    if match:
        day, month, year = match.groups()
        return f"lunch_receipt_{month}_{day}_{year}.json"
    else:
        print("Date format not recognized. Using a fallback filename.")
        return "lunch_receipt_unknown_date.json"


def save_json_data(parsed_data, filename):
    """Save the parsed JSON data to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2)
        print(f"JSON saved to {filename}")
    except Exception as e:
        raise RuntimeError(f"Error saving JSON to {filename}: {e}")


def rename_image_file(original_image_path, json_filename):
    """
    Rename the original image file to match the JSON filename
    (keeping the original file extension).
    """
    base_dir = os.path.dirname(original_image_path)
    original_ext = os.path.splitext(original_image_path)[1]
    image_basename = os.path.splitext(json_filename)[0]
    new_image_name = image_basename + original_ext
    new_image_path = os.path.join(base_dir, new_image_name)
    try:
        os.rename(original_image_path, new_image_path)
        print(f"Image renamed to {new_image_path}")
    except Exception as e:
        raise RuntimeError(f"Error renaming image file: {e}")


def process_chat_response(chat_response, original_image_path):
    """Process the Mistral chat response: parse, save JSON, and rename image."""
    response_content = chat_response.choices[0].message.content.strip()
    print("Raw response content:\n", response_content)

    try:
        parsed_data = json.loads(response_content)
    except json.JSONDecodeError:
        raise ValueError("Error: The response is not valid JSON.")

    json_filename = extract_filename_from_date(parsed_data)
    save_json_data(parsed_data, json_filename)
    rename_image_file(original_image_path, json_filename)


def main():
    args = parse_arguments()
    image_path = args.image_path

    if not os.path.exists(image_path):
        print(f"Error: The file {image_path} was not found.")
        return

    # Encode the image to base64.
    try:
        base64_image = encode_image(image_path)
    except Exception as e:
        print(e)
        return

    # Retrieve API key.
    try:
        api_key = get_api_key()
    except KeyError as e:
        print(e)
        return

    # Initialize the Mistral client.
    client = Mistral(api_key=api_key)

    # Build the messages for the chat.
    messages = build_messages(base64_image)

    # Send the request to the Mistral model.
    try:
        chat_response = client.chat.complete(
            model="pixtral-12b-2409",  # free model; alternatively use 'pixtral-large-latest'
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
        )
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return

    # Process the response (parse JSON, save JSON file, and rename image).
    try:
        process_chat_response(chat_response, image_path)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
