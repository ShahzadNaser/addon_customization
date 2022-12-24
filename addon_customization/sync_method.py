
# -*- coding: utf-8 -*-
# Copyright (c) 2015, erpx and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _
from frappe.model.document import Document
import json
import os
import requests
import subprocess
from frappe.utils.background_jobs import enqueue
from frappe.utils import get_site_name

from frappe import utils
from frappe.utils import nowdate, add_days, random_string, get_url
from erpnext.assets.doctype.asset.depreciation import get_gl_entries_on_asset_disposal
import time
import datetime

from frappe import utils

from frappe.utils import cint, flt, cstr

from erpnext.stock.stock_ledger import get_valuation_rate
from erpnext.accounts.utils import get_account_currency, get_fiscal_year

from frappe.utils import getdate

from frappe.utils import add_days, date_diff, random_string
from frappe.utils import getdate



from erpnext.accounts.general_ledger import make_reverse_gl_entries


def get_gl():
    all_gl = frappe.get_all("GL Entry",['name','fiscal_year','posting_date'])
    count = 0
    for each in all_gl:
        if not correct_date(each):
            count+=1
            
            update_gl(each)
            print(f"{count} updated")
            

def correct_date(each):
    fy = frappe.get_all("Fiscal Year",{'name':each.fiscal_year},['year_start_date','year_end_date'])
    return fy[0].year_start_date <= each.posting_date <= fy[0].year_end_date



def update_gl(each):
    if frappe.db.exists("Fiscal Year",str(each.posting_date.year)):
        frappe.db.set_value("GL Entry",each.name,'fiscal_year',str(each.posting_date.year))
    



class SyncMethod(Document):
    pass


# datetime.datetime.strptime(s, "%d/%m/%Y").timestamp()

# utils.now()
# utils.today()



# @frappe.whitelist()
# def filter_warehouse_user_permission(doctype, txt, searchfield, start, page_len, filters):

# 	get_data = frappe.db.sql("""

# 		SELECT up.`for_value` FROM `tabUser Permission` up
# 		WHERE up.`user` = "{}"
# 		AND up.`allow` = "Warehouse`

# 	""".format(filters.get("user_id")))

# 	if get_data :
# 		return get_data

# 	else :
# 		return frappe.db.sql("""

# 			SELECT wh.`name` FROM `tabWarehouse` wh
# 			WHERE wh.`is_group` = 0
            
# 		""".format())


@frappe.whitelist()
def cek_duplicate_warehouse_min_max_qty(doc, method):
    
    # frappe.msgprint(frappe.utils.get_url())

    cek_warehouse = []
    cek_user = []
    patokan = ""

    if doc.min_max_qty_item :
        for i in doc.min_max_qty_item :
            if i.warehouse in cek_warehouse :
                frappe.throw("Got multiple row of warehouse "+str(i.warehouse))
            else :
                cek_warehouse.append(i.warehouse)

    if doc.email_user_for_min_max_qty :
        for i in doc.email_user_for_min_max_qty :
            patokan = str(i.user) + " || " + str(i.warehouse)
            if patokan in cek_user :
                frappe.throw("Got multiple row of user and warehouse "+str(patokan).split("||")[0]+" and "+str(patokan).split("||")[1])
            else:
                cek_user.append(patokan)




@frappe.whitelist()
def cek_document_schedule_email():

    # if frappe.utils.get_url() == "http://erpnext.winco-group.com" :
    get_data = frappe.db.sql("""
        SELECT dse.`name`, dse.`email_user` FROM `tabDocument Schedule Email` dse
        WHERE dse.`date_email` = "{}"
        AND dse.`docstatus` = 0

    """.format(utils.today()))

    if get_data :
        for i in get_data :
            get_docu = frappe.get_doc("Document Schedule Email", i[0])
            get_docu.flags.ignore_permissions = True
            get_docu.submit()




@frappe.whitelist()
def save_bin_cek_email_min_max(doc, method):

    # if frappe.utils.get_url() == "http://erpnext.winco-group.com" :

    get_data = frappe.db.sql("""
        select mmqi.`min_qty`, mmqi.`max_qty`, mmqi.`warehouse` 
        from `tabMin Max Qty Item` mmqi
        where mmqi.`parent` = "{}"
        and mmqi.`warehouse` = "{}"

    """.format(doc.item_code, doc.warehouse))

    min_qty = 0
    max_qty = 0
    subject = ""
    email_body = ""
    tgl_sekarang = str(utils.today())
    tgl_email = ""

    get_item = frappe.get_doc("Item", doc.item_code)
    if get_item.reminder_days :
        tgl_email = add_days(tgl_sekarang, int(get_item.reminder_days))
    else :
        tgl_email = tgl_sekarang

    if get_data :
        min_qty = get_data[0][0]
        max_qty = get_data[0][1]

        if doc.actual_qty < min_qty :
            subject = "Item "+get_item.item_name+" below min Qty"
            email_body = "Item "+get_item.item_name+" below min Qty. Min Qty = "+str(min_qty)+", Actual Qty = "+str(doc.actual_qty)
        elif doc.actual_qty > max_qty :
            subject = "Item "+get_item.item_name+" above max Qty"
            email_body = "Item "+get_item.item_name+" above max Qty. Max Qty = "+str(max_qty)+", Actual Qty = "+str(doc.actual_qty)

        if doc.actual_qty < min_qty or doc.actual_qty > max_qty :
            get_email_user = frappe.db.sql("""

                select eu.`user`, eu.`warehouse` from `tabEmail User for Min Max Qty` eu
                where eu.`parent` = "{}"

            """.format(doc.item_code))

            if get_email_user :
                for geu in get_email_user :

                    if geu[1] == "" or geu[1] is None or geu[1] == doc.warehouse :
                        
                        # untuk 3 hari
                        new_docu = frappe.new_doc("Document Schedule Email")
                        new_docu.email_user = geu[0]
                        new_docu.date_email = tgl_email
                        new_docu.subject_email = subject
                        new_docu.body_email = email_body
                        new_docu.item = doc.item_code
                        new_docu.warehouse = doc.warehouse

                        new_docu.flags.ignore_permissions = True
                        new_docu.save()

                        # untuk sekarang
                        new_docu = frappe.new_doc("Document Schedule Email")
                        new_docu.email_user = geu[0]
                        new_docu.date_email = tgl_email
                        new_docu.subject_email = subject
                        new_docu.body_email = email_body
                        new_docu.item = doc.item_code
                        new_docu.warehouse = doc.warehouse

                        new_docu.flags.ignore_permissions = True
                        new_docu.submit()

        frappe.db.sql("""
            UPDATE `tabDocument Schedule Email` dse
            SET dse.`docstatus` = 2
            WHERE dse.`date_email` < "{}"
            AND dse.`item` = "{}"
            AND dse.`warehouse` = "{}"

            """.format(tgl_email, doc.item_code, doc.warehouse))
        frappe.db.commit()






@frappe.whitelist()
def manual_make_je_for_payroll():
    get_docu = frappe.get_doc("Payroll Entry", "HR-PRUN-2020-00018")
    get_docu.make_accrual_jv_entry()

    print("done")




@frappe.whitelist()
def save_submit_cek_credit_limit_sub_customer(doc, method):

    if doc.doctype == "Sales Order" :
        get_csg = frappe.db.sql("""

            select * from `tabSub Customer` sc
            where sc.`customer` = "{}"

            """.format(doc.customer))

        if get_csg :
            if doc.sub_customer :
                # cek dulu bypass credit limit apa ndak

                sub_customer_outstanding = 0
                temp_outstanding_based_on_gle = 0
                temp_outstanding_based_on_so = 0
                outstanding_based_on_so = 0.0
                outstanding_based_on_gle = 0

                get_sub = frappe.get_doc("Sub Customer", doc.sub_customer)
                if get_sub.bypass_credit_limit_check != 1 :

                    # cek gle
                    temp_outstanding_based_on_gle = frappe.db.sql("""
                        select sum(debit) - sum(credit)
                        from `tabGL Entry` where party_type = 'Customer'
                        and party = "{}" and sub_customer = "{}"

                    """.format(doc.customer, doc.sub_customer))

                    outstanding_based_on_gle = flt(temp_outstanding_based_on_gle[0][0]) if temp_outstanding_based_on_gle else 0

                    # Outstanding based on Sales Order
                    outstanding_based_on_so = 0.0

                    # if credit limit check is bypassed at sales order level,
                    # we should not consider outstanding Sales Orders, when customer credit balance report is run
                    temp_outstanding_based_on_so = frappe.db.sql("""
                        select sum(base_grand_total*(100 - per_billed)/100)
                        from `tabSales Order`
                        where customer="{}" and docstatus = 1 and sub_customer="{}"
                        and per_billed < 100 and status != 'Closed' """.format(doc.customer, doc.sub_customer))

                    outstanding_based_on_so = flt(temp_outstanding_based_on_so[0][0]) if temp_outstanding_based_on_so else 0.0


                sub_customer_outstanding = outstanding_based_on_gle + outstanding_based_on_so

                if flt(get_sub.credit_limit) < sub_customer_outstanding :
                    frappe.throw("""Sub Customer credit limit is less than current outstanding amount. Credit limit has to be atleast {0}""".format(sub_customer_outstanding))

    else :

        if doc.is_return == 0 :
        
            get_csg = frappe.db.sql("""

                select * from `tabSub Customer` sc
                where sc.`customer` = "{}"

                """.format(doc.customer))

            if get_csg :
                if doc.sub_customer :
                    # cek dulu bypass credit limit apa ndak

                    sub_customer_outstanding = 0
                    temp_outstanding_based_on_gle = 0
                    temp_outstanding_based_on_so = 0
                    outstanding_based_on_so = 0.0

                    get_sub = frappe.get_doc("Sub Customer", doc.sub_customer)
                    if get_sub.bypass_credit_limit_check != 1 :

                        # cek gle
                        outstanding_based_on_gle = frappe.db.sql("""
                            select sum(debit) - sum(credit)
                            from `tabGL Entry` where party_type = 'Customer'
                            and party = "{}" and sub_customer = "{}"

                        """.format(doc.customer, doc.sub_customer))

                        temp_outstanding_based_on_gle = flt(outstanding_based_on_gle[0][0]) if outstanding_based_on_gle else 0

                        # Outstanding based on Sales Order
                        outstanding_based_on_so = 0.0

                        # if credit limit check is bypassed at sales order level,
                        # we should not consider outstanding Sales Orders, when customer credit balance report is run
                        outstanding_based_on_so = frappe.db.sql("""
                            select sum(base_grand_total*(100 - per_billed)/100)
                            from `tabSales Order`
                            where customer="{}" and docstatus = 1 and sub_customer="{}"
                            and per_billed < 100 and status != 'Closed' """.format(doc.customer, doc.sub_customer))

                        temp_outstanding_based_on_so = flt(outstanding_based_on_so[0][0]) if outstanding_based_on_so else 0.0


                        sub_customer_outstanding = temp_outstanding_based_on_gle + temp_outstanding_based_on_so

                        if flt(get_sub.credit_limit) < sub_customer_outstanding :
                            frappe.throw("""Sub Customer credit limit is less than current outstanding amount. Credit limit has to be atleast {0}""".format(sub_customer_outstanding))



@frappe.whitelist()
def cek_je_sub_customer(doc, method):
    for i in doc.accounts :
        if i.party_type == "Customer" :
            # ambil data sub customer group
            get_csg = frappe.db.sql("""

                select * from `tabSub Customer` sc
                where sc.`customer` = "{}"

                """.format(i.party))

            if get_csg :
                if not i.sub_customer :
                    frappe.throw("Please Enter Sub Customer name for "+str(i.party))


@frappe.whitelist()
def save_submit_cek_customer_with_sub(doc, method):
    
    get_csg = frappe.db.sql("""

        select * from `tabSub Customer` sc
        where sc.`customer` = "{}"

        """.format(doc.customer))

    if get_csg :
        if not doc.sub_customer :
            frappe.throw("Please Enter Sub Customer name for "+str(doc.customer))


@frappe.whitelist()
def save_submit_cek_pe_customer_with_sub(doc, method):
    
    if doc.payment_type == "Receive" :
        get_csg = frappe.db.sql("""

            select * from `tabSub Customer` sc
            where sc.`customer` = "{}"

            """.format(doc.party))

        if get_csg :
            if not doc.sub_customer :
                frappe.throw("Please Enter Sub Customer name for "+str(doc.party))



# --------------- cek warehouse setting access


# Stock Entry | Transformation | Block Production | Production Form | 
# Sales Order | Delivery Note | Sales Invoice | 
# Purchase Order | Purchase Receipt | Purchase Invoice |


@frappe.whitelist(allow_guest=True)
def create_accrual_je():

    payroll_entry = frappe.get_doc("Payroll Entry", "HR-PRUN-2020-00006")
    je_name = payroll_entry.make_accrual_jv_entry()

    print(je_name)



@frappe.whitelist(allow_guest=True)
def enqueue_repair():

    temp_doc =  ["MAT-PRE-2020-00053", "MAT-PRE-2020-00054"]
    # temp_doc = ["PREC-TBB2000606"]

    for i in temp_doc :

        docu = frappe.get_doc("Purchase Receipt", i)
        # # delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(i))
        # delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(i))
        # # # frappe.db.commit()
        # # docu.update_stock_ledger()
        # docu.make_gl_entries()
        # print("selesai")


        # docu.update_billing_status()
        delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(i))
        # delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(i))
        # frappe.db.commit()
        docu.update_stock_ledger()
        # docu.make_gl_entries()
        print(i)

@frappe.whitelist()
def filter_warehouse_user_permission(doctype, txt, searchfield, start, page_len, filters):

    get_data = frappe.db.sql("""

        SELECT up.`for_value` FROM `tabUser Permission` up
        WHERE up.`user` = "{}"
        AND up.`allow` = "Warehouse"

    """.format(filters.get("user_id")))

    if get_data :
        return get_data

    else :
        return frappe.db.sql("""

            SELECT wh.`name` FROM `tabWarehouse` wh
            WHERE wh.`is_group` = 0
            
        """.format())



