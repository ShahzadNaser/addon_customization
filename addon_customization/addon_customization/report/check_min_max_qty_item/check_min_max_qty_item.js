// Copyright (c) 2016, riconova and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Check Min Max Qty Item"] = {
	"filters": [
		{
			fieldname:"item_code",
			label: __("Item"),
			fieldtype: "Link",
			options : "Item"
		},
		{
			fieldname:"item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options : "Item Group"
		},
		{
			fieldname:"item_subgroup",
			label: __("Item SubGroup"),
			fieldtype: "Link",
			options : "Item SubGroup"
		},
		{
			fieldname:"warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options : "Warehouse"
		},
		{
			fieldname:"stock_status",
			label: __("Stock Status"),
			fieldtype: "Select",
			options : "All\nLow\nHigh\nNormal"
		},

	]
};
