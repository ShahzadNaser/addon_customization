# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import frappe.utils
from frappe import utils

class ProvisionSetup(Document):
	pass


@frappe.whitelist()
def auto_generate_je_based_on_date() :
	get_data = frappe.db.sql("""

		SELECT ps.`name` FROM `tabProvision Setup` ps
		WHERE ps.`disable` = 0

	""".format(utils.today()))

	today_date = str(utils.today())
	yesterday_date = str(frappe.utils.add_days(today_date, -1))

	clause_date = str(yesterday_date.split("-")[0])+"-"+str(yesterday_date.split("-")[1])+"%"

	if get_data :
		for i in get_data :

			docu = frappe.get_doc("Provision Setup", i[0])


			total_penjualan = 0
			calcu_provision = 0
			data_cust_group = ""
			for cg in docu.customer_group_list :

				get_sinv_amount = frappe.db.sql("""
					SELECT sinv.`customer`, c.`customer_group`, SUM(sinv.`grand_total`) FROM `tabSales Invoice` sinv
					LEFT JOIN `tabCustomer` c ON sinv.`customer` = c.`name`
					WHERE sinv.`docstatus` = 1
					AND c.`customer_group` = "{}"
					AND sinv.`posting_date` LIKE "{}"
					GROUP BY c.`customer_group`
				""".format(cg.customer_group, clause_date))

				if get_sinv_amount :
					total_penjualan = get_sinv_amount[0][2]

				calcu_provision += (cg.provision_percentage * total_penjualan) / 100
				data_cust_group += " " + str(cg.customer_group)

			if calcu_provision > 0 :

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

				new_docu.posting_date = yesterday_date
				new_docu.provision_setup = i[0]
				new_docu.user_remark = docu.purpose + " ( " + str(data_cust_group) + " ) "

				new_docu.location = docu.location

				child = new_docu.append("accounts", {})
				child.account = docu.debit_account
				child.debit_in_account_currency = calcu_provision
				child.debit = calcu_provision

				child = new_docu.append("accounts", {})
				child.account = docu.credit_account
				child.credit_in_account_currency = calcu_provision
				child.credit = calcu_provision

				new_docu.flags.ignore_permission = True

				if docu.save_as == "Draft" :
					new_docu.save()
				elif docu.save_as == "Submit" :
					new_docu.save()
					new_docu.submit()




@frappe.whitelist()
def manual_generate_je_based_on_date() :
	get_data = frappe.db.sql("""

		SELECT ps.`name` FROM `tabProvision Setup` ps
		WHERE ps.`disable` = 0

	""".format(utils.today()))

	today_date = str("2020-08-01")
	yesterday_date = str(frappe.utils.add_days(today_date, -1))

	clause_date = str(yesterday_date.split("-")[0])+"-"+str(yesterday_date.split("-")[1])+"%"

	if get_data :
		for i in get_data :

			docu = frappe.get_doc("Provision Setup", i[0])


			total_penjualan = 0
			calcu_provision = 0
			data_cust_group = ""
			for cg in docu.customer_group_list :

				get_sinv_amount = frappe.db.sql("""
					SELECT sinv.`customer`, c.`customer_group`, SUM(sinv.`grand_total`) FROM `tabSales Invoice` sinv
					LEFT JOIN `tabCustomer` c ON sinv.`customer` = c.`name`
					WHERE sinv.`docstatus` = 1
					AND c.`customer_group` = "{}"
					AND sinv.`posting_date` LIKE "{}"
					GROUP BY c.`customer_group`
				""".format(cg.customer_group, clause_date))

				if get_sinv_amount :
					total_penjualan = get_sinv_amount[0][2]

				calcu_provision += (cg.provision_percentage * total_penjualan) / 100
				data_cust_group += " " + str(cg.customer_group)

			if calcu_provision > 0 :

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

				new_docu.posting_date = yesterday_date
				new_docu.provision_setup = i[0]
				new_docu.user_remark = docu.purpose + " ( " + str(data_cust_group) + " ) "

				new_docu.location = docu.location

				child = new_docu.append("accounts", {})
				child.account = docu.debit_account
				child.debit_in_account_currency = calcu_provision
				child.debit = calcu_provision

				child = new_docu.append("accounts", {})
				child.account = docu.credit_account
				child.credit_in_account_currency = calcu_provision
				child.credit = calcu_provision

				new_docu.flags.ignore_permission = True

				if docu.save_as == "Draft" :
					new_docu.save()
				elif docu.save_as == "Submit" :
					new_docu.save()
					new_docu.submit()
