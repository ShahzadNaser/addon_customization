# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _, scrub
from frappe.utils import getdate, nowdate
from six import iteritems, itervalues

class PartyLedgerSummaryReport(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.filters.from_date = getdate(self.filters.from_date or nowdate())
		self.filters.to_date = getdate(self.filters.to_date or nowdate())

		if not self.filters.get("company"):
			self.filters["company"] = frappe.db.get_single_value('Global Defaults', 'default_company')

	def run(self, args):
		if self.filters.from_date > self.filters.to_date:
			frappe.throw(_("From Date must be before To Date"))

		self.filters.party_type = args.get("party_type")
		self.party_naming_by = frappe.db.get_value(args.get("naming_by")[0], None, args.get("naming_by")[1])

		self.get_gl_entries()
		self.get_return_invoices()
		

		columns = self.get_columns()
		data = self.get_data()
		return columns, data

	def get_columns(self):
		columns = [{
			"label": _(self.filters.party_type),
			"fieldtype": "Link",
			"fieldname": "party",
			"options": self.filters.party_type,
			"width": 110
		}]

		if self.party_naming_by == "Naming Series":
			columns.append({
				"label": _(self.filters.party_type + "Name"),
				"fieldtype": "Data",
				"fieldname": "party_name",
				"width": 200
			})

		columns.append({
			"label": _("Sub Customer"),
			"fieldtype": "Data",
			"fieldname": "sub_customer",
			"width": 200
		})

		credit_or_debit_note = "Credit Note" 

		columns += [
			{
				"label": _("Opening Balance"),
				"fieldname": "opening_balance",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			},
			{
				"label": _("Invoiced Amount"),
				"fieldname": "invoiced_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			},
			{
				"label": _("Paid Amount"),
				"fieldname": "paid_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			},
			{
				"label": _(credit_or_debit_note),
				"fieldname": "return_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			},
		]

		columns += [
			{
				"label": _("Closing Balance"),
				"fieldname": "closing_balance",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			},
			{
				"label": _("Currency"),
				"fieldname": "currency",
				"fieldtype": "Link",
				"options": "Currency",
				"width": 50
			}
		]

		return columns

	def get_data(self):
		company_currency = frappe.get_cached_value('Company',  self.filters.get("company"),  "default_currency")
		invoice_dr_or_cr = "debit" if self.filters.party_type == "Customer" else "credit"
		reverse_dr_or_cr = "credit" if self.filters.party_type == "Customer" else "debit"

		self.party_data = frappe._dict({})
		for gle in self.gl_entries:
			sub_customer = gle.sub_customer

			self.party_data.setdefault(sub_customer, frappe._dict({
				"party": gle.party,
				"party_name": gle.party_name,
				"sub_customer" : sub_customer,
				"opening_balance": 0,
				"invoiced_amount": 0,
				"paid_amount": 0,
				"return_amount": 0,
				"closing_balance": 0,
				"currency": company_currency
				
			}))
			# else :
			# 	sub_customer = "not input"
			# 	self.party_data.setdefault(gle.party, frappe._dict({
			# 		"party": gle.party,
			# 		"party_name": gle.party_name,
			# 		"sub_customer" : sub_customer,
			# 		"opening_balance": 0,
			# 		"invoiced_amount": 0,
			# 		"paid_amount": 0,
			# 		"return_amount": 0,
			# 		"closing_balance": 0,
			# 		"currency": company_currency
					
			# 	}))

			amount = gle.get(invoice_dr_or_cr) - gle.get(reverse_dr_or_cr)
			self.party_data[sub_customer].closing_balance += amount

			if gle.posting_date < self.filters.from_date or gle.is_opening == "Yes":
				self.party_data[sub_customer].opening_balance += amount
			else:
				if amount > 0:
					self.party_data[sub_customer].invoiced_amount += amount
				elif gle.voucher_no in self.return_invoices:
					self.party_data[sub_customer].return_amount -= amount
				else:
					self.party_data[sub_customer].paid_amount -= amount

		out = []
		for party, row in iteritems(self.party_data):
			if row.opening_balance or row.invoiced_amount or row.paid_amount or row.return_amount or row.closing_amount:

				out.append(row)

		return out

	def get_gl_entries(self):
		conditions = self.prepare_conditions()
		join = join_field = ""
		if self.filters.party_type == "Customer":
			join_field = ", p.customer_name as party_name"
			join = "left join `tabCustomer` p on gle.party = p.name"
		

		self.gl_entries = frappe.db.sql("""
			select
				gle.posting_date, gle.party, gle.voucher_type, gle.voucher_no, gle.against_voucher_type,
				gle.against_voucher, gle.debit, gle.credit, gle.is_opening, IFNULL(gle.sub_customer, CONCAT(gle.`party`, "-", "EMPTY")) as sub_customer {join_field}
			from `tabGL Entry` gle
			{join}
			where
				gle.docstatus < 2 and gle.party_type=%(party_type)s and ifnull(gle.party, '') != ''
				and gle.posting_date <= %(to_date)s {conditions}
				and gle.sub_customer IS NOT NULL
			order by gle.posting_date
		""".format(join=join, join_field=join_field, conditions=conditions), self.filters, as_dict=True)

	def prepare_conditions(self):
		conditions = [""]

		if self.filters.company:
			conditions.append("gle.company=%(company)s")

		
		if self.filters.get("party"):
			conditions.append("party=%(party)s")

		if self.filters.party_type == "Customer":
			if self.filters.get("customer_group"):
				lft, rgt = frappe.db.get_value("Customer Group",
					self.filters.get("customer_group"), ["lft", "rgt"])

				conditions.append("""party in (select name from tabCustomer
					where exists(select name from `tabCustomer Group` where lft >= {0} and rgt <= {1}
						and name=tabCustomer.customer_group))""".format(lft, rgt))

			if self.filters.get("territory"):
				lft, rgt = frappe.db.get_value("Territory",
					self.filters.get("territory"), ["lft", "rgt"])

				conditions.append("""party in (select name from tabCustomer
					where exists(select name from `tabTerritory` where lft >= {0} and rgt <= {1}
						and name=tabCustomer.territory))""".format(lft, rgt))

			
		

		return " and ".join(conditions)

	def get_return_invoices(self):
		doctype = "Sales Invoice" if self.filters.party_type == "Customer" else "Purchase Invoice"
		self.return_invoices = [d.name for d in frappe.get_all(doctype, filters={"is_return": 1, "docstatus": 1,
			"posting_date": ["between", [self.filters.from_date, self.filters.to_date]]})]

	
def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	return PartyLedgerSummaryReport(filters).run(args)
