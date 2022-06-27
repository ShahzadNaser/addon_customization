# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import utils
# utils.now()
# utils.today()

class RequestExpenses(Document):

	def validate(self):
		if self.from_account == self.to_account :
			frappe.throw("Please use different Account on From Account and To Account")


	def on_update_after_submit(self):
		if self.status == "Actual Fund" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format(self.initial_money , self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money)

		elif self.status == "Not Enough Funds" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format((self.initial_money + self.money), self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money + self.money)


		elif self.status == "Excess Funds" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format((self.initial_money - self.money), self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money - self.money)

		elif self.status == "Returned Funds" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format(self.initial_money , self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money)
	
	def on_submit(self):
		if not self.je_initial_money :


			je = frappe.new_doc("Journal Entry")
			je.request_expenses = self.name
			je.user_remark = self.purpose
			je.naming_series = "JV-.YYYY.-"
			je.posting_date = utils.today()
			je.voucher_type = "Journal Entry"

			je.location = self.location

			je.request_expenses_status = "Initial Money"

			child = je.append('accounts', {})
			child.debit_in_account_currency = self.initial_money
			child.account = self.to_account

			child = je.append('accounts', {})
			child.credit_in_account_currency = self.initial_money
			child.account = self.from_account

			je.flags.ignore_permission = True
			je.save()
			je.submit()

			self.je_initial_money = je.name
			self.percent_je_initial_money = 100


		if self.status == "Not Enough Funds" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format((self.initial_money + self.money), self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money + self.money)


		elif self.status == "Excess Funds" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format((self.initial_money - self.money), self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money - self.money)

		else :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`final_money` = "{}" WHERE re.`name` = "{}" """.format(self.initial_money , self.name))
			frappe.db.commit()
			# self.final_money = (self.initial_money)

	
	# def on_submit(self):
	# 	if self.workflow_state == "Accountant Approved" :
	# 		self.account_user = frappe.session.user
	# 		self.approved_date_account_user = utils.today()

	# def on_update_after_submit(self):
	# 	if not self.status and self.docstatus :
	# 		frappe.throw("Please select the status")

	# 	if self.workflow_state == "Manager Approved" :
	# 		self.account_manager = frappe.session.user
	# 		self.approved_date_account_manager = utils.today()


		# validate: function(frm) {
		# 	if(frm.doc.workflow_state=="Accountant Approved")
		# 	{
		# 		cur_frm.set_value("account_user", user);
		# 		cur_frm.set_value("approved_date_account_user", String(frappe.datetime.nowdate()));
		# 		cur_frm.set_value("is_approved_account_user", 1);
		# 	}
		# },
		# on_submit: function(frm) {
		# 	if(frm.doc.workflow_state=="Manager Approved")
		# 	{
		# 		cur_frm.set_value("account_manager", user);
		# 		cur_frm.set_value("approved_date_account_manager", String(frappe.datetime.nowdate()));
		# 		cur_frm.set_value("is_approved_account_manager", 1);
		# 	}
		# },



# @frappe.whitelist()
# def create_je_initial_money(request_expenses):

# 	re = frappe.get_doc("Request Expenses", request_expenses)

# 	je = frappe.new_doc("Journal Entry")
# 	je.request_expenses = re.name
# 	je.user_remark = re.purpose
# 	je.voucher_type = "Journal Entry"

# 	je.request_expenses_status = "Initial Money"

# 	child = je.append('accounts', {})
# 	child.debit_in_account_currency = re.initial_money

# 	child = je.append('accounts', {})
# 	child.credit_in_account_currency = re.initial_money

# 	return je.as_dict()



@frappe.whitelist()
def create_je_final_money(request_expenses):

	re = frappe.get_doc("Request Expenses", request_expenses)

	je = frappe.new_doc("Journal Entry")
	je.request_expenses = re.name
	je.user_remark = re.purpose
	je.location = re.location

	je.request_expenses_status = "Final Money"


	# Enough Money
	# Not Enough Money
	# Got Changes

	if re.status == "Actual Fund" :
		

		ga = frappe.get_doc("Account", re.from_account)
		if ga.account_type == "Bank" :
			je.voucher_type = ""
			je.naming_series = "BPV-.YYYY.-"
		else :
			je.voucher_type = ""
			je.naming_series = "CPV-.YYYY.-"

		child = je.append('accounts', {})
		child.debit_in_account_currency = re.initial_money
		child = je.append('accounts', {})
		child.credit_in_account_currency = re.initial_money
		child.account = re.from_account

	elif re.status == "Not Enough Funds" :
		ga = frappe.get_doc("Account", re.from_account)
		if ga.account_type == "Bank" :
			je.voucher_type = ""
			je.naming_series = "BPV-.YYYY.-"
		else :
			je.voucher_type = ""
			je.naming_series = "CPV-.YYYY.-"

		child = je.append('accounts', {})
		child.debit_in_account_currency = (re.initial_money + re.money)
		child = je.append('accounts', {})
		child.credit_in_account_currency = (re.initial_money + re.money)
		child.account = re.from_account

	elif re.status == "Excess Funds" :
		ga = frappe.get_doc("Account", re.from_account)
		if ga.account_type == "Bank" :
			je.voucher_type = ""
			je.naming_series = "BPV-.YYYY.-"
		else :
			je.voucher_type = ""
			je.naming_series = "CPV-.YYYY.-"

		child = je.append('accounts', {})
		child.debit_in_account_currency = (re.initial_money - re.money)
		child = je.append('accounts', {})
		child.credit_in_account_currency = (re.initial_money - re.money)
		child.account = re.from_account




	elif re.status == "Returned Funds" :
		je.voucher_type = "Journal Entry"
		je.naming_series = "JV-.YYYY.-"

		child = je.append('accounts', {})
		child.debit_in_account_currency = re.initial_money
		child.account = re.from_account
		child = je.append('accounts', {})
		child.credit_in_account_currency = re.initial_money
		child.account = re.to_account


	return je.as_dict()


@frappe.whitelist()
def submit_je(doc, method):

	if doc.request_expenses :

		if doc.request_expenses_status == "Initial Money" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`je_initial_money` = "{0}", re.`percent_je_initial_money` = 100 WHERE re.`name` = "{1}" """.format(doc.name, doc.request_expenses))
			frappe.db.commit()



		elif doc.request_expenses_status == "Final Money" :
			re = frappe.get_doc("Request Expenses", doc.request_expenses)
			actual_amount = 0
			if re.status == "Actual Fund" :
				actual_amount = re.initial_money


				je = frappe.get_doc(
					{
						"doctype":"Journal Entry",
						"naming_series" : "JV-.YYYY.-",
						"request_expenses" : re.name,
						"location" : re.location,
						"posting_date" : utils.today(),
						"request_expenses_status" : "Reverse Initial Money",
						"voucher_type" : "Journal Entry",
						"user_remark" : re.je_initial_money
					}
				)
				child = je.append('accounts', {})
				child.debit_in_account_currency = re.initial_money
				child.account = re.from_account

				child = je.append('accounts', {})
				child.credit_in_account_currency = re.initial_money
				child.account = re.to_account
				je.insert(ignore_permissions=True)
				je.submit()


				# je = frappe.new_doc("Journal Entry")
				# je.naming_series = "JV-.YYYY.-"
				# je.request_expenses = re.name
				# je.location = re.location
				# je.posting_date = utils.today()
				# je.request_expenses_status = "Reverse Initial Money"
				# je.voucher_type = "Journal Entry"

				# child = je.append('accounts', {})
				# child.debit_in_account_currency = re.initial_money
				# child.account = re.from_account

				# child = je.append('accounts', {})
				# child.credit_in_account_currency = re.initial_money
				# child.account = re.to_account

				# je.flags.ignore_permission = True
				# je.save()
				# je.submit()
				frappe.db.commit()



			elif re.status == "Not Enough Funds" :
				actual_amount = (re.initial_money + re.money)

				je = frappe.get_doc(
					{
						"doctype":"Journal Entry",
						"naming_series" : "JV-.YYYY.-",
						"request_expenses" : re.name,
						"location" : re.location,
						"posting_date" : utils.today(),
						"request_expenses_status" : "Reverse Initial Money",
						"voucher_type" : "Journal Entry",
						"user_remark" : re.je_initial_money
					}
				)
				child = je.append('accounts', {})
				child.debit_in_account_currency = re.initial_money
				child.account = re.from_account

				child = je.append('accounts', {})
				child.credit_in_account_currency = re.initial_money
				child.account = re.to_account
				je.insert(ignore_permissions=True)
				je.submit()

				# je = frappe.new_doc("Journal Entry")
				# je.request_expenses = re.name
				# je.posting_date = utils.today()
				# je.location = re.location
				# je.request_expenses_status = "Reverse Initial Money"
				# je.voucher_type = "Journal Entry"
				# je.naming_series = "JV-.YYYY.-"

				# child = je.append('accounts', {})
				# child.debit_in_account_currency = re.initial_money
				# child.account = re.from_account

				# child = je.append('accounts', {})
				# child.credit_in_account_currency = re.initial_money
				# child.account = re.to_account

				# je.flags.ignore_permission = True
				# je.save()
				# je.submit()
				frappe.db.commit()

			elif re.status == "Excess Funds" :
				actual_amount = (re.initial_money - re.money)

				je = frappe.get_doc(
					{
						"doctype":"Journal Entry",
						"naming_series" : "JV-.YYYY.-",
						"request_expenses" : re.name,
						"location" : re.location,
						"posting_date" : utils.today(),
						"request_expenses_status" : "Reverse Initial Money",
						"voucher_type" : "Journal Entry",
						"user_remark" : re.je_initial_money
					}
				)
				child = je.append('accounts', {})
				child.debit_in_account_currency = re.initial_money
				child.account = re.from_account

				child = je.append('accounts', {})
				child.credit_in_account_currency = re.initial_money
				child.account = re.to_account
				je.insert(ignore_permissions=True)
				je.submit()

				# je = frappe.new_doc("Journal Entry")
				# je.request_expenses = re.name
				# je.posting_date = utils.today()
				# je.location = re.location
				# je.request_expenses_status = "Reverse Initial Money"
				# je.voucher_type = "Journal Entry"
				# je.naming_series = "JV-.YYYY.-"

				# child = je.append('accounts', {})
				# child.debit_in_account_currency = re.initial_money
				# child.account = re.from_account

				# child = je.append('accounts', {})
				# child.credit_in_account_currency = re.initial_money
				# child.account = re.to_account

				# je.flags.ignore_permission = True
				# je.save()
				# je.submit()
				frappe.db.commit()
				
			elif re.status == "Returned Funds" :
				actual_amount = 0

			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`je_final_money` = "{0}", re.`percent_je_final_money` = 100, re.`actual_amount` = {2} WHERE re.`name` = "{1}" """.format(doc.name, doc.request_expenses, actual_amount))
			frappe.db.commit()




@frappe.whitelist()
def cancel_je(doc, method):

	if doc.request_expenses :

		if doc.request_expenses_status == "Initial Money" :

			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`je_initial_money` = NULL, re.`percent_je_initial_money` = 0 WHERE re.`name` = "{}" """.format(doc.request_expenses))
			frappe.db.commit()

		elif doc.request_expenses_status == "Final Money" :
			frappe.db.sql(""" UPDATE `tabRequest Expenses` re SET re.`je_final_money` = NULL, re.`percent_je_final_money` = 0 WHERE re.`name` = "{}" """.format(doc.request_expenses))
			frappe.db.commit()