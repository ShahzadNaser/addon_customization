# -*- coding: utf-8 -*-
# Copyright (c) 2020, riconova and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ItemPriceAdjustment(Document):
	
	# total_hitung = self.total_blr_ditambah_biaya

	# if self.pendekatan_pembulatan == "10" :
	# 	self.total_round_up = round(total_hitung, -1)
	# elif self.pendekatan_pembulatan == "100" :
	# 	self.total_round_up = round(total_hitung, -2)
	# elif self.pendekatan_pembulatan == "1000" :
	# 	self.total_round_up = round(total_hitung, -3)
	# elif self.pendekatan_pembulatan == "10000" :
	# 	self.total_round_up = round(total_hitung, -4)
	# elif self.pendekatan_pembulatan == "100000" :
	# 	self.total_round_up = round(total_hitung, -5)
	# else :
	# 	self.total_round_up = total_hitung

	def get_data_item(self) :
		if self.by_amount_or_percentage == "Amount" :
			if not self.by_amount :
				frappe.throw("By Amount is mandatory")

		elif self.by_amount_or_percentage == "Percentage" :
			if not self.by_percentage :
				frappe.throw("By Percentage is mandatory")

		# ambil semua itemnya
		self.increase_decrease_item_price_current = []
		if self.increase_or_decrease_by == "Item" :
			self.by_item()
		elif self.increase_or_decrease_by == "Item Group" :
			self.by_item_group()
		elif self.increase_or_decrease_by == "Item SubGroup" :
			self.by_item_subgroup()


	


	def on_submit(self) :
		# ambil semua itemnya
		# self.increase_decrease_item_price_current = []

		# if self.increase_or_decrease_by == "Item" :
		# 	self.by_item()
		# elif self.increase_or_decrease_by == "Item Group" :
		# 	self.by_item_group()
		# elif self.increase_or_decrease_by == "Item SubGroup" :
		# 	self.by_item_subgroup()

		if self.increase_decrease_item_price_current :
			for i in self.increase_decrease_item_price_current :
				# update item price
				price = i.current_item_price
				item_price_id = i.current_item_price_id
				new_price = 0
				temp_new_price = 0

				if self.increase_or_decrease == "Increase" :
					if self.by_amount_or_percentage == "Amount" :
						new_price = price + self.by_amount

					elif self.by_amount_or_percentage == "Percentage" :
						temp_new_price = price + ((price * self.by_percentage) / 100)
						if self.rounding_based_on == "0" :
							new_price = temp_new_price
						elif self.rounding_based_on == "10" :
							new_price = round(temp_new_price, -1)
						elif self.rounding_based_on == "100" :
							new_price = round(temp_new_price, -2)
						elif self.rounding_based_on == "1000" :
							new_price = round(temp_new_price, -3)

				elif self.increase_or_decrease == "Decrease" :
					if self.by_amount_or_percentage == "Amount" :
						new_price = price - self.by_amount

					elif self.by_amount_or_percentage == "Percentage" :
						temp_new_price = price - ((price * self.by_percentage) / 100)
						if self.rounding_based_on == "0" :
							new_price = temp_new_price
						elif self.rounding_based_on == "10" :
							new_price = round(temp_new_price, -1)
						elif self.rounding_based_on == "100" :
							new_price = round(temp_new_price, -2)
						elif self.rounding_based_on == "1000" :
							new_price = round(temp_new_price, -3)

				i.new_item_price = new_price


				item_price = frappe.get_doc("Item Price", item_price_id)
				item_price.price_list_rate = new_price
				item_price.valid_from = self.valid_from_date
				item_price.flags.ignore_permission = True
				item_price.save()



	
	def validate(self) :

		if self.by_amount_or_percentage == "Amount" :
			if not self.by_amount :
				frappe.throw("By Amount is mandatory")

		elif self.by_amount_or_percentage == "Percentage" :
			if not self.by_percentage :
				frappe.throw("By Percentage is mandatory")

		if not self.increase_decrease_item_price_current :
			frappe.throw("You must get data before save")
		


		if self.increase_decrease_item_price_current :
			for i in self.increase_decrease_item_price_current :
				# update item price
				price = i.current_item_price
				item_price_id = i.current_item_price_id
				new_price = 0
				temp_new_price = 0

				if self.increase_or_decrease == "Increase" :
					if self.by_amount_or_percentage == "Amount" :
						new_price = price + self.by_amount

					elif self.by_amount_or_percentage == "Percentage" :
						temp_new_price = price + ((price * self.by_percentage) / 100)
						if self.rounding_based_on == "0" :
							new_price = temp_new_price
						elif self.rounding_based_on == "10" :
							new_price = round(temp_new_price, -1)
						elif self.rounding_based_on == "100" :
							new_price = round(temp_new_price, -2)
						elif self.rounding_based_on == "1000" :
							new_price = round(temp_new_price, -3)

				elif self.increase_or_decrease == "Decrease" :
					if self.by_amount_or_percentage == "Amount" :
						new_price = price - self.by_amount

					elif self.by_amount_or_percentage == "Percentage" :
						temp_new_price = price - ((price * self.by_percentage) / 100)
						if self.rounding_based_on == "0" :
							new_price = temp_new_price
						elif self.rounding_based_on == "10" :
							new_price = round(temp_new_price, -1)
						elif self.rounding_based_on == "100" :
							new_price = round(temp_new_price, -2)
						elif self.rounding_based_on == "1000" :
							new_price = round(temp_new_price, -3)

				i.new_item_price = new_price




	def by_item(self) :
		# cek jika ada price list yang dipilih
		if self.for_price_list :
			get_ip = frappe.db.sql("""

				select ip.`item_code`, ip.`price_list_rate`, ip.`price_list`, ip.`name`, ip.`valid_from`
				from `tabItem Price` ip
				where ip.`item_code` = "{}"
				and ip.`price_list` = "{}"
				and ip.`price_list_rate` > 0

			""".format(self.by_name, self.for_price_list))

			if get_ip :
				for gip in get_ip :
					child = self.append("increase_decrease_item_price_current", {})
					child.item_code = gip[0]
					get_item = frappe.get_doc("Item", gip[0])
					child.item_name = get_item.item_name
					child.current_item_price = gip[1]
					child.current_price_list = gip[2]
					child.current_item_price_id = gip[3]
					child.current_valid_from = gip[4]

		else :
			# jika tidak ada ambil semua
			get_ip = frappe.db.sql("""

				select ip.`item_code`, ip.`price_list_rate`, ip.`price_list`, ip.`name` , ip.`valid_from`
				from `tabItem Price` ip
				where ip.`item_code` = "{}"
				and ip.`selling` = 1
				and ip.`price_list_rate` > 0

			""".format(self.by_name))

			if get_ip :
				for gip in get_ip :
					child = self.append("increase_decrease_item_price_current", {})
					child.item_code = gip[0]
					get_item = frappe.get_doc("Item", gip[0])
					child.item_name = get_item.item_name
					child.current_item_price = gip[1]
					child.current_price_list = gip[2]
					child.current_item_price_id = gip[3]
					child.current_valid_from = gip[4]


	def by_item_group(self) :
		# ambil semua item 
		get_i = frappe.db.sql("""

			select i.`name` from `tabItem` i
			where i.`disabled` = 0
			and i.`item_group` = "{}"

			""".format(self.by_name))

		if get_i :
			for gi in get_i :

				# cek jika ada price list yang dipilih
				if self.for_price_list :
					get_ip = frappe.db.sql("""

						select ip.`item_code`, ip.`price_list_rate`, ip.`price_list`, ip.`name` , ip.`valid_from`
						from `tabItem Price` ip
						where ip.`item_code` = "{}"
						and ip.`price_list` = "{}"
						and ip.`price_list_rate` > 0

					""".format(gi[0], self.for_price_list))

					if get_ip :
						for gip in get_ip :
							child = self.append("increase_decrease_item_price_current", {})
							child.item_code = gip[0]
							get_item = frappe.get_doc("Item", gip[0])
							child.item_name = get_item.item_name
							child.current_item_price = gip[1]
							child.current_price_list = gip[2]
							child.current_item_price_id = gip[3]
							child.current_valid_from = gip[4]

				else :
					# jika tidak ada ambil semua
					get_ip = frappe.db.sql("""

						select ip.`item_code`, ip.`price_list_rate`, ip.`price_list`, ip.`name` , ip.`valid_from`
						from `tabItem Price` ip
						where ip.`item_code` = "{}"
						and ip.`selling` = 1
						and ip.`price_list_rate` > 0

					""".format(gi[0]))

					if get_ip :
						for gip in get_ip :
							child = self.append("increase_decrease_item_price_current", {})
							child.item_code = gip[0]
							get_item = frappe.get_doc("Item", gip[0])
							child.item_name = get_item.item_name
							child.current_item_price = gip[1]
							child.current_price_list = gip[2]
							child.current_item_price_id = gip[3]
							child.current_valid_from = gip[4]


	def by_item_subgroup(self) :
		get_i = frappe.db.sql("""

			select i.`name` from `tabItem` i
			where i.`disabled` = 0
			and i.`item_subgroup` = "{}"

			""".format(self.by_name))

		if get_i :
			for gi in get_i :

				# cek jika ada price list yang dipilih
				if self.for_price_list :
					get_ip = frappe.db.sql("""

						select ip.`item_code`, ip.`price_list_rate`, ip.`price_list`, ip.`name` , ip.`valid_from`
						from `tabItem Price` ip
						where ip.`item_code` = "{}"
						and ip.`price_list` = "{}"
						and ip.`price_list_rate` > 0

					""".format(gi[0], self.for_price_list))

					if get_ip :
						for gip in get_ip :
							child = self.append("increase_decrease_item_price_current", {})
							child.item_code = gip[0]
							get_item = frappe.get_doc("Item", gip[0])
							child.item_name = get_item.item_name
							child.current_item_price = gip[1]
							child.current_price_list = gip[2]
							child.current_item_price_id = gip[3]
							child.current_valid_from = gip[4]

				else :
					# jika tidak ada ambil semua
					get_ip = frappe.db.sql("""

						select ip.`item_code`, ip.`price_list_rate`, ip.`price_list`, ip.`name` , ip.`valid_from`
						from `tabItem Price` ip
						where ip.`item_code` = "{}"
						and ip.`selling` = 1
						and ip.`price_list_rate` > 0

					""".format(gi[0]))

					if get_ip :
						for gip in get_ip :
							child = self.append("increase_decrease_item_price_current", {})
							child.item_code = gip[0]
							get_item = frappe.get_doc("Item", gip[0])
							child.item_name = get_item.item_name
							child.current_item_price = gip[1]
							child.current_price_list = gip[2]
							child.current_item_price_id = gip[3]
							child.current_valid_from = gip[4]



