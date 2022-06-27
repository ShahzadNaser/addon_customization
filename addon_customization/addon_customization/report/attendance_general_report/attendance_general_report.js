// Copyright (c) 2016, riconova and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Attendance General Report"] = {
	"filters": [

		// {
		// 	fieldname: "filter_by",
		// 	label: __("Filter By"),
		// 	fieldtype: "Select",
		// 	options: "Employee ID\nBiometric Range",
		// 	default: "Employee ID",
		// 	on_change: function(query_report) 
		// 	{
		// 		var filter_by = query_report.get_values().filter_by;

		// 		if(filter_by == "Employee ID"){
		// 			var dt_filter= frappe.query_report.get_filter("employee");
		// 			dt_filter.toggle(true);
		// 			dt_filter.refresh();

		// 			var dt_filter= frappe.query_report.get_filter("employee_name");
		// 			dt_filter.toggle(true);
		// 			dt_filter.refresh();

		// 			frappe.query_report.set_filter_value("biometric_from", "")
		// 			frappe.query_report.set_filter_value("biometric_to", "")

		// 			var dt_filter= frappe.query_report.get_filter("biometric_from");
		// 			dt_filter.toggle(false);
		// 			dt_filter.refresh();

		// 			var dt_filter= frappe.query_report.get_filter("biometric_to");
		// 			dt_filter.toggle(false);
		// 			dt_filter.refresh();


		// 		} else {
		// 			var dt_filter= frappe.query_report.get_filter("employee");
		// 			dt_filter.toggle(false);
		// 			dt_filter.refresh();

		// 			var dt_filter= frappe.query_report.get_filter("employee_name");
		// 			dt_filter.toggle(false);
		// 			dt_filter.refresh();

		// 			frappe.query_report.set_filter_value("employee", "")
		// 			frappe.query_report.set_filter_value("employee_name", "")

		// 			var dt_filter= frappe.query_report.get_filter("biometric_from");
		// 			dt_filter.toggle(true);
		// 			dt_filter.refresh();

		// 			var dt_filter= frappe.query_report.get_filter("biometric_to");
		// 			dt_filter.toggle(true);
		// 			dt_filter.refresh();

		// 		}
		// 	}
		// },

		// {
		// 	fieldname: "employee",
		// 	label: __("Employee"),
		// 	fieldtype: "Link",
		// 	options: "Employee",
		// 	on_change: function(query_report) 
		// 	{
		// 		if(query_report.get_values().employee){
		// 			var employee = query_report.get_values().employee;
		// 			// frappe.msgprint(project);
		// 			frappe.model.get_value('Employee', {'name': employee}, ['employee_name'],
		// 				function(d) {
		// 					var employee_name = d['employee_name']
		// 					frappe.query_report.set_filter_value("employee_name", employee_name)
							
		// 				}
		// 			)
		// 		}
					
		// 	}
		// },
		// {
		// 	fieldname:"employee_name",
		// 	label: __("Employee Name"),
		// 	fieldtype: "Data",
		// 	read_only: 1,
		// 	hidden:0
		// 	// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
		// 	// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		// },
		{
			fieldname:"biometric_from",
			label: __("Biometric From"),
			fieldtype: "Link",
			options: "Employee"
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"biometric_to",
			label: __("Biometric To"),
			fieldtype: "Link",
			options: "Employee"
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"from_date",
			label: __("From Date"),
			fieldtype: "Date",
			// default: frappe.datetime.add_months(frappe.datetime.month_start(), -1),
			default: frappe.datetime.month_start(frappe.datetime.nowdate()),
			reqd: 1
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			default: frappe.datetime.month_end(frappe.datetime.nowdate()),
			reqd: 1
		},
		{
			fieldname:"report_type",
			label: __("Report Type"),
			fieldtype: "Select",
			options: "PRESENT REPORT\nABSENT REPORT\nLATE ARRIVAL\nEARLY EXIT\nATTENDANCE SUMMARY",
			reqd:1
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},
		{
			fieldname:"employee_status",
			label: __("Employee Status"),
			fieldtype: "Select",
			options: "Active\nLeft",
			default:"Active"
			// default: frappe.datetime.add_days(frappe.datetime.month_start(),-1),
			// fetch_from: frappe.query_report.get_filter('project').value.sales_order
		},



	],

	onload: function(query_report) 
	{
		var filter_by = query_report.get_values().filter_by;

		if(filter_by == "Employee ID"){
			var dt_filter= frappe.query_report.get_filter("employee");
			dt_filter.toggle(true);
			dt_filter.refresh();

			var dt_filter= frappe.query_report.get_filter("employee_name");
			dt_filter.toggle(true);
			dt_filter.refresh();

			var dt_filter= frappe.query_report.get_filter("biometric_from");
			dt_filter.toggle(false);
			dt_filter.refresh();

			var dt_filter= frappe.query_report.get_filter("biometric_to");
			dt_filter.toggle(false);
			dt_filter.refresh();


		} else {
			var dt_filter= frappe.query_report.get_filter("employee");
			dt_filter.toggle(false);
			dt_filter.refresh();

			var dt_filter= frappe.query_report.get_filter("employee_name");
			dt_filter.toggle(false);
			dt_filter.refresh();

			var dt_filter= frappe.query_report.get_filter("biometric_from");
			dt_filter.toggle(true);
			dt_filter.refresh();

			var dt_filter= frappe.query_report.get_filter("biometric_to");
			dt_filter.toggle(true);
			dt_filter.refresh();

		}
	}
};
