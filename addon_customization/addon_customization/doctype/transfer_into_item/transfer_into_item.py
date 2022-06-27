# -*- coding: utf-8 -*-
# Copyright (c) 2021, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TransferintoItem(Document):

	def ambil_valuation_rate_sle_sebelumnya(self, posting_date, posting_time, document_name, item_code, warehouse):

		arr_data = {}
		arr_data.update({ "item_code" : item_code, "posting_date" : posting_date, "posting_time" : posting_time, "warehouse" : "", "valuation_rate" : 0, "actual_qty" : 0 })

		get_data = frappe.db.sql("""
			SELECT 
			sle.`item_code` AS "item_code", 
			sle.`posting_date` AS "posting_date", 
			sle.`posting_time` AS "posting_time", 
			sle.`warehouse` AS "warehouse", 
			sle.`valuation_rate` AS "valuation_rate",
			sle.`qty_after_transaction` AS "actual_qty" 
			FROM `tabStock Ledger Entry` sle
			WHERE TIMESTAMP(sle.`posting_date`, sle.`posting_time`) <= TIMESTAMP("{}", "{}")
			AND sle.`voucher_no` != "{}"
			AND sle.`item_code` = "{}"
			AND sle.`warehouse` = "{}"

			ORDER BY TIMESTAMP(sle.`posting_date`, sle.`posting_time`) DESC
			LIMIT 1

		""".format(posting_date, posting_time, document_name, item_code, warehouse))

		if get_data :
			for i in get_data :
				arr_data.update({ "item_code" : i[0], "posting_date" : i[1], "posting_time" : i[2], "warehouse" : i[3], "valuation_rate" : i[4], "actual_qty" : i[5] })

		return arr_data
	

	def validate(self):
		if not self.items :
			frappe.throw("Please Choose the Item before continue")


		# cek item kembar
		cek_exist = []
		patokan_item = ""
		for i in self.items :
			patokan_item = str(i.from_item)+" and "+str(i.to_item)
			if patokan_item in cek_exist :
				frappe.throw("Duplicate Item "+str(patokan_item))
			else :
				cek_exist.append(patokan_item)


		for i in self.items :
			get_val_rate = self.ambil_valuation_rate_sle_sebelumnya(self.posting_date, self.posting_time, self.name, i.from_item, self.default_from_warehouse)
			i.basic_rate = get_val_rate["valuation_rate"]
			i.basic_amount = i.qty * i.basic_rate


	def before_cancel(self):
		get_ste = frappe.db.sql("""
			SELECT ste.`name` FROM `tabStock Entry` ste
			WHERE ste.`docstatus` = 1
			AND ste.`transfer_into_item` = "{}"

		""".format(self.name))

		if get_ste :
			for i in get_ste :
				ste = frappe.get_doc("Stock Entry", i[0])
				ste.flags.ignore_permissions = True
				ste.cancel()
				frappe.db.commit()


	def before_submit(self) :

		for i in self.items :
			get_val_rate = self.ambil_valuation_rate_sle_sebelumnya(self.posting_date, self.posting_time, self.name, i.from_item, self.default_from_warehouse)
			i.basic_rate = get_val_rate["valuation_rate"]
			i.basic_amount = i.qty * i.basic_rate
			# i.qty_balance = get_val_rate["actual_qty"]


	def on_submit(self):
		for i in self.items :
			get_item = frappe.get_doc("Item", i.from_item)
			if get_item.is_stock_item == 1 :
				if i.basic_rate == 0 :
					frappe.throw("Cannot continue this process, 0 cost at table Items row "+str(i.idx))


		se = frappe.new_doc("Stock Entry")
		se.purpose = "Repack"
		se.stock_entry_type = "Repack"

		se.transfer_into_item = self.name

		se.set_posting_time = 1
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time

		for i in self.items :

			gi = frappe.get_doc("Item", i.from_item)

			if gi.is_stock_item == 1 :

				child = se.append('items', {})
				child.item_code = i.from_item
				child.item_name = i.from_item_name

				
				child.item_group = gi.item_group

				child.description = i.from_item_name
				child.qty = i.qty
				child.basic_rate = i.basic_rate
				child.basic_amount = i.basic_amount
				child.amount = i.basic_amount
				child.valuation_rate = i.basic_rate

				child.uom = i.from_item_uom
				child.conversion_factor = 1
				child.stock_uom = i.from_item_uom
				child.transfer_qty = i.qty

				child.s_warehouse = i.from_warehouse


			gi = frappe.get_doc("Item", i.to_item)

			if gi.is_stock_item == 1 :

				child = se.append('items', {})
				child.item_code = i.to_item
				child.item_name = i.to_item_name

				
				child.item_group = gi.item_group

				child.description = i.to_item_name
				child.qty = i.qty
				child.basic_rate = i.basic_rate
				child.basic_amount = i.basic_amount
				child.amount = i.basic_amount
				child.valuation_rate = i.basic_rate

				child.uom = i.to_item_uom
				child.conversion_factor = 1
				child.stock_uom = i.to_item_uom
				child.transfer_qty = i.qty

				child.t_warehouse = i.to_warehouse


		se.flags.ignore_permissions = True
		se.save()
		se.submit()

		frappe.msgprint("Stock Entry created "+str(se.name))
