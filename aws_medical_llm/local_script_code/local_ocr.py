import easyocr
import torch

def extract_text_easyocr(image_path):
    """
    Extract text from an image using EasyOCR with automatic GPU detection.
    
    Args:
        image_path (str): Path to the image file.
        
    Returns:
        str: Extracted text from the image.
    """
    use_gpu = torch.cuda.is_available()
    reader = easyocr.Reader(['en', 'hi'], gpu=use_gpu)
    
    results = reader.readtext(image_path, detail=0)
    extracted_text = "\n".join(results)
    return extracted_text

if __name__ == "__main__":
    image_path = r"C:/Users/prana/OneDrive - University of Maryland/Desktop/Internship and Part time/Hackathon/aws_medical_llm/Doctor-Note-Template-V02.jpg"
    text = extract_text_easyocr(image_path)
    print("Extracted Text:\n", text)
