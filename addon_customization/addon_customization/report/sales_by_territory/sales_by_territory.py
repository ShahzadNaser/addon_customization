# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils import getdate, flt, add_to_date, add_days,date_diff
from six import iteritems
from erpnext.accounts.utils import get_fiscal_year
from datetime import date, timedelta
from erpnext.accounts.report.financial_statements import (get_period_list, get_columns, get_data)
# import frappe

def execute(filters=None):
	columns, data = [
		"Territory:Link/Territory:100"
	], []

	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

	from dateutil.relativedelta import relativedelta, MO
	from_date, to_date = getdate(filters.get("from_date")), getdate(filters.get("to_date"))

	increment = {
		"Monthly": 1,
		"Quarterly": 3,
		"Half-Yearly": 6,
		"Yearly": 12
	}.get(filters.get("range"), 1)

	if filters.get("range") in ['Monthly', 'Quarterly']:
		from_date = from_date.replace(day=1)
	elif filters.get("range") == "Yearly":
		from_date = get_fiscal_year(from_date)[1]
	else:
		from_date = from_date + relativedelta(from_date, weekday=MO(-1))

	periodic_daterange = []
	for dummy in range(1, 53):
		if filters.get("range") == "Weekly":
			period_end_date = add_days(from_date, 6)
		else:
			period_end_date = add_to_date(from_date, months=increment, days=-1)

		if period_end_date > to_date:
			period_end_date = to_date

		periodic_daterange.append(period_end_date)

		from_date = add_days(period_end_date, 1)
		if period_end_date == to_date:
			break


	if filters.get("range") == "Daily":
		periodic_daterange = []
		periodic_daterange.append(getdate(filters.get("from_date")))
		from_date_days = getdate(filters.get("from_date"))
		to_date_days  =  getdate(filters.get("from_date"))
		for dummy in range(1,date_diff(getdate(filters.get("to_date")),getdate(filters.get("from_date")))):
			period_end_date = add_days(from_date_days, 1)
			
			if period_end_date > to_date:
				period_end_date = periodic_daterange = []

			periodic_daterange.append(period_end_date)
			from_date_days = period_end_date
			if period_end_date == to_date_days:
				break
		periodic_daterange.append(getdate(filters.get("to_date")))

	if filters.get("range") == "Half-Yearly":
		periodic_daterange = []
		from_date_bi = getdate(filters.get("from_date"))
		to_date_bi = getdate(filters.get("to_date"))

		from_date = from_date_bi.strftime("%Y")
		to_date = to_date_bi.strftime("%Y")
		period_list = get_period_list(from_date, to_date,"Half-Yearly", False, filters.company)

		for i in period_list:
			periodic_daterange.append(i["label"])



	# frappe.throw("{}".format(period_list))

	def get_period(posting_date):
		if filters.get("range") == 'Weekly':
			period = "Week " + str(posting_date.isocalendar()[1]) + " " + str(posting_date.year)
		elif filters.get("range") == 'Monthly':
			period = str(months[posting_date.month - 1]) + " " + str(posting_date.year)
		elif filters.get("range") == 'Quarterly':
			period = "Quarter " + str(((posting_date.month - 1) // 3) + 1) + " " + str(posting_date.year)
		elif filters.get("range") == "Daily":
			period = str(posting_date)
		else:
			year = get_fiscal_year(posting_date, company=filters.get("company"))
			period = str(year[0])
		return period

	# count = 0
	for end_date in periodic_daterange:
		# count = count + 1
		if filters.get("range") == "Half-Yearly":
			columns.append({
				"label": end_date,
				"fieldname": end_date,
				"fieldtype": "Float",
				"width": 120
				})
		else:
			period = get_period(end_date)
			columns.append({
				"label": _(period),
				"fieldname": scrub(period),
				"fieldtype": "Float",
				"width": 120
				})

	columns.append({
		"label": "Net Total",
		"fieldname": "net_total",
		"fieldtype": "Float",
		"width": 120
		})
	data_sinv = {}
	conditions = ""
	sales_person_tab = ""
	sales_person_cond = ""
	item_tab = ""
	item_cond = ""



	if filters.get("sales_person"):
		sales_person_tab = """ , `tabSales Team` st """
		sales_person_cond = """  AND si.`name` =  st.`parent` AND st.`sales_person` = "{}" """.format(filters.get("sales_person"))

	if filters.get("item_subgroup"):
		item_tab = """ , `tabItem` i """
		item_cond = """ AND sii.`item_code` = i.`name` AND  i.`item_subgroup` = "{}"  """.format(filters.get("item_subgroup"))

	if filters.get("customer_group"):
		conditions += """ AND si.`customer_group` = "{}" """.format(filters.get("customer_group"))

	if filters.get("customer_from"):
		conditions += """ AND si.`customer` >= "{}" """.format(filters.get("customer_from"))

	if filters.get("customer_to"):
		conditions += """ AND si.`customer` <= "{}" """.format(filters.get("customer_to"))

	if filters.get("sub_customer"):
		conditions += """ AND si.`sub_customer` = "{}" """.format(filters.get("sub_customer"))

	if filters.get("territory"):
		conditions += """ AND si.`territory` = "{}" """.format(filters.get("territory"))

	if filters.get("item_group"):
		conditions += """ AND sii.`item_group` = "{}" """.format(filters.get("item_group"))

	if filters.get("item"):
		conditions += """ AND sii.`item_code` = "{}" """.format(filters.get("item"))

	if filters.get("warehouse"):
		conditions += """ AND  sii.`warehouse` = "{}" """.format(filters.get("warehouse"))

	if filters.get("from_date") and filters.get("to_date"):
		conditions += """ AND  si.`posting_date` between "{}" AND "{}" """.format(filters.get("from_date"), filters.get("to_date"))




	data_sinv = frappe.db.sql("""  SELECT si.`territory`, si.`posting_date`, sii.`net_amount` AS `net_total` 
		FROM `tabSales Invoice` si,`tabSales Invoice Item` sii {0} {2}
		WHERE si.`name` = sii.`parent`
		AND si.`docstatus` = 1
		{1}
		{3}
		{4}
		 """.format(sales_person_tab, sales_person_cond, item_tab, item_cond,  conditions), as_dict = 1)


	result = {}
	for i in data_sinv:

		if i["territory"] in result:

			for k in result[i["territory"]]:
				start_date_update = k
				if filters.get("range") == 'Weekly':
					start_date_update = k - timedelta(6)
				elif filters.get("range") == "Monthly":
					start_date_update = k - timedelta(int(k.strftime('%d'))-1)
				elif filters.get("range") == "Quarterly":
					start_date_update = (k - relativedelta(months=+3)) + timedelta(1)



				if filters.get("range") in ['Monthly', 'Quarterly',"Weekly"] :
					if i["posting_date"] >= start_date_update and i["posting_date"] <= k : 
						result[i["territory"]][k] = result[i["territory"]][k] + i["net_total"]
				elif filters.get("range") in ["Daily"]:
					if i["posting_date"] == k:
						result[i["territory"]][k] = result[i["territory"]][k] + i["net_total"]
				elif filters.get("range") in ["Yearly"]:
					if i["posting_date"].strftime('%Y') == k.strftime('%Y'):
						result[i["territory"]][k] =  result[i["territory"]][k] + i["net_total"]


			if filters.get("range") == "Half-Yearly":
				start_date = ""
				end_date = ""
				label = ""
				for l in period_list:
					# frappe.throw(str(i["posting_date"]) + " = " + str(l["from_date"]))
					if str(i["posting_date"]) >= str(l["from_date"]) and str(i["posting_date"]) <= str(l["to_date"]):
						start_date = str(l["from_date"])
						end_date = str(l["to_date"])
						label = l["label"]
		
				if str(i["posting_date"]) >= start_date and str(i["posting_date"]) <= end_date:
					result[i["territory"]][label] = result[i["territory"]][label]  +  i["net_total"]
		else:
			result[i["territory"]] = {}
			for j in periodic_daterange:
				result[i["territory"]].update({j : 0})
			
			for k in result[i["territory"]]:
				start_date_new = k

				
				if filters.get("range") == 'Weekly':
					start_date_new = k - timedelta(6)
				elif filters.get("range") == "Monthly":
					start_date_new = k - timedelta(int(k.strftime('%d'))-1)
				elif filters.get("range") == "Quarterly":
					start_date_new = (k - relativedelta(months=+3)) + timedelta(1)

				if filters.get("range") in ['Monthly', 'Quarterly',"Weekly"] :
					if i["posting_date"] >= start_date_new and i["posting_date"] <= k : 
						result[i["territory"]][k] = i["net_total"]
				elif filters.get("range") in ["Daily"]:
					if i["posting_date"] == k:
						result[i["territory"]][k] =  i["net_total"]
				elif filters.get("range") == "Yearly":
					if i["posting_date"].strftime('%Y') == k.strftime('%Y'):
						result[i["territory"]][k] =  i["net_total"]

			if filters.get("range") == "Half-Yearly":
				start_date = ""
				end_date = ""
				label = ""
				for l in period_list:
					if str(i["posting_date"]) >= str(l["from_date"]) and str(i["posting_date"]) <= str(l["to_date"]):
						start_date = str(l["from_date"])
						end_date = str(l["to_date"])
						label = l["label"]

				if str(i["posting_date"]) >= start_date and str(i["posting_date"]) <= end_date:
					result[i["territory"]][label] =  i["net_total"]



	for i in data_sinv:
		result[i["territory"]].update({"net_total" : 0 })
	    

	for i in data_sinv:
		total = 0
		for j in result[i["territory"]]:
			if j != "net_total" :
				total += result[i["territory"]][j] 
		result[i["territory"]]["net_total"] = total



	# frappe.throw(str(result))
	for key, value in result.items():
		result_data = []
		result_data.append(key)
		for i , j in value.items():
			result_data.append(j)

		data.append(result_data)




	return columns, data




