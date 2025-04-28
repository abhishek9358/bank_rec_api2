
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from datetime import datetime
import shutil
import os
from llama_extractor import HandleBankStatement, HandleLlamaExtract
from extracter import Process1
from fastapi import BackgroundTasks, FastAPI, File, UploadFile, Form, Response
from prepare_resp import HandleJsonForResp

app = FastAPI()
jobs = {}


# === Import your pipeline functions ===
from bankst_new import (
    remove_annotations_from_pdf,
    extract_text,
    split_into_chunks,
    find_relevant_pages,
    preprocess_and_save_images,
    save_filtered_pdf,
    remove_annotations_and_enhance,
    cleanup_temp_images,
)


UPLOAD_DIR = "./uploads"
FILE_PATH = "./output_uploaded"
os.makedirs(UPLOAD_DIR, exist_ok=True)
last_file = None

@app.post("/upload/")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), fiscal_date: str = Form(...)):
    print('hitting upload recon api')
    with open("data.json", 'w') as files:
            json.dump({}, files)

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    last_file = file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    output_pdf = os.path.join(FILE_PATH, file.filename)
    rst = Process1(file_path, fiscal_date, output_pdf, False)

    if rst == False: return {"data": []}
    # olm_resp = await RunProcess(output_pdf)
    # background_tasks.add_task(RunProcess, output_pdf)
    # print(olm_resp, "olm respon")
                                                                                    
    # CovertJsonlToTxt('/home/nova/projects/projects/olm_output/results/output.jsonl')
    jobs = {"status": "processing"}
    
    background_tasks.add_task(HandleLlamaExtract, output_pdf) 

    try:
        # os.remove('projects/olm_output/results/output.jsonl')
        # os.remove('output.txt')
        os.remove(f"{UPLOAD_DIR}/{file.filename}")
        
        # os.remove('output.txt')
    except:
        pass
    


    return jobs


@app.get("/upload/status", status_code=200)
async def upload_file(response: Response):
    print('hitting upload recon status api')
    with open("data.json", 'r') as file:
            extracted_text = file.read()

    if len(extracted_text) < 20:
        response.status_code = 404
        return {"data": [], "status": "pending"}
   
                                                                                    
    # CovertJsonlToTxt('/home/nova/projects/projects/olm_output/results/output.jsonl')

    result = HandleJsonForResp('data.json')
    print(result, "result")

    try:
        # os.remove('projects/olm_output/results/output.jsonl')
        # os.remove('output.txt')
        # os.remove(f"{UPLOAD_DIR}/{last_file}")
        print('trying')
        
        # os.remove('output.txt')
    except:
        pass
    

    list_images = os.listdir("temp_images")

    if len(list_images):
        for img in list_images:
            os.remove(f"temp_images/{img}")
    return {"data": result}
    


# @app.post("/upload/")
# async def process_pdf(
#     file: UploadFile = File(...),
#     fiscal_date: str = Form(...)
# ):
#     # === Save Uploaded File ===
#     input_pdf_path = f"uploaded_{file.filename}"
#     with open(input_pdf_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     # === Parse Reconciliation Date ===
#     try:
#         rec_date = datetime.strptime(fiscal_date, "%m/%d/%Y")
#     except ValueError:
#         return {"error": "Invalid date format. Use MM/DD/YYYY."}

#     base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
#     cleaned_pdf = f"{base_name}_annoted.pdf"

#     # === Run Pipeline ===
#     try:
#         # out_path = remove_annotations_from_pdf(input_pdf_path, cleaned_pdf)
#         # extracted_pages = extract_text(cleaned_pdf)
#         # chunks = split_into_chunks(extracted_pages)
#         # relevant_pages = find_relevant_pages(chunks, rec_date)

#         out_path = remove_annotations_from_pdf(input_pdf_path, cleaned_pdf)
#         extracted_pages = extract_text(cleaned_pdf)
#         chunks = split_into_chunks(extracted_pages)
#         relevant_pages = find_relevant_pages(chunks, rec_date)

#         if not relevant_pages:
#             return {"message": "No relevant pages found for the given reconciliation date."}

#         temp_img_dir = "temp_images"
#         preprocess_and_save_images(cleaned_pdf, relevant_pages, temp_img_dir)

#         output_dir = "output_uploaded"
#         filtered_pdf = save_filtered_pdf(cleaned_pdf, output_dir, relevant_pages)

#         final_pdf = os.path.join(output_dir, f"{base_name}.pdf")
#         remove_annotations_and_enhance(filtered_pdf, "temp_cleaned_images", final_pdf)
#         # Cleanup
#         # os.remove(cleaned_pdf)
#         # os.remove(filtered_pdf)
#         # cleanup_temp_images("temp_images")
#         # cleanup_temp_images("temp_cleaned_images")
#         os.remove(input_pdf_path)

#         result = HandleLlamaExtract(filtered_pdf)
#         print(result, "results")
#         print(result)
#         # os.remove(final_pdf)
#         return {"data": result}

#     except Exception as e:
#         return {"error": str(e)}    
    


from bankst_new import  send_first_page_to_gemini
import json

from fastapi.responses import JSONResponse




@app.post("/upload_st")
async def process_and_extract_pdf(
    file: UploadFile = File(...),
    fiscal_date: str = Form(...)
):
    # === Save Uploaded File ===
    input_pdf_path = f"uploaded_{file.filename}"
    with open(input_pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # === Parse Reconciliation Date ===
    try:
        rec_date = datetime.strptime(fiscal_date, "%m/%d/%Y")
    except ValueError:
        return {"error": "Invalid date format. Use MM/DD/YYYY."}

    base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
    cleaned_pdf = f"{base_name}_annoted.pdf"

    try:
        # === PDF Cleanup Pipeline ===
        out_path = remove_annotations_from_pdf(input_pdf_path, cleaned_pdf)
        extracted_pages = extract_text(cleaned_pdf)
        chunks = split_into_chunks(extracted_pages)
        relevant_pages = find_relevant_pages(chunks, rec_date)

        if not relevant_pages:
            return {"message": "No relevant pages found for the given reconciliation date."}

        temp_img_dir = "temp_images_st"
        preprocess_and_save_images(cleaned_pdf, relevant_pages, temp_img_dir)

        output_dir = "output_uploaded"
        filtered_pdf = save_filtered_pdf(cleaned_pdf, output_dir, relevant_pages)

        final_pdf = os.path.join(output_dir, f"{base_name}.pdf")
        remove_annotations_and_enhance(filtered_pdf, "temp_cleaned_images", final_pdf)

        # === Bank Info Extraction ===
        # result = extract_bank_data_from_pdf(final_pdf)
        # result1 = extract_bank_data_from_pdf(filtered_pdf)

        result = send_first_page_to_gemini(final_pdf)
        # resul2 = send_first_page_to_gemini(filtered_pdf)
        # print(resul2)

        # === Cleanup ===
        os.remove(input_pdf_path)
        os.remove(cleaned_pdf)
        # os.remove(filtered_pdf)  # Optional
        cleanup_temp_images("temp_images_st")
        cleanup_temp_images("temp_cleaned_images")
        os.remove(filtered_pdf)
        os.remove(final_pdf)

        return {"data": result}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)   
