import boto3
import json
import requests
import datetime
from requests_aws4auth import AWS4Auth

# Reference: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/search-example.html
# Reference: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

CUISINE = "Cuisine"
DATE = "Date"
TIME = "Time"
LOCATION = "Location"
NUM_PEOPLE = "NumPeople"
EMAIL = "Email"
TABLE_NAME = 'yelp-restaurants'
FROM_EMAIL = 'hikaru.ikebe@columbia.edu'

region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://search-restaurants-mwx5jjcfnqlgrhefflocrkhoe4.us-east-1.es.amazonaws.com' 
index = 'restaurants'
url = host + '/' + index + '/_search'

def retrieveSQSMessage():
    import boto3

    # Create SQS client
    sqs = boto3.client('sqs')

    queue_url = 'https://sqs.us-east-1.amazonaws.com/828815413195/Q1'

    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        # AttributeNames=[
        #     'SentTimestamp'
        # ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    print(f"Number of messages received: {len(response.get('Messages', []))}")

    entries = []
    for message in response.get("Messages", []):
        message_body = message["Body"]
        # print(f"Message body: {json.loads(message_body)}")
        # print(f"Receipt Handle: {message['ReceiptHandle']}")

        # Delete received message from queue
        # sqs.delete_message(
        #     QueueUrl=queue_url,
        #     ReceiptHandle=message['ReceiptHandle']
        # )

        entries.append({'Id': message['MessageId'], 'ReceiptHandle': message['ReceiptHandle']})
    
    response = sqs.delete_message_batch(
        QueueUrl = queue_url,
        Entries = entries
    )
    print(f"Successfully deleted {len(response['Successful'])} entries.")

    return response.get("Messages", [])

def opensearchQuery(cuisine):
    query = {
        "size": 3,
        "query": {
            "multi_match": {
                "query": cuisine
            }
        }
    }
    
    headers = { "Content-Type": "application/json" }

    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    response['body'] = r.text
    return response
    
def getRestaurantInfo(restaurantId):
    client = boto3.client('dynamodb')
    restaurantName = client.get_item(
        TableName=TABLE_NAME,
        Key={
            'id': {'S': restaurantId}
        }
    )
    
    return restaurantName
    
def parseRestaurantInfo(requests, restaurantInfos):
    cuisine = requests.get('cuisine').capitalize()

    message = f"Hello! Here are my {cuisine} restaurant suggestions for {requests.get('numOfPeople')} people, for {requests.get('date')} at {requests.get('time')}: "

    counter = 1
    for restaurantInfo in restaurantInfos:
        item = restaurantInfo['Item']
        location = item['location']
        address = [s['S'] for s in location['M']['display_address']['L']][0]
        name = item['name']['S']
    
        message += f"{counter}. {name}, located at {address}"
        if counter != len(restaurantInfos):
            message += ", "
        else:
            message += ". Enjoy your meal!"

        counter += 1

    return message    

def sendSES(email, message, cuisine):
    from_email = FROM_EMAIL
    # config_set_name = os.environ["SES_CONFIG_SET_NAME"]
    client = boto3.client('ses')

    body_html = f"""<html>
        <head></head>
        <body>
          <p>{message}</p> 
        </body>
        </html>
                    """

    email_message = {
        'Body': {
            'Html': {
                'Charset': 'utf-8',
                'Data': body_html,
            },
        },
        'Subject': {
            'Charset': 'utf-8',
            'Data': f"{cuisine.capitalize()} Restaurant Recommendations!",
        },
    }

    ses_response = client.send_email(
        Destination={
            'ToAddresses': [email],
        },
        Message=email_message,
        Source=from_email,
        # ConfigurationSetName=config_set_name,
    )

    return ses_response
    
# Lambda execution starts here
def lambda_handler(event, context):
    # messages = retrieveSQSMessage()
    messages = [json.loads(x['body']) for x in event['Records']]
    
    for message in messages:
        body = message
        requests = {}
        requests['cuisine'] = body[CUISINE].lower()
        if requests.get('cuisine') == "new american":
            requests['cuisine'] = "newamerican"
            
        requests['date'] = body[DATE]
        requests['time'] = body[TIME]
        requests['location'] = body[LOCATION]
        requests['numOfPeople'] = body[NUM_PEOPLE]
        requests['email'] = body[EMAIL]
        print(requests)
    
        response = opensearchQuery(requests.get('cuisine'))
        hits = json.loads(response['body'])
        
        restaurantInfos = []
        for hit in hits['hits']['hits']:
            restaurantId = hit['_source']['RestaurantID']        
            restaurantInfos.append(getRestaurantInfo(restaurantId))

        message = parseRestaurantInfo(requests, restaurantInfos)
        ses_response = sendSES(requests.get('email'), message, requests.get('cuisine'))
        # print(ses_response)