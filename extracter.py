import os
import re
import tempfile
import pytesseract
import pdfplumber
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from dateutil.parser import parse
from PIL import Image, ImageEnhance, ImageOps
from utils import images_to_pdf


def format_date(date_str):
    """Ensure the date is in the correct format."""
    date_str = date_str.strip()
    try:
        global d
        try:
            d = datetime.strptime(date_str, '%B %d, %Y').strftime('%m/%d/%Y')
            return d
        except:
             pass
        try:
            d = datetime.strptime(date_str, '%b %d, %Y').strftime('%m/%d/%Y')  # Jun 3, 2024
            return d
        except:
            pass
        try:
            d = datetime.strptime(date_str, '%m/%Y').strftime('%m/%d/%Y')  # Jun 3, 2024
            return d
        except:
            pass
        try:
            d = datetime.strptime(date_str, '%m/%d/%y').strftime('%m/%d/%Y')
            return d
        except:
             pass
        try:
            d = datetime.strptime(date_str, '%m/%d/%Y').strftime('%m/%d/%Y')
        except:
            d = datetime.strptime(date_str, '%m/%d').strftime('%m/%d')
        return d
    except ValueError:
        return datetime.strptime(date_str, '%m/%d/%Y').strftime('%m/%d/%Y')


# def extract_text_from_pdf_with_tesseract(pdf_path):
#     """Extract text using OCR (Tesseract) from scanned PDFs."""
#     with tempfile.TemporaryDirectory() as temp_dir:
#         images = convert_from_path(pdf_path, output_folder="temp_images", output_file="out_", dpi=300, fmt="png")
#         pages_text = {}

#         all_images = os.listdir("temp_images")
#         all_images = sorted(all_images)
#         for i, image in enumerate(all_images):
#             # image_path = os.path.join(temp_dir, f'page_{i+1}.png')
#             # image.save(image_path, 'PNG')
#             config = "--oem 3 --psm 6"
#             text = pytesseract.image_to_string(f"temp_images/{image}", config)
#             pages_text[i+1] = text
#             os.remove(f"temp_images/{image}")

#         return pages_text


def extract_text_from_pdf_with_tesseract(pdf_path):
    """Extract text using OCR (Tesseract) from scanned PDFs, with contrast-enhancing preprocessing."""
    
    def preprocess_image_for_ocr(image_path):
        img = Image.open(image_path).convert("L")      # Convert to grayscale
        img = ImageOps.invert(img)                     # Invert (for light-colored text)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)                    # Boost contrast
        return img

    # with tempfile.TemporaryDirectory() as temp_dir:
    convert_from_path(pdf_path, output_folder="temp_images", output_file="out_", dpi=450, fmt="jpeg", jpegopt={"quality": True})
    pages_text = {}

    all_images = sorted(os.listdir("temp_images"))
    for i, image in enumerate(all_images):
        image_path = os.path.join("temp_images", image)
        # preprocessed_img = preprocess_image_for_ocr(image_path)
        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(image_path, config=config)
        pages_text[i + 1] = text
        # os.remove(image_path)

    return pages_text


def extract_text_from_pdf_with_plumber(pdf_path):
    """Extract text from a PDF using pdfplumber."""
    pages_text = {}
    # convert_from_path(pdf_path, output_folder="temp_images", output_file="out_", dpi=450, fmt="jpeg", jpegopt={"quality": True})
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text() or ""
            pages_text[page_num] = page_text
    return pages_text

