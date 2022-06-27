# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class EmailforCustomer(Document):

	def on_submit(self) :
		if self.email_type == "Periode" :
			for i in self.customer_email :
				new_doc = frappe.new_doc("Hidden Document Email to Customer")
				new_doc.email_to_customer = self.name
				new_doc.posting_date = self.posting_date
				new_doc.customer = self.customer
				new_doc.customer_name = self.customer_name
				new_doc.customer_email = i.email_address
				new_doc.from_date_gl = self.from_date_gl
				new_doc.to_date_gl = self.to_date_gl
				new_doc.email_for_customer_child_data_list = self.email_for_customer_child_data_list

				new_doc.email_body = self.email_body
				new_doc.email_subject = self.email_subject

				new_doc.flags.ignore_permission = True
				new_doc.submit()

	
	def validate(self) :
		if not self.customer :
			frappe.throw("Customer is mandatory")

		if not self.customer_email :
			frappe.throw("Customer email is mandatory")

		if self.email_type == "Periode" :
			self.email_subject = "Account Statement As Requested"

		if self.email_type == "Periode" :
			if not self.from_date_gl :
				frappe.throw("From Date GL is mandatory")

			if not self.to_date_gl :
				frappe.throw("To Date GL is mandatory")

			# get data previous
			gdp = frappe.db.sql("""
				select gle.`party`, sum(gle.`debit`), sum(gle.`credit`), sum(gle.`debit`) - sum(gle.`credit`) as balance  from `tabGL Entry` gle
				where gle.`party` = "{}"
				and gle.posting_date < "{}"

				group by gle.`party`
				""".format(self.customer, self.from_date_gl))


			self.email_for_customer_child_data_list = []

			

			opening_debit = 0
			opening_credit = 0
			opening_balance = 0

			if gdp :
				child = self.append("email_for_customer_child_data_list", {})
				child.date = ""
				child.ref = ""
				child.remark = "Opening"
				child.debit = gdp[0][1]
				child.credit = gdp[0][2]
				child.balance = gdp[0][3]

				opening_debit = gdp[0][1]
				opening_credit = gdp[0][2]
				opening_balance = gdp[0][3]

			else :
				child = self.append("email_for_customer_child_data_list", {})
				child.date = ""
				child.ref = ""
				child.remark = "Opening"
				child.debit = 0
				child.credit = 0
				child.balance = 0

			gle = frappe.db.sql("""

				select 
					gle.`party`, 
					gle.`debit`, 
					gle.`credit`, 
					gle.`debit` - gle.`credit` AS balance, 
					gle.`posting_date`, 
					gle.`voucher_type`,
					gle.`voucher_no`,
					gle.`against`,
					gle.`remarks`

				from `tabGL Entry` gle
				where gle.`party` = "{}"
				and gle.`posting_date` between "{}" and "{}"
				
			""".format(self.customer, self.from_date_gl, self.to_date_gl))

			total_debit = 0
			total_credit = 0
			total_balance = 0

			if gle :
				for i in gle :
					child = self.append("email_for_customer_child_data_list", {})
					child.date = i[4]
					child.ref = str(i[5])+"\n"+str(i[6])
					child.remark = "against : "+str(i[7])+"\n"+"remarks : "+str(i[8])
					child.debit = i[1]
					child.credit = i[2]
					child.balance = i[3]

					total_debit += i[1]
					total_credit += i[2]
					total_balance += i[3]

			child = self.append("email_for_customer_child_data_list", {})
			child.date = ""
			child.ref = ""
			child.remark = "TOTAL"
			child.debit = total_debit
			child.credit = total_credit
			child.balance = total_balance

			child = self.append("email_for_customer_child_data_list", {})
			child.date = ""
			child.ref = ""
			child.remark = "Closing (Opening + Total)"
			child.debit = total_debit + opening_debit
			child.credit = total_credit + opening_credit
			child.balance = total_balance + opening_balance




