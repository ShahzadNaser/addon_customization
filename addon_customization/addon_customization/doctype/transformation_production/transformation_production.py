# -*- coding: utf-8 -*-
# Copyright (c) 2020, RICO NOVA and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe.model.document import Document
from erpnext.accounts.utils import get_fiscal_year
import frappe.defaults
from erpnext.accounts.general_ledger import make_gl_entries, delete_gl_entries, process_gl_map

from erpnext.stock import get_warehouse_account_map
from frappe.utils import cstr, cint, flt, comma_or, getdate, nowdate, formatdate, format_time

import frappe, erpnext
import frappe.defaults
from frappe import _
from frappe.utils import cstr, cint, flt, comma_or, getdate, nowdate, formatdate, format_time
from erpnext.stock.utils import get_incoming_rate
from erpnext.stock.stock_ledger import get_previous_sle, NegativeStockError, get_valuation_rate
from erpnext.stock.get_item_details import get_bin_details, get_default_cost_center, get_conversion_factor, get_reserved_qty_for_so
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.stock.doctype.batch.batch import get_batch_no, set_batch_nos, get_batch_qty
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, add_additional_cost
from erpnext.stock.utils import get_bin
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.serial_no.serial_no import update_serial_nos_after_submit, get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import OpeningEntryAccountError

import json

from six import string_types, itervalues, iteritems

class TransformationProduction(Document):


	def validate(self):
		if not self.transformation_production_item :
			frappe.throw("Input your Production Item first")

		if not self.transformation_production_material :
			frappe.throw("Input your Material Item first")


		# calculation
		for pi in self.transformation_production_item :
			ge = frappe.get_doc("Item", pi.item_production)
			ai_rate = 0
			if ge.associated_item :
				ai = frappe.get_doc("Associated Items", ge.associated_item)
				ai_rate = ai.item_cost

			pi.rate = pi.ratio * ai_rate
			pi.total_cost = pi.qty * pi.rate


		total_cost_production = 0
		total_cost_material = 0

		for pi in self.transformation_production_item :
			total_cost_production += pi.total_cost
		self.total_cost_production = total_cost_production

		for pi in self.transformation_production_material :
			total_cost_material += pi.total_cost
		self.total_cost_material = total_cost_material

	

	def on_submit(self):
		# calculation
		for pi in self.transformation_production_item :
			ge = frappe.get_doc("Item", pi.item_production)
			ai_rate = 0
			if ge.associated_item :
				ai = frappe.get_doc("Associated Items", ge.associated_item)
				ai_rate = ai.item_cost

			pi.rate = pi.ratio * ai_rate
			pi.total_cost = pi.qty * pi.rate


		total_cost_production = 0
		total_cost_material = 0

		for pi in self.transformation_production_item :
			total_cost_production += pi.total_cost
		self.total_cost_production = total_cost_production

		for pi in self.transformation_production_material :
			total_cost_material += pi.total_cost
		self.total_cost_material = total_cost_material

		# ==============================================

		setting = frappe.get_single("General Setting")
		if setting.val_transformation == 0 :
			# check rate zero
			for i in self.transformation_production_item :
				get_item = frappe.get_doc("Item", i.item_production)
				if get_item.is_stock_item == 1 :
					if i.rate == 0 :
						frappe.throw("Items cannot be transformed, 0 cost at table Production Item row "+str(i.idx))

			for i in self.transformation_production_material :
				get_item = frappe.get_doc("Item", i.item_material)
				if get_item.is_stock_item == 1 :
					if i.rate == 0 :
						frappe.throw("Items cannot be transformed, 0 cost at table Production Material row "+str(i.idx))



		self.update_stock_ledger()
		self.make_gl_entries_atas()
		self.make_gl_entries_bawah()

		

	def on_cancel(self):
		self.update_stock_ledger()
		self.make_gl_entries_on_cancel()
		



