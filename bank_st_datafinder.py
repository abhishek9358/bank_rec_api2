import pdfplumber
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
import google.generativeai as genai
import os
import re
from datetime import datetime
import os
from pdf2image import convert_from_path
from PIL import Image
import shutil
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import numpy as np
import tempfile

from concurrent.futures import ThreadPoolExecutor


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


genai.configure(api_key= GEMINI_API_KEY)
# genai.configure(api_key="AIzaSyAhqUkwc1lGklT9jq7pBYoPjXwlnxn1eqs")

model = genai.GenerativeModel('models/gemini-1.5-flash')


from PIL import Image, ImageEnhance, ImageOps


def extract_header_text(pdf_path):
    print("🔍 Improved header text extraction...")
    header_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                config = "--oem 3 --psm 6"
                if text and len(text.strip()) > 30:
                    lines = text.split("\n")[:50]
                    header = "\n".join(lines)
                    print("--Plumber Processeed --")
                else:
                    print("--Pytesseract Processing --")
                    image = page.to_image(resolution=300).original #300 // 600
                    width, height = image.size

                    crop_area = (0, 0, width, int(height * 0.5))  # Crop top 30% of the image
                    cropped_image = image.crop(crop_area)

                    gray = ImageOps.grayscale(cropped_image)
                    enhancer = ImageEnhance.Contrast(gray)
                    enhanced = enhancer.enhance(2.0)  #

                    ocr_config = "--oem 3 --psm 4"
                    ocr_text = pytesseract.image_to_string(enhanced, config=ocr_config)
                    lines = ocr_text.split("\n")

                    lines = [line.strip() for line in lines if line.strip()]
                    header = "\n".join(lines)

                header_texts.append((i + 1, header))
            except Exception as e:
                print(f"❌ Failed to extract header from page {i + 1}: {e}")
    return header_texts






def split_into_chunks(header_texts, chunk_size=10):
    print("✂️ Splitting header text into chunks...")
    chunks = []
    for i in range(0, len(header_texts), chunk_size):
        chunk_pages = header_texts[i:i + chunk_size]
        chunk_text = ""
        for page_num, header in chunk_pages:
            chunk_text += f"[Page {page_num}]\n{header}\n\n"
        chunks.append(chunk_text)
        print(f"Chunk {len(chunks)} created with {len(chunk_pages)} pages.")
        # print(chunks)
    return chunks



def gemini_response(prompt):
    response = model.generate_content(prompt)
    return response.text.strip()

def detect_header_dates_with_gemini_chunks(header_texts):
    print("🧠 Detecting header dates using Gemini (with chunks)...")
    page_dates = {}
    chunks = split_into_chunks(header_texts, chunk_size=10)

    for idx, chunk in enumerate(chunks):
        prompt = f"""
You are analyzing headers from a bank reconciliation document.

Each header belongs to a different page. Below is the text:

--- BEGIN HEADERS ---
{chunk}
--- END HEADERS ---

Instructions:
- For each page (mentioned like [Page 1], [Page 2], etc.), detect the **period ending date** mentioned in the header (in MM/DD/YYYY format).
- If no period ending date is found for a page, respond with "No period ending date found" for that page.
- If the date is in the Month DD, YYYY format, convert it to MM/DD/YYYY.
    For example, convert June 30, 2023 to 06/30/2023.
- if you find a date like "e.g: Previous period ending date: 12/31/2022",   so don't be extract this type of date, just extract the date which is in the header. 
- Date ranges like JUNE 1, 2024 - JUNE 30, 2024 → ✅ Extract the last date (JUNE 30, 2024) and convert to 06/30/2024.
Format your response like:
Page 1: 12/31/2022
Page 2: No period ending date found
Page 3: 12/31/2022



...
"""

        response = gemini_response(prompt)
        print(f"📋 Gemini response for chunk {idx + 1}:\n{response}\n")

        lines = response.split("\n")
        for line in lines:
            match = re.match(r"Page\s+(\d+):\s*(.*)", line.strip())
            if match:
                page_num = int(match.group(1))
                date_info = match.group(2)
                page_dates[page_num] = date_info

    return page_dates

def group_pages_by_detected_dates(page_dates, target_date_str):
    print("📚 Grouping pages based on detected period ending dates...")
    grouped_pages = []
    capture = False

    # for page_num in sorted(page_dates.keys()):
    #     detected = page_dates[page_num]

    #     if detected == target_date_str:
    #         print(f"✅ Target period start detected at page {page_num}")
    #         capture = True

    #     if capture:
    #         grouped_pages.append(page_num)

    #     if detected not in ["No period ending date found", target_date_str] and capture:
    #         print(f"🚫 Different period detected at page {page_num}, stopping capture")
    #         break

    for page_num in sorted(page_dates.keys()):
        detected = page_dates[page_num]

        if detected == target_date_str:
            print(f"✅ Target period start detected at page {page_num}")
            capture = True

        

        if capture:
            grouped_pages.append(page_num)

        if detected not in ["No period ending date found", target_date_str] and capture:
            print(f"🚫 Different period detected at page {page_num}, stopping capture")
            break    

    return grouped_pages


















