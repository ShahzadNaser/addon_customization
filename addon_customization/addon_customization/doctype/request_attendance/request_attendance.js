// Copyright (c) 2020, riconova and contributors
// For license information, please see license.txt

frappe.ui.form.on('Request Attendance', {
	half_day: function(frm) {
		if(frm.doc.half_day == 1){
			frm.set_df_property('half_day_date', 'reqd', true);
		}
		else{
			frm.set_df_property('half_day_date', 'reqd', false);
		}
	}
});
