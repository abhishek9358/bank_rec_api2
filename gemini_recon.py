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
You are an expert financial data extraction AI. Your primary goal is to meticulously extract specific financial transactions from the provided document text and structure them perfectly according to the JSON schema below. Accuracy and completeness are paramount.

**Your Process:**

1.  **Identify Target Sections:** Carefully scan the entire document for headers that EXACTLY match or are VERY CLOSE VARIATIONS of:
    *   For `uncleared_checks`: "uncleared checks and payments AS OF mm/dd/yyyy" or "Outstanding Checks/Vouchers".
    *   For `uncleared_deposits`: "uncleared deposit and other credits as of mm/dd/yyyy" or "Outstanding Other Cash Items".
    *   For `suspense_items`: "Outstanding Suspense Items".

2.  **Extract ALL Line Items Within Each Section:**
    *   Once a target section is identified, you MUST extract **every single line item** listed under that section's header.
    *   Continue extracting items for that section until you encounter:
        *   A "Total" line that clearly corresponds to *that specific list of items*.
        *   The beginning of a new, different target section header.
        *   A clear and definitive end to the list of transactions for that section.
    *   **Do not stop prematurely.** Even if an item seems slightly different (e.g., "Receive Payment" vs. "Deposit"), if it's listed as a line item within that section before its subtotal, it must be extracted.
    *   If a target section header is not found, the corresponding array in the JSON should be empty (`[]`).

