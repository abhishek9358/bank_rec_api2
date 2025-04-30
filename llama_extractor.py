from llama_cloud_services import LlamaExtract
from dotenv import load_dotenv
load_dotenv()
import json

extractor = LlamaExtract(api_key='llx-3gy9QRCmzVRua2DPBOHcWTGrgrF8MsQWDQQJq3M5ynNJoPzI') #yha per bhi api keys pass kr skte h ya randon koi ek api key ya muiltple keys me se koi ek


def HandleLlamaExtract(pdf_path):
    try:
        agent = extractor.get_agent("extract-all") # change kr lena isko job name ho agent ka 
        list_items = agent.list_extraction_runs()

        if len(list_items.items) > 0:
            for ids in list_items.items:
                agent.delete_extraction_run(ids.id) # removing all caches

        result = agent.extract(pdf_path)


       

        with open("data.json", 'w') as _file:
            json.dump(result.data, _file) # type: ignore

        print(result.data)    

        return result.data # type: ignore
    except Exception as error:
        print("error in llama extract", error)
        return []
    


# def HandleBankStatement(pdf_path):
#     try:
#         agent = extractor.get_agent("bank_st") # change kr lena isko job name ho agent ka 
#         list_items = agent.list_extraction_runs()

#         if len(list_items.items) > 0:
#             for ids in list_items.items:
#                 agent.delete_extraction_run(ids.id) # removing all caches
#         result = agent.extract(pdf_path)
#         # with open("data.json", 'w') as _file:
#         #     json.dump(result.data, _file) # type: ignore

#         return result.data # type: ignore
#     except Exception as error:
#         print("error in llama extract", error)
#         return []    


def HandleBankStatement(pdf_path):
    from pdf2image import convert_from_path
    from PIL import Image
    import tempfile
    import os

    try:
        # Step 1: Convert first 2 pages to images
        images = convert_from_path(pdf_path, dpi=500)

        # Step 2: Save images as a new PDF (2 pages)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            temp_pdf_path = tmp_pdf.name
            images[0].save(temp_pdf_path, save_all=True, append_images=images[1:])

        # Step 3: Clear old runs
        agent = extractor.get_agent("bank_st")  # Adjust job name as needed
        list_items = agent.list_extraction_runs()

        if len(list_items.items) > 0:
            for ids in list_items.items:
                agent.delete_extraction_run(ids.id)

        # Step 4: Extract using 2-page temp PDF
        result = agent.extract(temp_pdf_path)

        return result.data  # type: ignore

    except Exception as error:
        print("❌ Error in llama extract:", error)
        return []
