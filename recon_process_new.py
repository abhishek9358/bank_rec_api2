import os
import base64
import json

from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")  # ⬅️ Replace with your Gemini API key
# genai.configure(api_key=GOOGLE_API_KEY)

client = genai.Client(api_key=GOOGLE_API_KEY)


def ReconProcessNew(file_path, fiscal_date):
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        base64_en = base64.b64encode(file_content)

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type="application/pdf",
                        data=base64.b64decode(base64_en)
                    ),
                    types.Part.from_text(text=f"""
                        extract Labled Data Uncleared checks and payments as of {fiscal_date}
                            json format
                            DATE | TYPE (Optional) | REF NO | PAYEE | AMOUNT
                    """) 
                ]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1), 
            response_mime_type='application/json',
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties= {
                    "Uncleared Checks and Payments": types.Schema(
                        type = types.Type.ARRAY,
                        items= types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "date": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "type": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "payee": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "amount": types.Schema(
                                    type=types.Type.STRING
                                ),
                                "reference number": types.Schema(
                                    type=types.Type.STRING,
                                    default="-",
                                    nullable=True,

                                )
                        }
                        )
                    )
                }
            )
            )
        # for chunk in client.models.generate_content_stream(
        #     model="gemini-2.5-pro",
        #     contents=contents, # type: ignore
        #     config=generate_content_config,
        # ):
        #     print(chunk.text, end="")

        response = client.models.generate_content(model="gemini-2.5-flash", contents=contents, # type: ignore 
                                       config=generate_content_config)
        # response = response.model_dump_json()
        resp_jsn = json.loads(response.text) # type: ignore
        total= 0
        total_1 = 0
        for values in resp_jsn['Uncleared Checks and Payments']:
            print(values, "values of ")
            total += float(values['amount'].replace(r",", ""))

        # for values in resp_jsn['Uncleared Deposits and Credits']:
        #     print(values, "values of ")
        #     total_1 += float(values['amount'].replace(r",", ""))
        resp_jsn['total'] = total
        resp_jsn['total_1'] = total_1
        
        print(resp_jsn)

        print(total_1)
        try:
            os.remove(file_path)
        except:
            pass
        return resp_jsn
    except Exception as error:
        print(error)




# ReconProcessNew("test.pdf", "")