import json
import pytz
import requests
import sys

from datetime import date, datetime, timedelta

# This is a basic demonstration on how to obtain an OAuth token then
# schedule & cancel a package pickup with the FedEx API.
# Change the code in main() depending on what you want to do.
# For Python 3. Tested in 3.6.9.
#
# This uses the sandbox API by default. You should use sandbox first to test.
# Uncomment the production API in the functions to use production.
#
# Please read the FedEx documentation!
# https://developer.fedex.com/api/en-us/catalog/pickup/v1/docs.html
#
# This script equires an OAuth token. See the OAuth example in this same repo.
#
# This software is neither created nor endorsed by FedEx.
# Use at your own risk.
# https://github.com/av1d/FedEx_API_examples_Python





#####################
###  USER SETTINGS
#####################

client_id     = ''
client_secret = ''

WORK_IN_SANDBOX = True  # change to False for production

### Pickup Information

# The time window you want the package(s) picked up tomorrow, in 24 hour time,
# your local time. Will be converted to the appropriate UTC time.
pickup_from      = '9'   # from 9 AM
pickup_to        = '18'  # to 6 PM
instructions     = 'down driveway near chairs'  # package location instructions
remarks          = 'please ring doorbell'
carrier_code     = 'FDXG'  # FedEx Ground. Use FDXE for FedEx Express.
package_count    = 1
package_weight   = 20  # weight is in LBs
package_location = 'REAR'
# The only possible locations:
#   FRONT
#   NONE
#   REAR
#   SIDE


### Sender info

# NOTE: if you are testing in the sandbox, you must use the sandbox account 
# number.You can find it under "My Projects" on the left-hand menu,
# then click your project.
account_number   = ''  # your 9-digit account number.
shippers_name    = 'test subject'
phone            = '6175553845'
street           = ''
city             = ''
state            = ''
postal_code      = ''  # 5-digit US postal code
country          = 'US'
residential      = 'true'  # false for biz


### notifications:
email_address    = 'someone@somewhere.ok'
email_message    = 'Your package has been picked up.'

############################
###  END OF USER SETTINGS
############################



# generate the appropriate timestamp from the given time window
def generate_pickup_date(time_string, from_or_to):

    # Check if Friday or Saturday as the pickups can only be made for weekdays
    today       = date.today()
    is_friday   = (today.weekday() == 4)  # Monday is 0, therefore Friday is 4.
    is_saturday = (today.weekday() == 5)

    # Add days to today's date
    if is_friday:
        tomorrow = datetime.now() + timedelta(days=3)  # pick up Monday
    elif is_saturday:
        tomorrow = datetime.now() + timedelta(days=2)  # pick up Monday
    else:
        tomorrow = datetime.now() + timedelta(days=1)  # add 1 for tomorrow

    # Convert pickup_date to datetime object
    user_datetime = datetime.strptime(time_string, '%H')

    # Combine tomorrow's date with the user input time
    user_datetime = datetime(tomorrow.year, tomorrow.month, tomorrow.day,
                             user_datetime.hour)

    # Convert user's datetime to UTC timezone
    utc = pytz.timezone('UTC')
    user_datetime_utc = user_datetime.astimezone(utc)

    # The final converted datetime in UTC
    try:
        if from_or_to == 'from':
            time_tomorrow = user_datetime_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        if from_or_to == 'to':
            time_tomorrow = user_datetime_utc.strftime('%H:%M:%S')
    except:
        import sys
        sys.exit(1)

    return time_tomorrow



# convert generated timestamp to date only, for use in canceling the pickup
def convert_timestamp(iso_timestamp):

    datetime_object = datetime.strptime(iso_timestamp, '%Y-%m-%dT%H:%M:%SZ')
    formatted_date  = datetime_object.strftime('%Y-%m-%d')

    return formatted_date



def get_oauth_token():

    global client_id
    global client_secret
    global WORK_IN_SANDBOX

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    if WORK_IN_SANDBOX == True:
        url = "https://apis-sandbox.fedex.com/oauth/token"
    else:
        url = "https://apis.fedex.com/oauth/token"  # production

    response = requests.post(url, data=payload)
    res_json = response.json()

    return res_json



