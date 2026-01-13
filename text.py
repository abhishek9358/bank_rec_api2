# from google import genai
# from google.genai import types
# import json
# import google.generativeai as gen
# import os
# from dotenv import load_dotenv

# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# gen.configure(api_key=GEMINI_API_KEY)

# def generate(pdf_path, fiscal_date):
#    try:
#        client = genai.Client(
#         # api_key="AIzaSyB7n-1IA7ms7i_IE6nFrhUzsJ81LrVxF_k",
#         api_key= GEMINI_API_KEY
#         )

#        files = [
#             client.files.upload(file=pdf_path),
            
#         ]
#        model = "models/gemini-1.5-flash"
#        contents = [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_uri(
#                         file_uri=files[0].uri, # type: ignore
#                         mime_type=files[0].mime_type, # type: ignore
#                     ),
#                     types.Part.from_text(text=f"Extract endingbalance as of {fiscal_date}"),
#                     types.Part.from_text(text="""extract data from provided document
#     Return in given json schema:
                                         
#         {
#         endingbalance: string,
#         statementdate: string,
#         accountnumber: string,
#         Bankname:string
#         }
#                                          """),
#                 ],
#             ),
#         ]
#        generate_content_config = types.GenerateContentConfig(
           
#             response_mime_type="application/json",
#         )
       
#        response = client.models.generate_content(
#             model=model,
#             contents=contents, # type: ignore
#             config=generate_content_config,
#         )
#        response = response.model_dump_json()
#        response = json.loads(response)
#        print(response)
#         # print(response['candidates'][0]['content']['parts'][0]['text'])
#         # print(chunk.model_dump_json)
#        response = response['candidates'][0]['content']['parts'][0]['text']
#        response = json.loads(response)
#        if type(response) is list:
#           return response[0]
#        else:
#           return response
       
   
#    except Exception as error:
#       print(error, "error in gemini")



from google import genai
from google.genai import types
import json
import google.generativeai as gen
import os
import time
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gen.configure(api_key=GEMINI_API_KEY)

# def generate(pdf_path, fiscal_date, retries=5, delay=2):
#     for attempt in range(retries):
#         try:
#             client = genai.Client(api_key=GEMINI_API_KEY)

#             files = [client.files.upload(file=pdf_path)]

#             model = "models/gemini-1.5-flash"
#             contents = [
#                 types.Content(
#                     role="user",
#                     parts=[
#                         types.Part.from_uri(
#                             file_uri=files[0].uri,  # type: ignore
#                             mime_type=files[0].mime_type,  # type: ignore
#                         ),
#                         types.Part.from_text(text=f"Extract endingbalance as of {fiscal_date}"),
#                         types.Part.from_text(text="""extract data from provided document
# Return in given json schema:
# {
#   endingbalance: string,
#   statementdate: string,
#   accountnumber: string,
#   Bankname: string
# }


def generate(pdf_path,  retries=5, delay=2):
    for attempt in range(retries):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            files = [client.files.upload(file=pdf_path)]

            model = "models/gemini-2.5-flash"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=files[0].uri,  # type: ignore
                            mime_type=files[0].mime_type,  # type: ignore
                        ),
                        types.Part.from_text(text="""extract data from provided document
Return in given json schema:
{
  endingbalance: string,
  statementdate: string,
  accountnumber: string,
  Bankname: string
}

Note :- if in the document have a multiple ending balanse so only extract the first ending balance from the document and pass this.
"""),
                    ],
                ),
            ]

            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json",
            )

            response = client.models.generate_content(
                model=model,
                contents=contents,  # type: ignore
                config=generate_content_config,
            )

            response = json.loads(response.model_dump_json())
            text = response['candidates'][0]['content']['parts'][0]['text']
            json_data = json.loads(text)
            return json_data[0] if isinstance(json_data, list) else json_data

        except Exception as error:
            # Check if the error is due to service unavailability
            if "UNAVAILABLE" in str(error) and attempt < retries - 1:
                print(f"[Retry {attempt + 1}/{retries}] Gemini is overloaded. Retrying in {delay} seconds...")
                time.sleep(delay * (2 ** attempt))  # exponential backoff
                continue
            print(error, "error in gemini")
            break