3.  **Populate Item Details Correctly:** For each extracted line item:
    *   `date`: Extract the transaction date from the line item itself and format it as an ISO date (YYYY-MM-DD).
    *   `description`: Create a comprehensive transaction description. This should include:
        *   The type of transaction if specified on the line (e.g., "Check", "Deposit", "Journal", "Receive Payment").
        *   Any reference number (e.g., check number, REF NO.).
        *   The payee, payor, or memo details.
        *   Combine these elements into a clear, descriptive string.
       *   `amount`: Extract the transaction amount as a string. Crucially, **include negative signs** for payments/checks (e.g., "-167.75") and positive (or no sign initially, but ensure it's a string representation of a positive number) for deposits/credits.


4. - Don't be take a uncleared_checks after, uncleared_deposits after, so don.t take a "after" section entries only take a "as of" section entries.

5.  **Calculate Totals:**
    *   `total_0`: This is the total of all 'amount' values from the `uncleared_checks` array.
    *   `tota_1`: This is the total of all 'amount' values from the `uncleared_deposits` array.
    *   `total_2`: This is the total of all 'amount' values from the `suspense_items` array.
    *   If a document **explicitly states a "Total" amount for one of these specific lists**, use that stated total as a string.
    *   If an array is empty, or no explicit total is given for that list and items exist, you should calculate the sum. If the array is empty and no total is given, the total should be "0".
    *   Ensure all total fields are strings.

6.  **Output Format:**
    *   Your final output MUST be a single, valid JSON object that strictly adheres to the provided schema.
    *   Do not include any conversational text, explanations, apologies, or markdown formatting (like ```json) before or after the JSON object.

7.  **Extract ALL Line Items Within Each Section:**
    *   When you identify a target section header (e.g., "Uncleared checks and payments as of 12/31/2022"):
        *   **Scan line by line beneath this header.**
        *   **For each line that appears to be a transaction item:** Extract its details (date, description, amount).
        *   **Continue this scanning process** until you clearly reach the "Total" for this specific list of uncleared checks/payments, or until a new major section header (like "Uncleared deposits") begins.
        *   Do not assume a section ends after finding just one item if more line items follow before a clear section terminator.
    *   For instance, if under "in the targetted section" there's an item dated 05/01/2022 and THEN another item dated 08/31/2022 before the 'Total' line for that section, BOTH items must be extracted individually.

    
8.  **CRITICAL INSTRUCTION FOR SCHEMA ADHERENCE:**
        Your final JSON output MUST strictly follow the schema definitions.
        *   For `uncleared_checks`, ONLY include items explicitly found under headers like "uncleared checks and payments AS OF mm/dd/yyyy" or "Outstanding Checks/Vouchers".
        *   For `uncleared_deposits`, ONLY include items explicitly found under headers like "uncleared deposit and other credits as of mm/dd/yyyy" or "Outstanding Other Cash Items".
        *   For `suspense_items`, ONLY include items explicitly found under "Outstanding Suspense Items".

  **EXCLUDE ALL OTHER ITEMS:** If items are listed under different headers, such as "Deposits and other credits CLEARED" or "Checks and payments CLEARED", they DO NOT BELONG in the `uncleared_checks`, `uncleared_deposits`, or `suspense_items` arrays. In such cases, these arrays in your output JSON should be empty (`[]`) unless a section with the exact "uncleared" or "outstanding" phrasing is also present.

9. **Extract EVERY SINGLE Line Item Within Each Identified Section:**
    *   Once a target section is identified (e.g., "Outstanding Checks/Vouchers"), your primary task is to list **EVERY INDIVIDUAL TRANSACTION LINE ITEM** found under that header.
    *   **DO NOT SUMMARIZE OR TRUNCATE THE LIST OF ITEMS.** Even if the list is long, each distinct line representing a check, voucher, deposit, or cash item must be extracted as a separate object in the relevant JSON array.
    *   Scan line by line directly beneath the identified section header. For each line that represents a distinct transaction:
        *   `date`: Extract the transaction date (Document Date) and format it as YYYY-MM-DD.
        *   `description`: Create a comprehensive description. Include the Document Number (if present), the full Document Description from the document, and the Payee. Example: "Document 45066 System Generated Check/Voucher Grays Harbor PUD".
        *   `amount`: Extract the Document Amount as a string. **Crucially, if the amount is shown in parentheses like (54.40), it represents a negative value and MUST be extracted as a negative string, e.g., "-54.40". Otherwise, extract as a positive string.**
    *   Continue extracting individual line items until you reach the explicitly stated "Total" line for *that specific section* (e.g., "Outstanding Checks/Vouchers 34,475.14") or a new major section header.
    
1.  **Identify Target Sections:** Carefully scan the **entire document text** for headers that EXACTLY match or are VERY CLOSE VARIATIONS of:
    *   For `uncleared_checks`: "Uncleared checks and payments as of 12/31/2023" (or similar date).
    *   For `uncleared_deposits`: "Uncleared deposits and other credits as of 12/31/2023" (or similar date).
    *   For `suspense_items`: "Outstanding Suspense Items" (if present).

2.  **Extract EVERY SINGLE Line Item Within Each Identified Section (Across Pages):**
    *   Once a target section is identified (e.g., "Uncleared checks and payments as of 12/31/2023"), your primary task is to list **EVERY INDIVIDUAL TRANSACTION LINE ITEM** found under that header.
    *   **IMPORTANT FOR MULTI-PAGE DOCUMENTS:** If a list of items for a section (e.g., "Uncleared checks and payments") starts on one page and appears to continue onto the next page (e.g., more line items before a "Total" or a new major section header), you MUST continue to scan and extract these items from the subsequent page(s) and include them in the same array. **Do not prematurely conclude a section at a page break if the content logically continues.**
    *   For example, if "Uncleared checks and payments as of 12/31/2023" lists some items, then there's a page break, and then more items like "Bill Payment 4067 Department of Justice" and "Expense Hawaii Employers Mutual Ins." appear before the "Total" for that section, ALL of these items must be included in the `uncleared_checks` array.
    *   Scan line by line directly beneath the identified section header. For each line that represents a distinct transaction:
        *   `date`: Extract the transaction date and format it as YYYY-MM-DD.
        *   `description`: Create a comprehensive description including TYPE, REF NO. (if present), and PAYEE.
        *   `amount`: Extract the transaction amount as a string, ensuring negative signs are included where appropriate.
    *   Continue extracting individual line items until you reach the explicitly stated "Total" line for *that specific section* (e.g., "Total -2,086.60" for uncleared checks) or a new major section header.


10. Don't be take a "Checks and payments cleared"  , "Deposits and other credits cleared", so don.t take a "after" section entries only take a "as of" section entries. if only these section are only avalaible in the document so pass the "0". "But ensure that not provide these sections entry in any condition".
    **JSON Schema:**
{
  "additionalProperties": false,
  "properties": {
    "uncleared_checks": {
      "description": "Specifically \"uncleared checks and payments AS OF mm/dd/yyyy\" or \"Outstanding Checks/Vouchers\" only if keys don't match assume [], if not specified, assume []",
      "items": {
        "additionalProperties": false,
        "properties": {
          "date": { "description": "ISO formatted date", "type": "string" },
          "description": { "description": "transaction description", "type": "string" },
          "amount": { "description": "transaction amount", "type": "string" }bu
        },
        "required": ["date", "description", "amount"],
        "type": "object"
      },
      "type": "array"
    },
    "uncleared_deposits": {
      "description": "Specifically \"uncleared deposit and \n other credits as of mm/dd/yyyy\" or \"Outstanding Other Cash Items\" only if not specified, assume []",
      "items": {
        "additionalProperties": false,
        "properties": {
          "date": { "description": "ISO formatted date", "type": "string" },
          "description": { "description": "transaction description", "type": "string" },
          "amount": { "description": "transaction amount", "type": "string" }
        },
        "required": ["date", "description", "amount"],
        "type": "object"
      },
      "type": "array"
    },
    "suspense_items": {
      "description": "Specifically \"Outstanding Suspense Items\" only if not specified, assume []",
      "items": {
        "additionalProperties": false,
        "properties": {
          "date": { "description": "ISO formatted date", "type": "string" },
          "description": { "description": "transaction description", "type": "string" },
          "amount": { "description": "transaction amount", "type": "string" }
        },
        "required": ["date", "description", "amount"],
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
  "required": [
    "uncleared_checks",
    "uncleared_deposits",
    "suspense_items",
    "total_0",
    "tota_1",
    "total_2"
  ],
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