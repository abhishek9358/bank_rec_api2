import os
import base64
import json
import asyncio
import re

from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")  # ⬅️ Replace with your Gemini API key
# genai.configure(api_key=GOOGLE_API_KEY)

client = genai.Client(api_key=GOOGLE_API_KEY)
model = "gemini-2.5-flash"

async def ReconProcessNew(file_path, fiscal_date):
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        base64_en = base64.b64encode(file_content)

        tasks = [
            ExtractChecks(base64_en, fiscal_date), 
            ExtractOtherDesposits(base64_en, fiscal_date)
            ]
        results = await asyncio.gather(*tasks)
        

        print(results[0], "*results")
        

        # results = {
        #     results[0],
        #     results[1]
        # }
        # results = {}
        resp = {}
        for res in results:
            for keys in res.keys():
                resp[keys] = res[keys]

            
        try:
            os.remove(file_path)
        except:
            pass
        return resp
    except Exception as error:
        print(error, 'some error')

async def ExtractChecks(base64_en_content, fiscal_date):
    try:
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type="application/pdf",
                        data=base64.b64decode(base64_en_content)
                    ),
                    types.Part.from_text(text=f"""
                        extract Labled Data
                        if you are able to exact match the label *Uncleared checks and payments as of {fiscal_date}* then extract in below format
                            json format
                            DATE | TYPE (Optional) | REF NO. | PAYEE | AMOUNT
                        if you able to exact match the label **Outsanding Checks/Vouchers**
                            only extract oustanding checks do not extract cleared checks
                            follow every page and make sure label Reconciliation Date: MM/DD/YYYY should match date {fiscal_date} you have to extract only pages that have this Reconciliation Date label exact match.
                            stop extracting data as file may contain multiple Reconciliation Date Data so only extract where {fiscal_date} match 
                            json format
                            DOCUMENT NUMBER | Document Date | Document Amount | Payee
                    """)
                ]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            system_instruction='you are a cpa audit reviewer having rich exprterties in analysing documents you will read the document and extract relevent data as asked by the user and you will consisitant with your resulst and everytime you will return same output for same file and will not hulicinate.',
            response_mime_type='application/json',
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties= {
                    "Uncleared Checks and Payments": types.Schema(
                        type = types.Type.ARRAY,
                        items= types.Schema(
                            type=types.Type.OBJECT,
                            required=['reference number','payee','amount'],
                            properties={
                                "date": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "type": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "reference number": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "payee": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "amount": types.Schema(
                                    type=types.Type.STRING
                                )
                        }
                        )
                    )
                }
            )
            )


        response = client.models.generate_content(model=model, contents=contents, # type: ignore 
                                       config=generate_content_config)
        resp_jsn = json.loads(response.text) # type: ignore
        total= 0
        for values in resp_jsn['Uncleared Checks and Payments']:
            # print(values, "values of ")
            total += float(convertToNum(values['amount']))
        resp_jsn['total'] = total
        
        return resp_jsn
    
    except Exception as error:
        raise error

async def ExtractOtherDesposits(base64_en_content, fiscal_date):
    try:
        

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type="application/pdf",
                        data=base64.b64decode(base64_en_content)
                    ),
                    types.Part.from_text(text=f"""
                        extract Labled Data
                        if you are able to exact match label **Uncleared deposits and other credits as of {fiscal_date}** 
                            json format
                            DATE | TYPE (Optional) | REF NO | PAYEE | AMOUNT
                        if you are able to exact match label **Outstanding Deposits**
                            json format
                            DATE | TYPE (Optional) | REF NO | PAYEE | AMOUNT
                    """) 
                ]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            # thinking_config=types.ThinkingConfig(thinking_budget=-1), 
            system_instruction='you are a cpa audit reviewer having rich exprterties in analysing documents you will read the document and extract relevent data as asked by the user and you will consisitant with your resulst and everytime you will return same output for same file and will not hulicinate.',
            response_mime_type='application/json',
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties= {
                    "Uncleared Deposits and Credits": types.Schema(
                        type = types.Type.ARRAY,
                        items= types.Schema(
                            type=types.Type.OBJECT,
                            required=['reference number', 'payee', 'amount'],
                            properties={
                                "date": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "type": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "reference number": types.Schema(
                                    type=types.Type.STRING,
                                    default="--"
                                ),
                                "payee": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "amount": types.Schema(
                                    type=types.Type.STRING
                                ),
                                
                        }
                        )
                    )
                }
            )
            )


        response = client.models.generate_content(model=model, contents=contents, # type: ignore 
                                       config=generate_content_config)
        resp_jsn = json.loads(response.text) # type: ignore

        # print(resp_jsn, "resp_jsn")
        total_1 = 0
        for values in resp_jsn['Uncleared Deposits and Credits']:
            print(values, "values of credits")
            total_1 += float(convertToNum(values['amount']))
        resp_jsn['total_1'] = total_1
        
        return resp_jsn
    except Exception as error:
        print('error in process')
        raise error



def convertToNum(number_string):
     if re.fullmatch(r'\(([^)]+)\)', number_string):
        match = re.fullmatch(r'\(([^)]+)\)', number_string)
        content_inside_parentheses = match.group(1) # type: ignore
        cleaned_string = "-" + re.sub(r',', '', content_inside_parentheses)
     else:
        cleaned_string = re.sub(r',', '', number_string)

     return cleaned_string


# ReconProcessNew("test.pdf", "")