# def save_filtered_pdf(input_pdf_path, output_dir, page_numbers):
#     import os
#     from pdf2image import convert_from_path
#     from PIL import Image, ImageEnhance, ImageFilter
#     import tempfile

#     print("📄 Enhancing selected pages from PDF...")

#     # Load original PDF and validate page numbers
#     reader = PdfReader(input_pdf_path)
#     total_pages = len(reader.pages)
#     valid_page_numbers = [p for p in page_numbers if 1 <= p <= total_pages]

#     if not valid_page_numbers:
#         print("❌ No valid pages to enhance. Aborting.")
#         return None

#     os.makedirs(output_dir, exist_ok=True)
#     input_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]
#     enhanced_pdf_path = os.path.join(output_dir, f"{input_filename}_enhanced.pdf")

#     try:
#         with tempfile.TemporaryDirectory() as temp_dir:
#             # Extract only selected pages to temp PDF
#             temp_pdf_path = os.path.join(temp_dir, "temp_selected.pdf")
#             writer = PdfWriter()
#             for p in valid_page_numbers:
#                 writer.add_page(reader.pages[p - 1])
#             with open(temp_pdf_path, "wb") as f:
#                 writer.write(f)

#             # Convert to images
#             images = convert_from_path(temp_pdf_path, dpi=400, fmt="png")


                

#             # # Enhance each image
#             enhanced_images = []
#             for img in images:
#                 img = img.filter(ImageFilter.MedianFilter(size=3))
#                 img = ImageEnhance.Sharpness(img).enhance(3.0)
#                 img = ImageEnhance.Contrast(img).enhance(1.8)
#                 img = ImageEnhance.Brightness(img).enhance(1.2)
#                 enhanced_images.append(img.convert("RGB"))

#             # # Save to enhanced PDF
#             enhanced_images[0].save(
#                 enhanced_pdf_path,
#                 save_all=True,
#                 append_images=images[1:]
#             )
#             # images[0].save(
#             #     enhanced_pdf_path,
#             #     save_all=True,
#             #     append_images=images[1:]
#             # )


#         print(f"✅ Enhanced PDF saved: {enhanced_pdf_path}")
#         return enhanced_pdf_path

#     except Exception as e:
#         print("❌ Error during enhancement:", e)
#         return None



def save_filtered_pdf(input_pdf_path, output_dir, page_numbers):
 

    print("📄 Enhancing selected pages from PDF...")

    # Load original PDF and validate page numbers
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    valid_page_numbers = [p for p in page_numbers if 1 <= p <= total_pages]

    if not valid_page_numbers:
        print("❌ No valid pages to enhance. Aborting.")
        return None

    # 🔁 Add 2 extra pages after last selected page (if they exist)
    last_page = max(valid_page_numbers)
    extra_pages = [p for p in range(last_page + 1, last_page + 4) if p <= total_pages]
    for ep in extra_pages:
        if ep not in valid_page_numbers:
            print(f"➕ Adding extra page {ep}")
            valid_page_numbers.append(ep)

    os.makedirs(output_dir, exist_ok=True)
    input_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]
    enhanced_pdf_path = os.path.join(output_dir, f"{input_filename}_enhanced.pdf")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract only selected pages to temp PDF
            temp_pdf_path = os.path.join(temp_dir, "temp_selected.pdf")
            writer = PdfWriter()
            for p in valid_page_numbers:
                writer.add_page(reader.pages[p - 1])
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)

            # Convert to images
            images = convert_from_path(temp_pdf_path, dpi=450, fmt="png")

            # Enhance each image
            enhanced_images = []
            for img in images:
                enhanced_images.append(img.convert("RGB"))

            # Save to enhanced PDF
            enhanced_images[0].save(
                enhanced_pdf_path,
                save_all=True,
                append_images=images[1:]
            )

        print(f"✅ Enhanced PDF saved: {enhanced_pdf_path}")
        return enhanced_pdf_path

    except Exception as e:
        print("❌ Error during enhancement:", e)
        return None












def run_pdf_filter_pipeline_st(pdf_path: str, target_date_str: str, output_dir: str = "output_folder"):
    """
    Full Pipeline to:
    1. Extract headers
    2. Detect period ending dates using Gemini
    3. Group relevant pages
    4. Save filtered PDF
    """

    target_date = datetime.strptime(target_date_str, "%m/%d/%Y")
    
    header_texts = extract_header_text(pdf_path)
    page_dates = detect_header_dates_with_gemini_chunks(header_texts)
    relevant_pages = group_pages_by_detected_dates(page_dates, target_date_str)

    if not relevant_pages:
        print("⚠️ No matching pages found based on detected header dates.")
        return None
    else:
        output_file_path = save_filtered_pdf(pdf_path, output_dir, relevant_pages)
        return output_file_path
    


