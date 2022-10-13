import json
import boto3

    
def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response
    
def dispatch(intent_request):
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    """
    Called when the user specifies an intent for this bot.
    """
    client = boto3.client("sqs")
    response = client.send_message(
    QueueUrl="https://sqs.us-east-1.amazonaws.com/828815413195/Q1",
    MessageBody=json.dumps(intent_request['currentIntent']['slots'])
    )
    #sometimes in this format?
    #MessageBody=json.dumps(intent_request['slots'])
    
    return close(session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, expect an email soon.'
        }
    )


def lambda_handler(event, context):
    print('event: ', event)
        
    return dispatch(event)
    