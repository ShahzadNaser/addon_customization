# -*- coding: utf-8 -*-
# Copyright (c) 2020, RICO NOVA and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document



from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate
from frappe.model.document import Document
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, get_bom_items_as_dict
from dateutil.relativedelta import relativedelta
from erpnext.stock.doctype.item.item import validate_end_of_life
from erpnext.manufacturing.doctype.workstation.workstation import WorkstationHolidayError
from erpnext.projects.doctype.timesheet.timesheet import OverlapError
from erpnext.manufacturing.doctype.manufacturing_settings.manufacturing_settings import get_mins_between_operations
from erpnext.stock.stock_balance import get_planned_qty, update_bin_qty
from frappe.utils.csvutils import getlink
from erpnext.stock.utils import get_bin, validate_warehouse_company, get_latest_stock_qty
from erpnext.utilities.transaction_base import validate_uom_is_integer
from frappe.model.mapper import get_mapped_doc

class ProductionForm(Document):



	def on_submit(self):

		if not self.production_order_material_item :
			frappe.throw("Please click on Get Material button before proceeding")


		# cek zero rate
		for i in self.production_order_material_item :
			if i.rate == 0 :

				if i.from_bom :
					get_bom = frappe.get_doc("BOM", i.from_bom)

					# append material
					for ei in get_bom.items :
						if ei.item_code == i.item_code :
							if ei.rate > 0 :
								i.rate = ei.rate
								i.amount = ei.rate * i.stock_qty
							else :

								frappe.throw("Item "+str(i.item_code)+" at table Material Item row "+str(i.idx)+" got 0 rate")
				else :
					frappe.throw("Item "+str(i.item_code)+" at table Material Item row "+str(i.idx)+" got 0 rate")



		self.calculation()





		se = frappe.new_doc("Stock Entry")
		se.purpose = "Manufacture"
		se.stock_entry_type = "Manufacture"
		se.company = self.company
		se.set_posting_time = 1
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time

		se.production_form = self.name

		# se.from_warehouse = prod_form.work_in_progress_warehouse
		# se.to_warehouse = prod_form.target_warehouse

		for i in self.production_order_material_item :

			gi = frappe.get_doc("Item", i.item_code)

			if gi.is_stock_item == 1 :

				child = se.append('items', {})
				child.item_code = i.item_code
				child.item_name = i.item_name

				child.item_group = gi.item_group

				child.description = i.item_name
				child.qty = i.qty
				child.basic_rate = i.rate
				child.basic_amount = i.amount
				child.amount = i.amount

				child.uom = i.stock_uom
				child.conversion_factor = i.conversion_factor
				child.stock_uom = i.stock_uom
				child.transfer_qty = i.qty

				child.s_warehouse = self.raw_material_source_warehouse
			

		for tc in self.production_order_total_cost :

			child = se.append('items', {})
			child.item_code = tc.item_to_manufacture
			child.item_name = tc.item_name

			gi = frappe.get_doc("Item", i.item_code)
			child.item_group = gi.item_group

			child.description = tc.item_name
			child.qty = tc.qty
			child.basic_rate = tc.total_cost / tc.qty
			child.basic_amount = tc.total_cost
			child.amount = tc.total_cost

			child.uom = tc.uom
			child.conversion_factor = 1
			child.stock_uom = tc.uom
			child.transfer_qty = tc.qty

			child.t_warehouse = self.raw_material_source_warehouse

		se.flags.ignore_permissions = True
		se.save()
		se.submit()

		frappe.msgprint("Stock Entry created "+str(se.name))




	def cek_double_item_to_manufcature(self):
		cek_exist = []
		if self.production_order_item :
			for i in self.production_order_item :
				if i.item_to_manufacture in cek_exist :
					frappe.throw("Duplicate item found "+str(i.item_to_manufacture))
				else :
					cek_exist.append(i.item_to_manufacture)


	def get_material(self):
		self.cek_double_item_to_manufcature()

		if not self.production_order_item :
			frappe.throw("Item to Manufacture not found !")

		self.production_order_material_item = []
		self.production_order_total_cost = []

		for i in self.production_order_item :
			if i.bom_no :
				get_bom = frappe.get_doc("BOM", i.bom_no)

				# append material
				for ei in get_bom.items :
					up = self.append('production_order_material_item', {})

					up.item_code = ei.item_code
					up.item_name = ei.item_name
					up.warehouse = self.raw_material_source_warehouse
					up.from_bom = i.bom_no

					up.qty = ei.stock_qty * i.qty
					up.uom = ei.stock_uom
					up.stock_qty = ei.stock_qty * i.qty
					up.stock_uom = ei.stock_uom
					up.conversion_factor = 1

					get_bin = frappe.get_value("Bin", {"warehouse":self.raw_material_source_warehouse, "item_code":ei.item_code}, "actual_qty")
					if get_bin :
						up.qty_exist = get_bin
					else :
						up.qty_exist = 0

					up.rate = ei.rate
					up.amount = ei.rate * ei.stock_qty

					# setting = frappe.get_single("General Setting")
					# if setting.val_production_form == 0 :
					# 	if ei.rate == 0 :
					# 		frappe.throw("Got rate 0 on BOM "+str(i.bom_no)+" at Item "+str(ei.item_code))


				# append total cost
				tc = self.append('production_order_total_cost', {})
				tc.item_to_manufacture = i.item_to_manufacture
				tc.item_name = i.item_name
				tc.bom_no = i.bom_no
				tc.warehouse = i.warehouse
				tc.qty = i.qty
				tc.uom = i.uom

				tc.operating_cost = get_bom.operating_cost * i.qty
				tc.raw_material_cost = get_bom.raw_material_cost * i.qty
				tc.scrap_material_cost = get_bom.scrap_material_cost * i.qty
				tc.total_cost = get_bom.total_cost * i.qty

				tc.unit_cost = tc.total_cost / tc.qty


		if self.production_order_total_cost :
			total_cost = 0
			for i in self.production_order_total_cost :
				total_cost += i.total_cost

			self.total_cost = total_cost



	def calculation(self) :
		for mi in self.production_order_material_item :
			
			get_item = frappe.get_doc("Item", mi.item_code)
			mi.item_name = get_item.item_name
			mi.warehouse = self.raw_material_source_warehouse

			mi.uom = get_item.stock_uom
			mi.stock_qty = mi.qty
			mi.stock_uom = get_item.stock_uom
			mi.conversion_factor = 1

			get_bin = frappe.get_value("Bin", {"warehouse":self.raw_material_source_warehouse, "item_code":mi.item_code}, "actual_qty")
			if get_bin :
				mi.qty_exist = get_bin
			else :
				mi.qty_exist = 0

			mi.amount = mi.qty * mi.rate


		# calculate order material item
		if self.production_order_item :
			for i in self.production_order_item :
				bom_no = i.bom_no
				get_bom = frappe.get_doc("BOM", i.bom_no)
				bom_item_qty = {}
				bom_item_rate = {}
				patokan_item = []
				for ei in get_bom.items :
					bom_item_qty.update({ ei.item_code : ei.stock_qty })
					bom_item_rate.update({ ei.item_code : ei.rate })
					patokan_item.append(ei.item_code)

				for mi in self.production_order_material_item :
					if i.bom_no == mi.from_bom :
						if mi.item_code in patokan_item :
							mi.qty = bom_item_qty[mi.item_code] * i.qty
							get_bin_rate = frappe.get_value("Bin", {"warehouse":self.raw_material_source_warehouse, "item_code":mi.item_code}, "valuation_rate")
							if get_bin_rate :
								mi.rate = get_bin_rate
							else :
								mi.rate = 0
							# mi.rate = bom_item_rate[mi.item_code]
							mi.amount = mi.rate * mi.qty
						else :
							get_item = frappe.get_doc("Item", mi.item_code)
							mi.item_name = get_item.item_code
							mi.warehouse = self.raw_material_source_warehouse

							mi.uom = get_item.stock_uom
							mi.stock_qty = mi.qty
							mi.stock_uom = get_item.stock_uom
							mi.conversion_factor = 1

							get_bin = frappe.get_value("Bin", {"warehouse":self.raw_material_source_warehouse, "item_code":mi.item_code}, "actual_qty")
							if get_bin :
								mi.qty_exist = get_bin
							else :
								mi.qty_exist = 0


							get_bin_rate = frappe.get_value("Bin", {"warehouse":self.raw_material_source_warehouse, "item_code":mi.item_code}, "valuation_rate")
							if get_bin_rate :
								mi.rate = get_bin_rate
							else :
								mi.rate = 0



							mi.amount = mi.qty * mi.rate


		# calculate total cost
		self.production_order_total_cost = []

		for i in self.production_order_item :

			operating_cost = 0
			raw_material_cost = 0
			scrap_material_cost = 0
			total_cost = 0

			if i.bom_no :
				get_bom = frappe.get_doc("BOM", i.bom_no)

				operating_cost = get_bom.operating_cost * i.qty
				scrap_material_cost = get_bom.scrap_material_cost * i.qty


			for mi in self.production_order_material_item :
				if i.bom_no == mi.from_bom :
					raw_material_cost += mi.amount

			total_cost = operating_cost + raw_material_cost + scrap_material_cost

			tc = self.append('production_order_total_cost', {})
			tc.item_to_manufacture = i.item_to_manufacture
			tc.item_name = i.item_name
			tc.bom_no = i.bom_no
			tc.warehouse = i.warehouse
			tc.qty = i.qty
			tc.uom = i.uom

			tc.operating_cost = operating_cost
			tc.raw_material_cost = raw_material_cost
			tc.scrap_material_cost = scrap_material_cost
			tc.total_cost = total_cost

			tc.unit_cost = tc.total_cost / tc.qty


		if self.production_order_total_cost :
			total_cost = 0
			for i in self.production_order_total_cost :
				total_cost += i.total_cost

			self.total_cost = total_cost



	

	def validate(self):

		if not self.production_order_item :
			frappe.throw("Please choose material you want to Manufacture")

		if not self.production_order_material_item :
			frappe.throw("Please click on Get Material button before proceeding")


		self.calculation()



