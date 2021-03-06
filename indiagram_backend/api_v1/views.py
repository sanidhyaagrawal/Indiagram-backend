from rest_framework.views import exception_handler
from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
import secrets
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

from .models import *
from django.db.models import Q

from .serializers import *
import json
import re 
import datetime

# custom build functions
from .usernames.username_suggestion import check_or_get_username

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.crypto import get_random_string
from django.core.signing import Signer
from django.core import signing
signer = Signer()





######################################################################
######################################################################
############################LOGIN FUNCTIONS###########################
######################################################################
######################################################################
def userTokenisValid(userToken):
    try:
            user = user_details.objects.get(userToken=userToken)
            return (True, user)
    except:
            return (False, None)

def usernameisValid(username):
    try:
            user = user_details.objects.get(username=username)
            return (True, user)
    except:
            return (False, None)

def createSessionToken():
    return secrets.token_urlsafe(256) #2848 bits security

def sessionIsValid(Token):  
    expirationTime = 120 #Minutes #IMP 
    try:
            token_obj = sessionToken.objects.get(sessionToken=Token)
            print(token_obj)
            if (token_obj.time_created + datetime.timedelta(minutes=expirationTime)).replace(tzinfo=datetime.timezone.utc) <  datetime.datetime.now().replace(tzinfo=datetime.timezone.utc):
                token_obj.sessionToken = createSessionToken()
                token_obj.save()
                return (False, token_obj.user)
            else:
                return (True, token_obj.user)
    except:
            return (None, None)

@api_view(['POST'])
def getSessionToken(request):
    if request.method == 'POST':
        data = request.data
        if data.get('userToken') == None:
            return Response({'error': "Invalid body parameter, body must contain 'userToken'"}, status=status.HTTP_400_BAD_REQUEST)
        
        userToken = data.get('userToken')
        userTokenValid, user = userTokenisValid(userToken)
        if userTokenValid:
            try:   
                sessionToken_obj = sessionToken.objects.get(user=user)
            except:
                sessionToken_obj = sessionToken.objects.create(user=user, token=createSessionToken())
            
            serializer = sessionTokenSerializer(sessionToken_obj).data
            return Response(serializer, status=status.HTTP_202_ACCEPTED)
        else:   
            return Response({'error_header':'Something went wrong','error_body': "Something went wrong, please try again later.", "actions": [{"error_code": "1001", 'error_message': 'Try Again'}]}, status=status.HTTP_401_UNAUTHORIZED)


def authenticate(credential, password): 
    try:
            user = user_details.objects.get(Q(username=credential) | Q(email=credential))
            if user.password == password:
                return user
            else:
                return None
    except:
        try:
            if len(credential) > 5 and len(credential) < 14:
                _PhoneNumber = credential.replace(' ','')
                _PhoneNumber = _PhoneNumber.replace('+','')
                _PhoneNumber = _PhoneNumber.replace('-','')

                user = user_details.objects.get(Q(complete_number=_PhoneNumber) | Q(phone_number=_PhoneNumber))
                if user.password == password:
                    return user
                else:
                    return None
            else:
                return False
      
        except:
            return False


