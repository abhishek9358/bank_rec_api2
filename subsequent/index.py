
from subsequent.sub_pr import SubSequentResponse
from subsequent._pdfextract import Subsequent_Extractor


async def HandleSubSequent(fiscal_date, pdf_path):
    # Subsequent_Extractor(pdf_path)
    # md_path = "output/sub.md"

    response = await SubSequentResponse(pdf_path) 
    # response = []

    return response
    




    