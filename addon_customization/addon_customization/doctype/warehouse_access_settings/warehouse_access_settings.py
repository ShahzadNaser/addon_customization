# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WarehouseAccessSettings(Document):
	
	def validate(self):
		if self.rules_setting:
			count = 0
			for i in self.rules_setting :
				if i.document == "Stock Entry" :
					if not i.type in ["Material Receipt","Material Issue", "Material Transfer", "Manufacture", "Repack", "Send to Warehouse", "Receive at Warehouse"] :
						frappe.throw("Stock Entry must select one of the type at row "+str(i.idx))

				else :
					if i.type in ["Material Receipt","Material Issue", "Material Transfer", "Manufacture", "Repack", "Send to Warehouse", "Receive at Warehouse"] :
						frappe.throw("Dont select type except for Stock Entry at row "+str(i.idx))

				if i.type == "Material Issue" :
					if not i.source_wh :
						frappe.throw("Must select Source WH for Stock Entry = Material Issue at row "+str(i.idx))

				if i.type == "Material Receipt" :
					if not i.target_wh :
						frappe.throw("Must select Target WH for Stock Entry = Material Receipt at row "+str(i.idx))



				if i.type == "Material Transfer" or i.type == "Manufacture" or i.type == "Repack" or i.type == "Send to Warehouse" or i.type == "Receive at Warehouse" :
					if i.source_wh and i.target_wh :
						count = 0
					else :
						frappe.throw("Must select Source WH and Target WH for Stock Entry at row "+str(i.idx))

				if i.document == "Block Production" :
					if i.source_wh and i.target_wh :
						count = 0
					else :
						frappe.throw("Must select Source WH and Target WH for Block Production at row "+str(i.idx))

				# if i.type != "Stock Entry" :
				# 	if not i.source_wh :
				# 		frappe.throw("Must select Source WH at row "+str(i.idx))