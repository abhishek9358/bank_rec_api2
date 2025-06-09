import os
from pdf2image import convert_from_path
import pytesseract
import pdfplumber
import cv2
from pytesseract import Output
import re
import fitz
import numpy as np
import os
import cv2


def preprocess_image(path):
    img = cv2.imread(path)
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_yellow = np.array([20, 100, 100])  
    upper_yellow = np.array([40, 255, 255])
    
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    result = cv2.bitwise_and(img, img, mask=cv2.bitwise_not(mask))
    
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    
    # gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21) #can be reomved if not working

    processed_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  #working
                                          cv2.THRESH_BINARY, 11, 2)
    # _, processed_img = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    
    return processed_img

def Ocr_extract(path):
    custom_config = r'--oem 3 --psm 6'

    img = preprocess_image(path)
    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    keys = list(d.keys())

    date_pattern = "^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/(19|20)\d\d$"

    n_boxes = len(d["text"])
    for i in range(n_boxes):
        if int(d["conf"][i]) > 60:
            if re.match(date_pattern, d["text"][i]):
                (x, y, w, h) = (d["left"][i], d["top"][i], d["width"][i], d["height"][i])
                img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)


    return pytesseract.image_to_string(img, config=custom_config)

def extract_text_from_pdf(pdf_path):
    # OCR_CONFIG = "--oem 3 --psm 6"
    text = ""
    # convert_from_path(pdf_path, output_folder="temp_images", fmt="png",)
    pdf_doc = fitz.open(pdf_path)


    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):

            extracted_text = page.extract_text()

            if not extracted_text:
                print("yes it was in loop")
                # imag = convert_from_path(pdf_path, output_folder="temp_images", output_file="outfile_", fmt="png", dpi=300)
                imag = convert_from_path(pdf_path, output_folder="subsequent/temp_images", output_file="outfile_", fmt="jpeg", dpi=500)
                print("saved images")

                # list_dir = os.listdir('temp_images')
                list_dir = os.listdir('subsequent/temp_images')
                pp = 1
                list_dir = sorted(list_dir)
                # for file_name in list_dir:
                #     print(file_name, 'dd')
                #     text += f"\n\n## Page {pp}\n\n"
                #     text += Ocr_extract(f"temp_images/{file_name}") + "\n\n"
                #     pp  += 1
                #     os.remove(f'temp_images/{file_name}')

                for file_name in list_dir:
                    img_path = os.path.join("subsequent/temp_images", file_name)
                    print(file_name, 'dd')

                    if not os.path.exists(img_path):
                        print(f"❌ File not found: {img_path}")
                        continue

                    # Check if image can be read before running OCR
                    test_img = cv2.imread(img_path)
                    if test_img is None:
                        print(f"❌ Failed to read image: {img_path}")
                        continue

                    # Now safely extract text
                    text += f"\n\n## Page {pp}\n\n"
                    try:
                        text += Ocr_extract(img_path) + "\n\n"
                    except Exception as e:
                        print(f"⚠️ OCR failed for {file_name}: {e}")
                    pp += 1

                    # Optionally remove image after successful OCR
                    os.remove(img_path)










                # for page_num in range(len(pdf_doc)):
                #     page = pdf_doc[page_num]
                #     for img_index, img in enumerate(page.get_images(full=True)):
                #         xref = img[0]
                #         base_image = pdf_doc.extract_image(xref)
                #         image_bytes = base_image["image"]
                #         image_ext = base_image["ext"]
                #         image_path = os.path.join("/home/nova/projects/reconsiliation_project/bank_rec_api2/subsequent/temp_images",
                #                                     f"outfile_0001-{page_num + 1:02}.png")
                #         with open(image_path, "wb") as f:
                #             f.write(image_bytes)

                #         text += f"\n\n## Page {page_num}\n\n"
                #         text += Ocr_extract(image_path) + "\n\n"
                
                # return text
                break
                    
            
                # if()
            text += f"\n\n## Page {i}\n\n"
            text += extracted_text + "\n\n"

    return text


def save_as_markdown(text, output_path, msg):
    with open(output_path, "w", encoding="utf-8") as md_file:
        # md_file.write(f"# {msg}\n\n")
        md_file.write(text)

def Subsequent_Extractor(pdf_path):
    output_folder = "./output"
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "sub.md")
    text = extract_text_from_pdf(pdf_path)
    save_as_markdown(text, output_path, "Subsequent Report")
    print(f"Markdown file saved at: {output_path}")