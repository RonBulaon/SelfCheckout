from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib import messages

from email.mime.image import MIMEImage

import requests
import json
import re
import os

import pyqrcode
import random
import string

import datetime


API = os.environ.get('API')
API_SERVER = os.environ.get('API_SERVER')
CIRC_DESK = os.environ.get('CIRC_DESK')
LIBRARY = os.environ.get('LIBRARY')

IMAGE_PATH = '/app/checkout/images/code.png'
bookDetails = {}
patronDetails = {}

code = ""
code_timstamp = None


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def check_email(patron_email):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.fullmatch(email_regex, patron_email)):
        return True
    else:
        return False


def email(patron_email):
    global code
    global code_timstamp
    code = get_random_string(6)
    code_timstamp = datetime.datetime.now()

    subject = 'OTP from Library'
    message = 'OTP : ' + str(code)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [patron_email,]

    msg = EmailMultiAlternatives(subject, message, email_from,recipient_list)

    url = pyqrcode.create(code)
    url.png(IMAGE_PATH, scale = 6)
    
    try:
        with open(IMAGE_PATH, mode='rb') as f:
            image = MIMEImage(f.read())
            msg.attach(image)
            image.add_header('Content-ID', f"<{'code.png'}>")

        msg.send()
    except:
        print("-------------->can't send email")

    return 

def pullInfo(query):
    response = requests.get(query, headers={"accept":"application/json"})
    # print(query)
    if response.status_code == 200:
        return response.text
    else:
        return response.status_code

def step1(request):
    global bookDetails
    global patronDetails
    global code
    global code_timstamp
    code = ""
    code_timstamp = None
    bookDetails = {
            'book' : False,
            'title' : "",    
            'author' : "",
            'call_number' : "",
            'isbn' : "",
            'complete_edition' : "",
            'mms_id' : "",
            'holding_id' : "",
            'item_pid' : "",
        }
    patronDetails = {
            'patron' : False,
            'total_sum' : "",
            'total_record_count' : "",
            'primary_id' : "",
            'patron_name' : "",
            'status' : "",
            'patronID' : "",
            'email' : "",
        } 
    return render(request, 'checkout/step1.html',  {'bookDetails' : bookDetails, 
                                                    'patronDetails' : patronDetails})

def step2(request, item_barcode):
    global bookDetails
    global patronDetails

    def getAvailability(item_barcode):
        query = API_SERVER + '/almaws/v1/items?item_barcode='+item_barcode+'&apikey='+API
        return pullInfo(query)

    try:
        data = json.loads(getAvailability(item_barcode))
    except:
        bookDetails = {
            'book' : False,
            'title' : "",    
            'author' : "",
            'call_number' : "",
            'isbn' : "",
            'complete_edition' : "",
            'mms_id' : "",
            'holding_id' : "",
            'item_pid' : "",
            'barcode':""
        }
        messages.error(request, "Item not found! Please check your item and scan again! ")
        return redirect('step1')

    else:
        if str(data["bib_data"]["title"])[-1] == "/":
            title = str(data["bib_data"]["title"])[:-1] 

        bookDetails = {
            'book' : True,
            'title' : title,    
            'author' : data["bib_data"]["author"],
            'call_number' : data["holding_data"]["call_number"],
            'isbn' : data["bib_data"]["isbn"],
            'complete_edition' : data["bib_data"]["complete_edition"],
            'mms_id' : data["bib_data"]["mms_id"],
            'holding_id' : data["holding_data"]["holding_id"],
            'item_pid' : data["item_data"]["pid"],
            'barcode':item_barcode,
        }
        
    return render(request, 'checkout/step2.html',  {'bookDetails' : bookDetails, 
                                                    'patronDetails' : patronDetails})

def step3(request, patron_id):
    global bookDetails
    global patronDetails

    def getLoans(patron_id):
        query = API_SERVER + '/almaws/v1/users/'+patron_id+'/loans?user_id_type=all_unique&limit=10&offset=0&order_by=id&direction=ASC&apikey='+API
        return pullInfo(query)

    def getFines(patron_id):
        query = API_SERVER + '/almaws/v1/users/'+patron_id+'/fees?user_id_type=all_unique&status=ACTIVE&apikey='+API
        return pullInfo(query)

    def getPatronDetails(patron_id):
        query = API_SERVER + '/almaws/v1/users/'+patron_id+'?user_id_type=all_unique&view=full&expand=none&apikey='+API
        return pullInfo(query)

    try:
        data1 = json.loads(getFines(patron_id))
        data2 = json.loads(getLoans(patron_id))
        data3 = json.loads(getPatronDetails(patron_id))
    except:
        patronDetails = {
            'patron' : False,
            'total_sum' : "",
            'total_record_count' : "",
            'primary_id' : "",
            'patron_name' : "",
            'status' : "",
            'patronID' : "",
            'email' : "",
        }
        messages.error(request, "We are not able to find your information.")
        return redirect('step1')
    else:
        patronDetails = {
            'patron' : True,
            'total_sum' : data1["total_sum"],
            'total_record_count' : data2["total_record_count"],
            'primary_id' : data3["primary_id"],
            'patron_name' : data3["last_name"],
            'status' : data3["status"]["value"],
            'patronID' : patron_id,
            'email' : data3["contact_info"]["email"][0]["email_address"],
        }
        patron_email = data3["contact_info"]["email"][0]["email_address"]
        if check_email(patron_email):
            email(patron_email)
        else:
            print('----------> Wrong email format')

    return render(request, 'checkout/step3.html',  {'bookDetails' : bookDetails, 
                                                    'patronDetails' : patronDetails})

def step4(request, patron_code):
    global bookDetails
    global patronDetails
    global code
    global code_timstamp

    now = datetime.datetime.now()
    diff = now - code_timstamp
    diff = int(diff.total_seconds())

    def code_check(patron_code):
        if code != patron_code:
            return False, "Wrong code!"
        
        if diff > 60000:
            return False, "Expired code"
            
        return True, "Code OK!"

    asses_code = code_check(patron_code)

    if asses_code[0]:

        headers = {
            "accept":"application/json",
            "Content-Type":"application/json",
        }

        params = (
            ("user_id_type", "all_unique"),
            ("item_barcode", bookDetails.get('barcode')),
            ("generate_linked_user", "false"),
            ("apikey", API),
        )

        data = '{ "circ_desk": {"value": "'+CIRC_DESK+'"},"library": { "value": "'+LIBRARY+'"}}'

        query = API_SERVER + "almaws/v1/users/"+patronDetails.get('primary_id')+"/loans"
        response = requests.post(API_SERVER + "/almaws/v1/users/"+patronDetails.get('primary_id')+"/loans", headers=headers, params=params, data=data)
        
        data = json.loads(response.text)


        try: 
            if data["loan_id"]:
                messages.success(request, "Success!")
                return render(request, 'checkout/step4.html',  {'bookDetails' : bookDetails, 
                                                            'patronDetails' : patronDetails})
        except:
            messages.error(request, asses_code[1])
            return redirect('step1')
            
    else:
        messages.error(request, asses_code[1])
        return redirect('step1')


    