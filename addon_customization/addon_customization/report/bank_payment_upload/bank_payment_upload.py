# Copyright (c) 2013, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data, temp_data = [], [], []

	columns = [
		"TRANSACTION REFERENCE NUMBER:Data:200",
		"BENEFICIARY NAME:Data:200",
		"AMOUNT:Currency:150",
		"PAYMENT DUE DATE:Data:150",
		"BENEFICIARY CODE:Data:150",
		"BENEFICIARY ACCT NUMBER:Data:200",
		"BRANCH SORT CODE(9 DIGITS):Data:200",
		"DEBIT ACCT:Data:100",
		]


	payroll_entry = ""
	if filters.get("payroll_entry") :
		payroll_entry = """ AND pe.`name` = "{}" """.format(filters.get("payroll_entry"))


	bank_account = ""
	if filters.get("bank_account") :
		bank_account = """ AND pe.`payment_account` = "{}" """.format(filters.get("bank_account"))


	temp_data = frappe.db.sql("""
		SELECT

		sp.`name`,
		sp.`employee_name`,
		sp.`net_pay`,
		CURDATE(),
		sp.`employee`,
		e.`bank_ac_no`,
		pe.`payment_account`,
		e.`sort_code`

		FROM `tabPayroll Entry` pe
		LEFT JOIN `tabSalary Slip` sp ON pe.`name` = sp.`payroll_entry`
		LEFT JOIN `tabEmployee` e ON sp.`employee` = e.`name`

		WHERE pe.`docstatus` = 1
		AND sp.`docstatus` = 1

		{}
		{}

		ORDER BY pe.`name`, sp.`employee`

	""".format(payroll_entry, bank_account))

	if temp_data :
		for i in temp_data :
			sort_code = ""
			bank_account_no = ""
			if i[6] :
				bank_account_no = frappe.get_doc("Account", str(i[6])).bank_account_no


			if i[7] :
				data.append([ str(i[0]).replace("Sal ",""), i[1], i[2], str(i[3]).split("-")[2]+"/"+str(i[3]).split("-")[1]+"/"+str(i[3]).split("-")[0], str(i[4]), str(i[5]), str(i[7]), str(bank_account_no) ])
			else :
				data.append([ str(i[0]).replace("Sal ",""), i[1], i[2], str(i[3]).split("-")[2]+"/"+str(i[3]).split("-")[1]+"/"+str(i[3]).split("-")[0], str(i[4]), str(i[5]),"", str(bank_account_no) ])






	return columns, data
