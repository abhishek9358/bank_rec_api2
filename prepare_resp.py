import json
import os



def HandleJsonForResp(json_path):
    try:
        print("hi")
        final_resp: dict = {}
        with open("data.json", 'r') as f:
            content = f.read()

        jsn: dict = json.loads(content)

        for item in jsn.items():

            if item[1] == [None]:
                 continue
            # print(item[1], "pringint")
            
            if item[0] == "uncleared_checks":
                child_items = []
                if item[1] == None: continue
                for child_values in item[1]:
                    child_items.append({
                        "date": child_values['date'],
                        "type": child_values['description'],
                        "amount": child_values['amount']
                    })
                final_resp["Uncleared Checks and Payments"] =  child_items
             
            if item[0] == "uncleared_deposits":
                    child_items = []
                    if item[1] == None: continue
                    for child_values in item[1]:
                        child_items.append({
                            "date": child_values['date'],
                            "type": child_values['description'],
                            "amount": child_values['amount']
                        })
                    final_resp["Uncleared Deposits and Credits"] =  child_items

                    
            
            

            if item[0] == "suspense_items":
                    child_items = []
                    if item[1] == None: continue
                    for child_values in item[1]:
                        child_items.append({
                            "date": child_values['date'],
                            "type": child_values['description'],
                            "amount": child_values['amount']
                            
                        })
                    final_resp["Outstanding Suspense Items"] =  child_items        
            if item[0] == "total_0":
                 final_resp["total"] =  item[1]

            if item[0] == "tota_1":
                 final_resp["total_1"] =  item[1]

            if item[0] == "total_2":
                 final_resp["total_2"] =  item[1]          
                 
        print(final_resp)
        os.remove('data.json') 

        return final_resp
    except Exception as err:
        print("something went wrong in the process", err)