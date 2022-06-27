from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'transfer_into_item',
		'transactions': [
			{
				'items': ['Stock Entry']
			}
		]
	}