@frappe.whitelist()
def make_stock_entry(production_form_id, purpose):

	prod_form = frappe.get_doc("Production Form", production_form_id)
	
	if prod_form.material_sent == 0 :

		se = frappe.new_doc("Stock Entry")
		se.purpose = "Material Transfer for Manufacture"
		se.stock_entry_type = "Material Transfer for Manufacture"
		se.from_warehouse = prod_form.raw_material_source_warehouse
		se.to_warehouse = prod_form.work_in_progress_warehouse

		se.set_posting_time = 1
		se.posting_date = prod_form.posting_date
		se.posting_time = prod_form.posting_time

		se.production_form = production_form_id

		for i in prod_form.production_order_material_item :

			child = se.append('items', {})
			child.item_code = i.item_code

			gi = frappe.get_doc("Item", i.item_code)
			child.item_group = gi.item_group

			child.item_name = i.item_name
			child.description = i.item_name
			child.qty = i.qty
			child.basic_rate = i.rate
			child.basic_amount = i.amount
			child.amount = i.amount

			child.uom = i.stock_uom
			child.conversion_factor = i.conversion_factor
			child.stock_uom = i.stock_uom
			child.transfer_qty = i.qty

			child.s_warehouse = se.from_warehouse
			child.t_warehouse = se.to_warehouse




	elif prod_form.material_sent == 1 :

		se = frappe.new_doc("Stock Entry")
		se.purpose = "Manufacture"
		se.stock_entry_type = "Manufacture"

		se.set_posting_time = 1
		se.posting_date = prod_form.posting_date
		se.posting_time = prod_form.posting_time

		se.production_form = production_form_id

		# se.from_warehouse = prod_form.work_in_progress_warehouse
		# se.to_warehouse = prod_form.target_warehouse

		for i in prod_form.production_order_material_item :

			child = se.append('items', {})
			child.item_code = i.item_code
			child.item_name = i.item_name

			gi = frappe.get_doc("Item", i.item_code)
			child.item_group = gi.item_group

			child.description = i.item_name
			child.qty = i.qty
			child.basic_rate = i.rate
			child.basic_amount = i.amount
			child.amount = i.amount

			child.uom = i.stock_uom
			child.conversion_factor = i.conversion_factor
			child.stock_uom = i.stock_uom
			child.transfer_qty = i.qty

			child.s_warehouse = prod_form.work_in_progress_warehouse
			

		for tc in prod_form.production_order_total_cost :

			child = se.append('items', {})
			child.item_code = tc.item_to_manufacture
			child.item_name = tc.item_name

			gi = frappe.get_doc("Item", i.item_code)
			child.item_group = gi.item_group

			child.description = tc.item_name
			child.qty = tc.qty
			child.basic_rate = tc.total_cost / tc.qty
			child.basic_amount = tc.total_cost
			child.amount = tc.total_cost

			child.uom = tc.uom
			child.conversion_factor = 1
			child.stock_uom = tc.uom
			child.transfer_qty = tc.qty

			child.t_warehouse = prod_form.target_warehouse



	
	return se.as_dict()







@frappe.whitelist()
def submit_ste_production_form(doc, method):
	if doc.stock_entry_type == "Material Transfer for Manufacture" :
		frappe.db.sql(""" UPDATE `tabProduction Form` pf SET pf.`material_sent` = 1 WHERE pf.`name` = "{}" """.format(doc.name))
		frappe.db.commit()

	elif doc.stock_entry_type == "Manufacture" :
		frappe.db.sql(""" UPDATE `tabProduction Form` pf SET pf.`production_done` = 1 WHERE pf.`name` = "{}" """.format(doc.name))
		frappe.db.commit()

@frappe.whitelist()
def cancel_ste_production_form(doc, method):
	if doc.stock_entry_type == "Material Transfer for Manufacture" :
		frappe.db.sql(""" UPDATE `tabProduction Form` pf SET pf.`material_sent` = 0 WHERE pf.`name` = "{}" """.format(doc.name))
		frappe.db.commit()

	elif doc.stock_entry_type == "Manufacture" :
		frappe.db.sql(""" UPDATE `tabProduction Form` pf SET pf.`production_done` = 0 WHERE pf.`name` = "{}" """.format(doc.name))
		frappe.db.commit()

