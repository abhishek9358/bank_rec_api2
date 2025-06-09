import google.generativeai as genai
import json
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv

load_dotenv()

# STEP 1: Configure Gemini
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# STEP 2: Load the Gemini model
model = genai.GenerativeModel("models/gemini-1.5-flash")

# STEP 3: Chunk PDF into 10-page segments
def split_pdf(pdf_path, chunk_size=10):
    doc = fitz.open(pdf_path)
    chunks = []
    for i in range(0, len(doc), chunk_size):
        chunk_path = f"temp_chunk_{i//chunk_size + 1}.pdf"
        chunk_doc = fitz.open()
        for j in range(i, min(i + chunk_size, len(doc))):
            chunk_doc.insert_pdf(doc, from_page=j, to_page=j)
        chunk_doc.save(chunk_path)
        chunks.append(chunk_path)
        chunk_doc.close()
    doc.close()
    return chunks

# STEP 4: Upload and query each chunk
def upload_and_extract(pdf_chunk_path):
    try:
        file = genai.upload_file(pdf_chunk_path)
        print(f"✅ Uploaded: {file.uri}")
    except Exception as e:
        print(f"❌ Failed to upload {pdf_chunk_path}: {e}")
        return None

    prompt = """
You are an expert in bank statement parsing. Extract structured data in the following JSON schema:

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

        amount: number,
        }
    ]
}

Extraction Rules:
- Always return valid and complete JSON, no markdown formatting.
- Extract all transaction types: Deposits, Withdrawals, Checks, Bankcard activity, DDA deposits, Loan payments, Service charges, etc.
- If any field is **not clearly available**, assume `null` (do not skip the transaction).
- Always include the `amount`. If it’s missing or illegible, return `0`.
- Convert all dates into ISO format: `YYYY-MM-DD`.
- The `statementDate` should reflect the "Statement Dates" range ending date from the document.

Goal:
Ensure that **every financial transaction entry is extracted**, even if incomplete, and normalize it into a uniform structure.
"""

    try:
        response = model.generate_content([prompt, file], stream=False)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"❌ Error during content generation or JSON parsing: {e}")
        return None

# STEP 5: Merge all chunks' results
def merge_chunks_results(results):
    final_result = {
        "statementDate": "",
        "trx": []
    }
    for res in results:
        if res:
            if not final_result["statementDate"] and res.get("statementDate"):
                final_result["statementDate"] = res["statementDate"]
            final_result["trx"].extend(res.get("trx", []))
    return final_result

# STEP 6: Main Runner
if __name__ == "__main__":
    pdf_path = "/home/abhishek/bank_rec_api2/output_folder/2024-1 Community Bank statement.pdf"  # ⬅️ Change to your actual PDF path
    chunks = split_pdf(pdf_path)

    all_results = []
    for chunk in chunks:
        result = upload_and_extract(chunk)
        if result:
            all_results.append(result)

    merged = merge_chunks_results(all_results)
    with open("final_extracted_data.json", "w") as f:
        json.dump(merged, f, indent=2)
        print("📝 Final merged JSON saved to final_extracted_data.json")

    # Clean up temp files
    for file in chunks:
        os.remove(file)
