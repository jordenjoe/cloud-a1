"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'BookTrip' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import datetime
import time
import os
import dateutil.parser
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


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


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n

def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


def isvalid_city(city):
    valid_cities = ['new york', 'nyc', 'new york city', 'manhattan', 'queens', 'staten island', 'brooklyn']
    return city.lower() in valid_cities


def isvalid_date(date):
    try:
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return False
        return True
    except ValueError:
        return False
        
def isvalid_time(date, time):
    #print('date 1: ', datetime.datetime.strptime(time, "%H:%M:%S") )
    #print('date 2: ', datetime.datetime.now().time())
    try:
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() == datetime.date.today():
            if datetime.datetime.strptime(time, "%H:%M").time() < datetime.datetime.now().time():
                return False
        return True
    except ValueError:
        return False
        
def isvalid_cuisine(cuisine):
    valid_cuisines = ['new american', 'breakfast', 'brunch', 'burgers', 'cafe', 'chinese', 'delis', 'italian', 'japanese', 'mexican', 'pizza', 'sandwiches', 'seafood']
    return cuisine.lower() in valid_cuisines

def get_day_difference(later_date, earlier_date):
    later_datetime = dateutil.parser.parse(later_date).date()
    earlier_datetime = dateutil.parser.parse(earlier_date).date()
    return abs(later_datetime - earlier_datetime).days

def add_days(date, number_of_days):
    new_date = dateutil.parser.parse(date).date()
    new_date += datetime.timedelta(days=number_of_days)
    return new_date.strftime('%Y-%m-%d')

def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }



""" --- Functions that control the bot's behavior --- """

def validate(slots, inputTranscript):
    
    date = try_ex(lambda: slots['Date'])
    location = try_ex(lambda: slots['Location'])
    cuisine = try_ex(lambda: slots['Cuisine'])
    num_people = try_ex(lambda: slots['NumPeople'])
    time =  try_ex(lambda: slots['Time'])

    if location and not isvalid_city(location):
        return build_validation_result(
            False,
            'Location',
            'We currently do not support {} as a valid destination. For now, this app is NYC based only.  Can you try a different city?'.format(location)
        )
        
    if cuisine and not isvalid_cuisine(cuisine):
        return build_validation_result(
            False,
            'Cuisine',
            'We currently do not support that cuisine. Can you try a different type of restaurant?'
        )
       
    if num_people: 
        if int(num_people) > 6:
            return build_validation_result(False, 'NumPeople', 'We currently require groups less than 7. Can you enter a new amount?')
        elif int(num_people) < 1:
            return build_validation_result(False, 'NumPeople', 'Please enter at least one person.')
    
    if date:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'You cannot choose a date in the past.  Can you try a different date?')        
    
    if time:
        if inputTranscript[0] == '-':
            return build_validation_result(False, 'Time', 'You cannot choose a negative time. Can you try a different time?')

        if not isvalid_time(date, time):
            return build_validation_result(False, 'Time', 'You cannot choose a time in the past or very close to the current time for today.  Can you try a different time?')
    #if date and datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
    #        return build_validation_result(False, 'Date', 'Reservations must be scheduled at least one day in advance.  Can you try a different date?')
    
    return {'isValid': True}


def validate_suggestions(intent_request):
    location = try_ex(lambda: intent_request['currentIntent']['slots']['Location'])
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate(intent_request['currentIntent']['slots'], intent_request['inputTranscript'])
        if not validation_result['isValid']:
            
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None
    
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

    # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.  Pass price
    # back in sessionAttributes once it can be calculated; otherwise clear any setting from sessionAttributes.

    return delegate(session_attributes, intent_request['currentIntent']['slots'])



# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    #if intent_name == 'BookHotel':
    #    return book_hotel(intent_request)
    #elif intent_name == 'BookCar':
    #    return book_car(intent_request)
    if intent_name == 'DiningSuggestionsIntent':
        return validate_suggestions(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    print('event: ', event)
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
