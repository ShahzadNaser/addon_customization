// Copyright (c) 2020, RICO NOVA and contributors
// For license information, please see license.txt


cur_frm.add_fetch('item_production', 'item_name', 'item_name');
cur_frm.add_fetch('item_production', 'stock_uom', 'stock_uom');
cur_frm.add_fetch('item_production', 'block_size', 'foam_block_size');

cur_frm.add_fetch('item_material', 'item_name', 'item_name');
cur_frm.add_fetch('item_material', 'stock_uom', 'stock_uom');


cur_frm.cscript.custom_item_material = function(doc,dt,dn) {
	
	var d = locals[dt][dn];

	var posting_date = doc.posting_date
	var posting_time = doc.posting_time
	if(doc.name){
		var document_name = doc.name
	} else {
		var document_name = ""
	}
	
	var item_code = d.item_material
	var warehouse = doc.source_warehouse

	if(doc.source_warehouse){
		frappe.call({
			method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
			args: {
				"posting_date" : doc.posting_date,
				"posting_time" : doc.posting_time,
				"document_name" : doc.name,
				"item_code" : d.item_material,
				"warehouse" : doc.source_warehouse
				
			},
			callback: function (data) {

				console.log(data.message)

				frappe.model.set_value(d.doctype, d.name, "qty_balance", data.message["actual_qty"]);
			}
		});
		frappe.call({
			method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
			args: {
				"posting_date" : doc.posting_date,
				"posting_time" : doc.posting_time,
				"document_name" : doc.name,
				"item_code" : d.item_material,
				"warehouse" : doc.source_warehouse
				
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "rate", data.message["valuation_rate"]);
				d.total_cost = d.qty_material * data.message["valuation_rate"]
			}
		});
	}
	refresh_field("block_production_material")
}

cur_frm.cscript.custom_qty_material = function(doc,dt,dn) {
	
	var d = locals[dt][dn];

	d.total_cost = d.qty_material * d.rate

	
	refresh_field("block_production_material")
}

cur_frm.cscript.custom_source_warehouse = function(doc,dt,dn) {
	
	if(doc.block_production_material){

		$.each(doc.block_production_material || [], function(i, d) {

			frappe.call({
				method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
				args: {
					"posting_date" : doc.posting_date,
					"posting_time" : doc.posting_time,
					"document_name" : doc.name,
					"item_code" : d.item_material,
					"warehouse" : doc.source_warehouse
					
				},
				callback: function (data) {
					d.qty_balance = data.message["actual_qty"];
				}
			});
			frappe.call({
				method: "addon_customization.sync_method.ambil_valuation_rate_sle_sebelumnya",
				args: {
					"posting_date" : doc.posting_date,
					"posting_time" : doc.posting_time,
					"document_name" : doc.name,
					"item_code" : d.item_material,
					"warehouse" : doc.source_warehouse
					
				},
				callback: function (data) {
					d.rate = data.message["valuation_rate"];
					d.total_cost = d.qty * data.message["valuation_rate"]
				}
			});

		})

			
	}
	refresh_field("block_production_material")
}


cur_frm.set_query("item_production", "block_production_item", function(doc, cdt, cdn) {
		if(doc.item_subgroup){
			return {
	            "filters": [
	                ["item_subgroup", "=", doc.item_subgroup]
	            ]
	        }
	    } else {
        	frappe.throw("Please choose Item Subgroup first")
        }
	
});


frappe.ui.form.on('Block Production', {
	// refresh: function(frm) {

	// }
});
