from google import genai
from google.genai import types
import json

def generate(pdf_path, fiscal_date):
    client = genai.Client(
        api_key="AIzaSyB7n-1IA7ms7i_IE6nFrhUzsJ81LrVxF_k",
    )

    files = [
        client.files.upload(file=pdf_path),
        
    ]
    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri, # type: ignore
                    mime_type=files[0].mime_type, # type: ignore
                ),
                types.Part.from_text(text=f"Extract endingbalance as of {fiscal_date}"),
                types.Part.from_text(text="""extract data from provided document
Schema
{
endingbalance: string,
statementdate: string,
accountnumber: string,
bankname:string
}"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        # thinking_config = types.ThinkingConfig(
        #     thinking_budget=0,
        # ),
        response_mime_type="application/json",
    )
    # for chunk in client.models._generate_content_stream(
    #     model=model,
    #     contents=contents, # type: ignore
    #     config=generate_content_config,
    # ):
        
    response = client.models.generate_content(
        model=model,
        contents=contents, # type: ignore
        config=generate_content_config,
    )
    response = response.model_dump_json()
    response = json.loads(response)
    # print(response['candidates'][0]['content']['parts'][0]['text'])
    # print(chunk.model_dump_json)
    response = response['candidates'][0]['content']['parts'][0]['text']
    response = json.loads(response)
    return response[0]

# print(
#     generate("output_uploaded/uploaded_10200 Tri Counties Bank-10772 (July-1-2023 to June-30-2024)_enhanced.pdf","06-30-2024")
# )