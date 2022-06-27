# -*- coding: utf-8 -*-
# Copyright (c) 2020, RICO NOVA and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BlockProduction(Document):

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

	def before_submit(self) :
		

		for i in self.block_production_material :
			get_val_rate = self.ambil_valuation_rate_sle_sebelumnya(self.posting_date, self.posting_time, self.name, i.item_material, self.source_warehouse)
			i.rate = get_val_rate["valuation_rate"]
			i.qty_balance = get_val_rate["actual_qty"]



	def on_submit(self):


		# kalkulasi sebelum submit
		# kalkulasi raw material
		total_cost_material = 0
		for i in self. block_production_material :
			total_cost_material += i.total_cost

		self.total_cost_material = total_cost_material

		# kalkulasi production item
		
		total_size = 0
		for i in self.block_production_item :
			i.total_size = float(i.qty) * float(i.foam_block_size)
			total_size += float(i.total_size)

		self.total_size = total_size

		total_cost_production = 0

		# frappe.throw(str(float(self.total_cost_material) / float(self.total_size)))

		for k in self.block_production_item :

			k.rate = float(float(self.total_cost_material) / float(self.total_size)) * float(k.foam_block_size)
			k.total_cost = float(k.qty) * float(k.rate)

			total_cost_production += float(k.total_cost)

		self.total_cost_production_item = total_cost_production


		# validasi rate
		setting = frappe.get_single("General Setting")
		if setting.val_block_production == 0 :
			# check rate zero
			for i in self.block_production_material :
				get_item = frappe.get_doc("Item", i.item_material)
				if get_item.is_stock_item == 1 :
					if i.rate == 0 :
						frappe.throw("Cannot continue this process, 0 cost at table Material Item row "+str(i.idx))

			for i in self.block_production_item :
				get_item = frappe.get_doc("Item", i.item_production)
				if get_item.is_stock_item == 1 :
					if i.rate == 0 :
						frappe.throw("Cannot continue this process, 0 cost at table Production Item row "+str(i.idx))





		se = frappe.new_doc("Stock Entry")
		se.purpose = "Manufacture"
		se.stock_entry_type = "Manufacture"

		se.block_production = self.name
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.set_posting_time = 1

		# se.from_warehouse = prod_form.work_in_progress_warehouse
		# se.to_warehouse = prod_form.target_warehouse

		for i in self.block_production_material :

			gi = frappe.get_doc("Item", i.item_material)

			if gi.is_stock_item == 1 :

				child = se.append('items', {})
				child.item_code = i.item_material
				child.item_name = i.item_name

				
				child.item_group = gi.item_group

				child.description = i.item_name
				child.qty = i.qty_material
				child.basic_rate = i.rate
				child.basic_amount = i.total_cost
				child.amount = i.total_cost
				child.valuation_rate = i.rate

				child.uom = i.stock_uom
				child.conversion_factor = 1
				child.stock_uom = i.stock_uom
				child.transfer_qty = i.qty_material

				child.s_warehouse = self.source_warehouse
			

		for tc in self.block_production_item :

			child = se.append('items', {})
			child.item_code = tc.item_production
			child.item_name = tc.item_name

			gi = frappe.get_doc("Item", tc.item_production)
			child.item_group = gi.item_group

			child.description = tc.item_name
			child.qty = tc.qty
			child.basic_rate = tc.rate
			child.basic_amount = tc.total_cost
			child.amount = tc.total_cost

			child.uom = tc.stock_uom
			child.conversion_factor = 1
			child.stock_uom = tc.stock_uom
			child.transfer_qty = tc.qty

			child.t_warehouse = self.target_warehouse

		se.flags.ignore_permissions = True
		se.save()
		se.submit()

		frappe.msgprint("Stock Entry created "+str(se.name))
	

	def validate(self):

		# cek2
		if not self.source_warehouse :
			frappe.throw("Please choose Source Warehouse")

		if not self.target_warehouse :
			frappe.throw("Please choose Target Warehouse")

		if not self.block_production_item :
			frappe.throw("Please choose Item to Produce to continue")

		if not self.block_production_material :
			frappe.throw("Please choose Material Item to continue")


		# cek item kembar
		cek_exist = []
		for i in self.block_production_item :
			if i.item_production in cek_exist :
				frappe.throw("Duplicate Production Item "+str(i.item_production))
			else :
				cek_exist.append(i.item_production)

		cek_exist = []
		for i in self.block_production_material :
			if i.item_material in cek_exist :
				frappe.throw("Duplicate Material Item "+str(i.item_material))
			else :
				cek_exist.append(i.item_material)


		# kalkulasi raw material
		total_cost_material = 0
		for i in self. block_production_material :
			total_cost_material += i.total_cost

		self.total_cost_material = total_cost_material

		# kalkulasi production item
		
		total_size = 0
		for i in self.block_production_item :
			i.total_size = float(i.qty) * float(i.foam_block_size)
			total_size += float(i.total_size)

		self.total_size = total_size

		total_cost_production = 0

		# frappe.throw(str(float(self.total_cost_material) / float(self.total_size)))

		for k in self.block_production_item :

			k.rate = float(float(self.total_cost_material) / float(self.total_size)) * float(k.foam_block_size)
			k.total_cost = float(k.qty) * float(k.rate)

			total_cost_production += float(k.total_cost)

		self.total_cost_production_item = total_cost_production


		for i in self.block_production_material :
			get_val_rate = self.ambil_valuation_rate_sle_sebelumnya(self.posting_date, self.posting_time, self.name, i.item_material, self.source_warehouse)
			i.rate = get_val_rate["valuation_rate"]
			i.qty_balance = get_val_rate["actual_qty"]



