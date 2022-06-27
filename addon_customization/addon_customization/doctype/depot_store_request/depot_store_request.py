# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe import msgprint, _
from erpnext.stock.doctype.item.item import get_item_defaults

class DepotStoreRequest(Document):
	# def before_save(self):
	# 	self.set_status(update=True)

	# def before_submit(self):
	# 	self.set_status(update=True)

	pass



@frappe.whitelist()
def update_status(name, status):
	material_request = frappe.get_doc('Depot Store Request', name)
	material_request.check_permission('write')
	material_request.update_status(status)


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		qty = obj.qty
		target.qty = qty
		target.transfer_qty = qty
		target.conversion_factor = 1

		target.uom = obj.stock_uom

		if source_parent.material_request_type == "Material Transfer" :
			target.t_warehouse = obj.warehouse
		else:
			target.s_warehouse = obj.warehouse

	def set_missing_values(source, target):

		if source.material_request_type == "Material Transfer":
			target.stock_entry_type = "Send to Warehouse"
			target.purpose = "Send to Warehouse"
			target.to_warehouse = source.for_warehouse

		else :
			target.purpose = source.material_request_type
			target.to_warehouse = source.for_warehouse

		target.depot_store_request = source.name
		
		target.run_method("calculate_rate_and_amount")
		target.set_stock_entry_type()

	doclist = get_mapped_doc("Depot Store Request", source_name, {
		"Depot Store Request": {
			"doctype": "Stock Entry",
			"validation": {
				"docstatus": ["=", 1],
				"material_request_type": ["in", ["Material Transfer", "Material Issue"]]
			}
		},
		"Depot Store Request Item": {
			"doctype": "Stock Entry Detail",
			"field_map": {
				"uom": "stock_uom"

			},
			"postprocess": update_item
		}
	}, target_doc, set_missing_values)

	return doclist