@frappe.whitelist()
def save_submit_cek_wh_stock_entry(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    document_type = doc.stock_entry_type

    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        AND s.`type` = "{}"

    """.format(user_id, document, document_type))

    if get_setting :

        for i in doc.items :
            if i.s_warehouse :
                var_source = i.s_warehouse

            if i.t_warehouse :
                var_target = i.t_warehouse

        # Material Issue, Material Transfer, Manufacture, Repack, Send to Warehouse, Receive at Warehouse

        if doc.stock_entry_type == "Material Issue" :

            cek_user = frappe.db.sql("""
                SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                FROM `tabWarehouse Access Settings Child` s 
                WHERE s.`user` = "{}" 
                AND s.`document` = "{}"
                AND s.`type` = "{}"
                AND s.`source_wh` = "{}"
            """.format(user_id, document, document_type, var_source))

            if not cek_user :
                frappe.throw("You don't have access to this Combination of Warehouse")

        elif doc.stock_entry_type == "Material Receipt" :

            cek_user = frappe.db.sql("""
                SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                FROM `tabWarehouse Access Settings Child` s 
                WHERE s.`user` = "{}" 
                AND s.`document` = "{}"
                AND s.`type` = "{}"
                AND s.`target_wh` = "{}"
            """.format(user_id, document, document_type, var_target))

            if not cek_user :
                frappe.throw("You don't have access to this Combination of Warehouse")

        elif doc.stock_entry_type == "Material Transfer" :
            cek_user = frappe.db.sql("""
                SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                FROM `tabWarehouse Access Settings Child` s 
                WHERE s.`user` = "{}" 
                AND s.`document` = "{}"
                AND s.`type` = "{}"
                AND s.`source_wh` = "{}"
                AND s.`target_wh` = "{}"
            """.format(user_id, document, document_type, var_source, var_target))

            if not cek_user :
                frappe.throw("You don't have access to this Combination of Warehouse")

        elif doc.stock_entry_type == "Manufacture" :
            if not doc.block_production and not doc.production_form :
                cek_user = frappe.db.sql("""
                    SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                    FROM `tabWarehouse Access Settings Child` s 
                    WHERE s.`user` = "{}" 
                    AND s.`document` = "{}"
                    AND s.`type` = "{}"
                    AND s.`source_wh` = "{}"
                    AND s.`target_wh` = "{}"
                """.format(user_id, document, document_type, var_source, var_target))

                if not cek_user :
                    frappe.throw("You don't have access to this Combination of Warehouse")

        elif doc.stock_entry_type == "Repack" :
            cek_user = frappe.db.sql("""
                SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                FROM `tabWarehouse Access Settings Child` s 
                WHERE s.`user` = "{}" 
                AND s.`document` = "{}"
                AND s.`type` = "{}"
                AND s.`source_wh` = "{}"
                AND s.`target_wh` = "{}"
            """.format(user_id, document, document_type, var_source, var_target))

            if not cek_user :
                frappe.throw("You don't have access to this Combination of Warehouse")

        elif doc.stock_entry_type == "Send to Warehouse" :
            cek_user = frappe.db.sql("""
                SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                FROM `tabWarehouse Access Settings Child` s 
                WHERE s.`user` = "{}" 
                AND s.`document` = "{}"
                AND s.`type` = "{}"
                AND s.`source_wh` = "{}"
                AND s.`target_wh` = "{}"
            """.format(user_id, document, document_type, var_source, var_target))

            if not cek_user :
                frappe.throw("You don't have access to this Combination of Warehouse")

        elif doc.stock_entry_type == "Receive at Warehouse" :
            cek_user = frappe.db.sql("""
                SELECT s.`user`, s.`source_wh`, s.`target_wh` 
                FROM `tabWarehouse Access Settings Child` s 
                WHERE s.`user` = "{}" 
                AND s.`document` = "{}"
                AND s.`type` = "{}"
                AND s.`source_wh` = "{}"
                AND s.`target_wh` = "{}"
            """.format(user_id, document, document_type, var_source, var_target))

            if not cek_user :
                frappe.throw("You don't have access to this Combination of Warehouse")




@frappe.whitelist()
def save_submit_cek_wh_transformation(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"


    """.format(user_id, document))

    if get_setting :

        var_source = doc.warehouse

        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
    
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")

        


@frappe.whitelist()
def save_submit_cek_wh_block_production(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"


    """.format(user_id, document))

    if get_setting :

        var_source = doc.source_warehouse
        var_target = doc.target_warehouse

        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
    
            AND s.`source_wh` = "{}"
            AND s.`target_wh` = "{}"
        """.format(user_id, document, var_source, var_target))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_production_form(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"


    """.format(user_id, document))

    if get_setting :

        var_source = doc.raw_material_source_warehouse

        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
    
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_sales_order(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        
    """.format(user_id, document))

    if get_setting :

        for i in doc.items :
            if i.warehouse :
                var_source = i.warehouse
        
        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
            
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_delivery_note(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        
    """.format(user_id, document))

    if get_setting :

        for i in doc.items :
            if i.warehouse :
                var_source = i.warehouse
        
        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
            
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_sales_invoice(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        
    """.format(user_id, document))

    if get_setting :

        for i in doc.items :
            if i.warehouse :
                var_source = i.warehouse
        
        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
            
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_purchase_order(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        
    """.format(user_id, document))

    if get_setting :

        for i in doc.items :
            if i.warehouse :
                var_source = i.warehouse
        
        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
            
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_purchase_receipt(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        
    """.format(user_id, document))

    if get_setting :

        for i in doc.items :
            if i.warehouse :
                var_source = i.warehouse
        
        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
            
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


@frappe.whitelist()
def save_submit_cek_wh_purchase_invoice(doc, method):
    user_id = frappe.session.user
    document = doc.doctype
    
    var_source = ""
    var_target = ""

    get_setting = frappe.db.sql("""

        SELECT s.`user`, s.`source_wh`, s.`target_wh` 
        FROM `tabWarehouse Access Settings Child` s 
        WHERE s.`user` = "{}" 
        AND s.`document` = "{}"
        
    """.format(user_id, document))

    if get_setting :

        for i in doc.items :
            if i.warehouse :
                var_source = i.warehouse
        
        cek_user = frappe.db.sql("""
            SELECT s.`user`, s.`source_wh`, s.`target_wh` 
            FROM `tabWarehouse Access Settings Child` s 
            WHERE s.`user` = "{}" 
            AND s.`document` = "{}"
            
            AND s.`source_wh` = "{}"
        """.format(user_id, document, var_source))

        if not cek_user :
            frappe.throw("You don't have access to this Combination of Warehouse")


# --------------- end cek warehouse setting access

@frappe.whitelist()
def auto_delete_duplicate_attendance():

    get_count_duplicate = frappe.db.sql("""
        SELECT abc.employee, abc.biometric_id, abc.attendance_date, abc.counter 
        FROM (
            SELECT a.`employee` AS employee, a.`biometric_id` AS biometric_id, COUNT(a.`attendance_date`) AS counter, a.`attendance_date` AS attendance_date 
            FROM `tabAttendance` a
            WHERE a.`docstatus` = 1

            GROUP BY a.`attendance_date`, a.`biometric_id`
            ORDER BY a.`biometric_id` ASC, a.`attendance_date` ASC
        ) AS abc

        WHERE abc.counter = "2"

        """)

    if get_count_duplicate :
        for i in get_count_duplicate :
            # delete yang biometric saja
            att_id = str(i[1])+"#"+str(i[2])

            get_kembar = frappe.db.sql("""
                SELECT
                a.`name`,
                a.`creation`,
                a.`modified`,
                a.`modified_by`,
                a.`owner`,
                a.`docstatus`,
                a.`naming_series`,
                a.`company`,
                a.`attendance_date`,
                a.`amended_from`, 
                a.`_comments`,
                a.`leave_type`,
                a.`attendance_request`,
                a.`employee`,
                a.`employee_name`,
                a.`late_entry`, 
                a.`early_exit`,
                a.`shift`,
                a.`leave_application`,
                a.`working_hours`,
                a.`daily_check`,
                a.`biometric_id`,
                IFNULL(a.`start_time`,"00:00:00"),
                IFNULL(a.`exit_time`,"00:00:00"),
                IFNULL(a.`old_start_time_update`,"00:00:00"),
                IFNULL(a.`old_exit_time_update`,"00:00:00"),
                a.`request_attendance`,
                IFNULL(a.`work_start_time`,"00:00:00"),
                IFNULL(a.`work_exit_time`,"00:00:00")

                FROM `tabAttendance` a
                WHERE a.`name` = "{}"

            """.format(str(att_id)))

            if get_kembar :
                for gk in get_kembar :
                    # insert ke deleted document
                    frappe.db.sql("""

                        INSERT INTO `tabDeleted Attendance` (name,creation,modified,modified_by,owner,docstatus,series,company,attendance_date,amended_from,_comments,leave_type,attendance_request,employee,employee_name,late_entry,early_exit,shift,leave_application,working_hours,biometric_id,start_time,exit_time,old_start_time_update,old_exit_time_update,request_attendance,work_start_time,work_exit_time, attendance_name)
                        VALUES ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")


                    """.format(str(random_string(5)),gk[1],gk[2],gk[3],gk[4],gk[5],gk[6],gk[7],gk[8],gk[9],gk[10],gk[11],gk[12],gk[13],gk[14],gk[15],gk[16],gk[17],gk[18],gk[19],gk[21],gk[22],gk[23],gk[24],gk[25],gk[26],gk[27],gk[28], gk[0]))

                    frappe.db.commit()

                    frappe.db.sql(""" DELETE FROM `tabAttendance` WHERE name = "{}" """.format(str(att_id)))
                    frappe.db.commit()



@frappe.whitelist()
def auto_check_att_manual():
    
    get_data = frappe.db.sql("""

        SELECT a.`name`, a.`employee`, TIME(a.`start_time`), TIME(a.`exit_time`), e.`default_shift`, a.`attendance_date`
        FROM `tabAttendance` a
        LEFT JOIN `tabEmployee` e ON a.`employee` = e.`name`
        WHERE a.`docstatus` = 1
        AND (a.`status` = "Present" or a.`status` = "Half Day")
        AND a.`biometric_id` = "00002"

        order by a.`attendance_date` ASC
        

    """)

    if get_data :
        late_entry = 0
        early_exit = 0
        work_start_time = "00:00:00"
        work_exit_time = "00:00:00"
        for i in get_data :

            if i[4] :
                get_work_time = frappe.get_doc("Shift Type", i[4]).work_time
                get_shift = frappe.get_doc("Shift Type", i[4])
                if get_work_time :
                    for z in get_work_time :
                        if z.days == str(getdate(str(i[5])).strftime("%A")) and z.days != "Sunday" :

                            work_start_time = str(z.start_time)
                            work_exit_time = str(z.exit_time)

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
                            attendance_time_hour = str(i[2]).split(":")[0]
                            attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
                            attendance_time_minute = int(str(i[2]).split(":")[1]) 
                            attendance_time_total_minute = attendance_time_hour_in_minutes + attendance_time_minute

                            if str(work_time_total_minute) < str(attendance_time_total_minute) :
                                late_entry = 1
                            else :
                                late_entry = 0


                            print(""" att = {} emp = {} work_time_minute = {} ({}) att_time_minute = {} ({}) late_entry = {} """.format(i[5], i[1], work_time_total_minute, str(z.start_time), attendance_time_total_minute, str(i[2]), late_entry ))


                            # convert time to minutes
                            # work_time
                            # ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
                            work_time_total_minute = 0
                            work_time_hour = str(z.exit_time).split(":")[0]
                            work_time_hour_in_minutes = int(work_time_hour) * 60
                            work_time_minute = int(str(z.exit_time).split(":")[1]) 
                            work_time_total_minute = work_time_hour_in_minutes + work_time_minute - get_shift.grace_period_for_early_exit

                            # attendance_time
                            # ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
                            attendance_time_total_minute = 0
                            attendance_time_hour = str(i[3]).split(":")[0]
                            attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
                            attendance_time_minute = int(str(i[3]).split(":")[1]) 
                            attendance_time_total_minute = attendance_time_hour_in_minutes + attendance_time_minute


                            if str(work_time_total_minute) > str(attendance_time_total_minute) :
                                early_exit = 1
                            else :
                                early_exit = 0

                            print(""" att = {} emp = {} work_time_minute = {} ({}) att_time_minute = {} ({}) early_exit = {} """.format(i[5], i[1], work_time_total_minute, str(z.exit_time), attendance_time_total_minute, str(i[3]), late_entry ))



            frappe.db.sql("""

                UPDATE `tabAttendance` a
                
                SET a.`daily_check` = 1,
                a.`late_entry` = "{}",
                a.`early_exit` = "{}",
                a.`work_start_time` = "{}",
                a.`work_exit_time` = "{}"

                WHERE a.`name` = "{}"

            """.format(late_entry,early_exit, work_start_time, work_exit_time, str(i[0])))
            frappe.db.commit()

    return "update_berhasil"





@frappe.whitelist()
def calculation_working_days_and_absent(doc, method):
    working_days_from_shift = 0
    total_absent_from_attendance = 0
    total_late_entry_from_attendance = 0
    total_early_exit_from_attendance = 0

    total_present_days = 0

    # get working hours
    berapa_hari = date_diff(doc.end_date, doc.start_date)

    for z in range(berapa_hari+1):
        pertambahan_hari = add_days(doc.start_date, z)

        if str(getdate(str(pertambahan_hari)).strftime("%A")) != "Sunday" :

            get_holiday = frappe.db.sql(""" SELECT * FROM `tabHoliday` h WHERE h.`holiday_date` = "{}" """.format(pertambahan_hari))
            if not get_holiday :
                working_days_from_shift += 1

    doc.working_days_from_shift = working_days_from_shift

    # get absent
    temp_data = frappe.db.sql("""

        SELECT 
        COUNT(att.`name`),
        e.`employee`

        FROM `tabAttendance` att
        LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
        WHERE att.`docstatus` = 1
        AND (att.`status` = "Present" OR att.`status` = "On Leave" AND att.`leave_type` != "Leave Without Pay" )
        AND att.`attendance_date` BETWEEN "{0}" AND "{1}"
        AND e.`employee` = "{2}"


    """.format(doc.start_date, doc.end_date, doc.employee))

    if temp_data :
        for gpd in temp_data :
            total_present_days = gpd[0]

    if total_present_days > 0 :
        total_absent_from_attendance = working_days_from_shift - total_present_days

    doc.total_absent_from_attendance = total_absent_from_attendance

    # get late entry

    get_late_entry = frappe.db.sql("""

        SELECT 

        COUNT(att.`name`),
        SUM( TIME_TO_SEC( IF(SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00")) < "00:00:00", "00:00:00",SUBTIME(att.`start_time`, IFNULL(ADDTIME(att.`work_start_time`, SEC_TO_TIME(st.`grace_period_for_late_entry` * 60)), "00:00:00"))) ) ) / 3600 AS timeSum

        FROM `tabAttendance` att 
        LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
        LEFT JOIN `tabShift Type` st ON e.`default_shift` = st.`name`
        WHERE att.`docstatus` = 1 
        AND att.`late_entry` = 1
        AND e.`employee` = "{}"
        AND att.`attendance_date` BETWEEN "{}" AND "{}"

        GROUP BY e.`employee`

    """.format(doc.employee, doc.start_date, doc.end_date))

    if get_late_entry :
        for gle in get_late_entry :
            total_late_entry_from_attendance = gle[1]

    doc.total_late_entry_from_attendance = total_late_entry_from_attendance

    # get early exit

    get_early_exit = frappe.db.sql("""

        SELECT 
        COUNT(att.`name`),
        SUM( TIME_TO_SEC( IF(SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`) < "00:00:00", "00:00:00", SUBTIME(SUBTIME(att.`work_exit_time`, SEC_TO_TIME(st.`grace_period_for_early_exit` * 60)), att.`exit_time`)) ) ) / 3600  AS timeSum

        FROM `tabAttendance` att 
        LEFT JOIN `tabEmployee` e ON (att.`biometric_id` = e.`biometric_id` OR att.`employee` = e.`name`)
        LEFT JOIN `tabShift Type` st ON e.`default_shift` = st.`name`
        WHERE att.`docstatus` = 1 
        AND att.`early_exit` = 1
        AND e.`employee` = "{}"
        AND att.`attendance_date` BETWEEN "{}" AND "{}"n

        GROUP BY e.`employee`

    """.format(doc.employee, doc.start_date, doc.end_date))

    if get_early_exit :
        for gle in get_early_exit :
            total_early_exit_from_attendance = gle[1]

    doc.total_early_exit_from_attendance = total_early_exit_from_attendance




@frappe.whitelist(allow_guest=True)
def ambil_valuation_rate_sle_sebelumnya(posting_date, posting_time, document_name, item_code, warehouse):

    arr_data = {}
    arr_data.update({ "item_code" : item_code, "posting_date" : posting_date, "posting_time" : posting_time, "warehouse" : "", "valuation_rate" : 0, "actual_qty" : 0 })

    get_data = frappe.db.sql("""
        SELECT 
        sle.`item_code` AS "item_code", 
        sle.`posting_date` AS "posting_date", 
        sle.`posting_time` AS "posting_time", 
        sle.`warehouse` AS "warehouse", 
        sle.`valuation_rate` AS "valuation_rate",
        sle.`qty_after_transaction` AS "actual_qty" 
        FROM `tabStock Ledger Entry` sle
        WHERE TIMESTAMP(sle.`posting_date`, sle.`posting_time`) <= TIMESTAMP("{}", "{}")
        AND sle.`voucher_no` != "{}"
        AND sle.`item_code` = "{}"
        AND sle.`warehouse` = "{}"

        ORDER BY TIMESTAMP(sle.`posting_date`, sle.`posting_time`) DESC
        LIMIT 1

    """.format(posting_date, posting_time, document_name, item_code, warehouse))

    if get_data :
        for i in get_data :
            arr_data.update({ "item_code" : i[0], "posting_date" : i[1], "posting_time" : i[2], "warehouse" : i[3], "valuation_rate" : i[4], "actual_qty" : i[5] })

    return arr_data


