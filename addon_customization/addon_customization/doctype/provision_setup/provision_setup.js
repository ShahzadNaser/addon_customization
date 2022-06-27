// Copyright (c) 2020, riconova and contributors
// For license information, please see license.txt

frappe.ui.form.on('Provision Setup', {
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

	}
});
