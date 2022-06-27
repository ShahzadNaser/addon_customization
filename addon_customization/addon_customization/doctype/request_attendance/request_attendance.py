# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, getdate
from erpnext.hr.doctype.employee.employee import is_holiday
from erpnext.hr.utils import validate_dates
from frappe.utils import formatdate, format_datetime, getdate, get_datetime, nowdate, flt, cstr, add_days, today

from frappe.utils import getdate

class RequestAttendance(Document):


	def validate_dates_custom(self, doc, from_date, to_date):
		date_of_joining, relieving_date = frappe.db.get_value("Employee", doc.employee, ["date_of_joining", "relieving_date"])
		if getdate(from_date) > getdate(to_date):
			frappe.throw(_("To date can not be less than from date"))
		elif getdate(from_date) > getdate(nowdate()):
			frappe.throw(_("Future dates not allowed"))
		elif date_of_joining and getdate(from_date) < getdate(date_of_joining):
			frappe.throw(_("From date can not be less than employee's joining date"))
		elif relieving_date and getdate(to_date) > getdate(relieving_date):
			frappe.throw(_("To date can not greater than employee's relieving date"))

	def get_all_employee(self) :
		self.employee_list = []
		get_employee_data = frappe.db.sql(""" SELECT e.`name`, e.`employee_name` FROM `tabEmployee` e WHERE e.`status` = "Active" """)
		if get_employee_data :

			for ep in get_employee_data :
				new_child = self.append("employee_list", {})
				new_child.employee = ep[0]
				new_child.employee_name = ep[1]
					
	def validate(self):

		
		for i in self.employee_list : 
			self.validate_dates_custom(i, self.from_date, self.to_date)
			if self.half_day:
				if not getdate(self.from_date)<=getdate(self.half_day_date)<=getdate(self.to_date):
					frappe.throw(_("Half day date should be in between from date and to date"))

	def on_submit(self):
		self.create_attendance()

	def on_cancel(self):
		for i in self.employee_list : 
			attendance_list = frappe.get_list("Attendance", {'employee': i.employee, 'request_attendance': self.name})
			if attendance_list:
				for attendance in attendance_list:
					attendance_obj = frappe.get_doc("Attendance", attendance['name'])
					attendance_obj.cancel()

	def create_attendance(self):

		get_setting = frappe.get_single("HR Configuration")
		employee_exclude = []
		# if get_setting.exclude_employee_attendance :
		# 	for ex in get_setting.exclude_employee_attendance :
		# 		employee_exclude.append(ex.employee)

		request_days = date_diff(self.to_date, self.from_date) + 1
		for number in range(request_days):

			for i in self.employee_list :

				if i.employee not in employee_exclude :

					attendance_date = add_days(self.from_date, number)
					skip_attendance = self.validate_if_attendance_not_applicable(attendance_date, i)
					if not skip_attendance:

						# edited rico
						get_employee = frappe.get_doc("Employee", i.employee)
						att_id = str(get_employee.biometric_id)+"#"+str(attendance_date)

						if frappe.get_value("Attendance", {"name" : att_id}, "name") :

							start_time = "00:00:00"
							exit_time = "00:00:00"

							get_shift = frappe.get_doc("Employee", i.employee).default_shift

							if get_shift :
								get_work_time = frappe.get_doc("Shift Type", get_shift).work_time
								if get_work_time :
									for i in get_work_time :
										if i.days == str(getdate(str(attendance_date)).strftime("%A")) :
											start_time = i.start_time
											exit_time = i.exit_time

							frappe.db.sql(""" UPDATE `tabAttendance` a SET a.`start_time` = "{}", a.`exit_time` = "{}", a.`attendance_request` = "{}" WHERE a.`name` = "{}" """.format(start_time, exit_time, self.name, att_id))
							frappe.db.commit()



						else :

							attendance = frappe.new_doc("Attendance")
							attendance.employee = i.employee
							attendance.employee_name = i.employee_name
							if self.half_day and date_diff(getdate(self.half_day_date), getdate(attendance_date)) == 0:
								attendance.status = "Half Day"
							else:
								attendance.status = "Present"
							attendance.attendance_date = attendance_date
							attendance.company = self.company
							attendance.request_attendance = self.name


							# edited rico
							
							attendance.biometric_id = get_employee.biometric_id

							get_shift = frappe.get_doc("Employee", i.employee).default_shift

							if get_shift :
								get_work_time = frappe.get_doc("Shift Type", get_shift).work_time
								if get_work_time :
									for i in get_work_time :
										if i.days == str(getdate(str(attendance_date)).strftime("%A")) :
											attendance.start_time = i.start_time
											attendance.exit_time = i.exit_time


							attendance.save(ignore_permissions=True)
							attendance.submit()

	def validate_if_attendance_not_applicable(self, attendance_date, i):
		# Check if attendance_date is a Holiday
		if is_holiday(i.employee, attendance_date):
			frappe.msgprint(_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date), alert=1)
			return True

		# Check if employee on Leave
		leave_record = frappe.db.sql("""select half_day from `tabLeave Application`
			where employee = %s and %s between from_date and to_date
			and docstatus = 1""", (i.employee, attendance_date), as_dict=True)
		if leave_record:
			frappe.msgprint(_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, i.employee), alert=1)
			return True

		return False
