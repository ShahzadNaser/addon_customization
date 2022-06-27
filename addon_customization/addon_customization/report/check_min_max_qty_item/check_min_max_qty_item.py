# Copyright (c) 2013, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []

	columns = [
		"Item Code:Data:150",
		"Item Name:Data:150",
		"Qty Actual:Float:100",
		"Qty Min:Float:100",
		"Qty Max:Float:100",
		"Warehouse:Data:100",
		"Reminder Days:Data:100",
		"Stock Status:Data:100",
		"Recommended Qty:Float:100"
	]


	item_code_clause = ""
	if filters.get("item_code") :
		item_code_clause = """ AND i.`item_code` = "{}" """.format(filters.get("item_code"))

	item_group_clause = ""
	if filters.get("item_group") :
		item_group_clause = """ AND i.`item_group` = "{}" """.format(filters.get("item_group"))


	item_subgroup_clause = ""
	if filters.get("item_subgroup") :
		item_subgroup_clause = """ AND i.`item_subgroup` = "{}" """.format(filters.get("item_subgroup"))


	warehouse_clause = ""
	if filters.get("warehouse") :
		warehouse_clause = """ AND b.`warehouse` = "{}" """.format(filters.get("warehouse"))

	stock_status_clause = ""
	if filters.get("stock_status") == "All" :
		stock_status_clause = ""
	elif filters.get("stock_status") == "Low" :
		stock_status_clause = """ AND (b.`actual_qty` < mmq.`min_qty`) """
	elif filters.get("stock_status") == "High" :
		stock_status_clause = """ AND (b.`actual_qty` > mmq.`max_qty`) """
	elif filters.get("stock_status") == "Normal" :
		stock_status_clause = """ AND b.`actual_qty` BETWEEN mmq.`min_qty` AND mmq.`max_qty` """


	data = frappe.db.sql("""
		
		SELECT 
		b.`item_code`, 
		i.`item_name`, 
		b.`actual_qty`, 
		mmq.`min_qty`, 
		mmq.`max_qty`, 
		b.`warehouse`, 
		i.`reminder_days`,
		IF(b.`actual_qty` < mmq.`min_qty`, "Low", IF( b.`actual_qty` > mmq.`max_qty`, "High", "Normal" ) ), 
		IF(b.`actual_qty` < mmq.`min_qty`, mmq.`max_qty` - b.`actual_qty` , 0)

		FROM `tabBin` b
		LEFT JOIN `tabMin Max Qty Item` mmq ON b.`item_code` = mmq.`parent` AND b.`warehouse` = mmq.`warehouse`
		LEFT JOIN `tabItem` i ON b.`item_code` = i.`name`
		WHERE mmq.`min_qty` >= 0
		AND mmq.`max_qty` >= 0
		{}
		{}
		{}
		{}
		{}


	""".format(item_group_clause, item_subgroup_clause, warehouse_clause, item_code_clause, stock_status_clause))





	return columns, data
