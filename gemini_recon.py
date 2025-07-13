import google.generativeai as genai
import json
import os 
from dotenv import load_dotenv
load_dotenv()

# STEP 1: Configure Gemini API
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")  # ⬅️ Replace with your Gemini API key
genai.configure(api_key=GOOGLE_API_KEY)

# STEP 2: Load Gemini Model with file capabilities
model = genai.GenerativeModel("models/gemini-1.5-flash")

# STEP 3: Upload the PDF
def upload_pdf_to_gemini(pdf_path):
    try:
        file = genai.upload_file(pdf_path)
        print(f"📄 Uploaded: {file.uri}")
        return file
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

# STEP 4: Ask Gemini using schema prompt
def query_with_file(file):
    prompt = """
1. Role & Primary Objective
You are an AI expert specializing in financial data extraction. Your sole purpose is to meticulously scan the provided document text, identify specific lists of financial transactions, and extract every line item with perfect accuracy. You will then structure this data into a single, raw JSON object that strictly adheres to the provided schema.
2. Core Extraction Logic: A Step-by-Step Process
Step 1: Identify Target Sections
Your first task is to locate the specific sections containing the data you need. Scan the entire document for headers that are exact matches or extremely close variations of the following. The date mm/dd/yyyy can vary.
For uncleared_checks:
"Uncleared checks and payments as of mm/dd/yyyy"
"Outstanding Checks/Vouchers"
"Uncleared checks and payments as of [Date]"
For uncleared_deposits:
"Uncleared deposits and other credits as of mm/dd/yyyy"
"Outstanding Other Cash Items"
"Uncleared deposits and other credits as of [Date]"
For suspense_items:
"Outstanding Suspense Items"
Step 2: Meticulous Line Item Extraction
Once you identify a valid target section, you must extract EVERY SINGLE transaction line item listed beneath that header.
Extraction Scope: Continue extracting items line by line until you encounter one of the following "stop" signals:
A "Total" line that clearly summarizes the list you are currently extracting.
The header of a new, different target section (e.g., you are extracting checks and you see the "Uncleared deposits" header).
A clear and definitive end to the list of transactions for that section.
Multi-Page Lists: If a list of items for a section starts on one page and continues onto the next, you MUST continue extracting from the subsequent pages until you hit a "stop" signal. Do not end a section prematurely at a page break.
Step 3: Accurate Field Population
For each individual line item you extract, populate its details into a JSON object as follows:
date: Extract the transaction date from the line. Format it as an ISO date string: YYYY-MM-DD.
description: Create a comprehensive string. Combine the transaction TYPE (e.g., "Check", "Bill Pmt-Check", "Deposit"), the REF NO. (if present), and the PAYEE or NAME/MEMO field.
amount: Extract the transaction amount as a string. This is critical:
MUST include the negative sign for checks, payments, or debits (e.g., "-167.75").
Amounts shown in parentheses, like (167.75), represent negative values and MUST be extracted as a negative string (e.g., "-167.75").
Deposits and credits should be positive (e.g., "100.00").
ref no: Extract the reference number (e.g., Check Number, REF NO., Num).
payee: Extract the payee, name, or memo associated with the transaction.
3. Critical Rules & Exclusions (What NOT to Extract)
EXCLUDE "CLEARED" TRANSACTIONS: You MUST ignore any sections with headers like "Cleared Transactions," "Checks and payments cleared," or "Deposits and other credits cleared." Items from these sections DO NOT belong in the output.
EXCLUDE "AFTER" DATE TRANSACTIONS: You MUST ignore any sections with headers like "Uncleared transactions after mm/dd/yyyy". Only extract from sections explicitly labeled "as of mm/dd/yyyy" or "Outstanding...".
HANDLE MISSING SECTIONS: If a document does not contain a specific target section (e.g., there are no "Uncleared deposits"), the corresponding array in the JSON output must be empty ([]).
4. Finalization & Output Formatting
Step 4: Calculate Totals
After extracting all items, calculate the totals.
total_0: The total for uncleared_checks.
tota_1: The total for uncleared_deposits.
total_2: The total for suspense_items.
Prioritize Explicit Totals: If the document provides an explicit "Total" amount for a specific list you extracted, use that value.
Calculate if Necessary: If no explicit total is given for a list with items, you must calculate the sum of the amount fields.
Formatting: All total values must be strings. If an array is empty, its total must be "0".
Step 5: Strict JSON Output
Your final output MUST be a single, raw, and perfectly valid JSON object conforming to the schema below.
DO NOT include any conversational text, explanations, apologies, or markdown formatting (like ```json).
The entire response should be only the JSON object itself.
5. JSON Schema (Reference)
Generated json
{
  "additionalProperties": false,
  "properties": {
    "uncleared_checks": {
      "description": "Specifically \"uncleared checks and payments AS OF mm/dd/yyyy\" or \"Outstanding Checks/Vouchers\" only. If not specified, assume [].",
      "items": {
        "additionalProperties": false,
        "properties": {
          "date": {
            "description": "ISO formatted date (YYYY-MM-DD).",
            "type": "string"
          },
          "description": {
            "description": "Comprehensive transaction description (Type, Ref No, Payee/Name).",
            "type": "string"
          },
          "amount": {
            "description": "Transaction amount as a string, with negative sign if applicable.",
            "type": "string"
          },
          "ref no": {
            "description": "Reference number, REF NO., or document number.",
            "type": "string"
          },
          "payee": {
            "description": "Payee, Name, or Memo.",
            "type": "string"
          }
        },
        "required": ["date", "description", "amount", "ref no", "payee"],
        "type": "object"
      },
      "type": "array"
    },
    "uncleared_deposits": {
      "description": "Specifically \"uncleared deposit and other credits as of mm/dd/yyyy\" or \"Outstanding Other Cash Items\" only. If not specified, assume [].",
      "items": {
        "additionalProperties": false,
        "properties": {
          "date": { "type": "string" },
          "description": { "type": "string" },
          "amount": { "type": "string" },
          "ref no": { "type": "string" },
          "payee": { "type": "string" }
        },
        "required": ["date", "description", "amount", "ref no", "payee"],
        "type": "object"
      },
      "type": "array"
    },
    "suspense_items": {
      "description": "Specifically \"Outstanding Suspense Items\" only. If not specified, assume [].",
      "items": {
        "additionalProperties": false,
        "properties": {
          "date": { "type": "string" },
          "description": { "type": "string" },
          "amount": { "type": "string" },
          "Item Number": { "type": "string" }
        },
        "required": ["date", "description", "amount", "Item Number"],
        "type": "object"
      },
      "type": "array"
    },
    "total_0": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "description": "total of all items amount value from \"uncleared_checks\" if not specified assume 0"
    },
     "tota_1": {
      "description": "total of all items amount value from \"uncleared_deposits array\" if not specified assume 0",
      "type": "string"
    },
    "total_2": {
      "description": "total of all items amount value from \"suspense_items array\" if not specified assume 0",
      "type": "string"
    }
  },
  "required": ["uncleared_checks", "uncleared_deposits", "suspense_items", "total_0", "tota_1", "total_2"],
  "type": "object"
}

"""

    response = model.generate_content([prompt, file], stream=False)
    text = response.text.strip()

    # Remove Markdown wrappers if Gemini includes them
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    
    try:
        parsed = json.loads(text)
        print("✅ Extracted JSON:")
        print(json.dumps(parsed, indent=2))
        with open ("data.json","w")as f:
            json.dump(parsed, f,indent=2)
            print("json file saved")

        return parsed
    except json.JSONDecodeError as e:
        print("❌ JSON Parsing Error:", e)
        print("🔴 Raw response:")
        print(text)
        return None

# # STEP 5: Main logic
# if __name__ == "__main__":
#     pdf_path = "/home/nova/projects/reconsiliation_project/bank_rec_api2/output_folder/10200.1 June_enhanced.pdf"  # ⬅️ Replace with your PDF path
#     file = upload_pdf_to_gemini(pdf_path)
    
#     if file:
#         final_result = query_with_file(file)