def schedule_pickup():

    global	oauth_token
    global	pickup_from
    global	pickup_to
    global	account_number
    global	shippers_name
    global	phone
    global	street
    global	city
    global	state
    global	postal_code
    global	country
    global	residential
    global	package_count
    global	package_weight
    global	package_location
    global	instructions
    global	remarks
    global	carrier_code
    global	email_address
    global	email_message

    global WORK_IN_SANDBOX

    # generate datetime objects
    pickup_from = generate_pickup_date(pickup_from, 'from')
    pickup_to   = generate_pickup_date(pickup_to,     'to')

    # HTTP headers
    headers = {
        'content-type': 'application/json',
        'x-locale': 'en_US',
        'authorization': 'Bearer ' + oauth_token
    }

    # create the JSON object
    data = {
      'associatedAccountNumber': {
        'value': account_number
      },
      'originDetail': {
        'pickupLocation': {
          'contact': {
            'personName': shippers_name,
            'phoneNumber': phone
          },
          'address': {
            'streetLines': [
              street
            ],
            'city': city,
            'stateOrProvinceCode': state,
            'postalCode': postal_code,
            'countryCode': country,
            'residential': 'true'
          },
          'deliveryInstructions': instructions
        },
        'remarks': remarks,
        'pickupNotificationDetail': {
            'emailDetails': [
            {
              'address': email_address,
              'locale': 'en_US'
            }
            ],
            'format': 'HTML',
            'userMessage': email_message
        },
        'totalWeight': {
            'units': 'LB',
            'value': package_weight
        },
        'packageCount': package_count,
        'packageLocation': package_location,
        'readyDateTimestamp': pickup_from,
        'customerCloseTime': pickup_to
      },
      'packageCount': package_count,
      'carrierCode': carrier_code
    }

    if WORK_IN_SANDBOX == True:
        url = 'https://apis-sandbox.fedex.com/pickup/v1/pickups'
    else:
        url = 'https://apis.fedex.com/pickup/v1/pickups'  # production

    response = requests.post(url, json=data, headers=headers)
    res_json = response.json()

    return res_json



def cancel_pickup(confirmation_code, pickup_timestamp):

    global oauth_token
    global account_number
    global pickup_to
    global WORK_IN_SANDBOX

    pickup_timestamp = str(convert_timestamp(pickup_timestamp))  # get date

    headers = {
        'content-type': 'application/json',
        'x-locale': 'en_US',
        'authorization': 'Bearer ' + oauth_token
    }

    data = {
      'associatedAccountNumber': {
        'value': account_number
      },
      'pickupConfirmationCode': confirmation_code,
      'carrierCode': carrier_code,
      'scheduledDate': pickup_timestamp
    }

    if WORK_IN_SANDBOX == True:
        url = 'https://apis-sandbox.fedex.com/pickup/v1/pickups/cancel'
    else:
        url = 'https://apis.fedex.com/pickup/v1/pickups/cancel'  # production

    response = requests.put(url, json=data, headers=headers)
    res_json = response.json()

    return res_json


# basic error handling
def is_error(json_response):

    try:
        errors = json_response['errors']
        print('There was an error. The following was received:\n')
        print(' Transaction ID:', json_response['transactionId'])
        print('Errors Occurred:', 'Please correct the following errors:')
        for error in errors:
            code    = error['code']
            message = error['message']
            print('           Code:', code)
            print('        Message:', message)

        return True

    except:
        return False



def main():

    # obtain OAuth token:
    oauth = get_oauth_token()
    try:
        global oauth_token
        oauth_token  = oauth['access_token']
        token_type   = oauth['token_type']
        expires_in   = oauth['expires_in']
        scope        = oauth['scope']
        print("Access Token:", oauth_token)
        print("  Token Type:", token_type)
        print("  Expires In:", expires_in)
        print("       Scope:", scope)
    except:
        print(oauth.text)
        sys.exit(1)


    print ('------------------------')  # separator


    # schedule the pickup
    json_response = schedule_pickup()

    # check for errors
    if is_error(json_response):
        sys.exit(1)
    else:
        print(json_response)
        transaction_id    = json_response['transactionId']
        confirmation_code = json_response['output']['pickupConfirmationCode']
        print('   Transaction ID:', transaction_id)
        print('Confirmation Code:', confirmation_code)
        print('      Pickup Date:', pickup_from)

        pickup_timestamp  = pickup_from


    print ('------------------------')  # separator


    # cancel the pickup
    cancel = cancel_pickup(confirmation_code, pickup_timestamp)

    # check for errors
    if is_error(cancel):
        sys.exit(1)
    else:
        transaction_id       = cancel['transactionId']
        confirmation_code    = cancel['output']['pickupConfirmationCode']
        confirmation_message = cancel['output']['cancelConfirmationMessage']
        print('      Transaction ID:', transaction_id)
        print('   Confirmation Code:', confirmation_code)
        print('Confirmation Message:', confirmation_message)


if __name__ == '__main__':
    main()
