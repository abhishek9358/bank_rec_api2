import os
import re
import cv2
import numpy as np
from datetime import datetime
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import pdfplumber
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
import google.generativeai as genrate
from google import genai
from google.genai import types
import json

from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
# === Gemini Config ===
genrate.configure(api_key=gemini_api_key)
model = genrate.GenerativeModel("models/gemini-2.5-flash")

def gemini_response(prompt):
    response = model.generate_content(prompt)
    return response.text.strip()


def preprocess_image_for_ocr(image):
    """
    Preprocesses the image before applying OCR.
    """
    open_cv_image = np.array(image)
    
    gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    
    threshold_image = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )

    denoised_image = cv2.fastNlMeansDenoising(threshold_image, None, 30, 7, 21)
    
    processed_image = Image.fromarray(denoised_image)
    
    return processed_image


def extract_text(pdf_path):
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                
                if not text or len(text.strip()) < 300:
                    image = page.to_image(resolution=300).original
                    preprocessed_img = preprocess_image_for_ocr(image)
                    ocr_text = pytesseract.image_to_string(preprocessed_img, config="--oem 3 --psm 6")
                    text_chunks.append((i + 1, ocr_text.strip())) 
                else:
                    text_chunks.append((i + 1, text.strip()))  

            except Exception as e:
                print(f"Error on page {i+1}: {e}")
    
    return text_chunks

def split_into_chunks(pages_text, chunk_size=5):
    chunks = []
    for i in range(0, len(pages_text), chunk_size):
        chunk_pages = pages_text[i:i + chunk_size]
        chunk_text = "\n".join(f"[Page {pgno}]\n{text}" for pgno, text in chunk_pages)
        chunks.append({
            "pages": [pgno for pgno, _ in chunk_pages],
            "text": chunk_text
        })
    return chunks

def find_relevant_pages(chunks, target_date):
    found_pages = set()
    for chunk in chunks:
        prompt = f"""
        Based on the following text chunk, identify the PDF pages relevant to the reconciliation period ending on {target_date.strftime('%B %Y')} (Reconciliation Date: {target_date.strftime('%-m/%-d/%Y')}). 
        Only respond with actual page numbers if they directly reference that date or match the reconciliation period.
        Example response format:
        'Pages relevant to June 2024: 5, 6, 7' or 'No pages found for June 2024.'
        \n\nText:\n{chunk['text']}
        """
        response = gemini_response(prompt)
        current_pages = set(map(int, re.findall(r'\b\d+\b', response)))
        found_pages.update(current_pages)
    return sorted(found_pages)

def remove_annotations_from_pdf(input_pdf, output_pdf):
    original = fitz.open(input_pdf)
    new_doc = fitz.open()
    for page in original:
        annot = page.first_annot
        while annot:
            next_annot = annot.next
            page.delete_annot(annot)
            annot = next_annot
        new_doc.insert_pdf(original, from_page=page.number, to_page=page.number)
    new_doc.save(output_pdf, garbage=4, clean=True)
    new_doc.close()
    original.close()
    print(f"📄 Annotation-free PDF saved: {output_pdf}")
    return output_pdf

