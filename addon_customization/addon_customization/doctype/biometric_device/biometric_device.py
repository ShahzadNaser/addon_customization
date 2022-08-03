# -*- coding: utf-8 -*-
# Copyright (c) 2022, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from urllib import response
from frappe.utils import get_datetime
import frappe
import datetime
import requests
import json
from frappe.model.document import Document

def sort_time(row):
    #Sort the punch times from the smallest to the largest then pick just the first and last entries
    row.sort()
    return(row[0],row[-1])

class BiometricDevice(Document):
    def get_token(self):
        #Fetch the token to be used for each api call
        params = {"password":self.get_password(),"username":self.username,"email":self.username,"company":self.company_id}
        header= {"Content-Type": "application/json; charset=utf-8"}
        url = self.api_url+'/api-token-auth/'
        resp = requests.post(url,json=params,headers=header)
        return resp.json().get('token')
        

    def validate(self):
        if not self.token:
                self.token = self.get_token()
    
    def combine_all_entries(self,response):
        pass


    def process_data(self,data):
        #sort the api response and create attendance records where necessary
        pack = {}
        for each in data:
            #TODO: Change this to ternary operator
            #Create a key using the employee id and date, this way we can keep the attendance creation simple for multiple dates
            if pack.get(each['emp_code']+'@'+each['punch_time'].split()[0]):
                pack[each['emp_code']+'@'+each['punch_time'].split()[0]].append(each['punch_time'])
            else:
                pack[each['emp_code']+'@'+each['punch_time'].split()[0]] = [each['punch_time']]
        #remove entries that are less than 2, because a valid attendance must contain 2 records
        new_pack = dict(filter(lambda val:len(val[1])>1,pack.items()))
        self.create_attendance(new_pack)

    def existing_record(self,one,day):
        #Check if an attendance record for that day already exists
        
        exists = frappe.db.exists('Attendance',{'docstatus':1,'employee':one,'attendance_date':day})
        return bool(exists)


    def create_attendance_for_employee():
        pass


    def create_attendance(self,pack):
        #Create the attendance records from the sorted dict
        for one in pack:
            one_emp,one_day = one.split("@")[0],one.split("@")[1]
            sorted_times = sort_time(pack.get(one))
            
            emps = frappe.get_all("Employee",{'biometric_id':one_emp})
            if emps:
                if not self.existing_record(emps[0]['name'],one_day):
                    args = {
                        "doctype":"Attendance",
                        'employee':emps[0]['name'],
                        'attendance_date':one_day,
                        'status':'Present',
                        'start_time':sorted_times[0],
                        'exit_time':sorted_times[1],
                        'company':self.company
                        }
                    self.create_attendance_document(args)
                    

    def create_attendance_document(self,args):
        att_doc = frappe.get_doc(args)
        att_doc.save()
                    # att_doc.insert()
        att_doc.submit()




    
@frappe.whitelist()
def fetch_attendance(from_date,to_date,doc):
    try:
    #Connect to the biometric api and retrieve the required data.
        doc = frappe.get_doc("Biometric Device",doc)
        auth_token = "Token "+f"{doc.token if doc.token else doc.get_token}"
        start = get_datetime(from_date)
        end = get_datetime(to_date)
        start_time = start.strftime("%Y-%m-%d 00:00:00")
        end_time = end.strftime("%Y-%m-%d 23:59:59")
        params = {
            'start_time':start_time,
            'end_time':end_time,
            'page_size':50000
        }
        headers = {"Content-Type": "application/json; charset=utf-8",\
            "Authorization":auth_token}
        url = doc.api_url+'/iclock/api/transactions/'
        resp = requests.get(url,headers=headers,params=params)
        if resp.status_code == 200 and resp.json().get('count')>0:
            doc.process_data(resp.json().get('data'))
            return True
    except:
        frappe.log_error(frappe.get_traceback(),'Biometric Device Error')
        return False


        
            

    