def find_period_ending_pages(pages_text, start_date):
    """Find pages belonging to a specific period until a new date appears."""
    try:
        formatted_target_date = format_date(start_date)
    
        period_patterns = [
            re.compile(r'STATEMENT DATES\s+(\d{1,2}/\d{1,2}/\d{2,4})\s*-'),
            re.compile(r'Period Ending (\d{1,2}/\d{1,2}/\d{2,4})'),
            re.compile(r'Reconciliation\s+Date[:]?\s+\d{1,2}/\d{1,2}/\d{2,4}'),
            re.compile(r'As of (\d{1,2}/\d{1,2}/\d{2,4})'),
            re.compile(r'As of (\d{2}/\d{2}/\d{4})'),
            # re.compile(r'This statement: (:?January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})'),
            re.compile(r'This\s+Statement\s+\n*.*\d{1,2},\s*\d{2,4}'),
            # re.compile(r'StatementPeriod.*\n.*\d{1,2}/\d{1,2}/\d{2,4}'),
            re .compile(r'This\s+statement[:]?\s+\n*.*\d{1,2},\s*\d{2,4}'),
            re.compile(r'Ending Balance on\s+\n*.*\d{1,2},\s*\d{2,4}'),
            re.compile (r'Statement Ending\s\d{1,2}/\d{1,2}/\{2,4}'),
            re.compile (r'(\d{2}/\d{2}/\d{2,4})\s*-\s*(\d{2}/\d{2}/\d{2,4})'),


            re.compile(r'Account\s+Statement\s+\n*.*\d{1,2},\s*\d{2,4}'),
            re.compile(r'Statement\s+Period[:]?\s+\n*.*\d{1,2},\s*\d{2,4}'),
            re.compile(r'STATEMENT DATE\s+(\d{1,2}/\d{1,2}/\d{2,4})'),
            re.compile(r'Date\s*\n+\d{1,2}/\d{1,2}/\d{4}'),
            re.compile(r'Date\n(\d{2}/\d{2}/\d{4})'),
            re.compile(r'Ending Market Value\s\d{1,2}/\d{1,2}/\d{2,4}'),
            re.compile(r'Date\s*(\S+)'),
            re.compile(r'This\s+Statement\s*[:]?\s+\d{1,2}/\d{1,2}/\d{2,4}'),
            re.compile(r'Ending balance on \d{1,2}/\d{1,2}'),
            re.compile(r'Processing\s*Month.*\d{1,2}/\d{2,4}.*'),
            re.compile(r'thru \d{1,2}/\d{1,2}/\d{1,2}'),
            re.compile(r'through\n\d{1,2}/\d{1,2}/\d{4}'),
            # re.compile(r'Initiate Business Checking\n \d{1,2}/\d{1,2}/\d{1,2}'),
            re.compile(r'Card Account Statement\s*\n\s*\d{2}/\d{2}/\d{4}\s*-\s*(\d{2}/\d{2}/\d{4})'),
            re.compile(r'Balance Summary\s*\(\d{1,2}/\d{1,2}/\d{2}\s*-\s*(\d{1,2}/\d{1,2}/\d{2})\)'),
            re.compile(r'.*\d{1,2}, \d{2,4}'),
            re.compile(r'Ending\s*Balance.*\d{1,2}/\d{2,3}.*')
            # re.compile(r"\d{2}/\d{2}/\d{4}\s*-\s*(\d{2}/\d{2}/\d{4})")

        ]

        clean_date_patterns = [
            re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}'),
            re.compile(r'\d{1,2}/\d{2,4}'),
            re.compile(r'\d{1,2}/\d{1,2}'),
            re.compile(r'([A-Za-z]+ \d{1,2}, \d{2,4})')
        ] 

        relevant_pages = set()
        collecting = False  # Track whether we're within the correct date range
        
        for page_num, text in pages_text.items():
            for pattern in period_patterns:
                match = pattern.findall(text)
                print(match) 
                if match:
                    try:
                        new_dte = None
                        date_str = match[0]


                        if isinstance(date_str, tuple):
                            date_str = ' '.join(date_str)  
                        print(date_str, 'before parse')
                        # date_str = clean_date.findall(date_str)
                      
                        for _dte in clean_date_patterns:
                            _matched = _dte.findall(date_str)
                            if len(_matched) == 0 : continue
                            new_dte = _matched[0]
                            break
                        if new_dte == None: continue
                        extracted_date = format_date(new_dte)
                        print(extracted_date, 'parsed date')
                        
                        date_str = _dte.findall(date_str)
                        print(new_dte, 'match new date')

                       






                    except Exception as _date_error:
                        print(_date_error, "parsing date errro")
                        extracted_date = None
                    # print(extracted_date, formatted_target_date, 'target date')
                    t = str(extracted_date).split("/")
                    k = str(formatted_target_date).split("/")
                    print(k, t)
                    if len(t) > 2:
                        formated_t = f"{t[0]}/{t[2]}"
                        formated_k = f"{k[0]}/{k[2]}"
                        if formated_t == formated_k:
                            collecting = True  # Start collecting pages
                            relevant_pages.add(page_num)
                            print("yes it was match", formated_k, formated_t)
                        elif formated_t and collecting:
                            # Stop when we encounter a new date different from the original
                            collecting = False
                            break
                    # elif :
                    #     formated_t = extracted_date if extracted_date else date_str[0] if len(date_str) > 0 else None
                    #     formated_k = f"{k[0]}/{k[1]}"
                    #     print(formated_k, formated_t, "hello else")
                    #     if formated_t == formated_k:
                    #         collecting = True  # Start collecting pages
                    #         relevant_pages.add(page_num)
                    #         print("yes it was match", formated_k, formated_t)
                    #     elif formated_t and collecting:
                    #         # Stop when we encounter a new date different from the original
                    #         collecting = False
                    #         break
                    else:
                        formated_t = extracted_date if extracted_date else date_str[0] if len(date_str) > 0 else None
                        formated_k = f"{k[0]}/{k[1]}"
                        print(formated_k, formated_t, "hello else")
                        if formated_t == formated_k:
                            collecting = True  # Start collecting pages
                            relevant_pages.add(page_num)
                            print("yes it was match", formated_k, formated_t)
                        elif formated_t and collecting:
                            # Stop when we encounter a new date different from the original
                            collecting = False
                            break
            if collecting:
                relevant_pages.add(page_num)

        return sorted(relevant_pages)
    except Exception as err:
        print(err, ": error in finding revelet pages")
        return []

