# doctors_handwritten_text
import boto3

def extract_text_from_image(image_path, region="us-east-1"):
    # Initialize Textract client
    textract = boto3.client('textract', region_name=region)
    
    # Read the image bytes
    with open(image_path, 'rb') as document:
        image_bytes = document.read()
    
    # Call Textract to detect text
    response = textract.detect_document_text(Document={'Bytes': image_bytes})
    
    # Extract and print detected text
    text = ""
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            text += block['Text'] + '\n'
    return text

if __name__ == "__main__":
    image_file = "doctors_handwritten_text.png"
    extracted_text = extract_text_from_image(image_file)
    print("Extracted Text:\n", extracted_text)
