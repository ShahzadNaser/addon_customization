# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import frappe.utils
from frappe import utils

class Prepayment(Document):
	

	def generate_schedule_date(self) :

		if not self.prepayment_type :
			frappe.throw("Please select Prepayment Type")

		if not self.date_start :
			frappe.throw("Please select Date Start")

		if not self.total_amount :
			frappe.throw("Please input Total Amount")

		if self.prepayment_type == "Based on Month" and not self.month :
			frappe.throw("Please input Month")

		if self.prepayment_type == "Based on Amount per Month" and not self.amount_per_month :
			frappe.throw("Please input Amount per Month")


		if self.prepayment_type == "Based on Month" :

			self.amount_per_month = float(self.total_amount / self.month)

		elif self.prepayment_type == "Based on Amount per Month" :

			self.month = int(self.total_amount / self.amount_per_month)

		count = -1
		for i in range(self.month) :
			count += 1

			if count == 0 :
				child = self.append("prepayment_child", {})
				child.date_prepayment = self.date_start
				child.disable = 0
				child.closed = 0
			else :
				child = self.append("prepayment_child", {})
				child.date_prepayment = frappe.utils.add_months(str(self.date_start), count)
				child.disable = 0
				child.closed = 0

	def validate(self) :

		# check debit account
		get_acc = frappe.get_doc("Account", self.debit_account)
		if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
			if not self.debit_party_type and not self.debit_party :
				frappe.throw("You must choose Debit Party Type and Debit Party")

		# check credit account
		get_acc = frappe.get_doc("Account", self.credit_account)
		if get_acc.account_type == "Payable" or get_acc.account_type == "Receivable" :
			if not self.credit_party_type and not self.credit_party :
				frappe.throw("You must choose Credit Party Type and Credit Party")


		if not self.prepayment_child :
			frappe.throw("You must generate schedule date before continue this action")

		count = 0
		arr_date = []
		for i in self.prepayment_child :
			if i.date_prepayment in arr_date :
				frappe.throw("Got multiple date "+str(i.date_prepayment))
			else :
				arr_date.append(i.date_prepayment)

			if i.disable == 0 and i.closed == 0 :
				count += 1

		if count > self.month :
			frappe.throw("Date Schedule cannot have more than "+str(self.month)+" active dates")


	def on_update_after_submit(self) :

		# check debit account
		get_acc = frappe.get_doc("Account", self.debit_account)
		if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
			if not self.debit_party_type and not self.debit_party :
				frappe.throw("You must choose Debit Party Type and Debit Party")

		# check credit account
		get_acc = frappe.get_doc("Account", self.credit_account)
		if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
			if not self.credit_party_type and not self.credit_party :
				frappe.throw("You must choose Credit Party Type and Credit Party")


		count = 0
		arr_date = []
		for i in self.prepayment_child :
			if i.date_prepayment in arr_date :
				frappe.throw("Got multiple date "+str(i.date_prepayment))
			else :
				arr_date.append(i.date_prepayment)

			if i.disable == 0 and i.closed == 0 :
				count += 1

		if count > self.month :
			frappe.throw("Date Schedule cannot have more than "+str(self.month)+" active dates")



@frappe.whitelist()
def close_prepayment(docname) :
	frappe.db.sql(""" UPDATE `tabPrepayment` p SET p.`status_prepayment` = "Closed" WHERE p.`name` = "{}" """.format(docname))
	frappe.db.commit()

	frappe.db.sql(""" UPDATE `tabPrepayment Child` p SET p.`disable` = 1, p.`closed` = 1 WHERE p.`parent` = "{}" AND p.`disable` = 0 AND p.`closed` = 0 """.format(docname))
	frappe.db.commit()


@frappe.whitelist()
def open_prepayment(docname) :
	frappe.db.sql(""" UPDATE `tabPrepayment` p SET p.`status_prepayment` = "Open" WHERE p.`name` = "{}" """.format(docname))
	frappe.db.commit()

	frappe.db.sql(""" UPDATE `tabPrepayment Child` p SET p.`disable` = 0, p.`closed` = 0 WHERE p.`parent` = "{}" AND p.`disable` = 1 AND p.`closed` = 1 """.format(docname))
	frappe.db.commit()



@frappe.whitelist()
def submit_je(doc, method):
	if doc.prepayment :
		frappe.db.sql(""" UPDATE `tabPrepayment Child` re SET re.`journal_entry` = "{0}" WHERE re.`parent` = "{1}" AND re.`date_prepayment` = "{2}" """.format(doc.name, doc.prepayment, doc.posting_date))
		frappe.db.commit()

@frappe.whitelist()
def cancel_je(doc, method):
	if doc.prepayment :
		frappe.db.sql(""" UPDATE `tabPrepayment Child` re SET re.`journal_entry` = "" WHERE re.`parent` = "{0}" AND re.`date_prepayment` = "{1}" """.format(doc.prepayment, doc.posting_date))
		frappe.db.commit()