@frappe.whitelist(allow_guest=True)
def coba_submit_pinv():
    docu = frappe.get_doc("Purchase Invoice", "ACC-PINV-2020-00007")
    docu.flags.ignore_permissions = True
    docu.submit()


@frappe.whitelist(allow_guest=True)
def repair_gl_entry_pinv():

    arr_docu_no = ["ACC-PINV-2020-00003","ACC-PINV-2020-00004","ACC-PINV-2020-00005", "ACC-PINV-2020-00006"]



    for docu_no in arr_docu_no :

        # docu_no = "DN-2020-00103"
        print(docu_no)

        docu = frappe.get_doc("Purchase Invoice", docu_no)
        delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docu_no))

        create_pinv_gle_repair(docu)

        print(docu_no)


def make_gl_entries_pinv(gl_map, cancel=False, adv_adj=False, merge_entries=True, update_outstanding='Yes', from_repost=False):
    

    if gl_map:
        if not cancel:
            # validate_accounting_period(gl_map)
            gl_map = process_gl_map(gl_map, merge_entries)
            if gl_map and len(gl_map) > 1:
                
                for entry in gl_map:
                    gle = frappe.new_doc("GL Entry")
                    gle.update(entry)
                    gle.flags.ignore_permissions = 1
                    gle.validate()
                    gle.db_insert()
                    gle.flags.ignore_validate = True
                    gle.submit()
                    



            else:
                frappe.throw(_("Incorrect number of General Ledger Entries found. You might have selected a wrong Account in the transaction."))
        else:
            make_reverse_gl_entries(gl_map, adv_adj=adv_adj, update_outstanding=update_outstanding)



@frappe.whitelist()
def create_pinv_gle_repair(doc):

    repost_future_gle=True
    from_repost=False

    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_sales_invoice == "Yes" :

        gl_entries = get_gl_entries_pinv(doc)

        if gl_entries:
            update_outstanding = "No" if (cint(doc.is_paid) or doc.write_off_account) else "Yes"

            make_gl_entries_pinv(gl_entries,  cancel=(doc.docstatus == 2), update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)

            if update_outstanding == "No":
                update_outstanding_amt(doc.credit_to, "Supplier", doc.supplier,
                    doc.doctype, doc.return_against if cint(doc.is_return) and doc.return_against else doc.name)


            if doc.update_stock==1 :
                make_gle_item_pinv(doc)

            # edited rico
            
            # if (repost_future_gle or doc.flags.repost_future_gle) and cint(doc.update_stock) and doc.auto_accounting_for_stock:
            # 	from erpnext.controllers.stock_controller import update_gl_entries_after
            # 	items, warehouses = doc.get_items_and_warehouses()
            # 	update_gl_entries_after(doc.posting_date, doc.posting_time,
            # 		warehouses, items, company = doc.company)

        elif doc.docstatus == 2 and cint(doc.update_stock) and doc.auto_accounting_for_stock:
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)




# @frappe.whitelist(allow_guest=True)
# def repair_gl_entry_pinv():

# 	arr_pinv = ["ACC-PINV-2020-00003", "ACC-PINV-2020-00004", "ACC-PINV-2020-00005", "ACC-PINV-2020-00006"]

# 	for pinv in arr_pinv :
    
# 		docu = frappe.get_doc("Purchase Invoice",pinv)
# 		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(pinv))
# 		docu.make_gl_entries()



@frappe.whitelist()
def auto_check_late_entry_or_early_exit():
    
    get_data = frappe.db.sql("""

        SELECT a.`name`, a.`employee`, TIME(a.`start_time`), TIME(a.`exit_time`), e.`default_shift`, a.`attendance_date`
        FROM `tabAttendance` a
        LEFT JOIN `tabEmployee` e ON a.`employee` = e.`name`
        WHERE a.`docstatus` = 1
        AND a.`daily_check` = 0
        AND (a.`status` = "Present" or a.`status` = "Half Day")
        

    """)

    if get_data :
        late_entry = 0
        early_exit = 0
        work_start_time = "00:00:00"
        work_exit_time = "00:00:00"
        for i in get_data :

            if i[4] :
                get_work_time = frappe.get_doc("Shift Type", i[4]).work_time
                get_shift = frappe.get_doc("Shift Type", i[4])
                if get_work_time :
                    for z in get_work_time :
                        if z.days == str(getdate(str(i[5])).strftime("%A")) and z.days != "Sunday" :

                            work_start_time = str(z.start_time)
                            work_exit_time = str(z.exit_time)

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
                            attendance_time_hour = str(i[2]).split(":")[0]
                            attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
                            attendance_time_minute = int(str(i[2]).split(":")[1]) 
                            attendance_time_total_minute = attendance_time_hour_in_minutes + attendance_time_minute

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
                            work_time_total_minute = work_time_hour_in_minutes + work_time_minute - get_shift.grace_period_for_early_exit

                            # attendance_time
                            # ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
                            attendance_time_total_minute = 0
                            attendance_time_hour = str(i[3]).split(":")[0]
                            attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
                            attendance_time_minute = int(str(i[3]).split(":")[1]) 
                            attendance_time_total_minute = attendance_time_hour_in_minutes + attendance_time_minute


                            if str(work_time_total_minute) > str(attendance_time_total_minute) :
                                early_exit = 1
                            else :
                                early_exit = 0



            frappe.db.sql("""

                UPDATE `tabAttendance` a
                
                SET a.`daily_check` = 1,
                a.`late_entry` = "{}",
                a.`early_exit` = "{}",
                a.`work_start_time` = "{}",
                a.`work_exit_time` = "{}"


                WHERE a.`name` = "{}"

            """.format(late_entry,early_exit, work_start_time, work_exit_time, str(i[0])))
            frappe.db.commit()


@frappe.whitelist()
def auto_apply_employee_id_and_employee_name():
    
    frappe.db.sql("""

        UPDATE `tabAttendance` a
        INNER JOIN `tabEmployee` b ON a.`biometric_id` = b.`biometric_id`

        SET	a.`employee` = b.`name`, 
            a.`employee_name` = b.`employee_name`,
            a.`department` = b.`department`

        WHERE a.`employee` IS NULL OR a.`employee` = ""

    """)

    frappe.db.commit()


@frappe.whitelist()
def auto_check_late_entry_or_early_exit_cs_script():
    
    get_data = frappe.db.sql("""

        SELECT a.`name`, a.`employee`, TIME(a.`start_time`), TIME(a.`exit_time`), e.`default_shift`, a.`attendance_date`
        FROM `tabAttendance` a
        LEFT JOIN `tabEmployee` e ON a.`employee` = e.`name`
        WHERE a.`docstatus` = 1
        AND (a.`status` = "Present" or a.`status` = "Half Day")
        

    """)

    if get_data :
        late_entry = 0
        early_exit = 0
        work_start_time = "00:00:00"
        work_exit_time = "00:00:00"
        for i in get_data :

            if i[4] :
                get_work_time = frappe.get_doc("Shift Type", i[4]).work_time
                get_shift = frappe.get_doc("Shift Type", i[4])
                if get_work_time :
                    for z in get_work_time :
                        if z.days == str(getdate(str(i[5])).strftime("%A")) and z.days != "Sunday" :

                            work_start_time = str(z.start_time)
                            work_exit_time = str(z.exit_time)

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
                            attendance_time_hour = str(i[2]).split(":")[0]
                            attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
                            attendance_time_minute = int(str(i[2]).split(":")[1]) 
                            attendance_time_total_minute = attendance_time_hour_in_minutes + attendance_time_minute

                            if str(work_time_total_minute) < str(attendance_time_total_minute) :
                                late_entry = 1
                            else :
                                late_entry = 0


                            print(""" att = {} emp = {} work_time_minute = {} att_time_minute = {} late_entry = {} """.format(i[0], i[1], work_time_total_minute, attendance_time_total_minute, late_entry ))


                            # convert time to minutes
                            # work_time
                            # ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
                            work_time_total_minute = 0
                            work_time_hour = str(z.exit_time).split(":")[0]
                            work_time_hour_in_minutes = int(work_time_hour) * 60
                            work_time_minute = int(str(z.exit_time).split(":")[1]) 
                            work_time_total_minute = work_time_hour_in_minutes + work_time_minute - get_shift.grace_period_for_early_exit

                            # attendance_time
                            # ex = 08:30:00 > (8*60) + 30 = 480 + 30 = 510
                            attendance_time_total_minute = 0
                            attendance_time_hour = str(i[3]).split(":")[0]
                            attendance_time_hour_in_minutes = int(attendance_time_hour) * 60
                            attendance_time_minute = int(str(i[3]).split(":")[1]) 
                            attendance_time_total_minute = attendance_time_hour_in_minutes + attendance_time_minute


                            if str(work_time_total_minute) > str(attendance_time_total_minute) :
                                early_exit = 1
                            else :
                                early_exit = 0

                            print(""" att = {} emp = {} work_time_minute = {} att_time_minute = {} ealry_exit = {} """.format(i[0], i[1], work_time_total_minute, attendance_time_total_minute, early_exit ))



            frappe.db.sql("""

                UPDATE `tabAttendance` a
                
                SET a.`daily_check` = 1,
                a.`late_entry` = "{}",
                a.`early_exit` = "{}",
                a.`work_start_time` = "{}",
                a.`work_exit_time` = "{}"

                WHERE a.`name` = "{}"

            """.format(late_entry,early_exit, work_start_time, work_exit_time, str(i[0])))
            frappe.db.commit()


    get_count_duplicate = frappe.db.sql("""
        SELECT abc.employee, abc.biometric_id, abc.attendance_date, abc.counter 
        FROM (
            SELECT a.`employee` AS employee, a.`biometric_id` AS biometric_id, COUNT(a.`attendance_date`) AS counter, a.`attendance_date` AS attendance_date 
            FROM `tabAttendance` a
            WHERE a.`docstatus` = 1

            GROUP BY a.`attendance_date`, a.`biometric_id`
            ORDER BY a.`biometric_id` ASC, a.`attendance_date` ASC
        ) AS abc

        WHERE abc.counter = "2"

        """)

    if get_count_duplicate :
        for i in get_count_duplicate :
            # delete yang biometric saja
            att_id = str(i[1])+"#"+str(i[2])

            get_kembar = frappe.db.sql("""
                SELECT
                a.`name`,
                a.`creation`,
                a.`modified`,
                a.`modified_by`,
                a.`owner`,
                a.`docstatus`,
                a.`naming_series`,
                a.`company`,
                a.`attendance_date`,
                a.`amended_from`, 
                a.`_comments`,
                a.`leave_type`,
                a.`attendance_request`,
                a.`employee`,
                a.`employee_name`,
                a.`late_entry`, 
                a.`early_exit`,
                a.`shift`,
                a.`leave_application`,
                a.`working_hours`,
                a.`daily_check`,
                a.`biometric_id`,
                IFNULL(a.`start_time`,"00:00:00"),
                IFNULL(a.`exit_time`,"00:00:00"),
                IFNULL(a.`old_start_time_update`,"00:00:00"),
                IFNULL(a.`old_exit_time_update`,"00:00:00"),
                a.`request_attendance`,
                IFNULL(a.`work_start_time`,"00:00:00"),
                IFNULL(a.`work_exit_time`,"00:00:00")

                FROM `tabAttendance` a
                WHERE a.`name` = "{}"

            """.format(str(att_id)))

            if get_kembar :
                for gk in get_kembar :
                    # insert ke deleted document
                    frappe.db.sql("""

                        INSERT INTO `tabDeleted Attendance` (name,creation,modified,modified_by,owner,docstatus,series,company,attendance_date,amended_from,_comments,leave_type,attendance_request,employee,employee_name,late_entry,early_exit,shift,leave_application,working_hours,biometric_id,start_time,exit_time,old_start_time_update,old_exit_time_update,request_attendance,work_start_time,work_exit_time, attendance_name)
                        VALUES ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")


                    """.format(str(random_string(5)),gk[1],gk[2],gk[3],gk[4],gk[5],gk[6],gk[7],gk[8],gk[9],gk[10],gk[11],gk[12],gk[13],gk[14],gk[15],gk[16],gk[17],gk[18],gk[19],gk[21],gk[22],gk[23],gk[24],gk[25],gk[26],gk[27],gk[28], gk[0]))

                    frappe.db.commit()

                    frappe.db.sql(""" DELETE FROM `tabAttendance` WHERE name = "{}" """.format(str(att_id)))
                    frappe.db.commit()




    return "Update is Done"


@frappe.whitelist()
def auto_apply_employee_id_and_employee_name_cs_script():
    
    frappe.db.sql("""

        UPDATE `tabAttendance` a
        INNER JOIN `tabEmployee` b ON a.`biometric_id` = b.`biometric_id`

        SET	a.`employee` = b.`name`, 
            a.`employee_name` = b.`employee_name`,
            a.`department` = b.`department`

        WHERE a.`employee` IS NULL OR a.`employee` = ""

    """)

    frappe.db.commit()

    return "Update ID and Name is Done"



@frappe.whitelist()
def validation_same_days(doc, method):
    cek_item = []

    if doc.work_time :
        for i in doc.work_time :
            if i.days in cek_item :
                frappe.throw("Duplicate days found "+str(i.days))
            else :
                cek_item.append(i.days)


@frappe.whitelist()
def validation_same_item_price(doc, method):
    get_similar = frappe.db.sql("""
        SELECT * FROM `tabItem Price` ip 
        WHERE ip.`name` != "{}"
        AND ip.`price_list` = "{}"
        AND ip.`item_code` = "{}"
        
    """.format(doc.name, doc.price_list, doc.item_code ))

    if get_similar :
        frappe.throw("Item Price already exist for this Item "+str(doc.item_code))


@frappe.whitelist()
def cek_similar_loan_disbursement(doc, method):
    cek_item = []

    for i in doc.accounts :
        if i.reference_type == "Loan" and i.reference_name and i.debit_in_account_currency > 0 and i.credit_in_account_currency == 0 :

            get_similar = frappe.db.sql("""
                SELECT jea.`parent` FROM `tabJournal Entry Account` jea 
                WHERE jea.`parent` != "{}"
                AND jea.`reference_type` = "Loan"
                AND jea.`reference_name` = "{}"
                AND jea.`debit_in_account_currency` > 0
                AND jea.`credit_in_account_currency` = 0

            """.format(doc.name, i.reference_name ))

            if get_similar :
                frappe.throw("This document cannot be created because already have similar document, please check "+str(get_similar[0][0]))



@frappe.whitelist()
def cek_similar_request_expenses(doc, method):
    cek_item = []

    if doc.request_expenses :
        if doc.request_expenses_status == "Final Money" :
            get_similar = frappe.db.sql("""
                SELECT je.`name` FROM `tabJournal Entry` je 
                WHERE je.`name` != "{}"
                AND je.`request_expenses` = "{}"
                AND je.`request_expenses_status` = "Final Money"
                AND je.`docstatus` < 2

            """.format(doc.name, doc.request_expenses ))


            if get_similar :
                frappe.throw("This document cannot be created because already have similar document, please check "+str(get_similar[0][0]))



@frappe.whitelist()
def cek_similar_loan(doc, method):
    cek_item = []

    get_similar = frappe.db.sql("""
        SELECT l.`name` FROM `tabLoan` l
        WHERE l.`loan_application` = "{}"
        AND l.`name` != "{}"

        """.format(doc.loan_application, doc.name))

    if get_similar :
        frappe.throw("This document cannot be created because already have similar document, please check "+str(get_similar[0][0]))



