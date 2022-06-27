// Copyright (c) 2020, riconova and contributors
// For license information, please see license.txt


cur_frm.set_query("from_account", function(doc, cdt, cdn) {
		
			return {
	            "filters": [
	                ["account_type", "in", ["Cash", "Bank"]],
	                ["is_group", "=", 0]
	            ]
	        }
	    
	
});

cur_frm.set_query("to_account", function(doc, cdt, cdn) {
		
			return {
	            "filters": [
	                ["is_group", "=", 0]
	            ]
	        }
	    
	
});

cur_frm.cscript.custom_workflow_state = function(doc,dt,dn) {

	if(doc.workflow_state=="Accountant Approved" || doc.workflow_state=="Approved")
		{
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);

			frm.set_df_property("initial_money", "read_only", 1);
			frm.set_df_property("from_account", "read_only", 1);
			frm.set_df_property("to_account", "read_only", 1);

			frm.set_df_property("purpose", "read_only", 1);

			// frm.set_df_property("naming_series", "options", r.message);

			refresh_field("posting_date");
			refresh_field("posting_time");
			refresh_field("initial_money");
			refresh_field("from_account");
			refresh_field("status");
			refresh_field("to_account");

			refresh_field("purpose");

		}
}



frappe.ui.form.on('Request Expenses', {
	
	refresh: function(frm) {
		if(frm.doc.je_initial_money && !frm.doc.je_final_money && frm.doc.docstatus==1)
		{
			var finish_btn = frm.add_custom_button(__('Make Final JE'), function() {
				frappe.call({
					method:"addon_customization.addon_customization.doctype.request_expenses.request_expenses.create_je_final_money",
					args: {
						'request_expenses': frm.doc.name
					},
					callback: function(r) {
						if(!frm.doc.status){
							frappe.throw("Please choose the status first")
						}
						var doclist = frappe.model.sync(r.message);
						frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
					}
				});
			});
			finish_btn.addClass('btn-primary');
		}

		if(frm.doc.percent_je_final_money==100)
		{
			frm.set_df_property("status", "read_only", 1);
			frm.set_df_property("money", "read_only", 1);

			// frm.set_df_property("naming_series", "options", r.message);

			refresh_field("status");
			refresh_field("money");

		}

		if(frm.doc.workflow_state=="Accountant Approved" || doc.workflow_state=="Approved")
		{
			frm.set_df_property("posting_date", "read_only", 1);
			frm.set_df_property("posting_time", "read_only", 1);

			frm.set_df_property("initial_money", "read_only", 1);
			frm.set_df_property("from_account", "read_only", 1);
			frm.set_df_property("to_account", "read_only", 1);

			frm.set_df_property("purpose", "read_only", 1);

			// frm.set_df_property("naming_series", "options", r.message);

			refresh_field("posting_date");
			refresh_field("posting_time");
			refresh_field("initial_money");
			refresh_field("from_account");
			refresh_field("status");
			refresh_field("to_account");

			refresh_field("purpose");

		}

		

	}
});