@frappe.whitelist()
def auto_generate_je_based_on_date() :

	# 'Journal Entry':'JV-.YYYY.-',
 #    'Opening Entry':'OPJ-.YYYY.-',
 #    'Contra Entry':'CEV-.YYYY.-',
 #    'Credit Note':'CNV-.YYYY.-',
 #    'Debit Note':'DNV-.YYYY.-',
 #    'Cash Entry':'CPV-.YYYY.-',
 #    'Bank Entry':'BPV-.YYYY.-',
 #    'Depreciation Entry':'DEP-.YYYY.-'

	get_data = frappe.db.sql("""

		SELECT

		pc.`parent`,
		pc.`date_prepayment`

		FROM `tabPrepayment Child` pc
		WHERE pc.`disable` = 0
		AND pc.`closed` = 0
		AND pc.`docstatus` = 1
		AND pc.`date_prepayment` = "{}"

		ORDER BY pc.`parent`

	""".format(utils.today()))

	if get_data :
		for i in get_data :

			docu = frappe.get_doc("Prepayment", i[0])

			# create new JE
			new_docu = frappe.new_doc("Journal Entry")
			new_docu.voucher_type = docu.journal_entry_type
			new_docu.workflow_state = 'draft'

			if docu.journal_entry_type == "Journal Entry" :
				new_docu.naming_series = "JV-.YYYY.-"
			elif docu.journal_entry_type == "Opening Entry" :
				new_docu.naming_series = "OPJ-.YYYY.-"
			elif docu.journal_entry_type == "Contra Entry" :
				new_docu.naming_series = "CEV-.YYYY.-"
			elif docu.journal_entry_type == "Credit Note" :
				new_docu.naming_series = "CNV-.YYYY.-"
			elif docu.journal_entry_type == "Debit Note" :
				new_docu.naming_series = "DNV-.YYYY.-"
			elif docu.journal_entry_type == "Cash Entry" :
				new_docu.naming_series = "CPV-.YYYY.-"
			elif docu.journal_entry_type == "Bank Entry" :
				new_docu.naming_series = "BPV-.YYYY.-"
			elif docu.journal_entry_type == "Depreciation Entry" :
				new_docu.naming_series = "DEP-.YYYY.-"

			new_docu.posting_date = utils.today()
			new_docu.prepayment = i[0]
			new_docu.user_remark = docu.description

			new_docu.location = docu.location

			child = new_docu.append("accounts", {})
			child.account = docu.debit_account

			get_acc = frappe.get_doc("Account", docu.debit_account)
			if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
				child.party_type = docu.debit_party_type
				child.party = docu.debit_party


			child.debit_in_account_currency = docu.amount_per_month
			child.debit = docu.amount_per_month

			child = new_docu.append("accounts", {})
			child.account = docu.credit_account

			get_acc = frappe.get_doc("Account", docu.credit_account)
			if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
				child.party_type = docu.credit_party_type
				child.party = docu.credit_party

			child.credit_in_account_currency = docu.amount_per_month
			child.credit = docu.amount_per_month

			new_docu.flags.ignore_permission = True

			if docu.save_as == "Draft" :
				new_docu.save()
			elif docu.save_as == "Submit" :
				new_docu.save()
				new_docu.submit()
