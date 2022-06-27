// Copyright (c) 2021, riconova and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transfer into Item', {
	// refresh: function(frm) {

	// }
});

cur_frm.set_query("from_item", "items", function(doc, cdt, cdn) {
		
			return {
	            "filters": [
	                ["item_group", "in", ["Foam Block", "Chemical"]],
	            ]
	        }
	    
	
});



cur_frm.cscript.custom_from_item = function(doc,dt,dn) {
	
	var d = locals[dt][dn];

	var posting_date = doc.posting_date
	var posting_time = doc.posting_time
	if(doc.name){
		var document_name = doc.name
	} else {
		var document_name = ""
	}
	
	var item_code = d.from_item
	var warehouse = doc.default_from_warehouse

	d.from_warehouse = doc.default_from_warehouse
	d.to_warehouse = doc.default_to_warehouse

	if(doc.default_from_warehouse){
		
		frappe.call({
			method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
			args: {
				"posting_date" : doc.posting_date,
				"posting_time" : doc.posting_time,
				"document_name" : doc.name,
				"item_code" : d.from_item,
				"warehouse" : doc.default_from_warehouse
				
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "basic_rate", data.message["valuation_rate"]);
				d.basic_amount = d.qty * data.message["valuation_rate"]
			}
		});
	}
	refresh_field("items")
}

cur_frm.cscript.custom_qty = function(doc,dt,dn) {
	
	var d = locals[dt][dn];

	d.basic_amount = d.qty * d.basic_rate

	
	refresh_field("items")
}

cur_frm.cscript.custom_default_from_warehouse = function(doc,dt,dn) {
	
	if(doc.items){

		$.each(doc.items || [], function(i, d) {

			d.from_warehouse = doc.default_from_warehouse
			
			frappe.call({
				method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
				args: {
					"posting_date" : doc.posting_date,
					"posting_time" : doc.posting_time,
					"document_name" : doc.name,
					"item_code" : d.from_item,
					"warehouse" : doc.default_from_warehouse
					
				},
				callback: function (data) {
					d.basic_rate = data.message["valuation_rate"];
					d.basic_amount = d.qty * data.message["valuation_rate"]
				}
			});

		})

			
	}
	refresh_field("items")
	refresh_field("default_from_warehouse")
}

cur_frm.cscript.custom_default_to_warehouse = function(doc,dt,dn) {
	
	if(doc.items){

		$.each(doc.items || [], function(i, d) {

			d.to_warehouse = doc.default_to_warehouse
				
		})
	}
	refresh_field("items")
	refresh_field("default_to_warehouse")
}

cur_frm.cscript.custom_default_warehouse = function(doc,dt,dn) {
	
	var d = locals[dt][dn];

	var posting_date = doc.posting_date
	var posting_time = doc.posting_time
	if(doc.name){
		var document_name = doc.name
	} else {
		var document_name = ""
	}
	
	var item_code = d.from_item
	var warehouse = d.default_warehouse

	if(warehouse){
		
		frappe.call({
			method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
			args: {
				"posting_date" : doc.posting_date,
				"posting_time" : doc.posting_time,
				"document_name" : doc.name,
				"item_code" : d.from_item,
				"warehouse" : warehouse
				
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "basic_rate", data.message["valuation_rate"]);
				d.basic_amount = d.qty * data.message["valuation_rate"]
			}
		});
	}
	refresh_field("items")
}