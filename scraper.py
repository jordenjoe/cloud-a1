import pandas as pd
import os
import boto3
import json
from decimal import Decimal
import requests
import time

url = "https://api.yelp.com/v3/businesses/search"
client_id = "f6rRpZLDe1hdas4GH5Bpaw"
key = "wPFEOjLaxx9SYzF1h3oAu7Qn95rRjushwAthUpQ4J4vYYjadsAoo_Ql7_0GNqVy0FibR7DeUpgf5UzzSoMMYi1FRI-d0jxRLIu1zIiO4J6xnL3S-qVYPrq-VEf08Y3Yx"

headers = {
    'Authorization': 'Bearer %s' % key
}

# dataset_folder="homework/hw1/yelp_dataset"
key_file=pd.read_csv("homework/Hikaru_Ikebe_accessKeys.csv") 
MY_ACCESS_KEY_ID = key_file['Access key ID'] #AWS Access key
MY_SECRET_ACCESS_KEY = key_file['Secret access key'] #AWS secret key

resource = boto3.resource('dynamodb')

parameters = {
    'location': 'Manhattan',
    'categories': 'newamerican, [NO, US, SE, DK, IE, GB]',
    'limit': 50
}

cuisines = [
    'newamerican, [NO, US, SE, DK, IE, GB]',
    'breakfast_brunch, All',
    'burgers, All',
    'cafes, [AT, AU, BE, BR, CA, CH, CL, CZ, DE, DK, FR, GB, HK, IE, IT, JP, MY, NL, NO, NZ, PH, PL, PT, SE, SG, TR, TW, US]',
    'chinese, All',
    'delis, [AR, AT, AU, BR, CA, CH, CZ, DE, DK, ES, FI, GB, HK, IE, JP, MX, MY, NO, NZ, PH, PL, SG, TR, TW, US]',
    'italian, All',
    'japanese, All',
    'mexican, All',
    'pizza, All',
    'sandwiches, All',
    'seafood, All']

table_name = 'yelp-manhattan'
table = resource.Table(table_name)
response = requests.get(url, headers=headers, params=parameters)
json_response = response.json()

list_float=[]
for key,value in json_response['businesses'][0].items():
    if isinstance(value,float):
        list_float.append(key)
    elif isinstance(value,dict):
        while isinstance(value,dict):
            for key,value in value.items():
                if isinstance(value,float):
                    list_float.append(key)

item_count = 0
def convert_floats(item,list_float=list_float):
    for var in item:
        if var in list_float:
            item[var]=Decimal(str(item[var]))
    item['coordinates']['latitude']=Decimal(str(item[var]))
    item['coordinates']['longitude']=Decimal(str(item[var]))
    item['insertedAtTimestamp']=Decimal(str(item[var]))

    return item

total = response.json()['total']
offset = 0

timestamp = time.time()
for cuisine in cuisines:
    parameters['categories'] = cuisine
    response = requests.get(url, headers=headers, params=parameters)
    total = response.json()['total']
    item_count += min(total, 1000)
    offset = 0

    print(cuisine.split(',')[0], ", total: ", total)
    while offset < total + 50 and offset <= 950:
        parameters['offset'] = offset
        response = requests.get(url, headers=headers, params=parameters)

        json_response = response.json()
        with table.batch_writer() as batch:
            for item in json_response['businesses']:
                item['insertedAtTimestamp'] = timestamp
                batch.put_item(Item=convert_floats(item))
        print("Number of items in the",table_name,"table:",len(table.scan()['Items']))
        print(offset)
        offset += 50

cuisines_list = [
    'newamerican',
    'breakfast_brunch',
    'burgers',
    'cafes',
    'chinese',
    'delis',
    'italian',
    'japanese',
    'mexican',
    'pizza',
    'sandwiches',
    'seafood']

# def get_cuisine(categories):
#     for category in categories:
#         if category['alias'] in cuisines_list:
#             return category['alias']
#     return ''

# print("Item count: ", item_count)

# response = table.scan()
# restaurants_data = response['Items']

# while 'LastEvaluatedKey' in response:
#     response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
#     restaurants_data.extend(response['Items'])

# for i, restaurant in enumerate(restaurants_data):
#     counter = i + 1
#     id = restaurant['id']
#     cuisine = get_cuisine(restaurant['categories'])
    
#     indexDict = {"index": {"_index": "restaurants", "_id": counter}}
#     bodyDict = {"RestaurantID": id, "Cuisine": cuisine}

#     with open("restaurants.json", "a") as outfile:
#         json.dump(indexDict, outfile)
#         outfile.write('\n')
#         json.dump(bodyDict, outfile)
#         outfile.write('\n')