@frappe.whitelist()
def auto_generate_je() :

	# 'Journal Entry':'JV-.YYYY.-',
 #    'Opening Entry':'OPJ-.YYYY.-',
 #    'Contra Entry':'CEV-.YYYY.-',
 #    'Credit Note':'CNV-.YYYY.-',
 #    'Debit Note':'DNV-.YYYY.-',
 #    'Cash Entry':'CPV-.YYYY.-',
 #    'Bank Entry':'BPV-.YYYY.-',
 #    'Depreciation Entry':'DEP-.YYYY.-'

	get_data = frappe.db.sql("""

		SELECT

		pc.`parent`,
		pc.`date_prepayment`

		FROM `tabPrepayment Child` pc
		WHERE pc.`disable` = 0
		AND pc.`closed` = 0
		AND pc.`docstatus` = 1
		AND pc.`date_prepayment` = "{}"

		ORDER BY pc.`parent`

	""".format('2022-10-31'))

	if get_data :
		for i in get_data :

			docu = frappe.get_doc("Prepayment", i[0])

			# create new JE
			new_docu = frappe.new_doc("Journal Entry")
			new_docu.voucher_type = docu.journal_entry_type
			new_docu.workflow_state = 'draft'

			if docu.journal_entry_type == "Journal Entry" :
				new_docu.naming_series = "JV-.YYYY.-"
			elif docu.journal_entry_type == "Opening Entry" :
				new_docu.naming_series = "OPJ-.YYYY.-"
			elif docu.journal_entry_type == "Contra Entry" :
				new_docu.naming_series = "CEV-.YYYY.-"
			elif docu.journal_entry_type == "Credit Note" :
				new_docu.naming_series = "CNV-.YYYY.-"
			elif docu.journal_entry_type == "Debit Note" :
				new_docu.naming_series = "DNV-.YYYY.-"
			elif docu.journal_entry_type == "Cash Entry" :
				new_docu.naming_series = "CPV-.YYYY.-"
			elif docu.journal_entry_type == "Bank Entry" :
				new_docu.naming_series = "BPV-.YYYY.-"
			elif docu.journal_entry_type == "Depreciation Entry" :
				new_docu.naming_series = "DEP-.YYYY.-"

			new_docu.posting_date = '2022-10-31'
			new_docu.prepayment = i[0]
			new_docu.user_remark = docu.description

			new_docu.location = docu.location

			child = new_docu.append("accounts", {})
			child.account = docu.debit_account

			get_acc = frappe.get_doc("Account", docu.debit_account)
			if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
				child.party_type = docu.debit_party_type
				child.party = docu.debit_party


			child.debit_in_account_currency = docu.amount_per_month
			child.debit = docu.amount_per_month

			child = new_docu.append("accounts", {})
			child.account = docu.credit_account

			get_acc = frappe.get_doc("Account", docu.credit_account)
			if get_acc.account_type == "Receivable" or get_acc.account_type == "Payable" :
				child.party_type = docu.credit_party_type
				child.party = docu.credit_party

			child.credit_in_account_currency = docu.amount_per_month
			child.credit = docu.amount_per_month

			new_docu.flags.ignore_permission = True

			if docu.save_as == "Draft" :
				new_docu.save()
			elif docu.save_as == "Submit" :
				new_docu.save()
				new_docu.submit()


@frappe.whitelist()
def manual_generate_je_based_on_date() :

	# 'Journal Entry':'JV-.YYYY.-',
 #    'Opening Entry':'OPJ-.YYYY.-',
 #    'Contra Entry':'CEV-.YYYY.-',
 #    'Credit Note':'CNV-.YYYY.-',
 #    'Debit Note':'DNV-.YYYY.-',
 #    'Cash Entry':'CPV-.YYYY.-',
 #    'Bank Entry':'BPV-.YYYY.-',
 #    'Depreciation Entry':'DEP-.YYYY.-'

	get_data = frappe.db.sql("""

		SELECT

		pc.`parent`,
		pc.`date_prepayment`

		FROM `tabPrepayment Child` pc
		WHERE pc.`disable` = 0
		AND pc.`closed` = 0
		AND pc.`docstatus` = 1
		AND pc.`date_prepayment` = "{}"

		ORDER BY pc.`parent`

	""".format(str("2020-10-30")))

	if get_data :
		for i in get_data :

			docu = frappe.get_doc("Prepayment", i[0])

			# create new JE
			new_docu = frappe.new_doc("Journal Entry")
			new_docu.voucher_type = docu.journal_entry_type

			if docu.journal_entry_type == "Journal Entry" :
				new_docu.naming_series = "JV-.YYYY.-"
			elif docu.journal_entry_type == "Opening Entry" :
				new_docu.naming_series = "OPJ-.YYYY.-"
			elif docu.journal_entry_type == "Contra Entry" :
				new_docu.naming_series = "CEV-.YYYY.-"
			elif docu.journal_entry_type == "Credit Note" :
				new_docu.naming_series = "CNV-.YYYY.-"
			elif docu.journal_entry_type == "Debit Note" :
				new_docu.naming_series = "DNV-.YYYY.-"
			elif docu.journal_entry_type == "Cash Entry" :
				new_docu.naming_series = "CPV-.YYYY.-"
			elif docu.journal_entry_type == "Bank Entry" :
				new_docu.naming_series = "BPV-.YYYY.-"
			elif docu.journal_entry_type == "Depreciation Entry" :
				new_docu.naming_series = "DEP-.YYYY.-"

			new_docu.posting_date = str("2020-07-31")
			new_docu.prepayment = i[0]
			new_docu.user_remark = docu.description

			new_docu.location = docu.location

			child = new_docu.append("accounts", {})
			child.account = docu.debit_account
			child.debit_in_account_currency = docu.amount_per_month
			child.debit = docu.amount_per_month

			child = new_docu.append("accounts", {})
			child.account = docu.credit_account
			child.credit_in_account_currency = docu.amount_per_month
			child.credit = docu.amount_per_month

			new_docu.flags.ignore_permission = True

			if docu.save_as == "Draft" :
				new_docu.save()
			elif docu.save_as == "Submit" :
				new_docu.save()
				new_docu.submit()


