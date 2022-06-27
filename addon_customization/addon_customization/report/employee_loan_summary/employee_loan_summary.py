# Copyright (c) 2013, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils import getdate, flt, add_to_date, add_days,date_diff
from six import iteritems
from erpnext.accounts.utils import get_fiscal_year
from datetime import date, timedelta
from erpnext.accounts.report.financial_statements import (get_period_list, get_columns, get_data)

def execute(filters=None):
	columns, data = [
		"Employee ID:Link/Employee:100",
		"Employee Name:Data:100",
		"Opening Balance:Currency:100",
		"Loan Amount:Currency:100",
		"Paid Amount:Currency:100",
		"Closing Balance:Currency:100"
	], []

	# ambil employee dulu

	get_employee = frappe.db.sql("""
		SELECT e.`name`, e.`employee_name` FROM `tabEmployee` e
		where e.`status` = "Active"
		ORDER BY e.`name`
	""")

	if get_employee :
		employee_id = ""
		employee_name = ""
		opening_balance = 0
		loan_amount = 0
		paid_amount = 0
		closing_balance = 0
		
		account_loan = "Loan to Employees - WINSO"
		if filters.get("company"):
			get_comp = frappe.get_doc("Company", filters.get("company"))
			account_loan = "Loan to Employees - "+str(get_comp.abbr)

		for e in get_employee :
			employee_id = e[0]
			employee_name = e[1]

			opening_balance = 0
			loan_amount = 0
			paid_amount = 0
			closing_balance = 0

			# ambil opening
			get_opening = frappe.db.sql("""
				SELECT gle.`party`, SUM(gle.`debit`), SUM(gle.`credit`) FROM `tabGL Entry` gle
				WHERE gle.`account` = "{}"
				AND gle.`posting_date` < "{}"
				AND gle.`party` = "{}"
				GROUP BY gle.`party`
			""".format(account_loan,filters.get("from_date"), employee_id))

			if get_opening :
				for go in get_opening :
					opening_balance += float(go[1]) - float(go[2])

			# ambil current
			get_current = frappe.db.sql("""
				SELECT gle.`party`, SUM(gle.`debit`), SUM(gle.`credit`) FROM `tabGL Entry` gle
				WHERE gle.`account` = "{}"
				AND gle.`posting_date` BETWEEN "{}" AND "{}"
				AND gle.`party` = "{}"
				GROUP BY gle.`party`
			""".format(account_loan,filters.get("from_date"),filters.get("to_date"), employee_id))

			if get_current :
				for gc in get_current :
					loan_amount += float(gc[1])
					paid_amount += float(gc[2])

			closing_balance = opening_balance + loan_amount - paid_amount

			if closing_balance != 0 :
				data.append([employee_id, employee_name, opening_balance, loan_amount, paid_amount, closing_balance])





	return columns, data