@frappe.whitelist()
def cek_customer_sub_customer(customer):

    arr_data = {}

    arr_data.update({ "cek_sub" : 0 })
    

    cust = frappe.get_doc("Customer", customer)

    get_setting = frappe.get_single("General Setting")
    if get_setting.customer_child :
        for gs in get_setting.customer_child :
            if customer == gs.customer :
                arr_data.update({ "cek_sub" : 1 })

    return arr_data




@frappe.whitelist()
def get_customer_balance_detail(customer):

    arr_data = {}

    arr_data.update({ "customer_credit_limit" : 0 })
    arr_data.update({ "customer_rebate" : "" })
    arr_data.update({ "customer_balance" : 0 })
    arr_data.update({ "sub_customer_balance" : 0 })
    arr_data.update({ "customer_bypass_status" : "" })


    cust = frappe.get_doc("Customer", customer)

    if cust.credit_limits :
        for i in cust.credit_limits :
            arr_data.update({ "customer_credit_limit" : i.credit_limit })

            if i.bypass_credit_limit_check :
                arr_data.update({ "customer_bypass_status" : "Yes" })
            else :
                arr_data.update({ "customer_bypass_status" : "No" })

    arr_data.update({ "customer_rebate" : cust.rebate })

    get_balance = frappe.db.sql("""
        SELECT gle.`party`, SUM(gle.`debit_in_account_currency`) AS debit, SUM(gle.`credit_in_account_currency`) AS credit, (SUM(gle.`debit_in_account_currency`) - SUM(gle.`credit_in_account_currency`)) AS balance
        FROM `tabGL Entry` gle
        WHERE gle.`party_type` = "Customer"
        AND gle.`party` = "{}"
        GROUP BY gle.`party`

    """.format(customer))

    if get_balance :
        for i in get_balance :
            arr_data.update({ "customer_balance" : i[3] })

    return arr_data


@frappe.whitelist()
def get_sub_customer_balance_detail(customer, sub_customer):

    sub_customer_balance = 0


    
    get_balance = frappe.db.sql("""
        SELECT 
        gle.`party`, 
        SUM(gle.`debit_in_account_currency`) AS debit, 
        SUM(gle.`credit_in_account_currency`) AS credit, 
        (SUM(gle.`debit_in_account_currency`) - SUM(gle.`credit_in_account_currency`)) AS balance,
        gle.`sub_customer`
        FROM `tabGL Entry` gle
        WHERE gle.`party_type` = "Customer"
        AND gle.`party` = "{}"
        AND gle.`sub_customer` = "{}"
        GROUP BY gle.`sub_customer`

    """.format(customer, sub_customer))

    if get_balance :
        for i in get_balance :
            sub_customer_balance = float(i[3])

    return sub_customer_balance



@frappe.whitelist()
def create_dn_gle_repair(doc):
    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_delivery_note == "Yes" :

        
        

        gl_entries = []
        repost_future_gle=True
        from_repost=False

        if doc.docstatus == 2:
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)

    
        if doc.docstatus==1:
            if not gl_entries:
                gl_entries = get_gl_entries_dn(doc)
            
            make_gl_entries_dn(gl_entries, merge_entries=True)

        # if (repost_future_gle or doc.flags.repost_future_gle):
        # 	items, warehouses = doc.get_items_and_warehouses()
        # 	update_gl_entries_after(doc.posting_date, doc.posting_time, warehouses, items,
        # 		warehouse_account, company=doc.company)



# ============





@frappe.whitelist()
def create_sinv_gle_repair(doc):

    auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(doc.company)


    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_sales_invoice == "Yes" :
        repost_future_gle=True
        from_repost=False
        gl_entries = get_gl_entries_sinv(doc)
        if gl_entries:
            # if POS and amount is written off, updating outstanding amt after posting all gl entries
            update_outstanding = "No" if (cint(doc.is_pos) or doc.write_off_account) else "Yes"
            # frappe.msgprint(str(gl_entries))
            make_gl_entries_sinv(gl_entries, cancel=(doc.docstatus == 2), update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)
            if update_outstanding == "No":
                from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
                update_outstanding_amt(doc.debit_to, "Customer", doc.customer, doc.doctype, doc.return_against if cint(doc.is_return) and doc.return_against else doc.name)
            # if (repost_future_gle or doc.flags.repost_future_gle) and cint(doc.update_stock) and cint(auto_accounting_for_stock):
            # 		items, warehouses = doc.get_items_and_warehouses()
            # 		update_gl_entries_after(doc.posting_date, doc.posting_time, warehouses, items, company = doc.company)
        elif doc.docstatus == 2 and cint(doc.update_stock) and cint(auto_accounting_for_stock):
            
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)



            

            # gl_map = gl_list
            # if gl_map:
            # 	if gl_map and len(gl_map) > 1:
            # 		for entry in gl_map:
            # 			make_entry(entry)



@frappe.whitelist(allow_guest=True)
def repair_gl_entry():

    arr_docu_no = ["SI-00001","SI-2020-00010","SI-2020-00011","SI-2020-00012","SI-2020-00020","SI-2020-00021","SI-2020-00022","SI-2020-00025","SI-2020-00026","SI-2020-00030","SI-2020-00031","SI-2020-00032","SI-2020-00034","SI-2020-00037","SI-2020-00040","SI-2020-00041","SI-2020-00046","SI-2020-00047","SI-2020-00048","SI-2020-00049","SI-2020-00055","SI-2020-00056","SI-2020-00057","SI-2020-00062","SI-2020-00063","SI-2020-00064","SI-2020-00065","SI-2020-00066","SI-2020-00067","SI-2020-00068","SI-2020-00069","SI-2020-00070","SI-2020-00071","SI-2020-00079","SI-2020-00083","SI-2020-00086","SI-2020-00087","SI-2020-00089","SI-2020-00090","SI-2020-00092","SI-2020-00096","SI-2020-00103","SI-2020-00104","SI-2020-00105","SI-2020-00107","SI-2020-00108","SI-2020-00109","SI-2020-00113","SI-2020-00118","SI-2020-00120","SI-2020-00121","SI-2020-00122","SI-2020-00125","SI-2020-00133","SI-2020-00135","SI-2020-00138","SI-2020-00149","SI-2020-00150","SI-2020-00151","SI-2020-00152","SI-2020-00154","SI-2020-00157","SI-2020-00162","SI-2020-00165","SI-2020-00166","SI-2020-00167","SI-2020-00170","SI-2020-00171","SI-2020-00172","SI-2020-00173","SI-2020-00177","SI-2020-00178","SI-2020-00179","SI-2020-00183","SI-2020-00184","SI-2020-00185","SI-2020-00186","SI-2020-00187","SI-2020-00188","SI-2020-00189","SI-2020-00190","SI-2020-00191","SI-2020-00192","SI-FCT-GS-00003","SI-FCT-GS-00004","SI-FCT-GS-00005","SI-NAS-MD-00001","WAIT3-00003"]
    



    for docu_no in arr_docu_no :

        # docu_no = "DN-2020-00103"

        docu = frappe.get_doc("Sales Invoice",docu_no)
        delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docu_no))

        create_sinv_gle_repair(docu)

        print(docu_no)


    
    




@frappe.whitelist()
def cek_similar_sinv(doc, method):

    for i in doc.items :

        if i.delivery_note and i.dn_detail :

            get_sinv = frappe.db.sql("""

                SELECT dni.`parent`, dni.`qty` FROM `tabSales Invoice Item` dni
                WHERE dni.`docstatus` <= 1
                AND dni.`item_code` = "{}"
                AND dni.`delivery_note` = "{}"
                AND dni.`warehouse` = "{}"
                AND dni.`dn_detail` = "{}"
                AND dni.`parent` != "{}"


            """.format(i.item_code, i.delivery_note, i.warehouse, i.dn_detail, doc.name))

            get_qty_sinv_child = frappe.db.sql("""

                SELECT soi.`item_code`, soi.`qty` FROM `tabDelivery Note Item` soi
                WHERE soi.`name` = "{}"

            """.format(i.dn_detail))

            dn_qty = 0
            other_sinv_qty = 0
            total_sinv_qty = 0

            if get_qty_sinv_child :
                for soq in get_qty_sinv_child :
                    dn_qty = float(soq[1])

            if get_sinv :
                for gd in get_sinv :
                    other_sinv_qty = float(gd[1])
                    total_sinv_qty = i.qty + other_sinv_qty

                    if total_sinv_qty > dn_qty :

                        frappe.throw("This document is over limit by <b>Qty</b> <b>"+str(i.qty)+"</b> for item <b>"+str(i.item_code)+"</b> Are you making another <b>Sales Invoice</b> against the same <b>Delivery Note "+str(i.delivery_note)+" ?")


        else :
            get_dn = frappe.db.sql("""

                SELECT dni.`parent`, dni.`qty` FROM `tabSales Invoice Item` dni
                WHERE dni.`docstatus` <= 1
                AND dni.`item_code` = "{}"
                AND dni.`sales_order` = "{}"
                AND dni.`warehouse` = "{}"
                AND dni.`so_detail` = "{}"
                AND dni.`parent` != "{}"


            """.format(i.item_code, i.sales_order, i.warehouse, i.so_detail, doc.name))

            get_qty_so_child = frappe.db.sql("""

                SELECT soi.`item_code`, soi.`qty` FROM `tabSales Order Item` soi
                WHERE soi.`name` = "{}"

            """.format(i.so_detail))

            so_qty = 0
            other_dn_qty = 0
            total_dn_qty = 0

            if get_qty_so_child :
                for soq in get_qty_so_child :
                    so_qty = float(soq[1])

            if get_dn :
                for gd in get_dn :
                    other_dn_qty = float(gd[1])
                    total_dn_qty = i.qty + other_dn_qty

                    if total_dn_qty > so_qty :

                        frappe.throw("This document is over limit by <b>Qty</b> <b>"+str(i.qty)+"</b> for item <b>"+str(i.item_code)+"</b> Are you making another <b>Sales Invoice</b> against the same <b>Sales Order "+str(i.sales_order)+" ?")





@frappe.whitelist()
def cek_similar_dn(doc, method):
    cek_item = []

    for i in doc.items :
        against_so = i.against_sales_order
        item_code = i.item_code
        warehouse = i.warehouse
        so_child_name = i.so_detail

        get_dn = frappe.db.sql("""

            SELECT dni.`parent`, dni.`qty` FROM `tabDelivery Note Item` dni
            WHERE dni.`docstatus` <= 1
            AND dni.`item_code` = "{}"
            AND dni.`against_sales_order` = "{}"
            AND dni.`warehouse` = "{}"
            AND dni.`so_detail` = "{}"
            AND dni.`parent` != "{}"


        """.format(item_code, against_so, warehouse, so_child_name, doc.name))

        get_qty_so_child = frappe.db.sql("""

            SELECT soi.`item_code`, soi.`qty` FROM `tabSales Order Item` soi
            WHERE soi.`name` = "{}"

        """.format(so_child_name))

        so_qty = 0
        other_dn_qty = 0
        total_dn_qty = 0

        if get_qty_so_child :
            for soq in get_qty_so_child :
                so_qty = float(soq[1])

        if get_dn :
            for gd in get_dn :
                other_dn_qty = float(gd[1])
                total_dn_qty = i.qty + other_dn_qty

                if total_dn_qty > so_qty :

                    frappe.throw("This document is over limit by <b>Qty</b> <b>"+str(i.qty)+"</b> for item <b>"+str(i.item_code)+"</b> Are you making another <b>Delivery Note</b> against the same <b>Sales Order "+str(against_so)+" ?")





# =======================
def make_supplier_gl_entry(doc, gl_entries):
    # Checked both rounding_adjustment and rounded_total
    # because rounded_total had value even before introcution of posting GLE based on rounded total
    grand_total = doc.rounded_total if (doc.rounding_adjustment and doc.rounded_total) else doc.grand_total

    if grand_total:
        # Didnot use base_grand_total to book rounding loss gle
        grand_total_in_company_currency = flt(grand_total * doc.conversion_rate,
            doc.precision("grand_total"))
        gl_entries.append(
            doc.get_gl_dict({
                "account": doc.credit_to,
                "party_type": "Supplier",
                "party": doc.supplier,
                "company":doc.company,
                "due_date": doc.due_date,
                "against": doc.against_expense_account,
                "credit": grand_total_in_company_currency,
                "credit_in_account_currency": grand_total_in_company_currency \
                    if doc.party_account_currency==doc.company_currency else grand_total,
                "against_voucher": doc.return_against if cint(doc.is_return) and doc.return_against else doc.name,
                "against_voucher_type": doc.doctype,
                "cost_center": doc.cost_center
            }, doc.party_account_currency, item=doc)
        )

def make_stock_adjustment_entry(doc, gl_entries, item, voucher_wise_stock_value, account_currency):
    net_amt_precision = item.precision("base_net_amount")
    val_rate_db_precision = 6 if cint(item.precision("valuation_rate")) <= 6 else 9

    warehouse_debit_amount = flt(flt(item.valuation_rate, val_rate_db_precision) * flt(item.qty) * flt(item.conversion_factor), net_amt_precision)

    # Stock ledger value is not matching with the warehouse amount
    if (doc.update_stock and voucher_wise_stock_value.get(item.name) and warehouse_debit_amount != flt(voucher_wise_stock_value.get(item.name), net_amt_precision)):

        cost_of_goods_sold_account = doc.get_company_default("default_expense_account")
        stock_amount = flt(voucher_wise_stock_value.get(item.name), net_amt_precision)
        stock_adjustment_amt = warehouse_debit_amount - stock_amount

        gl_entries.append(
            doc.get_gl_dict({
                "account": cost_of_goods_sold_account,
                "company":doc.company,
                "against": item.expense_account,
                "debit": stock_adjustment_amt,
                "remarks": doc.get("remarks") or _("Stock Adjustment"),
                "cost_center": item.cost_center,
                "project": item.project
            }, account_currency, item=item)
        )

        warehouse_debit_amount = stock_amount

    return warehouse_debit_amount


# @frappe.whitelist()
# def create_prec_gle_manual(doc, method):
# 	get_setting = frappe.get_single("General Setting")
# 	if get_setting.replace_gle_purchase_receipt == "Yes" :

# 		from erpnext.accounts.general_ledger import make_gl_entries, _delete_gl_entries


# 		if doc.docstatus == 2:
# 			delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)

# 		if cint(erpnext.is_perpetual_inventory_enabled(doc.company)):
# 			warehouse_account = get_warehouse_account_map(doc.company)

# 			if doc.docstatus==1:
# 				if not gl_entries:
# 					gl_entries = get_gl_entries_prec(doc)
# 				make_gl_entries(gl_entries, from_repost=from_repost)

# 			if (repost_future_gle or doc.flags.repost_future_gle):
# 				items, warehouses = doc.get_items_and_warehouses()
# 				update_gl_entries_after(doc.posting_date, doc.posting_time, warehouses, items, warehouse_account, company=doc.company)

# 		elif doc.doctype in ['Purchase Receipt', 'Purchase Invoice'] and doc.docstatus == 1:
# 			gl_entries = []
# 			gl_entries = doc.get_asset_gl_entry(gl_entries)
# 			make_gl_entries(gl_entries, from_repost=from_repost)

@frappe.whitelist()
def get_stock_ledger_details(doc):
    stock_ledger = {}
    stock_ledger_entries = frappe.db.sql("""
        select
            name, warehouse, stock_value_difference, valuation_rate,
            voucher_detail_no, item_code, posting_date, posting_time,
            actual_qty, qty_after_transaction
        from
            `tabStock Ledger Entry`
        where
            voucher_type=%s and voucher_no=%s
    """, (doc.doctype, doc.name), as_dict=True)

    for sle in stock_ledger_entries:
            stock_ledger.setdefault(sle.voucher_detail_no, []).append(sle)
    return stock_ledger


