from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("General Ledger"),
			"items": [
				{
					"type": "report",
					"name": "Sundry Debtor Ledger Summary",
					"description":_("Sundry Debtor Ledger Summary"),
					
				},
				{
					"type": "report",
					"name": "Block Production",
					"description":_("Block Production"),
					"onboard": 1,
				},
				
			]
		},

		
	]