// Copyright (c) 2020, RICO NOVA and contributors
// For license information, please see license.txt

cur_frm.add_fetch('item_to_manufacture', 'stock_uom', 'uom');
cur_frm.add_fetch('item_to_manufacture', 'item_name', 'item_name');
cur_frm.cscript.custom_item_to_manufacture = function(doc,dt,dn) {
	
	// cur_frm.set_value("perusahaan", "PT. Mitra Asri Pratama")
	var d = locals[dt][dn];
	d["qty"] = 1

	if(doc.target_warehouse){
		d["warehouse"] = doc.target_warehouse
	}

	if (d.item_to_manufacture) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "BOM",
				filters: { "docstatus":1, "item":d.item_to_manufacture, "is_active":1, "is_default":1 },
				fieldname: "name",
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "bom_no", data.message.name);
			}
		});

		if(doc.production_order_item){

			$.each(doc.production_order_item || [], function(i, v) {
				frappe.model.set_value(v.doctype, v.name, "warehouse", doc.raw_material_source_warehouse);
			})

		}
		refresh_field("production_order_item")

		
	} else {
		// frappe.msgprint(__("Item didnt have any Active BOM"));
	}



	refresh_field("production_order_item")
	

}

cur_frm.cscript.custom_raw_material_source_warehouse = function(doc,dt,dn) {
	
	// cur_frm.set_value("perusahaan", "PT. Mitra Asri Pratama")

	if(doc.production_order_item){

		$.each(doc.production_order_item || [], function(i, v) {
			frappe.model.set_value(v.doctype, v.name, "warehouse", doc.raw_material_source_warehouse);
		})

	}
	refresh_field("production_order_item")
}




cur_frm.set_query("bom_no", "production_order_item", function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	if (d.item_to_manufacture) {
		return {
			query: "erpnext.controllers.queries.bom",
			filters: {item: cstr(d.item_to_manufacture)}
		};
	} else {
		frappe.msgprint(__("Please enter Production Item first"));
	}



	
});