def extract_pages(input_pdf, output_pdf, pages_to_extract: list):
    """Extract specified pages from a PDF and save them as a new PDF."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # images_to_pdf

    images_list = os.listdir("temp_images")
    images_list = sorted(images_list)

    all_image_list = []

    if len(images_list) > 1:
        for i,image_path in enumerate(images_list):
            x = i + 1
            for page_num in pages_to_extract:
                if x == page_num:
                    all_image_list.append(f"temp_images/{image_path}")
            # os.remove(f"temp_images/{image_path}")

        print("saving output PDF")            
        images_to_pdf(all_image_list, output_pdf)
    else:
          for page_num in pages_to_extract:
            if 1 <= page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])

            with open(output_pdf, "wb") as output_file:
                writer.write(output_file)


def Process2(pdf_path, date, output_path, memo):
    """Main function to process the PDF and extract relevant pages."""
    pages_text = {}
    if memo == False:
        print("Pdf Plumber...")
        pages_text = extract_text_from_pdf_with_plumber(pdf_path)
        print(pages_text, "from plumbur")

    if not any(pages_text.values()):
        print("PDF is scanned, using OCR...")
        pages_text = extract_text_from_pdf_with_tesseract(pdf_path)
        print(pages_text)

    relevant_pages = find_period_ending_pages(pages_text, date)

    if relevant_pages:
        print(f"The date {date} was found on the following pages: {relevant_pages}")
        extract_pages(pdf_path, output_path, relevant_pages)
        print(f"Extracted pages saved to {output_path}")
       
        return True
    else:
        print(f"The date {date} was not found in the document.")
    return False
       
max_try = 1

def Process1(pdf_path, date, output_path, retry):

    global max_try

    # if max_try > 1: return False
    result = Process2(pdf_path, date, output_path, False)
    # if result == False and retry == True:
    #     print('retry with ocr', f"max_try: {max_try}")
    #     result = Process2(pdf_path, date, output_path, True)
    #     max_try += 1
    
    return result


