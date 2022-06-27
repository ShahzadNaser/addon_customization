// Copyright (c) 2016, riconova and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales by Sales Person"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
        
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
			reqd: 1
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_end_date"),
			reqd: 1
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [
                { "value": "Daily", "label": __("Daily") },
				{ "value": "Weekly", "label": __("Weekly") },
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
                { "value": "Half-Yearly", "label": __("Half-Yearly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			default: "Monthly",
			reqd: 1
		},
        {
            fieldname: "customer_group",
            label: __("Customer Group"),
            fieldtype: "Link",
            options: "Customer Group" 
        },
        {
            fieldname: "customer_from",
            label: __("Customer From"),
            fieldtype: "Link",
            options: "Customer" 
        },
        {
            fieldname: "customer_to",
            label: __("Customer To"),
            fieldtype: "Link",
            options: "Customer" 
        },
        {
            fieldname: "sub_customer",
            label: __("Sub Customer"),
            fieldtype: "Link",
            options: "Sub Customer" 
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group" 
        },
        {
            fieldname: "item_subgroup",
            label: __("Item SubGroup"),
            fieldtype: "Link",
            options: "Item SubGroup" 
        },
        {
            fieldname: "item",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item" 
        },
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse" 
        },
        {
            fieldname: "territory",
            label: __("Territory"),
            fieldtype: "Link",
            options: "Territory" 
        },
        {
            fieldname: "sales_person",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person" 
        },

	]
};
