// Copyright (c) 2016, riconova and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank Payment Upload"] = {
	"filters": [
		{
			fieldname:"bank_format",
			label: __("Bank Format"),
			fieldtype: "Select",
			options: "Zenith Bank Format\nFidelity Bank Format\nAccess Bank Format",
			reqd : 1
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"bank_account",
			label: __("Bank Account"),
			fieldtype: "Link",
			options: "Account",
			reqd : 1,
			"get_query": function () {
				return {
					filters: [
						["Account", "account_type", "=", "Bank"],
						["Account", "is_group", "=", "0"]
					]
				}
			},
			on_change: function(query_report) 
			{
				if(query_report.get_values().bank_account){
					var bank_account = query_report.get_values().bank_account;
					// frappe.msgprint(project);
					frappe.model.get_value('Account', {'name': bank_account}, ['bank_account_no'],
						function(d) {
							var bank_account_no = d['bank_account_no']
							frappe.query_report.set_filter_value("company_account", bank_account_no)
							
						}
					)
				}
					
			}
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"payroll_entry",
			label: __("Payroll Entry"),
			fieldtype: "Link",
			options: "Payroll Entry",
			reqd : 1,
			"get_query": function () {
				return {
					filters: [
						["Payroll Entry", "docstatus", "=", "1"]
					]
				}
			},
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"today_date",
			label: __("Today Date"),
			fieldtype: "Date",
			default: frappe.datetime.nowdate()
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"company_account",
			label: __("Company Account"),
			fieldtype: "Data",
			read_only: 1
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},

	]
};
