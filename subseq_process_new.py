from PyPDF2 import PdfReader, PdfWriter
import base64
import os
import json
import math
import asyncio
import shutil
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")  
model = "gemini-2.5-flash"

client = genai.Client(api_key="AIzaSyCJvpdXTjkO3Dusta1I-EisbmOA0HuPACc")





def SplitPDF(input_pdf_path, output_dir="output_subs"):
    try:
        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)

        if total_pages < 4:
            print(f"Warning: PDF has only {total_pages} pages. Cannot split into 4 distinct parts effectively.")
        
        os.makedirs(output_dir, exist_ok=True)

        pages_per_part = math.ceil(total_pages / 4)

        current_page_index = 0
        for i in range(4):
            writer = PdfWriter()
            output_file_name = f"{os.path.basename(input_pdf_path).replace('.pdf', '')}_part{i+1}.pdf"
            output_path = os.path.join(output_dir, output_file_name)

            pages_added_to_current_part = 0
            while pages_added_to_current_part < pages_per_part and current_page_index < total_pages:
                writer.add_page(reader.pages[current_page_index])
                current_page_index += 1
                pages_added_to_current_part += 1

            if len(writer.pages) > 0: # Only write if pages were added
                with open(output_path, "wb") as fp:
                    writer.write(fp)
                print(f"Created '{output_path}' with {len(writer.pages)} pages.")
            else:
                print(f"Part {i+1} is empty (no pages written).")

        return True

    except FileNotFoundError:
        print(f"Error: Input PDF file not found at '{input_pdf_path}'")
        return False
    except Exception as e:
        print("error", e)
        return False



def ExtractSubsequentData(base64_en_content):
    try:
        print('reading ai starts')
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type="application/pdf",
                        data=base64.b64decode(base64_en_content)
                    ),
                    types.Part.from_text(text=f"""
                        extract Labled Data json format
                                         
                        // iso formated date
                        date: string,

                        // check number if specified otherwise ''

                        check: string

                        // transaction description

                        description: string,

                        // look for specified label such as "uncleared" or "cleared" 

                        label: string,

                        // if not specified, assume 0

                        amount: int,
                        
                    """)
                ]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
                # temperature=0,
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
                # response_mime_type="text/plain",
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type = types.Type.OBJECT,
                    properties = {
                        "items": types.Schema(
                            type = types.Type.ARRAY,
                            items = types.Schema(
                                type = types.Type.OBJECT,
                                properties = {
                                    "date": types.Schema(
                                        type = types.Type.STRING,
                                    ),
                                    "check": types.Schema(
                                        type = types.Type.STRING,
                                    ),
                                    "description": types.Schema(
                                        type = types.Type.STRING,
                                    ),
                                    "label": types.Schema(
                                        type = types.Type.STRING,
                                    ),
                                    "amount": types.Schema(
                                        type = types.Type.NUMBER,
                                    ),
                                },
                            ),
                        ),
                    },
                ),
                system_instruction=[
                    types.Part.from_text(
                        text="""You will extract each entry from provided context .

        and DO NOT HULICINATE also consider decimal values like $44.22 to 44.33 not like 4422""" 
                    ),
                ],
            )



        response = client.models.generate_content(model=model, contents=contents, # type: ignore 
                                       config=generate_content_config)
        resp_jsn = json.loads(response.text) # type: ignore
    
        
        return resp_jsn
    
    except Exception as error:
        raise error
    
async def LoopAsync(executor, context):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(executor, ExtractSubsequentData, context)
                return response
            except: 
                pass
import time
async def HandleSubsequentProcess(file_path):
    try:
        start = time.time()
        folder = "output_subs"
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print("old files deleted")
            except Exception as e:
                print(e, 'eror')
        split = SplitPDF(file_path)
        if split != True:
            return {'error', split}
        
        tasks = []
        files = os.listdir(folder)
        # with ThreadPoolExecutor() as executor:
        # loop = asyncio.get_event_loop()
      

        final_res = []
        with ThreadPoolExecutor() as executor:
            for file in files:
                with open(f"{folder}/{file}", 'rb') as f:
                    file_content = f.read()

                base64_en = base64.b64encode(file_content)
                tasks.append(LoopAsync(executor, base64_en))
            results = await asyncio.gather(*tasks)   

            for items in results:
                final_res.append(items)
        end = time.time()

        
        print(final_res)
        print(f"execution time", end - start)
        return final_res
        # len(tasks)
    except Exception as error:
        print(error)



# asyncio.run(HandleSubsequentProcess("test.pdf"))