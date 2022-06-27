// Copyright (c) 2020, riconova and contributors
// For license information, please see license.txt

frappe.ui.form.on('Prepayment', {

	refresh: function(frm) {
    frm.set_query("debit_account", function() {
      return {
        filters: {'is_group': 0}
      };
    });
    frm.set_query("credit_account", function() {
      return {
        filters: {'is_group': 0}
      };
    });
		// if(frm.doc.docstatus == 1 && frm.doc.status_prepayment == "Open") {

  //           cur_frm.add_custom_button(__('Close'), function() {
  //               frappe.call({
  //                   method: "addon_customization.addon_customization.doctype.prepayment.prepayment.close_prepayment",
  //                   args: {
  //                       "docname": frm.doc.name
  //                   },
  //                   callback: function(r) {
  //                       frm.reload_doc();
  //                       frappe.msgprint("All Date will be Disable")
  //                   }
  //               });
  //           });


  //       } else if(frm.doc.docstatus == 1 && frm.doc.status_prepayment == "Closed") {
  //       	cur_frm.add_custom_button(__('Open'), function() {
  //               frappe.call({
  //                   method: "addon_customization.addon_customization.doctype.prepayment.prepayment.open_prepayment",
  //                   args: {
  //                       "docname": frm.doc.name
  //                   },
  //                   callback: function(r) {
  //                       frm.reload_doc();
  //                       frappe.msgprint("All Date will be Enable")
  //                   }
  //               });
  //           });
  //       }

	}
});
