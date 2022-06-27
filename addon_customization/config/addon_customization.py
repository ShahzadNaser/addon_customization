from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Addons Manufacturing"),
			"items": [
				{
					"type": "doctype",
					"name": "Production Form",
					"description":_("Production Form"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Block Production",
					"description":_("Block Production"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Transformation Production",
					"description":_("Transformation"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Transfer into Item",
					"description":_("Transfer into Item"),
					"onboard": 1,
				}
			]
		},

		{
			"label": _("Request"),
			"items": [
				{
					"type": "doctype",
					"name": "Request Expenses",
					"description":_("Request Expenses"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Depot Store Request",
					"description":_("Depot Store Request"),
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Setting"),
			"items": [
				{
					"type": "doctype",
					"name": "General Setting",
					"description":_("General Setting"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "HR Configuration",
					"description":_("HR Configuration"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Warehouse Access Settings",
					"description":_("Warehouse Access Settings"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Prepayment",
					"description":_("Prepayment"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Provision Setup",
					"description":_("Provision Setup"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Negative Stock Settings",
					"description":_("Negative Stock Settings"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Email for Customer",
					"description":_("Email GL to Customer"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Item Price Adjustment",
					"description":_("Item Price Adjustment"),
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Fleet Management (Beta)"),
			"items": [
				{
					"type": "doctype",
					"name": "Checking Template",
					"description":_("Checking Template"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Vehicle",
					"description":_("Vehicle"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Vehicle Checking",
					"description":_("Vehicle Checking"),
					"onboard": 1,
				}
			]
		},
	]