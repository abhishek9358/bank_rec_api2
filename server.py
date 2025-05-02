
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from datetime import datetime
import shutil
import os
from llama_extractor import  HandleLlamaExtract
from fastapi import  FastAPI, File, UploadFile, Form, Response
from prepare_resp import HandleJsonForResp
from fastapi.responses import JSONResponse
from text import generate
import json
from bank_reconsiliation import run_pdf_filter_pipeline
import time 

from subsequent.index import  HandleSubSequent

from typing import Annotated

app = FastAPI()
jobs = {}


# === Import your pipeline functions ===
from bankst_new import (
    save_filtered_pdf,
    cleanup_temp_images,
    
)


UPLOAD_DIR = "./uploads"
FILE_PATH = "./output_uploaded"
os.makedirs(UPLOAD_DIR, exist_ok=True)
last_file = None


UPLOAD_DIR = "uploaded_files"
OUTPUT_DIR = "output_folder"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...),
                    fiscal_date: str = Form(...)):
    
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        output_path = run_pdf_filter_pipeline(file_location, fiscal_date, output_dir=OUTPUT_DIR)

        llamaextracter = HandleLlamaExtract(output_path)
        print(llamaextracter)
        
        preprocessd = HandleJsonForResp(llamaextracter)
        print(preprocessd)

        return preprocessd

    


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
        

        temp_img_dir = "temp_images_st"

        output_dir = "output_uploaded"
        filtered_pdf = save_filtered_pdf(input_pdf_path, output_dir, [1,2])
        print("working 0")
       
        gen = generate(filtered_pdf, fiscal_date)
        print(gen)

        print("working 1")
        # === Cleanup ===
        try:
            os.remove(input_pdf_path)
            os.remove(filtered_pdf)  # Optional
            cleanup_temp_images("temp_images_st")
            cleanup_temp_images("temp_cleaned_images")
        except Exception as err:
            print(err, "file remove error")
            pass
       
        return {"data": gen}

    except Exception as e:
        print(e, "error in api")
        return JSONResponse(content={"error": str(e)}, status_code=500)   
    

@app.post("/upload_sub/")
async def process_subsequent(fiscal_date: Annotated[str, Form()], file: UploadFile):

    print(file)
    file_path1 = f"./{time.time()}{file.filename}"
    try:
        contents1 = await file.read()

        with open(file_path1, "wb") as f:
            f.write(contents1)
        
        final_resp =  await HandleSubSequent(fiscal_date,file_path1)

        print(final_resp, 'hi')
        try:
            os.remove(f"./{file_path1}")
        except:
            pass

        return {
             "result": {
                "items": final_resp
             }
        }
    except Exception as err:
        print(err, "error in sub api")
        os.remove(f"./{file_path1}")
        return {
              "result": "Could not found"
         }
    


  