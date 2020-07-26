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

# custom build functions
from .usernames.username_suggestion import check_or_get_username

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.crypto import get_random_string
from django.core.signing import Signer
signer = Signer()


def authenticate(credential, password):
    try:
        user = user_details.objects.get(
            Q(username=credential) | Q(email=credential))
        if user.password == password:
            return user
        else:
            return None
    except:
        return False


@api_view(['POST'])
def login(request):  # login/
    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        if data.get('credential') == None or data.get('password') == None:
            return Response({'error': "Invalid body parameter, body must contain 'credential' and 'password'"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            data['credential'], data['password'])
        if user == False:
            return Response({'error': "The Email/Username you entered doesn't belong to an account. Please check your Email/Username and try again."}, status=status.HTTP_200_OK)
        elif user == None:
            return Response({'error': "Invalid Passowrd"}, status=status.HTTP_200_OK)
        else:
            serializer = loginSerializer(user)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

############################SIGNUP FUNCTIONS#########################
# returns True if username available
# returns False if username NOT available, returns also list of available suggestions
# returns None if username not safe/invalid regex


@api_view(['POST'])
def choose_username(request):  # signup/choose-username/
    if request.method == 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        data = request.data
        if data.get('username') == None:
            return Response({'error': "Invalid body parameter, body must contain 'username'"}, status=status.HTTP_400_BAD_REQUEST)

        response, suggestions = check_or_get_username(data['username'].strip())
        if response == None:  # if username not safe/invalid regex
            return Response({'error': suggestions}, status=status.HTTP_205_RESET_CONTENT)
        elif response == False:  # if username NOT available, returns also list of available suggestions
            returndata = {}
            returndata["error"] = "The username {} is not available".format(
                data['username'].strip())
            returndata["suggestions"] = suggestions
            return Response(returndata, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_202_ACCEPTED)

        # else:
        #    return Response({'error': "The Email/Username you entered doesn't belong to an account. Please check your Email/Username and try again."}, status=status.HTTP_401_UNAUTHORIZED)