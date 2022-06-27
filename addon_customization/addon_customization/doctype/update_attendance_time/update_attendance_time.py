# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import getdate

class UpdateAttendanceTime(Document):
	
	def validate(self):

		if not self.employee_list :
			frappe.throw("Please choose your employee to update")

		if self.log_type == "Start Time" :
			if not self.start_time :
				frappe.throw("Please input Start Time")


		elif self.log_type == "Exit Time" :
			if not self.exit_time :
				frappe.throw("Please input Exit Time")


		elif self.log_type == "Both Time" :
			frappe.throw("Please input Start Time and Exit Time")


	def get_all_employee(self) :
		self.employee_list = []
		get_employee_data = frappe.db.sql(""" SELECT e.`name`, e.`employee_name` FROM `tabEmployee` e WHERE e.`status` = "Active" """)
		if get_employee_data :

			for ep in get_employee_data :
				new_child = self.append("employee_list", {})
				new_child.employee = ep[0]
				new_child.employee_name = ep[1]


	def on_submit(self):

		for i in self.employee_list :


			biometric_id = frappe.get_doc("Employee", i.employee).biometric_id
			shift_type = frappe.get_doc("Employee", i.employee).default_shift
			att_name = biometric_id+"#"+str(self.attendance_date)
			cek_att = frappe.get_value("Attendance", {"name" : att_name}, "name")

			late_entry = 0
			early_exit = 0
			
			if shift_type :
				get_shift = frappe.get_doc("Shift Type", shift_type)
				get_work_time = frappe.get_doc("Shift Type", shift_type).work_time
				if get_work_time :
					for z in get_work_time :
						if z.days == str(getdate(str(self.attendance_date)).strftime("%A")) and z.days != "Sunday" :
							if self.log_type == "Start Time" :
								# frappe.msgprint("masuk sini")
								# frappe.msgprint(str(getdate(str(self.attendance_date)).strftime("%A")))
								# frappe.msgprint(str(z.start_time) < str(self.start_time))

								# convert time to minutes
								# work_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								work_time_total_minute = 0
								work_time_hour = str(z.start_time).split(":")[0]
								work_time_hour_in_minutes = int(work_time_hour) * 60
								work_time_minute = int(str(z.start_time).split(":")[1]) 
								work_time_total_minute = work_time_hour_in_minutes + work_time_minute + get_shift.grace_period_for_late_entry

								# attendance_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								attendance_time_total_minute = 0
								attendance_time_hour = str(self.start_time).split(":")[0]
								attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
								attendance_time_minute = int(str(self.start_time).split(":")[1]) 
								attendance_time_total_minute = work_time_hour_in_minutes + work_time_minute

								if str(work_time_total_minute) < str(attendance_time_total_minute) :
									late_entry = 1
								else :
									late_entry = 0

							elif self.log_type == "Exit Time" :

								# convert time to minutes
								# work_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								work_time_total_minute = 0
								work_time_hour = str(z.exit_time).split(":")[0]
								work_time_hour_in_minutes = int(work_time_hour) * 60
								work_time_minute = int(str(z.exit_time).split(":")[1]) 
								work_time_total_minute = work_time_hour_in_minutes + work_time_minute + get_shift.grace_period_for_early_exit

								# attendance_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								attendance_time_total_minute = 0
								attendance_time_hour = str(self.exit_time).split(":")[0]
								attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
								attendance_time_minute = int(str(self.exit_time).split(":")[1]) 
								attendance_time_total_minute = work_time_hour_in_minutes + work_time_minute


								if str(work_time_total_minute) > str(attendance_time_total_minute) :
									early_exit = 1
								else :
									early_exit = 0

							

			if cek_att :

				if self.log_type == "Start Time" :

					frappe.db.sql(""" UPDATE `tabAttendance` a SET a.`old_start_time_update` = a.`start_time`, a.`start_time` = "{}", a.`late_entry` = "{}", a.`daily_check` = 0 WHERE a.`name` = "{}" """.format(self.start_time, late_entry, att_name))
					frappe.db.commit()
					

				elif self.log_type == "Exit Time" :

					frappe.db.sql(""" UPDATE `tabAttendance` a SET a.`old_exit_time_update` = a.`exit_time`, a.`exit_time` = "{}", a.`early_exit` = "{}", a.`daily_check` = 0 WHERE a.`name` = "{}" """.format(self.exit_time, early_exit, att_name))
					frappe.db.commit()
					

				elif self.log_type == "Both Time" :
					frappe.db.sql(""" UPDATE `tabAttendance` a 
						SET a.`old_start_time_update` = a.`start_time`, a.`start_time` = "{}", a.`late_entry` = "{}", 
							a.`old_exit_time_update` = a.`exit_time`, a.`exit_time` = "{}", a.`early_exit` = "{}", a.`daily_check` = 0
						WHERE a.`name` = "{}" """.format(self.start_time, late_entry, self.exit_time, early_exit, att_name))
					frappe.db.commit()


				frappe.msgprint("Attendance Updated !")
		


	def on_cancel(self):

		for i in self.employee_list :

			biometric_id = frappe.get_doc("Employee", i.employee).biometric_id
			shift_type = frappe.get_doc("Employee", i.employee).default_shift
			att_name = biometric_id+"#"+str(self.attendance_date)
			cek_att = frappe.get_value("Attendance", {"name" : att_name}, "name")

			late_entry = 0
			early_exit = 0
			
			
			if cek_att :

				if self.log_type == "Start Time" :

					frappe.db.sql(""" UPDATE `tabAttendance` a SET a.`start_time` = a.`old_start_time_update`, a.`old_start_time_update` = "00:00:00", a.`daily_check` = 0 WHERE a.`name` = "{}" """.format(att_name))
					frappe.db.commit()
					

				elif self.log_type == "Exit Time" :

					frappe.db.sql(""" UPDATE `tabAttendance` a SET a.`exit_time` = a.`old_exit_time_update`, a.`old_exit_time_update` = "00:00:00", a.`daily_check` = 0 WHERE a.`name` = "{}" """.format(att_name))
					frappe.db.commit()
					

				elif self.log_type == "Both Time" :
					frappe.db.sql(""" UPDATE `tabAttendance` a 
						SET a.`start_time` = a.`old_start_time_update`, a.`old_start_time_update` = "00:00:00"
							a.`exit_time` = a.`old_exit_time_update`, a.`old_exit_time_update` = "00:00:00", a.`daily_check` = 0
						WHERE a.`name` = "{}" """.format(att_name))
					frappe.db.commit()


				if shift_type :

					get_att = frappe.get_doc("Attendance", att_name)

					get_work_time = frappe.get_doc("Shift Type", shift_type).work_time
					get_shift = frappe.get_doc("Shift Type", shift_type)
					if get_work_time :
						for z in get_work_time :
							if z.days == str(getdate(str(self.attendance_date)).strftime("%A")) and z.days != "Sunday" :

								# convert time to minutes
								# work_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								work_time_total_minute = 0
								work_time_hour = str(z.start_time).split(":")[0]
								work_time_hour_in_minutes = int(work_time_hour) * 60
								work_time_minute = int(str(z.start_time).split(":")[1]) 
								work_time_total_minute = work_time_hour_in_minutes + work_time_minute + get_shift.grace_period_for_late_entry

								# attendance_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								attendance_time_total_minute = 0
								attendance_time_hour = str(get_att.start_time).split(":")[0]
								attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
								attendance_time_minute = int(str(get_att.start_time).split(":")[1]) 
								attendance_time_total_minute = work_time_hour_in_minutes + work_time_minute

								if str(work_time_total_minute) < str(attendance_time_total_minute) :
									late_entry = 1
								else :
									late_entry = 0


								# convert time to minutes
								# work_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								work_time_total_minute = 0
								work_time_hour = str(z.exit_time).split(":")[0]
								work_time_hour_in_minutes = int(work_time_hour) * 60
								work_time_minute = int(str(z.exit_time).split(":")[1]) 
								work_time_total_minute = work_time_hour_in_minutes + work_time_minute + get_shift.grace_period_for_early_exit

								# attendance_time
								# ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
								attendance_time_total_minute = 0
								attendance_time_hour = str(get_att.exit_time).split(":")[0]
								attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
								attendance_time_minute = int(str(get_att.exit_time).split(":")[1]) 
								attendance_time_total_minute = work_time_hour_in_minutes + work_time_minute


								if str(work_time_total_minute) > str(attendance_time_total_minute) :
									early_exit = 1
								else :
									early_exit = 0

						frappe.db.sql(""" UPDATE `tabAttendance` a SET a.`late_entry` = "{}", a.`early_exit` = "{}" WHERE a.`name` = "{}" """.format(late_entry, early_exit, att_name))
						frappe.db.commit()



