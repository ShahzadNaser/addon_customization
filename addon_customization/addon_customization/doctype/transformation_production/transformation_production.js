// Copyright (c) 2020, RICO NOVA and contributors
// For license information, please see license.txt


cur_frm.add_fetch('item_production', 'item_name', 'item_name');
cur_frm.add_fetch('item_production', 'item_ratio', 'ratio');

cur_frm.add_fetch('item_material', 'item_name', 'item_name');




cur_frm.cscript.custom_item_material = function(doc,dt,dn) {

	
	var d = locals[dt][dn];

	if(doc.warehouse){
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Bin",
				filters: { "warehouse":doc.warehouse, "item_code":d.item_material},
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
				filters: { "warehouse":doc.warehouse, "item_code":d.item_material},
				fieldname: "valuation_rate",
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "rate", data.message.valuation_rate);
				frappe.model.set_value(d.doctype, d.name, "total_cost", (d.qty_material * data.message.valuation_rate));
				// d.amount = d.qty * data.message.valuation_rate
			}
		});
	}
	frappe.model.set_value(d.doctype, d.name, "warehouse", doc.warehouse);

	refresh_field("transformation_production_material")
};

cur_frm.cscript.custom_qty_material = function(doc,dt,dn) {

	
	var d = locals[dt][dn];

	if(doc.warehouse){
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Bin",
				filters: { "warehouse":doc.warehouse, "item_code":d.item_material},
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
				filters: { "warehouse":doc.warehouse, "item_code":d.item_material},
				fieldname: "valuation_rate",
			},
			callback: function (data) {
				frappe.model.set_value(d.doctype, d.name, "rate", data.message.valuation_rate);
				frappe.model.set_value(d.doctype, d.name, "total_cost", (d.qty_material * data.message.valuation_rate));
				// d.amount = d.qty * data.message.valuation_rate
			}
		});
	}
	frappe.model.set_value(d.doctype, d.name, "warehouse", doc.warehouse);

	refresh_field("transformation_production_material")
};






frappe.ui.form.on('Transformation Production', {
	setup: function(frm) {
		
		
		frm.set_query("item_production", "transformation_production_item", function() {
			return {
				filters: {'is_item_uncovered': "Yes"}
			};
		});

		frm.set_query("item_material", "transformation_production_material", function() {
			return {
				filters: {'is_item_uncovered': "Yes"}
			};
		});



	},
	onload: function(frm) {
		
		
		frm.set_query("item_production", "transformation_production_item", function() {
			return {
				filters: {'is_item_uncovered': "Yes"}
			};
		});

		frm.set_query("item_material", "transformation_production_material", function() {
			return {
				filters: {'is_item_uncovered': "Yes"}
			};
		});



	},

	refresh: function(frm) {
		erpnext.hide_company();
		frm.events.show_general_ledger(frm);
		frm.events.show_stock_ledger(frm);
	},

	show_stock_ledger: function(frm) {
		
		if(frm.doc.docstatus===1) {
			cur_frm.add_custom_button(__("Stock Ledger"), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company
				};
				frappe.set_route("query-report", "Stock Ledger");
			}, __("View"));
		}

	},

	show_general_ledger: function(frm) {
		
		if(frm.doc.docstatus===1) {
			cur_frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by: "Group by Voucher (Consolidated)"
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	}

});
