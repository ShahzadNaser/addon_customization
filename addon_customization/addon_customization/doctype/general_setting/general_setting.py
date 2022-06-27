# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class GeneralSetting(Document):
	def validate(self):
		if self.customer_child :
			frappe.db.sql(""" UPDATE `tabCustomer` c SET c.`for_sub_customer` = 0 """)
			frappe.db.commit()
			for i in self.customer_child :
				frappe.db.sql(""" UPDATE `tabCustomer` c SET c.`for_sub_customer` = 1 WHERE c.`name` = "{}" """.format(i.customer))
				frappe.db.commit()
