// Copyright (c) 2016, riconova and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Sales Performance Report"] = {
	"filters": [
		{
			fieldname:"fds",
			label: __("From Date Sales"),
			fieldtype: "Data",
			default: "From Date Sales",
			read_only: 1
		},
		{
			fieldname:"from_date_sales",
			label: __("From Date Sales"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(frappe.datetime.nowdate()),
			reqd: 1
		},
		{
			fieldname:"tds",
			label: __("To Date Sales"),
			fieldtype: "Data",
			default: "To Date Sales",
			read_only: 1
		},
		{
			fieldname:"to_date_sales",
			label: __("To Date Sales"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(frappe.datetime.nowdate()),
			reqd: 1
		},
		
		{
			"fieldtype": "Break",
		},
		{
			fieldname:"company",
			label: __("Company"),
			fieldtype: "Link",
			options : "Company",
			read_only : 1,
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname:"customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options : "Customer Group"
		},
		{
			fieldname:"customer_from",
			label: __("Customer From"),
			fieldtype: "Link",
			options : "Customer"
		},
		{
			fieldname:"customer_to",
			label: __("Customer To"),
			fieldtype: "Link",
			options : "Customer"
		},
		{
			fieldname:"sub_customer",
			label: __("Sub Customer"),
			fieldtype: "Link",
			options : "Sub Customer"
		},
		{
			fieldname:"territory",
			label: __("Territory"),
			fieldtype: "Link",
			options : "Territory"
		},
		{
            fieldname: "sales_person",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person" 
        },
		{
			"fieldtype": "Break",
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

	]
};
