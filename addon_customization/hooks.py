# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "addon_customization"
app_title = "Addon Customization"
app_publisher = "riconova"
app_description = "Addon Customization"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "suprayoto.riconova@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/addon_customization/css/addon_customization.css"
# app_include_js = "/assets/addon_customization/js/addon_customization.js"

# include js, css files in header of web template
# web_include_css = "/assets/addon_customization/css/addon_customization.css"
# web_include_js = "/assets/addon_customization/js/addon_customization.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "addon_customization.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "addon_customization.install.before_install"
# after_install = "addon_customization.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "addon_customization.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Journal Entry": {

		"before_save" : ["addon_customization.sync_method.cek_similar_loan_disbursement","addon_customization.sync_method.cek_similar_request_expenses","addon_customization.sync_method.cek_je_sub_customer"],
		"before_submit" : ["addon_customization.sync_method.cek_similar_loan_disbursement"],

		"on_submit": ["addon_customization.addon_customization.doctype.request_expenses.request_expenses.submit_je", "addon_customization.addon_customization.doctype.prepayment.prepayment.submit_je" ],
		"on_cancel": ["addon_customization.addon_customization.doctype.request_expenses.request_expenses.cancel_je", "addon_customization.addon_customization.doctype.prepayment.prepayment.cancel_je" ]
	},
	"Stock Entry": {
		# "before_save": "addon_customization.sync_method.calculate_qty_check_ste",
		"before_save": "addon_customization.sync_method.save_submit_cek_wh_stock_entry",
		"before_submit": "addon_customization.sync_method.save_submit_cek_wh_stock_entry",
		"on_submit": ["addon_customization.sync_method.check_ste_on_submit", "addon_customization.sync_method.create_ste_gle_manual", "addon_customization.sync_method.save_submit_cek_wh_stock_entry"],
		
	},
	"Delivery Note": {
		# "before_save": "addon_customization.sync_method.calculate_qty_check_ste",
		"before_save": ["addon_customization.sync_method.cek_similar_dn", "addon_customization.sync_method.save_submit_cek_wh_delivery_note", "addon_customization.sync_method.save_submit_cek_customer_with_sub"],
		"before_submit": ["addon_customization.sync_method.check_credit_limit_delivery_note", "addon_customization.sync_method.save_submit_cek_wh_delivery_note"],
		"on_submit": "addon_customization.sync_method.create_dn_gle_manual"
		
	},
	"Sales Invoice": {
		"before_save": ["addon_customization.sync_method.cek_similar_sinv","addon_customization.sync_method.save_submit_cek_wh_sales_invoice", "addon_customization.sync_method.save_submit_cek_customer_with_sub"],
		"validate": "addon_customization.sync_method.change_income_account_based_on_item_group",
		"before_submit": ["addon_customization.sync_method.check_credit_limit_sales_invoice","addon_customization.sync_method.save_submit_cek_wh_sales_invoice", "addon_customization.sync_method.save_submit_cek_customer_with_sub","addon_customization.sync_method.save_submit_cek_credit_limit_sub_customer"],
		"on_submit": "addon_customization.sync_method.create_sinv_gle_manual"
		
	},
	"Stock Reconciliation": {
		
		"on_submit": "addon_customization.sync_method.create_sr_gle_manual"
		
	},
	"Payment Entry": {
		
		"before_save": "addon_customization.sync_method.save_submit_cek_pe_customer_with_sub",
		"before_subit" : "addon_customization.sync_method.save_submit_cek_pe_customer_with_sub",
		
	},
	"Purchase Receipt": {
		"before_save" : "addon_customization.sync_method.save_submit_cek_wh_purchase_receipt",
		"before_submit" : "addon_customization.sync_method.save_submit_cek_wh_purchase_receipt",
		"on_submit": "addon_customization.sync_method.create_prec_gle_manual"
		
	},
	"Purchase Order": {
		"before_save" : "addon_customization.sync_method.save_submit_cek_wh_purchase_order",
		"before_submit" : "addon_customization.sync_method.save_submit_cek_wh_purchase_order"
	},
	"Purchase Invoice": {
		"before_save" : "addon_customization.sync_method.save_submit_cek_wh_purchase_invoice",
		"before_submit" : "addon_customization.sync_method.save_submit_cek_wh_purchase_invoice",
		"on_submit": "addon_customization.sync_method.create_pinv_gle_manual"
		
	},
	"Sales Order": {
		"before_save" : ["addon_customization.sync_method.save_submit_cek_wh_sales_order","addon_customization.sync_method.save_submit_cek_customer_with_sub"],
		"before_submit" : ["addon_customization.sync_method.save_submit_cek_wh_sales_order","addon_customization.sync_method.save_submit_cek_customer_with_sub","addon_customization.sync_method.save_submit_cek_credit_limit_sub_customer"],
	},
	"GL Entry": {
		
		# "validate": "addon_customization.sync_method.validate_gl_entry_sub_customer",
		# "after_insert": "addon_customization.sync_method.validate_gl_entry_sub_customer",
		# "before_save": "addon_customization.sync_method.validate_gl_entry_sub_customer",
		
		"on_submit": "addon_customization.sync_method.validate_gl_entry_sub_customer"
		
	},
	"Loan": {
		"before_save": "addon_customization.sync_method.cek_similar_loan",
		"before_submit": "addon_customization.sync_method.cek_similar_loan",
	},
	"Shift Type": {
		"validate": "addon_customization.sync_method.validation_same_days",
	},
	"Item Price": {
		"validate": "addon_customization.sync_method.validation_same_item_price",
	},
	"Bin": {
		"validate": "addon_customization.sync_method.save_bin_cek_email_min_max",
	},
	"Item": {
		"validate": "addon_customization.sync_method.cek_duplicate_warehouse_min_max_qty",
	},

	# "Landed Cost Voucher": {
	# 	# "before_save" : "addon_customization.sync_method.save_submit_cek_wh_purchase_receipt",
	# 	# "before_submit" : "addon_customization.sync_method.save_submit_cek_wh_purchase_receipt",
	# 	"after_submit": "addon_customization.sync_method.create_lcv_gle_manual"
		
	# },
	# "Salary Slip": {
	# 	"before_save": "addon_customization.sync_method.calculation_working_days_and_absent",
	# 	"after_insert": "addon_customization.sync_method.calculation_working_days_and_absent",
	# }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	
	"5 11 * * *": [
		"addon_customization.sync_method.auto_delete_duplicate_attendance",

	],
	"daily": [
		"addon_customization.addon_customization.doctype.prepayment.prepayment.auto_generate_je_based_on_date",
		"addon_customization.sync_method.auto_apply_employee_id_and_employee_name",
		"addon_customization.sync_method.auto_check_late_entry_or_early_exit",
		"addon_customization.sync_method.auto_delete_duplicate_attendance",
		"addon_customization.sync_method.cek_document_schedule_email",

	],
	"monthly": [
		"addon_customization.addon_customization.doctype.provision_setup.provision_setup.auto_generate_je_based_on_date"
	]
	
}

scheduler_events = {

	"cron": {
		"0 1 * * *": [
			"addon_customization.sync_method.misc_methods",
		]
		}
	
# 	"all": [
# 		"addon_customization.tasks.all"
# 	],
# 	"daily": [
# 		"addon_customization.tasks.daily"
# 	],
# 	"hourly": [
# 		"addon_customization.tasks.hourly"
# 	],
# 	"weekly": [
# 		"addon_customization.tasks.weekly"
# 	]
# 	"monthly": [
# 		"addon_customization.tasks.monthly"
# 	]
}

# Testing
# -------

# before_tests = "addon_customization.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "addon_customization.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "addon_customization.task.get_dashboard_data"
# }

