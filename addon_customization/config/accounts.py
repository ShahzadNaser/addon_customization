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
                    "doctype": "GL Entry",
					"is_query_report": True
					
				},
				
				
			]
		},

		
	]