def make_customer_gl_entry(doc, gl_entries):
    # Checked both rounding_adjustment and rounded_total
    # because rounded_total had value even before introcution of posting GLE based on rounded total
    grand_total = doc.rounded_total if (doc.rounding_adjustment and doc.rounded_total) else doc.grand_total
    if grand_total:
        # Didnot use base_grand_total to book rounding loss gle
        grand_total_in_company_currency = flt(grand_total * doc.conversion_rate,
            doc.precision("grand_total"))

        gl_entries.append(
            doc.get_gl_dict({
                "account": doc.debit_to,
                "party_type": "Customer",
                "company":doc.company,
                "party": doc.customer,
                "due_date": doc.due_date,
                "against": doc.against_income_account,
                "debit": grand_total_in_company_currency,
                "debit_in_account_currency": grand_total_in_company_currency \
                    if doc.party_account_currency==doc.company_currency else grand_total,
                "against_voucher": doc.return_against if cint(doc.is_return) and doc.return_against else doc.name,
                "against_voucher_type": doc.doctype,
                "cost_center": doc.cost_center
            }, doc.party_account_currency, item=doc)
        )


def make_tax_gl_entries(doc, gl_entries):
    for tax in doc.get("taxes"):
        if flt(tax.base_tax_amount_after_discount_amount):
            account_currency = get_account_currency(tax.account_head)
            gl_entries.append(
                doc.get_gl_dict({
                    "account": tax.account_head,
                    "company":doc.company,
                    "against": doc.customer,
                    "credit": flt(tax.base_tax_amount_after_discount_amount,
                        tax.precision("tax_amount_after_discount_amount")),
                    "credit_in_account_currency": (flt(tax.base_tax_amount_after_discount_amount,
                        tax.precision("base_tax_amount_after_discount_amount")) if account_currency==doc.company_currency else
                        flt(tax.tax_amount_after_discount_amount, tax.precision("tax_amount_after_discount_amount"))),
                    "cost_center": tax.cost_center
                }, account_currency, item=tax)
            )


def make_item_gl_entries(doc, gl_entries):

    get_setting = frappe.get_single("General Setting")

    # income account gl entries
    for item in doc.get("items"):
        if flt(item.base_net_amount, item.precision("base_net_amount")):
            if item.is_fixed_asset:
                asset = frappe.get_doc("Asset", item.asset)

                if (len(asset.finance_books) > 1 and not item.finance_book
                    and asset.finance_books[0].finance_book):
                    frappe.throw(_("Select finance book for the item {0} at row {1}")
                        .format(item.item_code, item.idx))

                fixed_asset_gl_entries = get_gl_entries_on_asset_disposal(asset,
                    item.base_net_amount, item.finance_book)

                for gle in fixed_asset_gl_entries:
                    gle["against"] = doc.customer
                    gl_entries.append(doc.get_gl_dict(gle, item=item))

                asset.db_set("disposal_date", doc.posting_date)
                asset.set_status("Sold" if doc.docstatus==1 else None)
            else:
                income_account = (item.income_account
                    if (not item.enable_deferred_revenue or doc.is_return) else item.deferred_revenue_account)

                account_currency = get_account_currency(income_account)
                gl_entries.append(
                    doc.get_gl_dict({
                        "account": income_account,
                        "against": doc.customer,
                        "credit": flt(item.base_net_amount, item.precision("base_net_amount")),
                        "credit_in_account_currency": (flt(item.base_net_amount, item.precision("base_net_amount"))
                            if account_currency==doc.company_currency
                            else flt(item.net_amount, item.precision("net_amount"))),
                        "cost_center": item.cost_center
                    }, account_currency, item=item)
                )

    # # expense account gl entries
    # if cint(doc.update_stock) and \
    # 	erpnext.is_perpetual_inventory_enabled(doc.company):
    # 	gl_entries += super(SalesInvoice, doc).get_gl_entries()

def get_round_off_account_and_cost_center(company):
    round_off_account, round_off_cost_center = frappe.get_cached_value('Company',  company,
        ["round_off_account", "round_off_cost_center"]) or [None, None]
    if not round_off_account:
        frappe.throw(_("Please mention Round Off Account in Company"))

    if not round_off_cost_center:
        frappe.throw(_("Please mention Round Off Cost Center in Company"))

    return round_off_account, round_off_cost_center

def make_gle_for_rounding_adjustment(doc, gl_entries):
    if flt(doc.rounding_adjustment, doc.precision("rounding_adjustment")) and doc.base_rounding_adjustment:
        round_off_account, round_off_cost_center = get_round_off_account_and_cost_center(doc.company)

        gl_entries.append(
            doc.get_gl_dict({
                "account": round_off_account,
                "against": doc.customer,
                "credit_in_account_currency": flt(doc.rounding_adjustment,
                    doc.precision("rounding_adjustment")),
                "credit": flt(doc.base_rounding_adjustment,
                    doc.precision("base_rounding_adjustment")),
                "cost_center": doc.cost_center or round_off_cost_center,
            }, item=doc))


