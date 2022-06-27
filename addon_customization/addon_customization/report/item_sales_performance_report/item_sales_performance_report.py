# Copyright (c) 2013, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []

	columns = [
		"Item Code:Data:150",
		"Description:Data:150",
		"Qty Return:Float:100",
		"Qty Sold:Float:100",
		"Qty Net:Float:100",
		"Net Sales:Currency:100"
	]


	date_clause = ""
	if filters.get("from_date_sales") and filters.get("to_date_sales") :
		date_clause = """ AND sinv.`posting_date` BETWEEN "{0}" AND "{1}" """.format(filters.get("from_date_sales"),filters.get("to_date_sales"))


	customer_clause = ""
	if filters.get("customer_from") and filters.get("customer_to") :
		customer_clause = """ AND sinv.`customer` BETWEEN "{}" AND "{}" """.format(filters.get("customer_from"),filters.get("customer_to"))

	elif filters.get("customer_from") :
		customer_clause = """ AND sinv.`customer` = "{}" """.format(filters.get("customer_from"))


	elif filters.get("customer_to") :
		customer_clause = """ AND sinv.`customer` = "{}" """.format(filters.get("customer_to"))


	customer_group_clause = ""
	if filters.get("customer_group") :
		customer_group_clause = """ AND sinv.`customer_group` = "{}" """.format(filters.get("customer_group"))


	item_group_clause = ""
	if filters.get("item_group") :
		item_group_clause = """ AND i.`item_group` = "{}" """.format(filters.get("item_group"))


	item_subgroup_clause = ""
	if filters.get("item_subgroup") :
		item_subgroup_clause = """ AND i.`item_subgroup` = "{}" """.format(filters.get("item_subgroup"))


	warehouse_clause = ""
	if filters.get("warehouse") :
		warehouse_clause = """ AND sinvi.`warehouse` = "{}" """.format(filters.get("warehouse"))

	sub_customer_clause = ""
	if filters.get("sub_customer") :
		sub_customer_clause = """ AND sinv.`sub_customer` = "{}" """.format(filters.get("sub_customer"))

	territory_clause = ""
	if filters.get("territory") :
		territory_clause = """ AND sinv.`territory` = "{}" """.format(filters.get("territory"))

	sales_person_tab = ""
	sales_person_cond = ""
	if filters.get("sales_person"):
		sales_person_tab = """ LEFT JOIN `tabSales Team` st ON sinv.`name` =  st.`parent` """
		sales_person_cond = """ AND st.`sales_person` = "{}" """.format(filters.get("sales_person"))


	data = frappe.db.sql("""
		
		SELECT

		sinvi.`item_code`,
		sinvi.`item_name`,
		SUM(IF(sinvi.`qty`<0,sinvi.`qty`,0)) AS qty_return,
		SUM(IF(sinvi.`qty`>0,sinvi.`qty`,0)) AS qty_sold,

		SUM(IF(sinvi.`qty`<0,sinvi.`qty`,0)) + SUM(IF(sinvi.`qty`>0,sinvi.`qty`,0)) AS qty_net,

		SUM(sinvi.`net_amount`) as net_sales


		FROM `tabSales Invoice` sinv
		LEFT JOIN `tabSales Invoice Item` sinvi ON sinv.`name` = sinvi.`parent`
		LEFT JOIN `tabItem` i ON sinvi.`item_code` = i.`name`
		{8}
		WHERE sinv.`docstatus` = 1

		{0}
		{1}
		{2}
		{3}
		{4}
		{5}
		{6}
		{7}
		{9}

		GROUP BY sinvi.`item_code`
		ORDER BY sinvi.`item_code`


	""".format(date_clause, customer_clause, customer_group_clause, item_group_clause, item_subgroup_clause, warehouse_clause, sub_customer_clause, territory_clause, sales_person_tab, sales_person_cond))






	return columns, data