# STOCK LEDGER ENTRYYY
	
	def get_sl_entries_production(self, d, args):
		sl_dict = frappe._dict({
			"item_code": d.get("item_production", None),
			"warehouse": self.warehouse,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			'fiscal_year': get_fiscal_year(self.posting_date, company=self.company)[0],
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": d.name,
			"actual_qty": (self.docstatus==1 and 1 or -1)*flt(d.get("qty")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_production") or d.get("item_production"), "stock_uom"),
			"incoming_rate": 0,
			"company": self.company,
			"batch_no": "",
			"serial_no": "",
			"project": "",
			"is_cancelled": self.docstatus==2 and "Yes" or "No"
		})

		sl_dict.update(args)
		return sl_dict


	def get_sl_entries_material(self, d, args):
		sl_dict = frappe._dict({
			"item_code": d.get("item_material", None),
			"warehouse": self.warehouse,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			'fiscal_year': get_fiscal_year(self.posting_date, company=self.company)[0],
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": d.name,
			"actual_qty": (self.docstatus==1 and 1 or -1)*flt(d.get("qty_material")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_material") or d.get("item_material"), "stock_uom"),
			"incoming_rate": 0,
			"company": self.company,
			"batch_no": "",
			"serial_no": "",
			"project": "",
			"is_cancelled": self.docstatus==2 and "Yes" or "No"
		})

		sl_dict.update(args)
		return sl_dict

	def update_stock_ledger(self):
		sl_entries = []

		# make sl entries for source warehouse first, then do for target warehouse
		for d in self.get('transformation_production_material'):
			
			sl_entries.append(self.get_sl_entries_material(d, {
				"warehouse": cstr(self.warehouse),
				"actual_qty": -flt(d.qty_material),
				"incoming_rate": 0
			}))

		for d in self.get('transformation_production_item'):
			
			sl_entries.append(self.get_sl_entries_production(d, {
				"warehouse": cstr(self.warehouse),
				"actual_qty": flt(d.qty),
				"incoming_rate": flt(d.rate)
			}))

		if self.docstatus == 2:
			sl_entries.reverse()

		self.make_sl_entries(sl_entries, self.amended_from and 'Yes' or 'No')


	def make_sl_entries(self, sl_entries, is_amended=None, allow_negative_stock=False,
			via_landed_cost_voucher=False):
		from erpnext.stock.stock_ledger import make_sl_entries
		make_sl_entries(sl_entries, is_amended, allow_negative_stock, via_landed_cost_voucher)

# END OF STOCK LEDGER ENTRY


# GENERAL LEDGER ENTRY


	def make_gl_entries_on_cancel(self, repost_future_gle=True):
		if frappe.db.sql("""select name from `tabGL Entry` where voucher_type=%s
			and voucher_no=%s""", (self.doctype, self.name)):
				self.make_gl_entries_cancel(repost_future_gle=repost_future_gle)

	def make_gl_entries_cancel(self, gl_entries=None, repost_future_gle=True, from_repost=False):
		if self.docstatus == 2:
			delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)


	def make_gl_entries_bawah(self):

		if cint(erpnext.is_perpetual_inventory_enabled(self.company)):

			# sle_map = self.get_stock_ledger_details()
			# voucher_details = self.get_voucher_details(default_expense_account, default_cost_center, sle_map)

			table_atas = self.get("transformation_production_material")
			precision = frappe.get_precision("GL Entry", "debit_in_account_currency")

			cost_center = frappe.get_doc("Company", self.company).cost_center

			if self.docstatus==1:
				gl_list = []
				for ta in table_atas :
					gi = frappe.get_doc("Item", ta.item_material)
					gig = frappe.get_doc("Item Group", gi.item_group)

					account_debit = gig.t_debit_raw_item
					account_credit = gig.t_credit_raw_item

					gl_list.append({
						"account": account_debit,
						"against": account_credit,
						"cost_center": cost_center,
						"remarks": "Accounting Entry for Transformation Material Item",
						"debit": flt(ta.total_cost, precision),
						"is_opening": "No",
						"voucher_type": "Transformation Production",
						"voucher_no": self.name,
						"posting_date": self.posting_date
					})

					gl_list.append({
						"account": account_credit,
						"against": account_debit,
						"cost_center": cost_center,
						"remarks": "Accounting Entry for Transformation Material Item",
						"credit": flt(ta.total_cost, precision),
						"is_opening": "No",
						"voucher_type": "Transformation Production",
						"voucher_no": self.name,
						"posting_date": self.posting_date
					})

					# to target warehouse / expense account

				# frappe.msgprint(str(gl_list))

				gl_map = gl_list


				if gl_map:
					
					# validate_accounting_period(gl_map)
					# gl_map = process_gl_map(gl_map, merge_entries)
					if gl_map and len(gl_map) > 1:
						
						for entry in gl_map:
							self.make_entry(entry)


	def make_gl_entries_atas(self):

		if cint(erpnext.is_perpetual_inventory_enabled(self.company)):

			# sle_map = self.get_stock_ledger_details()
			# voucher_details = self.get_voucher_details(default_expense_account, default_cost_center, sle_map)

			table_atas = self.get("transformation_production_item")
			precision = frappe.get_precision("GL Entry", "debit_in_account_currency")

			cost_center = frappe.get_doc("Company", self.company).cost_center

			if self.docstatus==1:
				gl_list = []
				for ta in table_atas :
					gi = frappe.get_doc("Item", ta.item_production)
					gig = frappe.get_doc("Item Group", gi.item_group)

					account_debit = gig.t_debit_production_item
					account_credit = gig.t_credit_production_item

					gl_list.append({
						"account": account_debit,
						"against": account_credit,
						"cost_center": cost_center,
						"remarks": "Accounting Entry for Transformation Production",
						"debit": flt(ta.total_cost, precision),
						"is_opening": "No",
						"voucher_type": "Transformation Production",
						"voucher_no": self.name,
						"posting_date": self.posting_date
					})

					gl_list.append({
						"account": account_credit,
						"against": account_debit,
						"cost_center": cost_center,
						"remarks": "Accounting Entry for Transformation Production Item",
						"credit": flt(ta.total_cost, precision),
						"is_opening": "No",
						"voucher_type": "Transformation Production",
						"voucher_no": self.name,
						"posting_date": self.posting_date
					})

					# to target warehouse / expense account


				# frappe.msgprint(str(gl_list))
				gl_map = gl_list


				if gl_map:
					
					# validate_accounting_period(gl_map)
					# gl_map = process_gl_map(gl_map, merge_entries)
					if gl_map and len(gl_map) > 1:
						
						for entry in gl_map:
							self.make_entry(entry)


	def process_gl_map(self, gl_map):
	
		for entry in gl_map:
			# toggle debit, credit if negative entry
			if flt(entry.debit) < 0:
				entry.credit = flt(entry.credit) - flt(entry.debit)
				entry.debit = 0.0

			if flt(entry.debit_in_account_currency) < 0:
				entry.credit_in_account_currency = \
					flt(entry.credit_in_account_currency) - flt(entry.debit_in_account_currency)
				entry.debit_in_account_currency = 0.0

			if flt(entry.credit) < 0:
				entry.debit = flt(entry.debit) - flt(entry.credit)
				entry.credit = 0.0

			if flt(entry.credit_in_account_currency) < 0:
				entry.debit_in_account_currency = \
					flt(entry.debit_in_account_currency) - flt(entry.credit_in_account_currency)
				entry.credit_in_account_currency = 0.0

		return gl_map
					

	def make_entry(self, args):
		args.update({"doctype": "GL Entry"})
		gle = frappe.get_doc(args)
		
		gle.flags.ignore_permissions = 1
		gle.insert()
		gle.submit()