@frappe.whitelist()
def get_gl_entries_sinv(doc):

    from erpnext.accounts.general_ledger import merge_similar_entries

    
    get_setting = frappe.get_single("General Setting")
    sle_map = get_stock_ledger_details(doc)

    precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
    
    gl_entries = []

    make_customer_gl_entry(doc, gl_entries)

    make_tax_gl_entries(doc, gl_entries)

    make_item_gl_entries(doc, gl_entries)

    for i in doc.items :
        sle_list = sle_map.get(i.name)
        if sle_list:
            for sle in sle_list:

                print(str(sle))
                
                if not sle.stock_value_difference and doc.doctype != "Stock Reconciliation" and not i.get("allow_zero_valuation_rate"):
                    sle = update_stock_ledger_entries(doc, sle)

                gi = frappe.get_doc("Item", i.item_code)
                gig = frappe.get_doc("Item Group", gi.item_group)

                account_credit = gig.sinv_cogs_account
                account_debit = gig.sinv_stock_credit_account



                if doc.is_return == 1 :
                    gl_entries.append({
                        "account": account_credit ,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Sales Invoice",
                        "debit": flt(sle.stock_value_difference *-1, precision),
                        "debit_in_account_currency":flt(sle.stock_value_difference *-1, precision),
                        "credit":0,
                        "company":doc.company,
                        "credit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Sales Invoice",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_entries.append({
                        "account": account_debit ,
                        "company":doc.company,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Sales Invoice",
                        "credit": flt(sle.stock_value_difference *-1, precision),
                        "credit_in_account_currency": flt(sle.stock_value_difference *-1, precision),
                        "debit":0,
                        "debit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Sales Invoice",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                else :

                    gl_entries.append({
                        "account": account_debit,
                        "company":doc.company,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Sales Invoice",
                        "debit": flt(sle.stock_value_difference, precision),
                        "debit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "credit":0,
                        "credit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Sales Invoice",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_entries.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Sales Invoice",
                        "credit": flt(sle.stock_value_difference, precision),
                        "credit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "debit":0,
                        "debit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Sales Invoice",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

    # frappe.throw(str(gl_list))


    # merge gl entries before adding pos entries
    # gl_entries = merge_similar_entries(gl_entries)


    # self.make_pos_gl_entries(gl_entries)
    # self.make_gle_for_change_amount(gl_entries)

    # self.make_write_off_gl_entry(gl_entries)
    make_gle_for_rounding_adjustment(doc, gl_entries)

    return gl_entries


@frappe.whitelist()
def get_gl_entries_prec(doc):

    get_setting = frappe.get_single("General Setting")
    sle_map = get_stock_ledger_details(doc)

    precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
    gl_list = []

    for i in doc.items :
        sle_list = sle_map.get(i.name)
        if sle_list:
            for sle in sle_list:
                if not sle.stock_value_difference and doc.doctype != "Stock Reconciliation" and not i.get("allow_zero_valuation_rate"):
                    sle = update_stock_ledger_entries(doc, sle)

                gi = frappe.get_doc("Item", i.item_code)
                gig = frappe.get_doc("Item Group", gi.item_group)

                account_debit = gig.pr_stock_account
                account_credit = frappe.get_doc("Company", doc.company).stock_received_but_not_billed


                if doc.is_return == 1 :
                    gl_list.append({
                        "account": account_credit ,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "debit": flt(sle.stock_value_difference *-1, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "company":doc.company,
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_debit ,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "credit": flt(sle.stock_value_difference *-1, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "company":doc.company,
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                else :

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "debit": flt(sle.stock_value_difference, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "voucher_no": doc.name,
                        "company":doc.company,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "credit": flt(sle.stock_value_difference, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "voucher_no": doc.name,
                        "company":doc.company,
                        "posting_date": doc.posting_date
                    })

    return gl_list




@frappe.whitelist()
def get_gl_entries_dn(doc):

    get_setting = frappe.get_single("General Setting")
    sle_map = get_stock_ledger_details(doc)

    precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
    gl_list = []

    for i in doc.items :
        sle_list = sle_map.get(i.name)
        if sle_list:
            for sle in sle_list:
                if not sle.stock_value_difference and doc.doctype != "Stock Reconciliation" and not i.get("allow_zero_valuation_rate"):
                    sle = update_stock_ledger_entries(doc, sle)

                gi = frappe.get_doc("Item", i.item_code)
                gig = frappe.get_doc("Item Group", gi.item_group)

                account_credit = gig.dn_cogs_account
                account_debit = gig.dn_stock_credit_account

                precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
                
                if doc.is_return == 1 :
                    gl_list.append({
                        "account": account_credit ,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Delivery Note",
                        "debit": flt(sle.stock_value_difference *-1, precision),
                        "debit_in_account_currency": flt(sle.stock_value_difference *-1, precision),
                        "credit":0,
                        "company":doc.company,
                        "credit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Delivery Note",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_debit ,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "company":doc.company,
                        "remarks": "Accounting Entry for Delivery Note",
                        "credit": flt(sle.stock_value_difference *-1, precision),
                        "credit_in_account_currency": flt(sle.stock_value_difference *-1, precision),
                        "debit":0,
                        "debit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Delivery Note",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                else :

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Delivery Note",
                        "debit": flt(sle.stock_value_difference, precision),
                        "debit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "credit":0,
                        "credit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Delivery Note",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Delivery Note",
                        "credit": flt(sle.stock_value_difference, precision),
                        "credit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "debit":0,
                        "debit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Delivery Note",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

    return gl_list



def update_stock_ledger_entries(doc, sle):
    sle.valuation_rate = get_valuation_rate(sle.item_code, sle.warehouse,
        doc.doctype, doc.name, currency=doc.company_currency, company=doc.company)

    sle.stock_value = flt(sle.qty_after_transaction) * flt(sle.valuation_rate)
    sle.stock_value_difference = flt(sle.actual_qty) * flt(sle.valuation_rate)

    if sle.name:
        frappe.db.sql("""
            update
                `tabStock Ledger Entry`
            set
                stock_value = %(stock_value)s,
                valuation_rate = %(valuation_rate)s,
                stock_value_difference = %(stock_value_difference)s
            where
                name = %(name)s""", (sle))

    return sle



def get_future_stock_vouchers(posting_date, posting_time, for_warehouses=None, for_items=None):
    future_stock_vouchers = []

    values = []
    condition = ""
    if for_items:
        condition += " and item_code in ({})".format(", ".join(["%s"] * len(for_items)))
        values += for_items

    if for_warehouses:
        condition += " and warehouse in ({})".format(", ".join(["%s"] * len(for_warehouses)))
        values += for_warehouses

    for d in frappe.db.sql("""select distinct sle.voucher_type, sle.voucher_no
        from `tabStock Ledger Entry` sle
        where timestamp(sle.posting_date, sle.posting_time) >= timestamp(%s, %s) {condition}
        order by timestamp(sle.posting_date, sle.posting_time) asc, creation asc for update""".format(condition=condition),
        tuple([posting_date, posting_time] + values), as_dict=True):
            future_stock_vouchers.append([d.voucher_type, d.voucher_no])

    return future_stock_vouchers


def get_voucherwise_gl_entries(future_stock_vouchers, posting_date):
    gl_entries = {}
    if future_stock_vouchers:
        for d in frappe.db.sql("""select * from `tabGL Entry`
            where posting_date >= %s and voucher_no in (%s)""" %
            ('%s', ', '.join(['%s']*len(future_stock_vouchers))),
            tuple([posting_date] + [d[1] for d in future_stock_vouchers]), as_dict=1):
                gl_entries.setdefault((d.voucher_type, d.voucher_no), []).append(d)

    return gl_entries


def compare_existing_and_expected_gle(existing_gle, expected_gle):
    matched = True
    for entry in expected_gle:
        account_existed = False
        for e in existing_gle:
            if entry.account == e.account:
                account_existed = True
            if entry.account == e.account and entry.against_account == e.against_account \
                    and (not entry.cost_center or not e.cost_center or entry.cost_center == e.cost_center) \
                    and (entry.debit != e.debit or entry.credit != e.credit):
                matched = False
                break
        if not account_existed:
            matched = False
            break
    return matched


def update_gl_entries_after(posting_date, posting_time, for_warehouses=None, for_items=None, warehouse_account=None, company=None):
    def _delete_gl_entries(voucher_type, voucher_no):
        frappe.db.sql("""delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s""", (voucher_type, voucher_no))

    # if not warehouse_account:
    # 	warehouse_account = get_warehouse_account_map(company)

    future_stock_vouchers = get_future_stock_vouchers(posting_date, posting_time, for_warehouses, for_items)
    gle = get_voucherwise_gl_entries(future_stock_vouchers, posting_date)

    for voucher_type, voucher_no in future_stock_vouchers:
        existing_gle = gle.get((voucher_type, voucher_no), [])
        voucher_obj = frappe.get_doc(voucher_type, voucher_no)
        expected_gle = voucher_obj.get_gl_entries(warehouse_account)
        if expected_gle:
            if not existing_gle or not compare_existing_and_expected_gle(existing_gle, expected_gle):
                _delete_gl_entries(voucher_type, voucher_no)
                voucher_obj.make_gl_entries(gl_entries=expected_gle, repost_future_gle=False, from_repost=True)
        else:
            _delete_gl_entries(voucher_type, voucher_no)




def make_gl_entries_sinv(gl_map, cancel=False, adv_adj=False, merge_entries=True, update_outstanding='Yes', from_repost=False):
    

    skip = 0
    if gl_map:
        if not cancel:
            # validate_accounting_period(gl_map)
            gl_map = process_gl_map(gl_map, merge_entries)
            # frappe.throw(str(gl_map))
            if gl_map and len(gl_map) > 1:
                
                for entry in gl_map:
                    # frappe.msgprint(str(entry["debit"]) + " " + str(entry["credit"]))
                    if not entry["debit"] :
                        if not entry["credit"] :
                            skip = 0
                        else :
                            gle = frappe.new_doc("GL Entry")
                            gle.update(entry)
                            gle.flags.ignore_permissions = 1
                            gle.fiscal_year = None
                            gle.validate()
                            gle.db_insert()
                            gle.flags.ignore_validate = True
                            gle.submit()
                            
                            

                    else :
                        gle = frappe.new_doc("GL Entry")
                        gle.update(entry)
                        gle.flags.ignore_permissions = 1
                        gle.fiscal_year = None
                        gle.validate()
                        gle.db_insert()
                        gle.flags.ignore_validate = True
                        gle.submit()
                        



            else:
                frappe.throw(_("Incorrect number of General Ledger Entries found. You might have selected a wrong Account in the transaction."))
        else:
            make_reverse_gl_entries(gl_map, adv_adj=adv_adj, update_outstanding=update_outstanding)


def process_gl_map(gl_map, merge_entries=True):
    

    # frappe.throw(str(gl_map))
    for entry in gl_map:
        # toggle debit, credit if negative entry
        # frappe.throw(str(entry) +"\n\n" + str(entry["debit"]) )
        if flt(entry["debit"]) < 0:
            entry["credit"] = flt(entry["credit"]) - flt(entry["debit"])
            entry["debit"] = 0.0

        if flt(entry["debit_in_account_currency"]) < 0:
            entry["credit_in_account_currency"] = \
                flt(entry["credit_in_account_currency"]) - flt(entry["debit_in_account_currency"])
            entry["debit_in_account_currency"] = 0.0

        if flt(entry["credit"]) < 0:
            entry["debit"] = flt(entry["debit"]) - flt(entry["credit"])
            entry["credit"] = 0.0

        if flt(entry["credit_in_account_currency"]) < 0:
            entry["debit_in_account_currency"] = \
                flt(entry["debit_in_account_currency"]) - flt(entry["credit_in_account_currency"])
            entry["credit_in_account_currency"] = 0.0

    return gl_map


def make_supplier_gl_entry_pinv(doc, gl_entries):
        # Checked both rounding_adjustment and rounded_total
        # because rounded_total had value even before introcution of posting GLE based on rounded total
        grand_total = doc.rounded_total if (doc.rounding_adjustment and doc.rounded_total) else doc.grand_total

        if grand_total:
            # Didnot use base_grand_total to book rounding loss gle
            grand_total_in_company_currency = flt(grand_total * doc.conversion_rate,
                doc.precision("grand_total"))
            gl_entries.append(
                doc.get_gl_dict({
                    "account": doc.credit_to,
                    "party_type": "Supplier",
                    "company":doc.company,
                    "party": doc.supplier,
                    "due_date": doc.due_date,
                    "against": doc.against_expense_account,
                    "credit": grand_total_in_company_currency,
                    "credit_in_account_currency": grand_total_in_company_currency \
                        if doc.party_account_currency==doc.company_currency else grand_total,
                    "against_voucher": doc.return_against if cint(doc.is_return) and doc.return_against else doc.name,
                    "against_voucher_type": doc.doctype,
                    "cost_center": doc.cost_center
                }, doc.party_account_currency, item=self)
            )

def make_stock_adjustment_entry(doc, gl_entries, item, voucher_wise_stock_value, account_currency):
    net_amt_precision = item.precision("base_net_amount")
    val_rate_db_precision = 6 if cint(item.precision("valuation_rate")) <= 6 else 9

    warehouse_debit_amount = flt(flt(item.valuation_rate, val_rate_db_precision) * flt(item.qty) * flt(item.conversion_factor), net_amt_precision)

    # Stock ledger value is not matching with the warehouse amount
    if (doc.update_stock and voucher_wise_stock_value.get(item.name) and warehouse_debit_amount != flt(voucher_wise_stock_value.get(item.name), net_amt_precision)):

        cost_of_goods_sold_account = doc.get_company_default("default_expense_account")
        stock_amount = flt(voucher_wise_stock_value.get(item.name), net_amt_precision)
        stock_adjustment_amt = warehouse_debit_amount - stock_amount

        gl_entries.append(
            doc.get_gl_dict({
                "account": cost_of_goods_sold_account,
                "company":doc.company,
                "against": item.expense_account,
                "debit": stock_adjustment_amt,
                "remarks": doc.get("remarks") or _("Stock Adjustment"),
                "cost_center": item.cost_center,
                "project": item.project
            }, account_currency, item=item)
        )

        warehouse_debit_amount = stock_amount

    return warehouse_debit_amount

def make_item_gl_entries_pinv(doc, gl_entries):
    # item gl entries
    stock_items = doc.get_stock_items()
    expenses_included_in_valuation = doc.get_company_default("expenses_included_in_valuation")

    # landed_cost_entries = get_item_account_wise_additional_cost(doc.name)

    voucher_wise_stock_value = {}
    if doc.update_stock:
        for d in frappe.get_all('Stock Ledger Entry',fields = ["voucher_detail_no", "stock_value_difference"], filters={'voucher_no': doc.name}):
            voucher_wise_stock_value.setdefault(d.voucher_detail_no, d.stock_value_difference)

    valuation_tax_accounts = [d.account_head for d in doc.get("taxes")if d.category in ('Valuation', 'Total and Valuation') and flt(d.base_tax_amount_after_discount_amount)]

    for item in doc.get("items"):
        if flt(item.base_net_amount):
            account_currency = get_account_currency(item.expense_account)
            if item.item_code:
                asset_category = frappe.get_cached_value("Item", item.item_code, "asset_category")

            if doc.update_stock and doc.auto_accounting_for_stock and item.item_code in stock_items:
                # warehouse account
                warehouse_debit_amount = make_stock_adjustment_entry(doc, gl_entries, item, voucher_wise_stock_value, account_currency)

                gl_entries.append(
                    doc.get_gl_dict({
                        "account": item.expense_account,
                        "company":doc.company,
                        "against": doc.supplier,
                        "debit": warehouse_debit_amount,
                        "remarks": doc.get("remarks") or _("Accounting Entry for Stock"),
                        "cost_center": item.cost_center,
                        "project": item.project
                    }, account_currency, item=item)
                )

                

            elif not item.is_fixed_asset or (item.is_fixed_asset and not doc.is_cwip_accounting_enabled(asset_category)):
                expense_account = (item.expense_account
                    if (not item.enable_deferred_expense or doc.is_return) else item.deferred_expense_account)

                if not item.is_fixed_asset:
                    amount = flt(item.base_net_amount, item.precision("base_net_amount"))
                else:
                    amount = flt(item.base_net_amount + item.item_tax_amount, item.precision("base_net_amount"))

                gl_entries.append(doc.get_gl_dict({
                        "account": expense_account,
                        "company":doc.company,
                        "against": doc.supplier,
                        "debit": amount,
                        "cost_center": item.cost_center,
                        "project": item.project
                    }, account_currency, item=item))

                # If asset is bought through this document and not linked to PR
                if doc.update_stock and item.landed_cost_voucher_amount:
                    expenses_included_in_asset_valuation = doc.get_company_default("expenses_included_in_asset_valuation")
                    # Amount added through landed-cost-voucher
                    gl_entries.append(doc.get_gl_dict({
                        "account": expenses_included_in_asset_valuation,
                        "against": expense_account,
                        "company":doc.company,
                        "cost_center": item.cost_center,
                        "remarks": doc.get("remarks") or _("Accounting Entry for Stock"),
                        "credit": flt(item.landed_cost_voucher_amount),
                        "project": item.project
                    }, item=item))

                    gl_entries.append(doc.get_gl_dict({
                        "account": expense_account,
                        "company":doc.company,
                        "against": expenses_included_in_asset_valuation,
                        "cost_center": item.cost_center,
                        "remarks": doc.get("remarks") or _("Accounting Entry for Stock"),
                        "debit": flt(item.landed_cost_voucher_amount),
                        "project": item.project
                    }, item=item))

                    # update gross amount of asset bought through this document
                    assets = frappe.db.get_all('Asset',
                        filters={ 'purchase_invoice': doc.name, 'item_code': item.item_code }
                    )
                    for asset in assets:
                        frappe.db.set_value("Asset", asset.name, "gross_purchase_amount", flt(item.valuation_rate))
                        frappe.db.set_value("Asset", asset.name, "purchase_receipt_amount", flt(item.valuation_rate))

        if doc.auto_accounting_for_stock and doc.is_opening == "No" and item.item_code in stock_items and item.item_tax_amount:
                # Post reverse entry for Stock-Received-But-Not-Billed if it is booked in Purchase Receipt
                if item.purchase_receipt and valuation_tax_accounts:
                    negative_expense_booked_in_pr = frappe.db.sql("""select name from `tabGL Entry`
                        where voucher_type='Purchase Receipt' and voucher_no=%s and account in %s""",
                        (item.purchase_receipt, valuation_tax_accounts))

                    if not negative_expense_booked_in_pr:
                        gl_entries.append(
                            doc.get_gl_dict({
                                "account": doc.stock_received_but_not_billed,
                                "against": doc.supplier,
                                "debit": flt(item.item_tax_amount, item.precision("item_tax_amount")),
                                "remarks": doc.remarks or "Accounting Entry for Stock",
                                "cost_center": doc.cost_center
                            }, item=item)
                        )

                        doc.negative_expense_to_be_booked += flt(item.item_tax_amount, item.precision("item_tax_amount"))


def get_gl_entries_pinv(doc):

    from erpnext.accounts.general_ledger import merge_similar_entries

    doc.auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(doc.company)
    if doc.auto_accounting_for_stock:
        doc.stock_received_but_not_billed = doc.get_company_default("stock_received_but_not_billed")
    else:
        doc.stock_received_but_not_billed = None
        
    doc.expenses_included_in_valuation = doc.get_company_default("expenses_included_in_valuation")
    doc.negative_expense_to_be_booked = 0.0
    gl_entries = []



    make_supplier_gl_entry(doc, gl_entries)
    make_item_gl_entries_pinv(doc, gl_entries)

    if doc.check_asset_cwip_enabled():
        doc.get_asset_gl_entry(gl_entries)

    doc.make_tax_gl_entries(gl_entries)

    gl_entries = merge_similar_entries(gl_entries)

    doc.make_payment_gl_entries(gl_entries)
    doc.make_write_off_gl_entry(gl_entries)
    doc.make_gle_for_rounding_adjustment(gl_entries)

    if doc.update_stock==1 :
        get_setting = frappe.get_single("General Setting")
        precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
        

        for i in doc.items :
            gi = frappe.get_doc("Item", i.item_code)
            gig = frappe.get_doc("Item Group", gi.item_group)

            account_debit = gig.pinv_stock_account
            account_credit = frappe.get_doc("Company", doc.company).stock_received_but_not_billed

            if doc.is_return == 1 :
                gl_entries.append({
                    "account": account_credit ,
                    "against": account_debit,
                    "cost_center": get_setting.cost_center,
                    "company":doc.company,
                    "remarks": "Accounting Entry for Purchase Invoice",
                    "debit": flt(i.amount*-1, precision),
                    "debit_in_account_currency": flt(i.amount*-1, precision),
                    "credit":0,
                    "credit_in_account_currency":0,
                    "is_opening": "No",
                    "voucher_type": "Purchase Invoice",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

                gl_entries.append({
                    "account": account_debit ,
                    "against": account_credit,
                    "company":doc.company,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Purchase Invoice",
                    "credit": flt(i.amount*-1, precision),
                    "debit": 0,
                    "debit_in_account_currency": 0,
                    
                    "credit_in_account_currency":flt(i.amount*-1, precision),
                    "is_opening": "No",
                    "voucher_type": "Purchase Invoice",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

            else :

                gl_entries.append({
                    "account": account_debit,
                    "against": account_credit,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Sales Invoice",
                    "debit": flt(i.amount, precision),
                    "debit_in_account_currency": flt(i.amount, precision),
                    "credit":0,
                    "company":doc.company,
                    "credit_in_account_currency":0,
                    "is_opening": "No",
                    "voucher_type": "Purchase Invoice",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

                gl_entries.append({
                    "account": account_credit,
                    "against": account_debit,
                    "company":doc.company,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Sales Invoice",
                    "credit": flt(i.amount, precision),
                    "credit_in_account_currency": flt(i.amount, precision),
                    "debit": 0,
                    "debit_in_account_currency": 0,
                    "is_opening": "No",
                    "voucher_type": "Purchase Invoice",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })


    return gl_entries



@frappe.whitelist()
def create_pinv_gle_manual(doc, method):

    repost_future_gle=True
    from_repost=False

    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_sales_invoice == "Yes" :

        gl_entries = get_gl_entries_pinv(doc)

        if gl_entries:
            update_outstanding = "No" if (cint(doc.is_paid) or doc.write_off_account) else "Yes"

            
            # frappe.throw(str(gl_entries))
            make_gl_entries_pinv(gl_entries,  cancel=(doc.docstatus == 2), update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)

            if update_outstanding == "No":
                update_outstanding_amt(doc.credit_to, "Supplier", doc.supplier,
                    doc.doctype, doc.return_against if cint(doc.is_return) and doc.return_against else doc.name)


            

            # edited rico
            
            # if (repost_future_gle or doc.flags.repost_future_gle) and cint(doc.update_stock) and doc.auto_accounting_for_stock:
            # 	from erpnext.controllers.stock_controller import update_gl_entries_after
            # 	items, warehouses = doc.get_items_and_warehouses()
            # 	update_gl_entries_after(doc.posting_date, doc.posting_time,
            # 		warehouses, items, company = doc.company)

        elif doc.docstatus == 2 and cint(doc.update_stock) and doc.auto_accounting_for_stock:
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)


    
        
            




@frappe.whitelist()
def create_sinv_gle_manual(doc, method):

    auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(doc.company)


    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_sales_invoice == "Yes" :
        repost_future_gle=True
        from_repost=False
        gl_entries = get_gl_entries_sinv(doc)
        if gl_entries:
            # if POS and amount is written off, updating outstanding amt after posting all gl entries
            update_outstanding = "No" if (cint(doc.is_pos) or doc.write_off_account) else "Yes"
            # frappe.msgprint(str(gl_entries))
            make_gl_entries_sinv(gl_entries, cancel=(doc.docstatus == 2), update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)
            if update_outstanding == "No":
                from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
                update_outstanding_amt(doc.debit_to, "Customer", doc.customer, doc.doctype, doc.return_against if cint(doc.is_return) and doc.return_against else doc.name)
            # if (repost_future_gle or doc.flags.repost_future_gle) and cint(doc.update_stock) and cint(auto_accounting_for_stock):
            # 		items, warehouses = doc.get_items_and_warehouses()
            # 		update_gl_entries_after(doc.posting_date, doc.posting_time, warehouses, items, company = doc.company)
        elif doc.docstatus == 2 and cint(doc.update_stock) and cint(auto_accounting_for_stock):
            
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)



            

            # gl_map = gl_list
            # if gl_map:
            # 	if gl_map and len(gl_map) > 1:
            # 		for entry in gl_map:
            # 			make_entry(entry)

def make_gl_entries_dn(gl_map, merge_entries=True, cancel=False):
    

    if gl_map:
        if not cancel:
            # validate_accounting_period(gl_map)
            gl_map = process_gl_map(gl_map, merge_entries)
            if gl_map and len(gl_map) > 1:
                
                for entry in gl_map:
                    gle = frappe.new_doc("GL Entry")
                    gle.update(entry)
                    gle.flags.ignore_permissions = 1
                    gle.validate()
                    gle.db_insert()
                    gle.flags.ignore_validate = True
                    gle.submit()
                    



            else:
                frappe.throw(_("Incorrect number of General Ledger Entries found. You might have selected a wrong Account in the transaction."))
        else:
            make_reverse_gl_entries(gl_map, adv_adj=adv_adj, update_outstanding=update_outstanding)

@frappe.whitelist()
def create_dn_gle_manual(doc, method):
    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_delivery_note == "Yes" :

        
        

        gl_entries = []
        repost_future_gle=True
        from_repost=False

        if doc.docstatus == 2:
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)

    
        if doc.docstatus==1:
            if not gl_entries:
                gl_entries = get_gl_entries_dn(doc)
            
            make_gl_entries_dn(gl_entries, merge_entries=True)

        # if (repost_future_gle or doc.flags.repost_future_gle):
        # 	items, warehouses = doc.get_items_and_warehouses()
        # 	update_gl_entries_after(doc.posting_date, doc.posting_time, warehouses, items,
        # 		warehouse_account, company=doc.company)



# ============


@frappe.whitelist()
def change_income_account_based_on_item_group(doc, method):
    for i in doc.items :
        get_i = frappe.get_doc("Item", i.item_code)
        get_ig = frappe.get_doc("Item Group", get_i.item_group)

        if get_ig.sinv_income_account :
            i.income_account = get_ig.sinv_income_account



@frappe.whitelist()
def validate_gl_entry_sub_customer(doc, method):

    

    if doc.party_type == "Customer" and doc.voucher_type != "Journal Entry" :
        # frappe.throw(doc.party_type +" "+ doc.party + " " + doc.voucher_type+ " " + doc.voucher_no)
        get_data = frappe.get_doc(doc.voucher_type, doc.voucher_no)
        if get_data.sub_customer :

        # frappe.throw(doc.party_type +" "+ doc.party + " " + doc.voucher_type+ " " + doc.voucher_no + " " + doc.sub_customer + " " + doc.name)

            frappe.db.sql(""" UPDATE `tabGL Entry` gle SET sub_customer = "{}" WHERE name = "{}" """.format(get_data.sub_customer, doc.name))
            frappe.db.commit()




@frappe.whitelist()
def get_allow_rate_setting(user_id, doctype):
    

    # frappe.get_roles(user_id)

    cek_role = 0

    get_data = frappe.get_single("General Setting")
    if get_data.setting_hidden_rate :
        for i in get_data.setting_hidden_rate :
            if i.role in frappe.get_roles(user_id) :
                if doctype == "Purchase Receipt" :
                    if i.pr > cek_role :
                        cek_role = i.pr
                elif doctype == "Purchase Invoice" :
                    if i.pinv > cek_role :
                        cek_role = i.pinv
                elif doctype == "Stock Entry" :
                    if i.se > cek_role :
                        cek_role = i.se
                elif doctype == "Stock Reconciliation" :
                    if i.src > cek_role :
                        cek_role = i.src
                elif doctype == "Production Form" :
                    if i.p_form > cek_role :
                        cek_role = i.p_form
                elif doctype == "Block Production" :
                    if i.block_prod > cek_role :
                        cek_role = i.block_prod
                elif doctype == "Transformation Production" :
                    if i.transformation > cek_role :
                        cek_role = i.transformation

                elif doctype == "Sales Order" :
                    if i.so > cek_role :
                        cek_role = i.so

                elif doctype == "Sales Invoice" :
                    if i.sinv > cek_role :
                        cek_role = i.sinv

                elif doctype == "Delivery Note" :
                    if i.dn > cek_role :
                        cek_role = i.dn


    return cek_role



@frappe.whitelist()
def get_allow_rate_setting_manual():
    
    user_id = "suprayoto.riconova@gmail.com"
    # frappe.get_roles(user_id)

    print(frappe.get_roles(user_id))

    cek_role = 0

    get_data = frappe.get_single("General Setting")
    if get_data.setting_hidden_rate :
        for i in get_data.setting_hidden_rate :
            if i.role in frappe.get_roles(user_id) :
                if doctype == "Purchase Receipt" :
                    if i.pr > cek_role :
                        cek_role = i.pr
                elif doctype == "Purchase Invoice" :
                    if i.pinv > cek_role :
                        cek_role = i.pinv
                elif doctype == "Stock Entry" :
                    if i.se > cek_role :
                        cek_role = i.se
                elif doctype == "Stock Reconciliation" :
                    if i.src > cek_role :
                        cek_role = i.src
                elif doctype == "Production Form" :
                    if i.p_form > cek_role :
                        cek_role = i.p_form
                elif doctype == "Block Production" :
                    if i.block_prod > cek_role :
                        cek_role = i.block_prod
                elif doctype == "Transformation Production" :
                    if i.transformation > cek_role :
                        cek_role = i.transformation


    return cek_role

    
@frappe.whitelist()
def create_lcv_gle_manual(doc, method):
    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_purchase_receipt == "Yes" :

        for d in doc.get("purchase_receipts"):
            docu = frappe.get_doc(d.receipt_document_type, d.receipt_document)

            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
            gl_list = []

            for i in docu.items :
                gi = frappe.get_doc("Item", i.item_code)
                gig = frappe.get_doc("Item Group", gi.item_group)

                account_debit = gig.pr_stock_account
                account_credit = frappe.get_doc("Company", docu.company).stock_received_but_not_billed

                if docu.is_return == 1 :

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "debit": flt(i.amount*-1, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "voucher_no": docu.name,
                        "posting_date": docu.posting_date
                    })

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "credit": flt(i.amount*-1, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "voucher_no": docu.name,
                        "posting_date": docu.posting_date
                    })

                else :

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "voucher_no": docu.name,
                        "posting_date": docu.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Purchase Receipt",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Purchase Receipt",
                        "voucher_no": docu.name,
                        "posting_date": docu.posting_date
                    })

            gl_map = gl_list
            if gl_map:
                if gl_map and len(gl_map) > 1:
                    for entry in gl_map:
                        make_entry(entry)


@frappe.whitelist()
def create_prec_gle_manual(doc, method):
    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_purchase_receipt == "Yes" :

        precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
        gl_list = []

        for i in doc.items :
            gi = frappe.get_doc("Item", i.item_code)
            gig = frappe.get_doc("Item Group", gi.item_group)

            account_debit = gig.pr_stock_account
            account_credit = frappe.get_doc("Company", doc.company).stock_received_but_not_billed

            if doc.is_return == 1 :

                gl_list.append({
                    "account": account_credit,
                    "against": account_debit,
                    "company":doc.company,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Purchase Receipt",
                    "debit": flt(i.amount*-1, precision),
                    "is_opening": "No",
                    "voucher_type": "Purchase Receipt",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

                gl_list.append({
                    "account": account_debit,
                    "against": account_credit,
                    "company":doc.company,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Purchase Receipt",
                    "credit": flt(i.amount*-1, precision),
                    "is_opening": "No",
                    "voucher_type": "Purchase Receipt",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

            else :

                gl_list.append({
                    "account": account_debit,
                    "against": account_credit,
                    "company":doc.company,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Purchase Receipt",
                    "debit": flt(i.amount, precision),
                    "is_opening": "No",
                    "voucher_type": "Purchase Receipt",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

                gl_list.append({
                    "account": account_credit,
                    "against": account_debit,
                    "company":doc.company,
                    "cost_center": get_setting.cost_center,
                    "remarks": "Accounting Entry for Purchase Receipt",
                    "credit": flt(i.amount, precision),
                    "is_opening": "No",
                    "voucher_type": "Purchase Receipt",
                    "voucher_no": doc.name,
                    "posting_date": doc.posting_date
                })

        gl_map = gl_list
        if gl_map:
            if gl_map and len(gl_map) > 1:
                for entry in gl_map:
                    make_entry(entry)
                    

def get_voucher_details(doc, sle_map):
    if doc.doctype == "Stock Reconciliation":
        reconciliation_purpose = frappe.db.get_value(doc.doctype, doc.name, "purpose")
        is_opening = "Yes" if reconciliation_purpose == "Opening Stock" else "No"
        details = []
        for voucher_detail_no in sle_map:
            details.append(frappe._dict({
                "name": voucher_detail_no,
                "expense_account": doc.expense_account,
                "cost_center": doc.cost_center,
                "is_opening": is_opening
            }))
        return details

def get_gl_entries_sr(doc):

    get_setting = frappe.get_single("General Setting")

    sle_map = get_stock_ledger_details(doc)
    voucher_details = get_voucher_details(doc, sle_map)

    gl_list = []
    
    precision = frappe.get_precision("GL Entry", "debit_in_account_currency")

    for i in doc.items :
        sle_list = sle_map.get(i.name)
        if sle_list:
            for sle in sle_list:

                print(str(sle))

                gi = frappe.get_doc("Item", i.item_code)
                gig = frappe.get_doc("Item Group", gi.item_group)

                account_debit = gig.sinv_cogs_account
                account_credit = gig.sinv_stock_credit_account

                stock_account = gig.sr_stock_account

                if i.amount_difference > 0 :
                    gl_list.append({
                        "account": stock_account,
                        "company":doc.company,
                        "against": doc.expense_account,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Reconciliation",
                        "debit": flt(sle.stock_value_difference, precision),
                        "debit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "credit" : 0,
                        "credit_in_account_currency" : 0,
                        "is_opening": "No",
                        "voucher_type": "Stock Reconciliation",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date,
                        "is_opening": doc.get("is_opening") or "No"
                    })

                    gl_list.append({
                        "account": doc.expense_account,
                        "company":doc.company,
                        "against": stock_account,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Reconciliation",
                        "credit": flt(sle.stock_value_difference, precision),
                        "credit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "debit":0,
                        "debit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Stock Reconciliation",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date,
                        "is_opening": doc.get("is_opening") or "No"
                    })
                else :
                    gl_list.append({
                        "account": doc.expense_account,
                        "company":doc.company,
                        "against": stock_account,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Reconciliation",
                        "debit": flt(sle.stock_value_difference, precision),
                        "debit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "credit" : 0,
                        "credit_in_account_currency" : 0,
                        "is_opening": "No",
                        "voucher_type": "Stock Reconciliation",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date,
                        "is_opening": doc.get("is_opening") or "No"
                    })

                    gl_list.append({
                        "account": stock_account,
                        "against": doc.expense_account,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Reconciliation",
                        "credit": flt(sle.stock_value_difference, precision),
                        "credit_in_account_currency": flt(sle.stock_value_difference, precision),
                        "debit":0,
                        "debit_in_account_currency":0,
                        "is_opening": "No",
                        "voucher_type": "Stock Reconciliation",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date,
                        "is_opening": doc.get("is_opening") or "No"
                    })

    merge_entries = True
    return process_gl_map(gl_list, merge_entries)


def make_gl_entries_sr(gl_map, cancel=False):
    

    if gl_map:
        if not cancel:
            if gl_map and len(gl_map) > 1:
                
                for entry in gl_map:
                    gle = frappe.new_doc("GL Entry")
                    gle.update(entry)
                    gle.flags.ignore_permissions = 1
                    gle.validate()
                    gle.db_insert()
                    gle.flags.ignore_validate = True
                    gle.submit()
                    


def update_gl_entries_after_sr(posting_date, posting_time, for_warehouses=None, for_items=None, warehouse_account=None, company=None):
    def _delete_gl_entries(voucher_type, voucher_no):
        frappe.db.sql("""delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s""", (voucher_type, voucher_no))

    # if not warehouse_account:
    # 	warehouse_account = get_warehouse_account_map(company)

    future_stock_vouchers = get_future_stock_vouchers(posting_date, posting_time, for_warehouses, for_items)
    gle = get_voucherwise_gl_entries(future_stock_vouchers, posting_date)

    for voucher_type, voucher_no in future_stock_vouchers:
        existing_gle = gle.get((voucher_type, voucher_no), [])
        voucher_obj = frappe.get_doc(voucher_type, voucher_no)

        doc = voucher_obj
        if voucher_type == "Sales Invoice" :
            _delete_gl_entries(voucher_type, voucher_no)
            repost_future_gle=True
            from_repost=False
            gl_entries = get_gl_entries_sinv(doc)
            if gl_entries:
                update_outstanding = "No" if (cint(doc.is_pos) or doc.write_off_account) else "Yes"
                make_gl_entries_sinv(gl_entries, cancel=(doc.docstatus == 2), update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)


        elif voucher_type == "Delivery Note" :
            
            _delete_gl_entries(voucher_type, voucher_no)
            gl_entries = []
            repost_future_gle=True
            from_repost=False
            if doc.docstatus == 2:
                _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)
            if doc.docstatus==1:
                if not gl_entries:
                    gl_entries = get_gl_entries_dn(doc)
                make_gl_entries_dn(gl_entries, merge_entries=True)




def get_items_and_warehouses(doc):
    items, warehouses = [], []

    if hasattr(doc, "items"):
        item_doclist = doc.get("items")
    elif doc.doctype == "Stock Reconciliation":
        import json
        item_doclist = []
        data = json.loads(doc.reconciliation_json)
        for row in data[data.index(doc.head_row)+1:]:
            d = frappe._dict(zip(["item_code", "warehouse", "qty", "valuation_rate"], row))
            item_doclist.append(d)

    if item_doclist:
        for d in item_doclist:
            if d.item_code and d.item_code not in items:
                items.append(d.item_code)

            if d.get("warehouse") and d.warehouse not in warehouses:
                warehouses.append(d.warehouse)

    return items, warehouses

@frappe.whitelist()
def create_sr_gle_manual(doc, method):
    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_stock_reconciliation == "Yes" :

        

        repost_future_gle=True, 
        from_repost=False
        gl_entries = []

        if doc.docstatus == 2:
            _delete_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)

        if cint(erpnext.is_perpetual_inventory_enabled(doc.company)):
            # warehouse_account = get_warehouse_account_map(doc.company)

            if doc.docstatus==1:
                if not gl_entries:
                    gl_entries = get_gl_entries_sr(doc)
                make_gl_entries_sr(gl_entries)

            if (repost_future_gle or doc.flags.repost_future_gle):

                items, warehouses = get_items_and_warehouses(doc)
                
                update_gl_entries_after_sr(doc.posting_date, doc.posting_time, warehouses, items, company=doc.company)



        



# @frappe.whitelist()
# def create_sinv_gle_manual(doc, method):
# 	if doc.update_stock==1 :
# 		get_setting = frappe.get_single("General Setting")
# 		if get_setting.replace_gle_sales_invoice == "Yes" :

# 			precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
# 			gl_list = []

# 			for i in doc.items :
# 				gi = frappe.get_doc("Item", i.item_code)
# 				gig = frappe.get_doc("Item Group", gi.item_group)

# 				account_debit = gig.sinv_cogs_account
# 				account_credit = gig.sinv_stock_credit_account

# 				if doc.is_return == 1 :
# 					gl_list.append({
# 						"account": account_credit ,
# 						"against": account_debit,
# 						"cost_center": get_setting.cost_center,
# 						"remarks": "Accounting Entry for Sales Invoice",
# 						"debit": flt(i.amount*-1, precision),
# 						"is_opening": "No",
# 						"voucher_type": "Sales Invoice",
# 						"voucher_no": doc.name,
# 						"posting_date": doc.posting_date
# 					})

# 					gl_list.append({
# 						"account": account_debit ,
# 						"against": account_credit,
# 						"cost_center": get_setting.cost_center,
# 						"remarks": "Accounting Entry for Sales Invoice",
# 						"credit": flt(i.amount*-1, precision),
# 						"is_opening": "No",
# 						"voucher_type": "Sales Invoice",
# 						"voucher_no": doc.name,
# 						"posting_date": doc.posting_date
# 					})

# 				else :

# 					gl_list.append({
# 						"account": account_debit,
# 						"against": account_credit,
# 						"cost_center": get_setting.cost_center,
# 						"remarks": "Accounting Entry for Sales Invoice",
# 						"debit": flt(i.amount, precision),
# 						"is_opening": "No",
# 						"voucher_type": "Sales Invoice",
# 						"voucher_no": doc.name,
# 						"posting_date": doc.posting_date
# 					})

# 					gl_list.append({
# 						"account": account_credit,
# 						"against": account_debit,
# 						"cost_center": get_setting.cost_center,
# 						"remarks": "Accounting Entry for Sales Invoice",
# 						"credit": flt(i.amount, precision),
# 						"is_opening": "No",
# 						"voucher_type": "Sales Invoice",
# 						"voucher_no": doc.name,
# 						"posting_date": doc.posting_date
# 					})

# 			gl_map = gl_list
# 			if gl_map:
# 				if gl_map and len(gl_map) > 1:
# 					for entry in gl_map:
# 						make_entry(entry)

# @frappe.whitelist()
# def create_dn_gle_manual(doc, method):
# 	get_setting = frappe.get_single("General Setting")
# 	if get_setting.replace_gle_delivery_note == "Yes" :

# 		precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
# 		gl_list = []

# 		for i in doc.items :
# 			gi = frappe.get_doc("Item", i.item_code)
# 			gig = frappe.get_doc("Item Group", gi.item_group)

# 			account_debit = gig.dn_cogs_account
# 			account_credit = gig.dn_stock_credit_account

# 			if doc.is_return == 1 :

# 				gl_list.append({
# 					"account": account_credit,
# 					"against": account_debit,
# 					"cost_center": get_setting.cost_center,
# 					"remarks": "Accounting Entry for Delivery Note",
# 					"debit": flt(i.amount*-1, precision),
# 					"is_opening": "No",
# 					"voucher_type": "Delivery Note",
# 					"voucher_no": doc.name,
# 					"posting_date": doc.posting_date
# 				})

# 				gl_list.append({
# 					"account": account_debit ,
# 					"against": account_credit,
# 					"cost_center": get_setting.cost_center,
# 					"remarks": "Accounting Entry for Delivery Note",
# 					"credit": flt(i.amount*-1, precision),
# 					"is_opening": "No",
# 					"voucher_type": "Delivery Note",
# 					"voucher_no": doc.name,
# 					"posting_date": doc.posting_date
# 				})


# 			else :

# 				gl_list.append({
# 					"account": account_debit,
# 					"against": account_credit,
# 					"cost_center": get_setting.cost_center,
# 					"remarks": "Accounting Entry for Delivery Note",
# 					"debit": flt(i.amount, precision),
# 					"is_opening": "No",
# 					"voucher_type": "Delivery Note",
# 					"voucher_no": doc.name,
# 					"posting_date": doc.posting_date
# 				})

# 				gl_list.append({
# 					"account": account_credit,
# 					"against": account_debit,
# 					"cost_center": get_setting.cost_center,
# 					"remarks": "Accounting Entry for Delivery Note",
# 					"credit": flt(i.amount, precision),
# 					"is_opening": "No",
# 					"voucher_type": "Delivery Note",
# 					"voucher_no": doc.name,
# 					"posting_date": doc.posting_date
# 				})

# 		gl_map = gl_list
# 		if gl_map:
# 			if gl_map and len(gl_map) > 1:
# 				for entry in gl_map:
# 					make_entry(entry)




@frappe.whitelist()
def create_ste_gle_manual(doc, method):
    get_setting = frappe.get_single("General Setting")
    if get_setting.replace_gle_stock_entry == "Yes" :

        # untuk PRODUCTION FORM
        if doc.stock_entry_type == "Manufacture" and doc.production_form :
            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
            gl_list = []

            # untuk source warehouse dulu
            for i in doc.items :
                if i.s_warehouse and not i.t_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    account_debit = gig.pf_adjustment_account
                    account_credit = gig.pf_credit_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Production Form",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "company":doc.company,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Production Form",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                elif i.t_warehouse and not i.s_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    account_debit = gig.pf_debit_account
                    account_credit = gig.pf_adjustment_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Production Form",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Production Form",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

            # frappe.msgprint(str(gl_list))
            gl_map = gl_list
            if gl_map:
                if gl_map and len(gl_map) > 1:
                    for entry in gl_map:
                        make_entry(entry)




        # untuk BLOCK PRODUCTION
        if doc.stock_entry_type == "Manufacture" and doc.block_production :
            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
            gl_list = []

            # untuk source warehouse dulu
            for i in doc.items :
                if i.s_warehouse and not i.t_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    # account_debit = gig.bl_adjustment_account
                    account_debit = gig.bl_debit_account
                    account_credit = gig.bl_credit_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Block Production",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Block Production",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                elif i.t_warehouse and not i.s_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    account_debit = gig.bl_debit_account
                    # account_credit = gig.bl_adjustment_account
                    account_credit = gig.bl_credit_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Block Production",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "company":doc.company,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Block Production",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

            # frappe.msgprint(str(gl_list))
            gl_map = gl_list
            if gl_map:
                if gl_map and len(gl_map) > 1:
                    for entry in gl_map:
                        make_entry(entry)


        # untuk MATERIAL ISSUE
        if doc.stock_entry_type == "Material Issue" :
            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
            gl_list = []

            # untuk source warehouse dulu
            for i in doc.items :
                if i.s_warehouse and not i.t_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    account_debit = gig.mi_adjustment_account
                    account_credit = gig.mi_credit_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Material Issue",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "company":doc.company,
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Material Issue",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "company":doc.company,
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

            # frappe.msgprint(str(gl_list))
            gl_map = gl_list
            if gl_map:
                if gl_map and len(gl_map) > 1:
                    for entry in gl_map:
                        make_entry(entry)

        # untuk MATERIAL RECEIPT
        if doc.stock_entry_type == "Material Receipt" :
            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
            gl_list = []

            # untuk source warehouse dulu
            for i in doc.items :
                if i.t_warehouse and not i.s_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    account_debit = gig.mr_debit_account
                    account_credit = gig.mr_adjustment_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Material Receipt",
                        "debit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "company":doc.company,
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Material Receipt",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "company":doc.company,
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

            # frappe.msgprint(str(gl_list))
            gl_map = gl_list
            if gl_map:
                if gl_map and len(gl_map) > 1:
                    for entry in gl_map:
                        make_entry(entry)




@frappe.whitelist()
def make_entry(args):
    args.update({"doctype": "GL Entry"})
    gle = frappe.get_doc(args)
    
    gle.flags.ignore_permissions = 1
    gle.validate()
    gle.insert()
    gle.submit()



@frappe.whitelist()
def get_naming_series(user_id):
    series_type = 'SO'

    series = []

    get_val = frappe.get_value("Employee", {"user_id" : user_id}, "name")
    if get_val :
        get_e = frappe.get_doc("Employee", get_val)

        if get_e.branch_access :
            for ba in get_e.branch_access :
                if ba.branch == "FCT Abuja HO" :
                    series.append(series_type + '-FCT-HO-')
                elif ba.branch == "Maraba Depot MD" :
                    series.append(series_type+'-NAS-MD-')

                elif ba.branch == "Kugbo Depot KD" :
                    series.append(series_type+'-FCT-KD-')

                elif ba.branch == "Suleja Depot SD" :
                    series.append(series_type+'-NIG-SD-')

                elif ba.branch == "Utako Showroom US" :
                    series.append(series_type+'-FCT-US-')

                elif ba.branch == "Gwarinpa Showroom GS" :
                    series.append(series_type+'-FCT-GS-')

    return series

                
@frappe.whitelist()
def get_journal_entry_type(user_id):
    
    series = []

    get_val = frappe.get_value("Employee", {"user_id" : user_id}, "name")
    if get_val :
        get_e = frappe.get_doc("Employee", get_val)

        if get_e.journal_type :
            for ba in get_e.journal_type :
                
                series.append(ba.journal_type)

                

    return series




@frappe.whitelist()
def get_allowed_item(user_id):
    

    # frappe.get_roles(user_id)

    cek_role = 0
    arr_item = []

    get_data = frappe.get_single("General Setting")
    if get_data.setting_item :
        for i in get_data.setting_item :
            arr_item.append(i.item_code)
            
    return arr_item



@frappe.whitelist()
def get_allowed_role(user_id):
    

    # frappe.get_roles(user_id)

    cek_role = 0

    get_data = frappe.get_single("General Setting")
    if get_data.setting_role :
        for i in get_data.setting_role :
            if i.role in frappe.get_roles(user_id) :
                cek_role = 1


    return cek_role



@frappe.whitelist()
def cek_sub_customer_role(user_id):
    

    # frappe.get_roles(user_id)

    sub_customer_time = 0

    get_data = frappe.get_single("General Setting")
    if get_data.setting_customer_and_sub_customer :
        for i in get_data.setting_customer_and_sub_customer :
            if i.role in frappe.get_roles(user_id) :
                if i.sub_customer > sub_customer_time :
                    sub_customer_time = i.sub_customer


    return sub_customer_time



@frappe.whitelist()
def cek_customer_role(user_id):
    

    # frappe.get_roles(user_id)

    customer_time = 0

    get_data = frappe.get_single("General Setting")
    if get_data.setting_customer_and_sub_customer :
        for i in get_data.setting_customer_and_sub_customer :
            if i.role in frappe.get_roles(user_id) :
                if i.customer > customer_time :
                    customer_time = i.customer


    return customer_time



@frappe.whitelist()
def get_role_list(user_id):
    

    # frappe.get_roles(user_id)

    cek_role = 0

    get_data = frappe.get_single("General Setting")
    if get_data.setting_role_sales_invoice :
        for i in get_data.setting_role_sales_invoice :
            if i.role_stock_entry in frappe.get_roles(user_id) :

                cek_role = 1


    return cek_role




@frappe.whitelist()
def check_credit_limit_sales_invoice(doc, method):
    get_cust = frappe.get_doc("Customer", doc.customer)
    if get_cust.credit_limits :
        for cl in get_cust.credit_limits :
            if doc.company != doc.company :

                get_gle = frappe.db.sql("""

                    SELECT SUM(gle.`credit_in_account_currency`) FROM `tabGL Entry` gle
                    WHERE gle.`party_type` = "Customer"
                    AND gle.`party` = "{}"
                    AND gle.`credit` != 0
                    AND (gle.`against_voucher_type` = "Sales Order" OR gle.`against_voucher_type` IS NULL)
                    AND gle.`company` = "{}"

                """.format(doc.customer, doc.company))

                if get_gle :
                    customer_outstanding = get_customer_outstanding_edited_rico(doc.customer, doc.company, ignore_outstanding_sales_order=False)

                    if customer_outstanding > float(get_gle[0][0]) :
                        frappe.throw("Cannot approve this Sales Invoice because Customer didnt have enough Payment or Credit Limit")


                else :
                    frappe.throw("Cannot approve this Sales Invoice because Customer didnt have enough Payment or Credit Limit")

                # jika tidak punya credit limit untuk company bersangkutan



@frappe.whitelist()
def check_credit_limit_delivery_note(doc, method):
    get_cust = frappe.get_doc("Customer", doc.customer)
    if get_cust.credit_limits :
        for cl in get_cust.credit_limits :
            if doc.company != doc.company :

                get_gle = frappe.db.sql("""

                    SELECT SUM(gle.`credit_in_account_currency`) FROM `tabGL Entry` gle
                    WHERE gle.`party_type` = "Customer"
                    AND gle.`party` = "{}"
                    AND gle.`credit` != 0
                    AND (gle.`against_voucher_type` = "Sales Order" OR gle.`against_voucher_type` IS NULL)
                    AND gle.`company` = "{}"

                """.format(doc.customer, doc.company))

                if get_gle :
                    customer_outstanding = get_customer_outstanding_edited_rico(doc.customer, doc.company, ignore_outstanding_sales_order=False)

                    if customer_outstanding > float(get_gle[0][0]) :
                        frappe.throw("Cannot approve this Delivery Note because Customer didnt have enough Payment or Credit Limit")


                else :
                    frappe.throw("Cannot approve this Delivery Note because Customer didnt have enough Payment or Credit Limit")

                # jika tidak punya credit limit untuk company bersangkutan



@frappe.whitelist()
def get_customer_outstanding_edited_rico(customer, company, ignore_outstanding_sales_order=False, cost_center=None):
    # Outstanding based on GL Entries

    cond = ""
    if cost_center:
        lft, rgt = frappe.get_cached_value("Cost Center",
            cost_center, ['lft', 'rgt'])

        cond = """ and cost_center in (select name from `tabCost Center` where
            lft >= {0} and rgt <= {1})""".format(lft, rgt)

    outstanding_based_on_gle = frappe.db.sql("""
        select sum(debit) - sum(credit)
        from `tabGL Entry` where party_type = 'Customer'
        and party = %s and company=%s {0}""".format(cond), (customer, company))

    outstanding_based_on_gle = flt(outstanding_based_on_gle[0][0]) if outstanding_based_on_gle else 0

    # Outstanding based on Sales Order
    outstanding_based_on_so = 0.0

    # if credit limit check is bypassed at sales order level,
    # we should not consider outstanding Sales Orders, when customer credit balance report is run
    if not ignore_outstanding_sales_order:
        outstanding_based_on_so = frappe.db.sql("""
            select sum(base_grand_total*(100 - per_billed)/100)
            from `tabSales Order`
            where customer=%s and docstatus = 1 and company=%s
            and per_billed < 100 and status != 'Closed'""", (customer, company))

        outstanding_based_on_so = flt(outstanding_based_on_so[0][0]) if outstanding_based_on_so else 0.0

    # Outstanding based on Delivery Note, which are not created against Sales Order
    unmarked_delivery_note_items = frappe.db.sql("""select
            dn_item.name, dn_item.amount, dn.base_net_total, dn.base_grand_total
        from `tabDelivery Note` dn, `tabDelivery Note Item` dn_item
        where
            dn.name = dn_item.parent
            and dn.customer=%s and dn.company=%s
            and dn.docstatus = 1 and dn.status not in ('Closed', 'Stopped')
            and ifnull(dn_item.against_sales_order, '') = ''
            and ifnull(dn_item.against_sales_invoice, '') = ''
        """, (customer, company), as_dict=True)

    outstanding_based_on_dn = 0.0

    for dn_item in unmarked_delivery_note_items:
        si_amount = frappe.db.sql("""select sum(amount)
            from `tabSales Invoice Item`
            where dn_detail = %s and docstatus = 1""", dn_item.name)[0][0]

        if flt(dn_item.amount) > flt(si_amount) and dn_item.base_net_total:
            outstanding_based_on_dn += ((flt(dn_item.amount) - flt(si_amount)) \
                / dn_item.base_net_total) * dn_item.base_grand_total

    return outstanding_based_on_gle + outstanding_based_on_so + outstanding_based_on_dn



@frappe.whitelist()
def check_ste_on_submit(doc, method):

    
    if doc.stock_entry_type == "Receive at Warehouse" :

        allowed_role = frappe.get_single("General Setting")
        arole = ""

        gps = ""
        total_prev_qty = 0
        total_curr_qty = 0

        if doc.outgoing_stock_entry :
            gps = frappe.get_doc("Stock Entry", doc.outgoing_stock_entry)
            
            for g in gps.items :
                total_prev_qty += g.qty

        for i in doc.items :
            total_curr_qty += i.qty

        if total_curr_qty != total_prev_qty :

            if allowed_role.setting_role_stock_entry :
                bypass = 0
                for i in allowed_role.setting_role_stock_entry :

                    if i.role_stock_entry in frappe.get_roles() :
                        bypass = 1

                if bypass == 0 :
                    frappe.throw("Please seek approval from Manager")





@frappe.whitelist()
def patch_ste_gle_manual():
    get_setting = frappe.get_single("General Setting")
    array_ste = ["MAT-STE-2020-00347","MAT-STE-2020-00352","MAT-STE-2020-00793","MAT-STE-2020-01130","MAT-STE-2020-01131","MAT-STE-2020-01305","MAT-STE-2020-01395","MAT-STE-2020-01679","MAT-STE-2020-01946","MAT-STE-2020-02057","MAT-STE-2021-01127","MAT-STE-2021-01524","MAT-STE-2021-01530","MAT-STE-2021-01730","MAT-STE-2021-01853","MAT-STE-2021-02186","MAT-STE-2021-02297","MAT-STE-2021-02367","MAT-STE-2021-02763"]

    for i in array_ste :
        doc = frappe.get_doc("Stock Entry", i)

        # untuk MATERIAL RECEIPT
        if doc.stock_entry_type == "Material Receipt" :
            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")
            gl_list = []

            # untuk source warehouse dulu
            for i in doc.items :
                if i.t_warehouse and not i.s_warehouse :

                    gi = frappe.get_doc("Item", i.item_code)
                    gig = frappe.get_doc("Item Group", gi.item_group)

                    account_debit = gig.mr_debit_account
                    account_credit = gig.mr_adjustment_account

                    gl_list.append({
                        "account": account_debit,
                        "against": account_credit,
                        "cost_center": get_setting.cost_center,
                        "remarks": "Accounting Entry for Stock Entry Material Receipt",
                        "debit": flt(i.amount, precision),
                        "company":doc.company,
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

                    gl_list.append({
                        "account": account_credit,
                        "against": account_debit,
                        "cost_center": get_setting.cost_center,
                        "company":doc.company,
                        "remarks": "Accounting Entry for Stock Entry Material Receipt",
                        "credit": flt(i.amount, precision),
                        "is_opening": "No",
                        "voucher_type": "Stock Entry",
                        "voucher_no": doc.name,
                        "posting_date": doc.posting_date
                    })

            # frappe.msgprint(str(gl_list))
            gl_map = gl_list
            if gl_map:
                if gl_map and len(gl_map) > 1:
                    for entry in gl_map:
                        make_entry(entry)

        print(str(i))



def _delete_gl_entries(voucher_type, voucher_no):
	frappe.db.sql(
		"""delete from `tabGL Entry`
		where voucher_type=%s and voucher_no=%s""",
		(voucher_type, voucher_no),
	)

