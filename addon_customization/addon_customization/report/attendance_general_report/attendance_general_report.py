# Copyright (c) 2013, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, date_diff
from frappe.utils import getdate

def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns, data = [], []
	temp_data = []

	get_data_customer = []

	exclude_employee = []
	get_employee = frappe.get_single("HR Configuration").exclude_employee_attendance
	if get_employee :
		for i in get_employee :
			exclude_employee.append(i.employee)

	# fieldname:"report_type",
	# options: "PRESENT REPORT\nABSENT REPORT\nLATE ARRIVAL\nEARLY EXIT\nATTEANDANCE SUMMARY",

	# CAST(att.`biometric_id` AS UNSIGNED)

	date_clause = ""
	if filters.get("from_date") and filters.get("to_date") :
		date_clause = """ AND att.`attendance_date` BETWEEN "{0}" AND "{1}" """.format(filters.get("from_date"),filters.get("to_date"))


	date_clause1 = ""
	if filters.get("from_date") and filters.get("to_date") :
		date_clause1 = """ AND att1.`attendance_date` BETWEEN "{0}" AND "{1}" """.format(filters.get("from_date"),filters.get("to_date"))

	employee_clause = ""
	# if filters.get("employee") :
	# 	employee_clause = """ AND e.`employee` = "{}" """.format(filters.get("employee"))

	range_clause = ""
	if filters.get("biometric_from") and filters.get("biometric_to") :
		biometric_f = frappe.get_doc("Employee", filters.get("biometric_from")).biometric_id
		biometric_t = frappe.get_doc("Employee", filters.get("biometric_to")).biometric_id

		range_clause = """ AND CAST(att.`biometric_id` AS UNSIGNED) BETWEEN {0} AND {1} """.format(int(biometric_f),int(biometric_t))

	range_clause1 = ""
	if filters.get("biometric_from") and filters.get("biometric_to") :
		biometric_f = frappe.get_doc("Employee", filters.get("biometric_from")).biometric_id
		biometric_t = frappe.get_doc("Employee", filters.get("biometric_to")).biometric_id

		range_clause1 = """ AND CAST(att1.`biometric_id` AS UNSIGNED) BETWEEN {0} AND {1} """.format(int(biometric_f),int(biometric_t))


	range_clause_employee = ""
	if filters.get("biometric_from") and filters.get("biometric_to") :
		biometric_f = frappe.get_doc("Employee", filters.get("biometric_from")).biometric_id
		biometric_t = frappe.get_doc("Employee", filters.get("biometric_to")).biometric_id

		range_clause_employee = """ AND CAST(e.`biometric_id` AS UNSIGNED) BETWEEN {0} AND {1} """.format(int(biometric_f),int(biometric_t))


	range_clause_employee1 = ""
	if filters.get("biometric_from") and filters.get("biometric_to") :
		biometric_f = frappe.get_doc("Employee", filters.get("biometric_from")).biometric_id
		biometric_t = frappe.get_doc("Employee", filters.get("biometric_to")).biometric_id

		range_clause_employee1 = """ AND CAST(e1.`biometric_id` AS UNSIGNED) BETWEEN {0} AND {1} """.format(int(biometric_f),int(biometric_t))


	employee_clause = ""
	if filters.get("employee_status") :
		employee_clause = """ AND e.`status` = "{}" """.format(filters.get("employee_status"))

	employee_clause1 = ""
	if filters.get("employee_status") :
		employee_clause1 = """ AND e1.`status` = "{}" """.format(filters.get("employee_status"))

	

	if filters.report_type == "PRESENT REPORT" :
		
		columns = [
		"ID:Data:100",
		"Employee Name:Data:200",
		"Department:Data:150",
		"Designation:Data:150",
		"Status:Data:100",
		"Company:Data:150",
		"Shift:Data:100",
		"Date:Date:100",
		"Start Time:Time:100",
		"Exit Time:Time:100",
		"Attendance Type:Data:150"
		]

		temp_data = frappe.db.sql("""

			SELECT 
			e.`name`,
			att.`biometric_id` as biometric_id, 
			e.`employee_name`, 
			e.`department`, 
			e.`designation`,
			e.`status`,
			att.`company`, 
			e.`default_shift`, 
			att.`attendance_date` as attendance_date,
			TIME_FORMAT(att.`start_time`, '%H:%i:%s'),
			TIME_FORMAT(att.`exit_time`, '%H:%i:%s'),
			IF(att.`request_attendance` != "", "Request Attendance", IF(att.`old_start_time_update` !="00:00:00" OR att.`old_exit_time_update` !="00:00:00", "Update Attendance Time", IF(att.`status`="On Leave", IF(att.`leave_type` != "Leave Without Pay", att.`leave_type`, "On Leave"), "Biometric") )) AS "attendance_type"

			FROM `tabAttendance` att
			LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
			WHERE att.`docstatus` = 1
			AND att.`status` = "Present"
			{0}
			{1}
			{2}

			UNION ALL

			SELECT 
			e1.`name`,
			att1.`biometric_id` AS biometric_id, 
			e1.`employee_name`, 
			e1.`department`, 
			e1.`designation`,
			e1.`status`,
			att1.`company`, 
			e1.`default_shift`, 
			att1.`attendance_date` AS attendance_date,
			TIME_FORMAT(att1.`start_time`, '%H:%i:%s'),
			TIME_FORMAT(att1.`exit_time`, '%H:%i:%s'),
			IF(att1.`request_attendance` != "", "Request Attendance", IF(att1.`old_start_time_update` !="00:00:00" OR att1.`old_exit_time_update` !="00:00:00", "Update Attendance Time", IF(att1.`status`="On Leave", IF(att1.`leave_type` != "Leave Without Pay", att1.`leave_type`, "On Leave"), "Biometric") )) AS "attendance_type"

			FROM `tabAttendance` att1
			LEFT JOIN `tabEmployee` e1 ON (att1.`biometric_id` = e1.`biometric_id` OR att1.`employee` = e1.`name`)
			LEFT JOIN `tabLeave Type` lt ON att1.`leave_type` = lt.`name`
			WHERE att1.`docstatus` = 1
			AND att1.`status` = "On Leave" 
			AND lt.`is_lwp` = 0

			{3}
			{4}
			{5}


			ORDER BY CAST(biometric_id AS UNSIGNED) ASC, attendance_date ASC

		""".format(date_clause, employee_clause, range_clause,date_clause1, employee_clause1, range_clause1))

		if temp_data :
			for i in temp_data :
				if i[0] not in exclude_employee :
					if str(i[7]) :
						get_shift = frappe.get_doc("Shift Type", str(i[7]))
						for hk in get_shift.work_time :
							if hk.days == str(getdate(str(i[8])).strftime("%A")) :
								data.append([ i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11] ])



	elif filters.report_type == "ABSENT REPORT" :
		columns = [
		"ID:Data:100",
		"Employee Name:Data:200",
		"Department:Data:150",
		"Designation:Data:150",
		"Status:Data:100",
		"Company:Data:150",
		"Shift:Data:100",
		"Date:Date:100",
		"Actual Absent:Data:100",
		
		]

		# rebuild absent

		exc_emp = ""
		
		get_employee = frappe.get_single("HR Configuration").exclude_employee_attendance
		if get_employee :
			for abc in get_employee :
				exc_emp += str(' AND e.`name` != "{}" '.format(abc.employee))

				


		gemp = frappe.db.sql("""

			SELECT 
			e.`name`,
			e.`biometric_id`, 
			e.`employee_name`, 
			e.`department`, 
			e.`designation`,
			e.`status`,
			e.`company`, 
			e.`default_shift`

			FROM `tabEmployee` e 
			WHERE e.`docstatus` = 0
			{}
			{}
			{}
			

			ORDER BY CAST(e.`biometric_id` AS UNSIGNED) ASC

		""".format(employee_clause, range_clause_employee, exc_emp))

		if gemp :
			for e in gemp :
				berapa_hari = date_diff(filters.get("to_date"), filters.get("from_date"))

				for z in range(berapa_hari+1):
					pertambahan_hari = add_days(filters.get("from_date"), z)

					# cek hari kerja employee di shift
					if str(e[7]) :
						get_shift = frappe.get_doc("Shift Type", str(e[7]))
						for hk in get_shift.work_time :
							if hk.days == str(getdate(str(pertambahan_hari)).strftime("%A")) :


								get_holiday = frappe.db.sql(""" SELECT * FROM `tabHoliday` h WHERE h.`holiday_date` = "{}" """.format(pertambahan_hari))
								if not get_holiday :

									get_attendance = frappe.db.sql(""" 
										SELECT 
										e.`name`,
										att.`biometric_id` as biometric_id, 
										e.`employee_name`, 
										e.`department`, 
										e.`designation`,
										e.`status`,
										att.`company`, 
										e.`default_shift`, 
										att.`attendance_date` as attendance_date,
										att.`leave_type`

										FROM `tabAttendance` att
										LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
										WHERE att.`docstatus` = 1
										AND att.`status` = "Present"
										AND e.`employee` = "{0}"
										AND att.`attendance_date` = "{1}"

										
										UNION ALL

										SELECT 
										e1.`name`,
										att1.`biometric_id` as biometric_id, 
										e1.`employee_name`, 
										e1.`department`, 
										e1.`designation`,
										e1.`status`,
										att1.`company`, 
										e1.`default_shift`, 
										att1.`attendance_date` as attendance_date,
										att1.`leave_type`

										FROM `tabAttendance` att1
										LEFT JOIN `tabEmployee` e1 ON (att1.`biometric_id` = e1.`biometric_id` OR att1.`employee` = e1.`name`)
										LEFT JOIN `tabLeave Type` lt ON att1.`leave_type` = lt.`name`
										WHERE att1.`docstatus` = 1
										AND att1.`status` = "On Leave" 
										AND lt.`is_lwp` = 0

										AND e1.`employee` = "{0}"
										AND att1.`attendance_date` = "{1}"


										ORDER BY CAST(biometric_id AS UNSIGNED) ASC, attendance_date ASC


										""".format(e[0], pertambahan_hari))

									if not get_attendance :

										cek_leave_without_pay = frappe.db.sql(""" 
											SELECT 
											e.`name`,
											att.`biometric_id` as biometric_id, 
											e.`employee_name`, 
											e.`department`, 
											e.`designation`,
											e.`status`,
											att.`company`, 
											e.`default_shift`, 
											att.`attendance_date` as attendance_date,
											att.`leave_type`

											FROM `tabAttendance` att
											LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
											WHERE att.`docstatus` = 1
											AND att.`status` = "Absent"
											AND e.`employee` = "{0}"
											AND att.`attendance_date` = "{1}"

											
											UNION ALL

											SELECT 
											e1.`name`,
											att1.`biometric_id` as biometric_id, 
											e1.`employee_name`, 
											e1.`department`, 
											e1.`designation`,
											e1.`status`,
											att1.`company`, 
											e1.`default_shift`, 
											att1.`attendance_date` as attendance_date,
											att1.`leave_type`

											FROM `tabAttendance` att1
											LEFT JOIN `tabEmployee` e1 ON (att1.`biometric_id` = e1.`biometric_id` OR att1.`employee` = e1.`name`)
											LEFT JOIN `tabLeave Type` lt ON att1.`leave_type` = lt.`name`
											WHERE att1.`docstatus` = 1
											AND att1.`status` = "On Leave" 
											AND lt.`is_lwp` = 1

											AND e1.`employee` = "{0}"
											AND att1.`attendance_date` = "{1}"


											ORDER BY CAST(biometric_id AS UNSIGNED) ASC, attendance_date ASC
											
											

											""".format(e[0], pertambahan_hari))

										if cek_leave_without_pay :
											data.append([  e[1], e[2], e[3], e[4], e[5], e[6], e[7], pertambahan_hari, cek_leave_without_pay[0][9] ])
										else :

											data.append([  e[1], e[2], e[3], e[4], e[5], e[6], e[7], pertambahan_hari, "Actual Absent" ])
							





	elif filters.report_type == "LATE ARRIVAL" :
		
		columns = [
		"ID:Data:100",
		"Employee Name:Data:100",
		"Department:Data:100",
		"Designation:Data:100",
		"Sex:Data:100",
		"Company:Data:100",
		"Shift:Data:100",
		"Date:Date:100",
		"Start Time:Time:100",
		"Grace:Time:100",
		"Arrived:Time:100",
		"Late:Time:100",
		"Attendance Type:Data:100"
		]

		temp_data = frappe.db.sql("""

			SELECT
			e.`name`,
			att.`biometric_id`,
			att.`employee_name`,
			e.`department`,
			e.`designation`, 
			e.`gender`,
			e.`company`,
			e.`default_shift`,
			att.`attendance_date`,
			TIME_FORMAT(att.`work_start_time`, '%H:%i:%s'),
			TIME_FORMAT(IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00"), '%H:%i:%s') AS grace,
			TIME_FORMAT(att.`start_time`, '%H:%i:%s') AS arrived,
			TIME_FORMAT(IF(SUBTIME(att.`start_time`, att.`work_start_time`) < "00:00:00", "00:00:00",SUBTIME(att.`start_time`, att.`work_start_time`)), '%H:%i:%s') AS late,
			IF(att.`request_attendance` != "", "Request Attendance", IF(att.`old_start_time_update` !="00:00:00" OR att.`old_exit_time_update` !="00:00:00", "Update Attendance Time", IF(att.`status`="On Leave", IF(att.`leave_type` != "Leave Without Pay", att.`leave_type`, "On Leave"), "Biometric") )) AS "attendance_type"


			FROM `tabAttendance` att
			LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
			LEFT JOIN `tabShift Type` st ON e.`default_shift` = st.`name`
			WHERE att.`docstatus` = 1
			AND att.`late_entry` = 1
			AND TIME_FORMAT(IF(SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00")) < "00:00:00", "00:00:00",SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00"))), '%H:%i:%s') > "00:00:00"

			{}
			{}
			{}

			ORDER BY CAST(att.`biometric_id` AS UNSIGNED) ASC, att.`attendance_date` ASC

		""".format(date_clause, employee_clause, range_clause))

		if temp_data :
			for i in temp_data :
				if i[0] not in exclude_employee :
					if str(i[7]) :
						get_shift = frappe.get_doc("Shift Type", str(i[7]))
						for hk in get_shift.work_time :
							if hk.days == str(getdate(str(i[8])).strftime("%A")) :
								data.append([ i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13] ])

	elif filters.report_type == "EARLY EXIT" :
		columns = [
		"ID:Data:100",
		"Employee Name:Data:100",
		"Department:Data:100",
		"Designation:Data:100",
		"Sex:Data:100",
		"Company:Data:100",
		"Shift:Data:100",
		"Date:Date:100",
		"Exit Time:Time:100",
		"Grace:Time:100",
		"Depart:Time:100",
		"Early:Time:100",
		"Attendance Type:Data:100"
		]

		temp_data = frappe.db.sql("""

			SELECT
			e.`name`,
			att.`biometric_id`,
			att.`employee_name`,
			e.`department`,
			e.`designation`, 
			e.`gender`,
			e.`company`,
			e.`default_shift`,
			att.`attendance_date`,
			TIME_FORMAT(att.`work_exit_time`, '%H:%i:%s'),
			TIME_FORMAT(IFNULL(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), "00:00:00"), '%H:%i:%s') AS grace,
			TIME_FORMAT(att.`exit_time`, '%H:%i:%s') AS depart,

			TIME_FORMAT(IF(SUBTIME(att.`work_exit_time`, att.`exit_time`) < "00:00:00", "00:00:00", SUBTIME(att.`work_exit_time`, att.`exit_time`)), '%H:%i:%s') AS early,
			IF(att.`request_attendance` != "", "Request Attendance", IF(att.`old_start_time_update` !="00:00:00" OR att.`old_exit_time_update` !="00:00:00", "Update Attendance Time", IF(att.`status`="On Leave", IF(att.`leave_type` != "Leave Without Pay", att.`leave_type`, "On Leave"), "Biometric") )) AS "attendance_type"

			FROM `tabAttendance` att
			LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
			LEFT JOIN `tabShift Type` st ON e.`default_shift` = st.`name`
			WHERE att.`docstatus` = 1
			AND att.`early_exit` = 1
			AND TIME_FORMAT(IF(SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`) < "00:00:00", "00:00:00", SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`)), '%H:%i:%s') > "00:00:00"

			{}
			{}
			{}

			ORDER BY CAST(att.`biometric_id` AS UNSIGNED) ASC, att.`attendance_date` ASC

		""".format(date_clause, employee_clause, range_clause))

		if temp_data :
			for i in temp_data :
				if i[0] not in exclude_employee :
					if str(i[7]) :
						get_shift = frappe.get_doc("Shift Type", str(i[7]))
						for hk in get_shift.work_time :
							if hk.days == str(getdate(str(i[8])).strftime("%A")) :
								data.append([ i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13] ])


	elif filters.report_type == "ATTENDANCE SUMMARY" :
		
		columns = [
		"ID:Data:100",
		"Employee Name:Data:200",
		"Department:Data:100",
		"Designation:Data:100",
		"Company:Data:100",
		"Shift:Data:100",
		"Total No of Working Days:Int:150",
		"Total No of Present Days:Int:150",
		"Total No of Absent Days:Int:150",
		"Total No of Late Days:Int:150",
		"Total No of Early Days:Int:150",
		"Total Late Arrival:Time:150",
		"Total Early Exit:Time:150",
		"Total No of Overtime Days:Float:150",
		"Total No of Penalty Days:Float:150"
		]

		get_data_customer = frappe.db.sql("""

			SELECT
			e.`name`,
			att.`biometric_id`,
			att.`employee_name`,
			e.`department`,
			e.`designation`,
			e.`company`,
			e.`default_shift`
			
			FROM `tabAttendance` att
			LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
			WHERE att.`docstatus` = 1
			AND att.`employee` IS NOT NULL
			
			{}
			{}
			{}

			GROUP BY e.`name`

		""".format(date_clause, employee_clause, range_clause))

		if get_data_customer :

			total_working_days = 0
			total_present_days = 0
			total_leave_days = 0
			total_absent_days = 0
			total_late_days = 0
			total_early_days = 0
			total_hour_late = 0
			total_hour_early = 0

			berapa_hari = date_diff(filters.get("to_date"), filters.get("from_date"))
			cek_panjang = 0



			for i in get_data_customer :


				total_working_days = 0
				total_present_days = 0
				total_leave_days = 0
				total_absent_days = 0
				total_late_days = 0
				total_early_days = 0
				total_hour_late = 0
				total_hour_early = 0

				berapa_hari = date_diff(filters.get("to_date"), filters.get("from_date"))
				cek_panjang = 0

				list_hari = ""


				if i[0] not in exclude_employee :

					for z in range(berapa_hari+1):
						cek_panjang += 1
						pertambahan_hari = add_days(filters.get("from_date"), z)

						if str(i[6]) :
							get_shift = frappe.get_doc("Shift Type", str(i[6]))
							for hk in get_shift.work_time :
								if hk.days == str(getdate(str(pertambahan_hari)).strftime("%A")) :

									get_holiday = frappe.db.sql(""" SELECT * FROM `tabHoliday` h WHERE h.`holiday_date` = "{}" """.format(pertambahan_hari))
									if not get_holiday :
										total_working_days += 1

										if z == 0 :
											list_hari = str('"')+str(pertambahan_hari)+str('"')
										else :
											list_hari = list_hari + "," + str('"')+str(pertambahan_hari)+str('"')


					# frappe.msgprint(str(i[0]) +" = "+str(list_hari))


					get_present_days = frappe.db.sql(""" SELECT att.`name`, att.`employee`, att.`attendance_date` FROM `tabAttendance` att 
						WHERE att.`docstatus` = 1 
						AND att.`status` = "Present"
						AND att.`employee` = "{0}" {1} 

						UNION ALL

						SELECT att1.`name`, att1.`employee`, att1.`attendance_date` FROM `tabAttendance` att1 
						LEFT JOIN `tabEmployee` e1 ON (att1.`biometric_id` = e1.`biometric_id` OR att1.`employee` = e1.`name`)
						LEFT JOIN `tabLeave Type` lt on att1.`leave_type` = lt.`name`

						WHERE att1.`docstatus` = 1 
						AND att1.`status` = "On Leave"
						AND att1.`attendance_date` BETWEEN "{2}" AND "{3}"
						AND e1.`employee` = "{0}"


					""".format(i[0], date_clause, filters.get("from_date"), filters.get("to_date")))

					get_leave = frappe.db.sql(""" 
						SELECT att.`name`, att.`employee`, att.`attendance_date` FROM `tabAttendance` att 
						LEFT JOIN `tabLeave Type` lt on att.`leave_type` = lt.`name`
						WHERE att.`docstatus` = 1 
						AND att.`status` = "On Leave"
						AND lt.`is_lwp` = 1
						AND att.`employee` = "{}" {} """.format(i[0], date_clause))

					if get_present_days :
						for gpd in get_present_days :
							if str(i[6]) :
								get_shift = frappe.get_doc("Shift Type", str(i[6]))
								for hk in get_shift.work_time :
									if hk.days == str(getdate(str(gpd[2])).strftime("%A")) :
										get_holiday = frappe.db.sql(""" SELECT * FROM `tabHoliday` h WHERE h.`holiday_date` = "{}" """.format(gpd[2]))
										if not get_holiday :
											total_present_days += 1

					if get_leave :
						for gl in get_leave :
							if str(i[6]) :
								get_shift = frappe.get_doc("Shift Type", str(i[6]))
								for hk in get_shift.work_time :
									if hk.days == str(getdate(str(gl[2])).strftime("%A")) :
										get_holiday = frappe.db.sql(""" SELECT * FROM `tabHoliday` h WHERE h.`holiday_date` = "{}" """.format(gl[2]))
										if not get_holiday :
											total_leave_days += 1
											

					
	

					get_late = frappe.db.sql("""
						SELECT 
						COUNT(att.`name`),
						TIME_FORMAT(SEC_TO_TIME( SUM( TIME_TO_SEC( IF(SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00")) < "00:00:00", "00:00:00",SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00"))) ) ) ), '%H:%i:%s') AS timeSum
						
						FROM `tabAttendance` att 
						LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
						LEFT JOIN `tabShift Type` st ON e.`default_shift` = st.`name`
						WHERE att.`docstatus` = 1 
						AND att.`late_entry` = 1
						AND TIME_FORMAT(IF(SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00")) < "00:00:00", "00:00:00",SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00"))), '%H:%i:%s') > "00:00:00"

						AND att.`employee` = "{}" 
						AND att.`attendance_date` IN ({})

						GROUP BY e.`employee`
						""".format(i[0], list_hari))

					if get_late :
						total_late_days = get_late[0][0]
						total_hour_late = get_late[0][1]


					get_early = frappe.db.sql("""
						SELECT 
						COUNT(att.`name`),
						TIME_FORMAT(SEC_TO_TIME( SUM( TIME_TO_SEC( IF(SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`) < "00:00:00", "00:00:00", SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`)) ) ) ), '%H:%i:%s')  AS timeSum
						
						FROM `tabAttendance` att 
						LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
						LEFT JOIN `tabShift Type` st ON e.`default_shift` = st.`name`
						WHERE att.`docstatus` = 1 
						AND att.`early_exit` = 1
						AND TIME_FORMAT(IF(SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`) < "00:00:00", "00:00:00", SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`)), '%H:%i:%s') > "00:00:00"

						AND att.`employee` = "{}" 
						AND att.`attendance_date` IN ({})

						GROUP BY e.`employee`
						""".format(i[0], list_hari))

					if get_early :
						total_early_days = get_early[0][0]
						total_hour_early = get_early[0][1]


					total_penalty_days = 0
					total_overtime_days = 0

					get_total_day = frappe.db.sql("""
						SELECT
						SUM(ese.`no_of_days_child`),
						ese.`employee`,
						es.`salary_component`
						FROM `tabExtra Salary` es
						LEFT JOIN `tabExtra Salary Employee` ese ON es.`name` = ese.`parent`
						WHERE es.`docstatus` = 1
						AND ese.`employee` = "{}"
						AND es.`posting_date` BETWEEN "{}" AND "{}"
						AND es.`type_extra_salary` = "OT and Penalty"

						GROUP BY es.`salary_component` 
					""".format(i[0], filters.get("from_date"), filters.get("to_date")))

					if get_total_day :
						for gtd in get_total_day :
							if gtd[2] == "Over Time" :
								total_overtime_days = float(gtd[0])
							elif gtd[2] == "Penalty" :
								total_penalty_days = float(gtd[0])

						

					data.append([ i[1], i[2], i[3], i[4], i[5], i[6], total_working_days, (total_present_days-total_leave_days), (total_working_days - total_present_days)+total_leave_days, total_late_days, total_early_days, total_hour_late, total_hour_early, total_overtime_days, total_penalty_days ])


	return columns,data
