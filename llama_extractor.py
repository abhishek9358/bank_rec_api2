from llama_cloud_services import LlamaExtract
from dotenv import load_dotenv
load_dotenv()
import json
import os 

llama_api_key = os.getenv("llama_api_key")
extractor = LlamaExtract(api_key=llama_api_key) #yha per bhi api keys pass kr skte h ya randon koi ek api key ya muiltple keys me se koi ek


def HandleLlamaExtract(pdf_path):
    try:
        agent = extractor.get_agent("extract-all") # change kr lena isko job name ho agent ka 
        list_items = agent.list_extraction_runs()

        if len(list_items.items) > 0:
            for ids in list_items.items:
                agent.delete_extraction_run(ids.id) # removing all caches

        result = agent.extract(pdf_path)


       

        with open("data.json", 'w') as _file:
            json.dump(result.data, _file) # type: ignore

        print(result.data)    

        return result.data # type: ignore
    except Exception as error:
        print("error in llama extract", error)
        return []