def preprocess_and_save_images(pdf_path, page_numbers, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved_images = []
    for pg_num in page_numbers:
        try:
            page = doc[pg_num - 1]
            for annot in page.annots() or []:
                page.delete_annot(annot)
            pix = page.get_pixmap(dpi=400)
            img_path = os.path.join(output_folder, f"page_{pg_num}.jpg")
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            binary = cv2.adaptiveThreshold(
                blurred, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
            cv2.imwrite(img_path, cleaned)
            saved_images.append(img_path)
        except Exception as e:
            print(f"❌ Error processing page {pg_num}: {e}")
    return saved_images

# def save_filtered_pdf(input_pdf_path, output_dir, page_numbers):
#     print("📦 Saving filtered PDF...")
#     reader = PdfReader(input_pdf_path)
#     writer = PdfWriter()
#     for page_number in page_numbers:
#         try:
#             writer.add_page(reader.pages[page_number - 1])
#         except IndexError:
#             print(f"⚠️ Skipping invalid page: {page_number}")
#     os.makedirs(output_dir, exist_ok=True)
#     input_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]
#     output_path = os.path.join(output_dir, f"{input_filename}_filtered.pdf")
#     with open(output_path, "wb") as f:
#         writer.write(f)
#     print(f"🎉 Filtered PDF saved: {output_path}")
    
#     return output_path

def save_filtered_pdf(input_pdf_path, output_dir, page_numbers):
    import os
    from PyPDF2 import PdfReader, PdfWriter
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance
    import tempfile

    print("📦 Saving filtered PDF...")

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    valid_page_numbers = []

    for page_number in page_numbers:
        if 1 <= page_number <= len(reader.pages):
            writer.add_page(reader.pages[page_number - 1])
            valid_page_numbers.append(page_number)
        else:
            print(f"⚠️ Skipping invalid page: {page_number}")

    if not valid_page_numbers:
        print("❌ No valid pages to extract. Aborting.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    input_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]
    filtered_pdf_path = os.path.join(output_dir, f"{input_filename}_filtered.pdf")

    with open(filtered_pdf_path, "wb") as f:
        writer.write(f)

    print(f"✅ Filtered PDF saved: {filtered_pdf_path}")

    # Step 2: Enhance the filtered PDF
    print("🎨 Enhancing PDF...")

    try:
        images = convert_from_path(filtered_pdf_path, dpi=300)
        if not images:
            raise ValueError("Filtered PDF has no pages")

        enhanced_images = []
        ct = 0
        for img in images:

            img = ImageEnhance.Sharpness(img).enhance(2.0)
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Brightness(img).enhance(1.2)
            enhanced_images.append(img.convert("RGB"))
            ct += 1

        enhanced_pdf_path = os.path.join(output_dir, f"{input_filename}_enhanced.pdf")
        enhanced_images[0].save(enhanced_pdf_path, save_all=True, append_images=enhanced_images[1:])

        print(f"🎉 Enhanced PDF saved: {enhanced_pdf_path}")
        with open(enhanced_pdf_path, "wb") as f:
            writer.write(f)
        os.remove(filtered_pdf_path)    
        return enhanced_pdf_path
    


    except Exception as e:
        print("❌ Error during enhancement:", e)
        return filtered_pdf_path


def remove_annotations_and_enhance(pdf_path, output_image_folder, final_pdf_path):
    os.makedirs(output_image_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        annot = page.first_annot
        while annot:
            next_annot = annot.next
            page.delete_annot(annot)
            annot = next_annot
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        enhanced = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        image_path = os.path.join(output_image_folder, f"page_{page_num + 1}.jpg")
        cv2.imwrite(image_path, enhanced)
        image_paths.append(image_path)
    images = [Image.open(p).convert("RGB") for p in image_paths]
    if images:
        images[0].save(final_pdf_path, save_all=True, append_images=images[1:])
    print(f"✅ Final cleaned PDF saved: {final_pdf_path}")
    return final_pdf_path


def cleanup_temp_images(folder_path):
    if os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, f))
        os.rmdir(folder_path)
        print(f"🧹 Cleaned temp folder: {folder_path}")




def send_first_page_to_gemini(pdf_path):
    import fitz  # PyMuPDF
    from PIL import Image
    import re
    import json
    from pdf2image import convert_from_path

    # # Load and render the first page
    # doc = fitz.open(pdf_path)
    # pix = doc[0].get_pixmap(dpi=300)
    # img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    doc = fitz.open(pdf_path)
    # doc = convert_from_path(pdf_path)
    images = []
    for i in range(min(2, len(doc))):  # Just in case PDF has less than 2 pages
        pix = doc[i].get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    # Prompt
    prompt = """
You are an AI that extracts structured financial information from bank statements. From this document page, extract:

- Bank Name  
- Account Number  
- Ending Balance  
- Date
Return the response strictly in the following JSON format:

{
  "date": "...",
  "endingbalance": "...",
  "Bankname": "...",
  "account_number": "..."
  
}
"""

    print("🧠 Querying Gemini...")
    
    # Send prompt and image to Gemini
    response = model.generate_content(contents=[prompt.strip(), img])
    response_text = response.text

    print(f"\n📋 Gemini Response:\n{response_text}\n")

    # Try to parse JSON-like structure from response
    try:
        json_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())  # use json.loads() if Gemini returns valid JSON
        else:
            parsed = {
                "date": "...",
                "ending_balance": "...",
                "bank_name": "...",
                "account_number": "..."
            }
    except Exception as e:
        print("❌ Error parsing response:", e)
        parsed = {
            "date": "...",
            "ending_balance": "...",
            "bank_name": "...",
            "account_number": "..."
        }

    return parsed     






# def generate(pdf_path, fiscal_date):
#     print(pdf_path, "path")
#     try:
#         client = genai.Client(
#         api_key="AIzaSyB7n-1IA7ms7i_IE6nFrhUzsJ81LrVxF_k",
#         )

#         files = [
#             client.files.upload(file=pdf_path),
            
#         ]
#         model = "gemini-2.0-flash"
#         contents = [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_uri(
#                         file_uri=files[0].uri, # type: ignore
#                         mime_type=files[0].mime_type, # type: ignore
#                     ),
#                     types.Part.from_text(text=f"Extract endingbalance as of {fiscal_date}"),
#                     types.Part.from_text(text="""extract data from provided document
#                     Schema
#                     {
#                     endingbalance: string,
#                     date: string,
#                     accountnumber: string,
#                     Bankname:string
#                     }"""),
#                 ],
#             ),
#         ]
#         generate_content_config = types.GenerateContentConfig(
#             # thinking_config = types.ThinkingConfig(
#             #     thinking_budget=0,
#             # ),
#             response_mime_type="application/json",
#         )
#         rsp = client.models.generate_content(
#             model=model,
#             contents=contents, # type: ignore
#             config=generate_content_config,
#         )
#         print(rsp)
#         rsp = json.loads(rsp.model_dump_json())

#         rsp = rsp['candidates'][0]['content']['parts'][0]['text']
#         rsp = json.loads(rsp)
#         return rsp[0]
#     except Exception as error:
#         print(error, "error in gemini")



def generate(pdf_path, fiscal_date):
    print(pdf_path, "path")
    try:
        client = genai.Client(api_key="AIzaSyB7n-1IA7ms7i_IE6nFrhUzsJ81LrVxF_k")

        try:
            uploaded_file = client.files.upload(file=pdf_path)
        except Exception as upload_error:
            print("❌ File upload failed:", upload_error)
            raise ValueError("Gemini file upload failed.")

        model = "models/gemini-2.5-flash"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri,
                        mime_type=uploaded_file.mime_type,
                    ),
                    types.Part.from_text(text=f"Extract endingbalance as of {fiscal_date}"),
                    types.Part.from_text(text="""extract data from provided document
                    Schema
                    {
                    endingbalance: string,
                    date: string,
                    accountnumber: string,
                    Bankname:string
                    }"""),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
        )

        rsp = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        print("Gemini raw response:", rsp)

        rsp_json = json.loads(rsp.model_dump_json())

        if (
            "candidates" not in rsp_json
            or not rsp_json["candidates"]
            or "content" not in rsp_json["candidates"][0]
        ):
            raise ValueError("❌ Invalid Gemini response structure")

        text_part = rsp_json["candidates"][0]["content"]["parts"][0]["text"]
        extracted_data = json.loads(text_part)

        return extracted_data[0] if isinstance(extracted_data, list) else extracted_data

    except Exception as error:
        print("❌ Error in Gemini generate():", error)
        raise

