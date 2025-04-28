
import re
import spacy
from datetime import datetime
from dateutil.parser import parse
import fitz


nlp = spacy.load("en_core_web_sm")

valid_types = ['check', 'journal', 'bill payment', 'deposit','receive payment']

def Convert_ISO_to_DateString(date_string):
    match = re.match(r"(\d{2})/(\d{2})/(\d{4})", date_string)
    if match:
        month, day, year = map(int, match.groups())
        new_date = datetime(year, month, day).strftime("%B %d, %Y")
        return new_date
    return None


def Is_Valid_Date(date_string):
    if re.match(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$', date_string) or re.match(r'\d{4}-\d{2}-\d{2}', date_string):
        try:
            parse(date_string, fuzzy=False)
            return True
        except ValueError:
            return False
    else:
        return False




def Is_Valid_Fin_Number(number_string):
    number_string = number_string.replace(",", "")
    pattern = r'^-?(?:\$)?(?:\d{1,3}(?:,\d{3})*|\d+)\.\d{2}$'
    
    if re.match(pattern, number_string):
        try:
            float(number_string)
            return True
        except ValueError:
            return False
    return False


def Is_Valid_balance(number_string):
    number_string = number_string.replace(",", "")
    pattern = r'^-?(?:\$)?(?:\d{1,3}(?:,\d{3})*|\d+)\.\d{2}$'
    
    if re.match(pattern, number_string):
        try:
            float(number_string)
            return True
        except ValueError:
            return False
    return False


def Is_Real_Name(text):
    doc = nlp(text)
    person_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    if "," in text:
        parts = text.split(",")
        if len(parts) == 2 and parts[0].istitle() and parts[1].istitle():
            person_names.append(text.strip())
            return True
    return False



def Is_Valid_Type(text):
    
    try:
        txt = text.lower()
        for valid in valid_types:
            if valid in txt:
                return True
    except:
        return False
    

def extract_memo_from_table(table_rows):
    
    def clean_memo(text):
        if not text:
            return ""
        return text.replace("<br>", " ").replace("<br/>", " ").replace("\n", " ").strip()

    memo_list = []
    for row in table_rows:
        if len(row) >= 2:
            memo = clean_memo(row[1])
            memo_list.append(memo)
        else:
            memo_list.append("")
    
    return memo_list
def extract_name_from_table(table_rows):
    
    def clean_name(text):
        if not text:
            return ""
        return text.replace("<br>", " ").replace("<br/>", " ").replace("\n", " ").strip()

    name_list = []
    for row in table_rows:
        if len(row) >= 1:
            name = clean_name(row[0])
            name_list.append(name)
        else:
            name_list.append("")
    
    return name_list

def extract_check_no_from_table(table_rows):
    """
    Extracts the 'Check no.' field from table rows.
    """
    check_no_list = []
    for row in table_rows:
        check_no = row[3] if len(row) > 3 else ""
        check_no_list.append(check_no.strip() if check_no else "")
    return check_no_list

def extract_cleared_from_table(table_rows):
    """
    Extracts and cleans the 'Cleared' field (removes commas, trims whitespace).
    """
    cleared_list = []
    for row in table_rows:
        cleared = row[4] if len(row) > 4 else ""
        if cleared:
            cleared = cleared.replace(",", "").strip()
        cleared_list.append(cleared if cleared else "")
    return cleared_list


def extract_outstanding_from_table(table_rows):
    """
    Extracts and cleans the 'Outstanding' field (removes commas, trims whitespace).
    """
    outstanding_list = []
    for row in table_rows:
        outstanding = row[5] if len(row) > 5 else ""
        if outstanding:
            outstanding = outstanding.replace(",", "").strip()
        outstanding_list.append(outstanding if outstanding else "")
    return outstanding_list



def images_to_pdf(image_paths, output_pdf_path):
    doc = fitz.open()

    for img_path in image_paths:
        img = fitz.open(img_path) 
        rect = img[0].rect        
        pdf_bytes = img.convert_to_pdf()  
        img_pdf = fitz.open("pdf", pdf_bytes)
        doc.insert_pdf(img_pdf) 

    doc.save(output_pdf_path)
    doc.close()




def Is_ValidDate(date_string):
    """Validate if a string is a valid date."""
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_string) or re.match(r'\d{4}-\d{2}-\d{2}', date_string):
        try:
            parse(date_string, fuzzy=False)
            return True
        except ValueError:
            return False
    return False


def Is_Valid_Transaction_Type(type_string):
    """Validate common transaction types like 'Check' or 'Bill Payment'."""
    valid_types = ['Bill Payment', 'Check', 'Deposit', 'Withdrawal', 'Transfer']
    return type_string.strip() in valid_types


def Is_Valid_Ref_No(ref_string):
    """Validate if the reference number is a valid integer-like string."""
    return bool(re.match(r'^\d{1,6}$', ref_string.strip()))


def Is_Valid_Payee(payee_string):
    """Validate payee name, ensuring it's not a financial amount."""
    if not payee_string.strip():
        return False
    # Check if it accidentally contains a financial number
    if Is_Valid_Fin_Number(payee_string.strip().replace(",", "")):
        return False
    return True

    if not payee_string.strip():
        return False

def Is_Valid_FinNumber(number_string):
    number_string = number_string.replace(",", "").replace("$", "")
    pattern = r'^-?\d+\.\d{2}$'
    
    if re.match(pattern, number_string):
        try:
            float(number_string)
            return True
        except ValueError:
            return False
    return False