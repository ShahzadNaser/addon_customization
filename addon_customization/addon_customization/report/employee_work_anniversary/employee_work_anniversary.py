# Copyright (c) 2013, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []

	columns = [
		"Employee ID:Link/Employee:100",
		"Employee Name:Data:200",
		"Gender:Data:100",
		"Department:Data:100",
		"Position:Data:100",
		"Date of Joining:Date:100",
		"Anniversary Year:Data:100"
	]

	position = ""
	if filters.get("position") :
		position = """ AND e.`designation` = "{}" """.format(filters.get("position"))

	department = ""
	if filters.get("department") :
		department = """ AND e.`department` = "{}" """.format(filters.get("department"))

	employee_name = ""
	if filters.get("employee_name") :
		employee_name = """ AND e.`employee_name` LIKE "%{}%" """.format(filters.get("employee_name"))

	month = ""
	if filters.get("month") :
		if filters.get("month") == "January" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("1")
		elif filters.get("month") == "February" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("2")
		elif filters.get("month") == "March" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("3")
		elif filters.get("month") == "April" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("4")
		elif filters.get("month") == "May" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("5")
		elif filters.get("month") == "June" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("6")
		elif filters.get("month") == "July" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("7")
		elif filters.get("month") == "August" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("8")
		elif filters.get("month") == "September" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("9")
		elif filters.get("month") == "October" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("10")
		elif filters.get("month") == "November" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("11")
		elif filters.get("month") == "December" :
			month = """ AND MONTH(e.`date_of_joining`) = "{}" """.format("12")

	data = frappe.db.sql("""

		SELECT e.`name`, e.`employee_name`, e.`gender`, e.`department`, e.`designation`, e.`date_of_joining`, YEAR(CURDATE()) - YEAR(e.`date_of_joining`)  
		FROM `tabEmployee` e
		WHERE e.`status` = "Active"
		{}
		{}
		{}
		{}

		ORDER BY e.`name` ASC


	""".format(position, department, employee_name, month))



	return columns, data