@api_view(['POST'])
def login(request):  # login/
    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        print(data)
        if data.get('credential') == None or data.get('password') == None:
            return Response({'error': "Invalid body parameter, body must contain 'credential' and 'password'"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            data['credential'], data['password'])
        print(user,user,user,user)    
        if user == False:
            return Response({'error_header':'Incorrect Username','error_body': "The username you entered doesn't appear to belong to an account. Please check your username and try again", "actions": [{"error_code": "1001", 'error_message': 'Try Again'}]}, status=status.HTTP_200_OK)
        elif user == None:
            try:
                user = user_details.objects.get(Q(username=data['credential']) | Q(email=data['credential']))
            except:
                _PhoneNumber = data['credential'].replace(' ','')
                _PhoneNumber = _PhoneNumber.replace('+','')
                _PhoneNumber = _PhoneNumber.replace('-','')
                user = user_details.objects.get(Q(complete_number=_PhoneNumber) | Q(phone_number=_PhoneNumber))
            if user.email != None:
                return Response({'error_header': "Forgotten Password?", 'error_body':"We can send you an email to help you get back into your account.", "actions": [{"error_code": "1004", 'error_message': 'Send Email'},{"error_code": "1001", 'error_message': 'Try Again'}]}, status=status.HTTP_200_OK)
            else: 
                return Response({'error_header': "Incorrect password for {}".format(data['credential']), 'error_body':"The password you entered is incorrect. Please try again.", "actions": [{"error_code": "1001", 'error_message': 'Try Again'}]}, status=status.HTTP_200_OK)

        else:
            serializer = loginSerializer(user).data
            return Response(serializer, status=status.HTTP_202_ACCEPTED)





############################SIGNUP FUNCTIONS#########################
# returns True if username available
# returns False if username NOT available, returns also list of available suggestions
# returns None if username not safe/invalid regex
######################################################################



@api_view(['POST'])
def choose_username(request):  # signup/choose-username/
    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        if data.get('username') == None:
            return Response({'error': "Invalid body parameter, body must contain 'username'"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            username = data.get('username')
            response, suggestions = check_or_get_username(username.strip())
            if response == None:  # if username not safe/invalid regex
                return Response({'error': suggestions}, status=status.HTTP_205_RESET_CONTENT)
            elif response == False:  # if username NOT available, returns also list of available suggestions
                returndata = {}
                returndata["error"] = "The username {} is not available".format(username.strip())
                returndata["suggestions"] = suggestions
                return Response(returndata, status=status.HTTP_200_OK)
            elif response == True:
                return Response(status=status.HTTP_202_ACCEPTED)



##################################################################################
##################################################################################
#############################CONTACT INFO VERIFY FUNCTIONS########################
##################################################################################
##################################################################################

def valid_phone_number(recived_code, recived_phone_number):
    recived_phone_number = recived_phone_number.replace(' ','')
    recived_phone_number = recived_phone_number.replace('+','')
    recived_phone_number = recived_phone_number.replace('-','')
    if not user_details.objects.all().filter(complete_number = str(recived_code).strip()+str(recived_phone_number).strip()).exists():
        country_codes = ["+93","+358","+355","+213","+1684","+376","+244","+1264","+672","+1268","+54","+374","+297","+61","+43","+994","+1242","+973","+880","+1246","+375","+32","+501","+229","+1441","+975","+591","+387","+267","+47","+55","+246","+673","+359","+226","+257","+855","+237","+1","+238","+1345","+236","+235","+56","+86","+61","+61","+57","+269","+242","+243","+682","+506","+225","+385","+53","+357","+420","+45","+253","+1767","+1","+593","+20","+503","+240","+291","+372","+251","+500","+298","+679","+358","+33","+594","+689","+262","+241","+220","+995","+49","+233","+350","+30","+299","+1473","+590","+1671","+502","+44","+224","+245","+592","+509","+0","+379","+504","+852","+36","+354","+91","+62","+98","+964","+353","+44","+972","+39","+1876","+81","+44","+962","+7","+254","+686","+850","+82","+383","+965","+996","+856","+371","+961","+266","+231","+218","+423","+370","+352","+853","+389","+261","+265","+60","+960","+223","+356","+692","+596","+222","+230","+262","+52","+691","+373","+377","+976","+382","+1664","+212","+258","+95","+264","+674","+977","+31","+599","+687","+64","+505","+227","+234","+683","+672","+1670","+47","+968","+92","+680","+970","+507","+675","+595","+51","+63","+64","+48","+351","+1939","+1787","+974","+40","+7","+250","+262","+590","+290","+1869","+1758","+590","+508","+1784","+685","+378","+239","+966","+221","+381","+248","+232","+65","+421","+386","+677","+252","+27","+211","+500","+34","+94","+249","+597","+47","+268","+46","+41","+963","+886","+992","+255","+66","+670","+228","+690","+676","+1868","+216","+90","+993","+1649","+688","+256","+380","+971","+44","+1","+598","+998","+678","+58","+84","+1284","+1340","+681","+967","+260","+263"]
        if recived_code in country_codes:
            if recived_code == '+91': #if number in indian
                
                if re.match("^[6-9]\d{9}$", recived_phone_number):
                    return (True, "Valid")
                else:
                    return (False, Response({'error_header': "Invalid Phone Number", 'error_body':"Looks like your phone number may be incorrect. Please try entering your full number, including the country code.", "actions": [{"error_code": "1001", 'error_message': 'Try Again'} ]}, status=status.HTTP_200_OK))
            else: #if international number
                
                if str(recived_phone_number).isnumeric() and len(str(recived_phone_number)) < 16 and len(str(recived_phone_number)) > 3:    
                    return (True, "Valid")
                else:
                    return (False, Response({'error_header': "Invalid Phone Number", 'error_body':"Looks like your phone number may be incorrect. Please try entering your full number, including the country code.", "actions": [{"error_code": "1001", 'error_message': 'Try Again'} ]}, status=status.HTTP_200_OK))
        else:
            return (False, Response({'error_header': "Invalid country code", 'error_body':"The country code you choose is not yet available, please re-check the country code or use email instead.", "actions": [{"error_code": "1001", 'error_message': 'Try Again'} ]}, status=status.HTTP_200_OK))
    else:
        return (False, Response({'error_header': "The phone number is on another account", 'error_body':"You can log in to the account associated with that phone number or you can use that phone number to create a new account","actions": [{"error_code": "1003", 'error_message': 'Login to existing account'},{"error_code": "1002", 'error_message':'Create New Account'}]}, status=status.HTTP_200_OK))


def validateEmail(email) :
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    if not user_details.objects.all().filter(email = email).exists():
        try:
            validate_email( email )
            return (True, 'Valid and Available')
        except ValidationError:
            return (False, Response({'error_header': "Please enter a valid email", 'error_body':"The email you entered seems to be invalid, please re-check or use a phone number instead.","actions": [{"error_code": "1001", 'error_message': 'Try Again'}]}, status=status.HTTP_200_OK))
    else:
        return (False, Response({'error_header': "The email address is on another account", 'error_body':"You can log in to the account associated with that email address or you can use that email address to create a new account", "actions": [{"error_code": "1003", 'error_message': 'Login to existing account'},{"error_code": "1002", 'error_message':'Create New Account'}]}, status=status.HTTP_200_OK))


import random
def send_phone_number_otp(recived_code, recived_phone_number):
    verifier_token = signing.dumps({"country_code": recived_code, "phone_number": recived_phone_number})
    otp = random.randint(1000,9999)
    print(otp) #send otp here
    otps.objects.create(token = verifier_token, otp = otp, time_created = datetime.datetime.now())
    return (True, verifier_token)

        
def send_email_otp(email):
    verifier_token = signing.dumps({"email": email})
    otp = random.randint(1000,9999)
    print(otp) #send otp here
    otps.objects.create(token = verifier_token, otp = otp, time_created = datetime.datetime.now() )
    return (True, verifier_token)

@api_view(['POST'])
def verify_contact(request):  # signup/verify-contact/
    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        print(data)
        if data.get('country_code') != None and data.get('phone_number') != None:
            _isValid, _Responce =  valid_phone_number(data['country_code'].strip(), data['phone_number'].strip())
            if _isValid:
                _Sent, verifier_token = send_phone_number_otp(data['country_code'].strip(), data['phone_number'].strip())
                if _Sent:
                    return Response({"verifier_token" : verifier_token},status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            else:
                return _Responce
        
        
        elif data.get('email') != None:
            _isValid, _Responce = validateEmail(data['email'].strip())
            if _isValid:    
                _Sent, verifier_token = send_email_otp(data['email'].strip())
                if _Sent:
                    return Response({"verifier_token" : verifier_token},status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
            else:
                return _Responce
        else:
            return Response({'error': "Invalid body parameter, body must contain 'country_code' and 'phone_number' or 'email' "}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def verify_otp(request):  # signup/verify-otp/
    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        print(data)
        if data.get('otp') == None or data.get('token') == None:
            return Response({'error': "Invalid body parameter, body must contain 'otp' and 'token'"}, status=status.HTTP_400_BAD_REQUEST)

        if otps.objects.all().filter(token = data['token'], otp = data['otp'].strip()).exists():
            otp = otps.objects.get(token = data['token'], otp = data['otp'].strip())
            print(otp.time_created)
            print((otp.time_created + datetime.timedelta(minutes=15)).replace(tzinfo=datetime.timezone.utc))
            print(datetime.datetime.now().replace(tzinfo=datetime.timezone.utc))

            if (otp.time_created + datetime.timedelta(minutes=15)).replace(tzinfo=datetime.timezone.utc) >  datetime.datetime.now().replace(tzinfo=datetime.timezone.utc):
                token_data = signing.loads(data['token'])
                if token_data.get('email') != None:
                    contact_token = tokenised_contact_info.objects.create(email=token_data['email'])
                    contact_token.sessionToken = signer.sign(contact_token.pk).split(':')[1]
                    contact_token.save()
                    return Response({'contact_token': contact_token.sessionToken},status=status.HTTP_202_ACCEPTED)
                elif token_data.get('country_code') != None and token_data.get('phone_number') != None:
                    contact_token = tokenised_contact_info.objects.create(country_code=token_data['country_code'],phone_number=token_data['phone_number'] )
                    contact_token.sessionToken = signer.sign(contact_token.pk).split(':')[1]
                    contact_token.save()
                    return Response({'contact_token': contact_token.sessionToken},status=status.HTTP_202_ACCEPTED)

                else:
                    return Response({"Lethal":"Something is really wrong! Unable to decode the token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error":"That OTP has been expired. You can request a new one."}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"That code isn't valid. You can request a new one."}, status=status.HTTP_200_OK)


def _decode_contact_token(contact_token):
    try:
        token_obj = tokenised_contact_info.objects.get(sessionToken = contact_token) 
        serializer = tokenised_contact_infoSerializer(token_obj)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    except tokenised_contact_info.DoesNotExist:
        return Response({'error_header': "Invalid Contact Token", 'error_body':"Request timeout, Please start over the sign-up process.", "actions": [{"error_code": "1005", 'error_message':'Retry signing up'}]}, status=status.HTTP_200_OK)


def _Isvalid_password(password):
    if not len(password) < 6:
        return Response(status=status.HTTP_202_ACCEPTED)
    else:
        return Response({'error_header': "Password too short", 'error_body':"Password needs to be at lest 6 character long", "actions": [{"error_code": "1005", 'error_message':'Retry signing up'}]}, status=status.HTTP_200_OK)

def _Isvalid_date_of_birth(date_of_birth):
    from datetime import datetime

    try:
        bday = datetime.strptime(date_of_birth, '%d/%m/%Y')
        if datetime.now().year - bday.year > 12:
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'error_header': "You need to atleast 13 years old", 'error_body':"We require everyone to be at least 13 years old before they can create an account.", "actions": [{"error_code": "1006", 'error_message':'Understood'}]}, status=status.HTTP_200_OK)

    except ValueError:
        return Response({'error_header': "Invalid date of birth", 'error_body':"Invalid date of format, please retry.", "actions": [{"error_code": "1005", 'error_message':'Retry signing up'}]}, status=status.HTTP_200_OK)

def _username_check(username):
        response, suggestions = check_or_get_username(username.strip())
        if response == None:  # if username not safe/invalid regex
            return Response({'error_header': "Username Error", 'error_body': suggestions, "actions": [{"error_code": "1005", 'error_message':'Retry signing up'}]}, status=status.HTTP_200_OK)
        elif response == False:  # if username NOT available, returns also list of available suggestions
            return Response({'error_header': "Username Error", 'error_body': "The username {} is not available".format(username.strip()), "actions": [{"error_code": "1005", 'error_message':'Retry signing up'}]}, status=status.HTTP_200_OK)
        elif response == True:
            return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def signup(request):  # signup/
    from datetime import datetime

    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        print(data)
        if data.get('username') == None or data.get('password') == None  or data.get('contact_token') == None or data.get('full_name') == None or data.get('date_of_birth') == None:
            return Response({'error': "Invalid body parameter, body must contain 'username', 'password', 'full_name', 'date_of_birth' and 'contact_token' "}, status=status.HTTP_400_BAD_REQUEST)
        else:
            username = data['username'].strip()
            contact_token = data['contact_token']
            password = data['password'].strip() 
            full_name = data['full_name']
            date_of_birth = data['date_of_birth'].strip() 

            username_responce = _username_check(username)
            if username_responce.status_code == 202: #username is correct

                contact_token_responce = _decode_contact_token(contact_token)
                if contact_token_responce.status_code == 202: #contact token is correct
                    contact_info = contact_token_responce.data
                    password_responce = _Isvalid_password(password)
                    if password_responce.status_code == 202: #password is valid

                        dob_responce = _Isvalid_date_of_birth(date_of_birth)
                        if dob_responce.status_code == 202: #date of birth is valid
                             user_obj = user_details.objects.create(username=username, password=password, name=full_name, date_of_birth=datetime.strptime(date_of_birth, '%d/%m/%Y'),email= contact_info['email'], country_code=contact_info['country_code'], phone_number=contact_info['phone_number'], complete_number=str(contact_info['country_code'])+str(contact_info['phone_number']) )
                             user_obj.sessionToken = signer.sign(user_obj.pk).split(':')[1]
                             user_obj.save()
                             serializer= user_detailsSerializer(user_obj)
                             return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

                              
                        else:    
                            return dob_responce

                    else:    
                        return password_responce

                else:
                    return contact_token_responce
                    
            else:
              return username_responce   
                

