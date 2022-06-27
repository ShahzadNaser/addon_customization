# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ExtraSalary(Document):

	def before_insert(self):

		for i in self.employee_list :

			cek_extra_salary = frappe.db.sql("""
					SELECT * FROM `tabExtra Salary` es LEFT JOIN `tabExtra Salary Employee` ese ON es.`name` = ese.`parent`
					WHERE ese.`employee` = "{}"
					AND es.`name` != "{}"
					AND es.`posting_date` = "{}"
					AND es.`type_extra_salary` = "{}"
					AND es.`salary_component` = "{}"
					AND es.`list_salary_component` = "{}"

				""".format(i.employee, self.name, self.posting_date, self.type_extra_salary, self.salary_component, self.list_salary_component, self.overwrite_salary_structure_amount))

			if cek_extra_salary :
				frappe.throw(_("Extra Salary Exists for "+str(i.employee_name)))


	
	def get_all_employee(self) :
		self.employee_list = []
		get_employee_data = frappe.db.sql(""" SELECT e.`name`, e.`employee_name` FROM `tabEmployee` e WHERE e.`status` = "Active" """)
		if get_employee_data :

			for ep in get_employee_data :
				new_child = self.append("employee_list", {})
				new_child.employee = ep[0]
				new_child.employee_name = ep[1]


	def pengecekan_mandatory(self) :

		if not self.employee_list :
			frappe.throw("Must select employee first")

		if self.type_extra_salary == "OT and Penalty" :
			if not self.salary_component :
				frappe.throw("Must select Salary Component")

			if not self.no_of_days :
				frappe.throw("Must input No of Days")

		elif self.type_extra_salary == "Other Component" :

			if not self.list_salary_component :
				frappe.throw("Must select Salary Component")

			if not self.amount :
				frappe.throw("Must input Amount")

			if self.amount < 0:
				frappe.throw(_("Amount should not be less than zero."))


	def validate(self):

		self.pengecekan_mandatory()



	def on_submit(self):

		self.pengecekan_mandatory()