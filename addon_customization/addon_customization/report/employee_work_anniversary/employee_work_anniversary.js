// Copyright (c) 2016, riconova and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Work Anniversary"] = {
	"filters": [
		{
			fieldname:"position",
			label: __("Position"),
			fieldtype: "Link",
			options: "Designation",
		},
		{
			fieldname:"department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname:"month",
			label: __("Month"),
			fieldtype: "Select",
			options: "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
		},
		{
			fieldname:"employee_name",
			label: __("Employee Name"),
			fieldtype: "Data"
		},

	]
};
