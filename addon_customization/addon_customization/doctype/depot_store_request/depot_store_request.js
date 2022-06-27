// Copyright (c) 2020, riconova and contributors
// For license information, please see license.txt



cur_frm.add_fetch('item_code', 'item_name', 'item_name');
cur_frm.add_fetch('item_code', 'description', 'description');
cur_frm.add_fetch('item_code', 'item_group', 'item_group');
cur_frm.add_fetch('item_code', 'brand', 'brand');
cur_frm.add_fetch('item_code', 'stock_uom', 'stock_uom');
cur_frm.add_fetch('item_code', 'item_name', 'item_name');

cur_frm.add_fetch('tc_name', 'terms', 'terms');

cur_frm.cscript.custom_for_warehouse = function(doc,dt,dn) {


	
	// var d = locals[dt][dn];


	 $.each(doc.items,  function(i,  d) {
            // calculate incentive
            
            d.warehouse = doc.for_warehouse

			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Bin",
					filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
					fieldname: "actual_qty",
				},
				callback: function (r) {
					if(r.message){
						d.actual_qty = r.message.actual_qty
					}
					else {
						d.actual_qty = 0
					}
						
					// frappe.model.set_value(d.doctype, d.name, "actual_qty", r.message.actual_qty);
				}
			});
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Bin",
					filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
					fieldname: "valuation_rate",
				},
				callback: function (r) {
					if(r.message){
						d.rate = r.message.valuation_rate
						d.amount = (d.qty * r.message.valuation_rate)
					}
					else{
						d.rate = 0
						d.amount = 0
					}
						
					// frappe.model.set_value(d.doctype, d.name, "rate", data.message.valuation_rate);
					// frappe.model.set_value(d.doctype, d.name, "amount", (d.qty * data.message.valuation_rate));
				}
			});

			console.log(d.warehouse)



        });



		
	refresh_field("depot_store_request_item")
};


cur_frm.cscript.custom_item_code = function(doc,dt,dn) {

	
	var d = locals[dt][dn];

	if(doc.for_warehouse){
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Bin",
				filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
				fieldname: "actual_qty",
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "actual_qty", data.message.actual_qty);
			}
		});
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Bin",
				filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
				fieldname: "valuation_rate",
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "rate", data.message.valuation_rate);
				frappe.model.set_value(d.doctype, d.name, "amount", (d.qty * data.message.valuation_rate));
				// d.amount = d.qty * data.message.valuation_rate
			}
		});
	}
	frappe.model.set_value(d.doctype, d.name, "warehouse", doc.for_warehouse);

	refresh_field("depot_store_request_item")
};

cur_frm.cscript.custom_qty = function(doc,dt,dn) {

	
	var d = locals[dt][dn];

	if(doc.for_warehouse){
		
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Bin",
				filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
				fieldname: "valuation_rate",
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "rate", data.message.valuation_rate);
				frappe.model.set_value(d.doctype, d.name, "amount", (d.qty * data.message.valuation_rate));
				// d.amount = d.qty * data.message.valuation_rate
			}
		});
	}
	frappe.model.set_value(d.doctype, d.name, "warehouse", doc.for_warehouse);

	refresh_field("depot_store_request_item")
};

// cur_frm.cscript.custom_warehouse = function(doc,dt,dn) {
	
// 	var d = locals[dt][dn];

	
// 	frappe.call({
// 		method: "frappe.client.get_value",
// 		args: {
// 			doctype: "Bin",
// 			filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
// 			fieldname: "actual_qty",
// 		},
// 		callback: function (data) {
// 			frappe.model.set_value(d.doctype, d.name, "actual_qty", data.message.actual_qty);
// 		}
// 	});
// 	frappe.call({
// 		method: "frappe.client.get_value",
// 		args: {
// 			doctype: "Bin",
// 			filters: { "warehouse":doc.for_warehouse, "item_code":d.item_code},
// 			fieldname: "valuation_rate",
// 		},
// 		callback: function (data) {
// 			frappe.model.set_value(d.doctype, d.name, "rate", data.message.valuation_rate);
// 			frappe.model.set_value(d.doctype, d.name, "amount", (d.qty * data.message.valuation_rate));
// 		}
// 	});

// 	refresh_field("depot_store_request_item")
// };





frappe.ui.form.on('Depot Store Request', {
	setup: function(frm) {
		
		
		frm.set_query("item_code", "items", function() {
			return {
				query: "erpnext.controllers.queries.item_query"
			};
		});
	},
	onload: function(frm) {
		
		frm.fields_dict["items"].grid.get_field("warehouse").get_query = function(doc) {
			return {
				filters: {'company': doc.company}
			};
		};
	},
	refresh: function(frm) {
		frm.events.make_custom_buttons(frm);
	},
	make_custom_buttons: function(frm) {
		
		if (frm.doc.docstatus == 1 && frm.doc.status != 'Stopped') {
			if (flt(frm.doc.per_ordered, 2) < 100) {
				

				if (frm.doc.material_request_type === "Material Transfer") {
					frm.add_custom_button(__("Transfer Material"),
						() => frm.events.make_stock_entry(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Material Issue") {
					frm.add_custom_button(__("Issue Material"),
						() => frm.events.make_stock_entry(frm), __('Create'));
				}
				
				
				frm.page.set_inner_btn_group_as_primary(__('Create'));

				// // stop
				// frm.add_custom_button(__('Stop'),
				// 	() => frm.events.update_status(frm, 'Stopped'));

			}
		}

		// if (frm.doc.docstatus===0) {
		// 	frm.add_custom_button(__('Sales Order'), () => frm.events.get_items_from_sales_order(frm),
		// 		__("Get items from"));
		// }

		if (frm.doc.docstatus == 1 && frm.doc.status == 'Stopped') {
			frm.add_custom_button(__('Re-open'), () => frm.events.update_status(frm, 'Submitted'));
		}
	},
	update_status: function(frm, stop_status) {
		frappe.call({
			method: 'addon_customization.addon_customization.doctype.depot_store_request.depot_store_request.update_status',
			args: { name: frm.doc.name, status: stop_status },
			callback(r) {
				if (!r.exc) {
					frm.reload_doc();
				}
			}
		});
	},
	get_items_from_sales_order: function(frm) {
		erpnext.utils.map_current_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_material_request",
			source_doctype: "Sales Order",
			target: frm,
			setters: {
				company: frm.doc.company
			},
			get_query_filters: {
				docstatus: 1,
				status: ["not in", ["Closed", "On Hold"]],
				per_delivered: ["<", 99.99],
			}
		});
	},
	make_stock_entry: function(frm) {
		frappe.model.open_mapped_doc({
			method: "addon_customization.addon_customization.doctype.depot_store_request.depot_store_request.make_stock_entry",
			frm: frm
		});
	},

	// refresh: function(frm) {

	// }
});
