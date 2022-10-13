import boto3

# Define the client to interact with Lex
client = boto3.client('lex-runtime')

def lambda_handler(event, context):
    
    print('event: ', event)
    userInput = event['messages'][0]['unstructured']['text']
    
    print(f"Message from frontend: {userInput}")

    client = boto3.client('lex-runtime')

    response = client.post_text(
                    botName='RestaurantRecommender',
                    botAlias='RestaurantRecommender',
                    userId='testuser',
                    sessionAttributes={
                    },
                    requestAttributes={
                    },
                    inputText= userInput
    )

    #Initiate conversation with Lex
    #Update botId, botAlisId and sessionId
    # response = client.recognize_text(botId='XIZSRO7VBJ',
    #                             botAliasId='GE3AQDBHK3',
    #                             localeId='en_US',
    #                             sessionId='testuser',
    #                             text=msg_from_user)
            

    
    #print('response: ', response)
    msg_from_lex = response['message']
    #print('msg_from_lex: ',msg_from_lex)
    if msg_from_lex:

        resp = {
            'statusCode': 200,
            'body': msg_from_lex
        }

        # modify resp to send back the next question Lex would ask from the user
        
        # format resp in a way that is understood by the frontend
        # HINT: refer to function insertMessage() in chat.js that you uploaded
        # to the S3 bucket
        return resp
