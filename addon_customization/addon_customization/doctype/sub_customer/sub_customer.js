// Copyright (c) 2020, riconova and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sub Customer', {
	refresh: function(frm) {
		if(!frm.doc.__islocal) {
			
			// custom buttons
			frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.set_route('query-report',"Detail General Ledger", { "group_by" : "Group by Voucher (Consolidated)", "party_type": "Customer", "party":frm.doc.customer,"sub_customer":frm.doc.name});
			});

			frm.add_custom_button(__('Accounts Receivable'), function() {
				frappe.set_route('query-report', 'Accounts Receivable', {"customer":frm.doc.customer});
			});

			
		}
	}
});
