# import base64
# import os
# from google import genai
# from google.genai import types
# import re
# import json
# import asyncio
# from concurrent.futures import ThreadPoolExecutor


# api_keys = ["AIzaSyCJvpdXTjkO3Dusta1I-EisbmOA0HuPACc", "AIzaSyB7n-1IA7ms7i_IE6nFrhUzsJ81LrVxF_k"]
# def SubSequentResponse1(txt):
#     try:
#         client = genai.Client(
#             api_key="AIzaSyDD4bFKst5K0J39VNqDhCO4y_OOgRna3R4",
#         )

#         model = "gemini-2.0-flash-lite"
#         contents = [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_text(
#                         text="""convert provided text in JSON format followed by the schema



#     {

#     statementDate: string,

#     trx: [

#     {

#     // iso formated date

#     date: string,

#     // check number if specified otherwise ''

#     check: string

#     // transaction description

#     description: string,

#     // look for specified label such as "uncleared" or "cleared" 

#     label: string,

#     // if not specified, assume 0

#     amount: int,

#     }

#     ],

#     }





#     This text



#     ```"""
#                     ),
#                 ],
#             ),
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_text(text=txt),
#                 ],
#             ),
#         ]
#         generate_content_config = types.GenerateContentConfig(
#             temperature=0,
#             top_p=0.95,
#             top_k=40,
#             max_output_tokens=8192,
#             # response_mime_type="text/plain",
#             response_mime_type="application/json",
#             response_schema=types.Schema(
#                 type = types.Type.OBJECT,
#                 properties = {
#                     "items": types.Schema(
#                         type = types.Type.ARRAY,
#                         items = types.Schema(
#                             type = types.Type.OBJECT,
#                             properties = {
#                                 "date": types.Schema(
#                                     type = types.Type.STRING,
#                                 ),
#                                 "check": types.Schema(
#                                     type = types.Type.STRING,
#                                 ),
#                                 "description": types.Schema(
#                                     type = types.Type.STRING,
#                                 ),
#                                 "label": types.Schema(
#                                     type = types.Type.STRING,
#                                 ),
#                                 "amount": types.Schema(
#                                     type = types.Type.NUMBER,
#                                 ),
#                             },
#                         ),
#                     ),
#                 },
#             ),
#             system_instruction=[
#                 types.Part.from_text(
#                     text="""You will extract each entry from provided context .

#     and DO NOT HULICINATE"""
#                 ),
#             ],
#         )

#         content =  client.models.generate_content(
#             model=model,
#             contents=contents, # type: ignore
#             config=generate_content_config,
#         )
#         # print(content.text, end="")
#         return content.text
#     except Exception as err:
#         print("error in gemini subquent:- ", err)



# async def process_page(executor, value):
#     loop = asyncio.get_event_loop()
#     resp = await loop.run_in_executor(executor, SubSequentResponse1, value)
#     jsn = json.loads(resp)  # type: ignore
#     return jsn.get('items', [])

# async def SubSequentResponse(md_path):
#    try:
#         with open(md_path, 'r') as f:
#             txt = f.read()
    
#         pages = re.split(r'## Page \d', txt)
#         final_resp = []
#         valid_pages = [p for i, p in enumerate(pages) if i != 0 and 'a' in p]

#         with ThreadPoolExecutor() as executor:
#             for i in range(0, len(valid_pages), 3):
#                 chunk = valid_pages[i:i+3]
#                 tasks = [process_page(executor, page) for page in chunk]
#                 results = await asyncio.gather(*tasks)

#                 for items in results:
#                     final_resp.extend(items)

#         print(final_resp)
#         return final_resp
#    except Exception as err:
#        print("sub sequent response error ", err)
#        return False
            


    

# SubSequentResponse("/home/nova/projects/reconsiliation_project/bank_rec_api2/output/sub.md")


import base64
import os
import re
import json
import asyncio
import time
import random
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types
import os 
from dotenv import load_dotenv

load_dotenv()
import io

import tempfile


GEMINI_API_KEY = os.getenv("subsequent_gemini_api")

# Use your actual API key
API_KEY = GEMINI_API_KEY

def SubSequentResponse1(part_data: types.Part, max_retries=3):
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=API_KEY)
            # files = [client.files.upload(file=file_path)]
            model = "models/gemini-1.5-flash"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        #   types.Part.from_uri(
                        #     file_uri=files[0].uri,  # type: ignore
                        #     mime_type=files[0].mime_type,  # type: ignore
                        # ),
                        part_data,
                        types.Part.from_text(
                            text="""extract data from provided document
Return in given json schema



        {

        statementDate: string,

        trx: [

        {

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

        }

        ],

        }



        ```"""
                        ),
                    ],
                ),
                # types.Content(
                #     role="user",
                #     parts=[
                #         types.Part.from_text(text=txt),
                #     ],
                # ),
            ]
            generate_content_config = types.GenerateContentConfig(
                temperature=0,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
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

            content = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config,
            )

            if not content.text:
                raise ValueError("Empty response from Gemini")

            return content.text

        except Exception as err:
            print(f"[Gemini] Attempt {attempt + 1} failed: {err}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt + random.uniform(0, 1)
                print(f"Retrying after {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("[Gemini] Max retries reached. Skipping this chunk.")
                return None


async def process_page(executor, img_obj):
    loop = asyncio.get_event_loop()
    img_byte_arr = io.BytesIO()

    img_obj.save(img_byte_arr, format="PNG", quality=100)
    img_bytes_data = img_byte_arr.getvalue()

    img_part = types.Part.from_bytes(
        data= img_bytes_data,
        mime_type= "image/png"
    )
    resp = await loop.run_in_executor(executor, SubSequentResponse1, img_part)

    if resp:
        try:
            jsn = json.loads(resp)
            return jsn.get('items', [])
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return []
    else:
        return []

from pdf2image import convert_from_path

async def SubSequentResponse(pdf_path):
    try:
        # print(pdf_path, "pdf path printing")
        start=  time.time()
        final_resp = []
    
        temp_folder = tempfile.mkdtemp()
        print(temp_folder, 'temp-folder')
        all_images =  os.listdir("subsequent/temp_images")
        
        images = convert_from_path(pdf_path, output_folder=temp_folder, thread_count=os.cpu_count(), dpi=300)
        
        print(
            'sta',  (time.time()) -start
        )
    
        all_images = os.listdir(temp_folder)
        
        # print(images)

        with ThreadPoolExecutor() as executor:
            for i in range(0, len(images), 50): 
                print("processing", i)
                tasks = [process_page(executor, img) for img in images]
                results = await asyncio.gather(*tasks)

                for items in results:
                    final_resp.extend(items)
       
        print(f"✅ Extraction complete. Total transactions extracted: {len(final_resp)}")
        end_ti = time.time()
    
        print(
            end_ti - start , 'printng '
        )
        return final_resp

    except Exception as err:
        print("SubSequentResponse error:", err)
        return False


# print(SubSequentResponse("test.pdf"))


# To run from script directly
# if __name__ == "__main__":
#     asyncio.run(SubSequentResponse("/home/nova/projects/reconsiliation_project/bank_rec_api2/output/sub.md"))
