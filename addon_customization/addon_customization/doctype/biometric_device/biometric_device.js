// Copyright (c) 2022, riconova and contributors
// For license information, please see license.txt

frappe.ui.form.on('Biometric Device', {
	refresh: function(frm) {
		if(cur_frm.doc.token){
			cur_frm.add_custom_button("Fetch Attendance for Date",()=>{
				frm.trigger('create_dialog')
			})
		}
	},
	create_dialog:function(frm){
		var fields=[]
		fields=fields.concat({
			"label": "From",
			"fieldname": 'from_date',
			"fieldtype": 'Date',
			"reqd": 1,
			"description": "Fetch Attendance From"
		},{
			"label": "To",
			"fieldname": 'to_date',
			"fieldtype": 'Date',
			"reqd": 1,
			"description": "Fetch Attendance Till"
		})
		var d = new frappe.ui.Dialog({
			title: __('Fetch Attendance Records'),
			fields: fields
		})
		d.set_primary_action(__('Fetch Attendance'), function() {
			var args_=d.get_values()
			if(!args_) return ;
			d.hide();
			frappe.call({
				method:"addon_customization.addon_customization.doctype.biometric_device.biometric_device.fetch_attendance",
				freeze: true,
				freeze_message:'Fetching Records',
				args:{
					from_date:d.get_value('from_date'),
					to_date:d.get_value('to_date'),
					doc:frm.doc.name
				},
				callback:(r)=>{
					r.message ? frappe.msgprint("Records Fetched!"):frappe.msgprint("An Error occured. Please check error logs")
					
				}


			})
			frm.refresh_fields()
		})
		d.show();
	}
});
