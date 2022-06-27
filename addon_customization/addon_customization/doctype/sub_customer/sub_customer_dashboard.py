from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'sub_customer',
		'transactions': [
			{
				'items': ['Sales Order', 'Delivery Note', 'Sales Invoice', 'Payment Entry']
			}
		]
	}