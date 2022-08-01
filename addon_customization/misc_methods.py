import frappe
from erpnext.assets.doctype.asset.depreciation import get_gl_entries_on_asset_disposal
from frappe.utils import today
from frappe import _

def set_values_for_assets(remark,branch):
    #Set values for existing assets, To be run once
    all_assets = frappe.get_all("Asset",{"docstatus":1},['name'])
    asset_branch = branch if frappe.db.exists("Branch",branch) else frappe.get_all("Branch")[0]['name']
    if all_assets:
        for each in all_assets:
            frappe.db.set_value("Asset",each.name,'remark',remark)
            frappe.db.set_value("Asset",each.name,'asset_branch',asset_branch)
    return 

@frappe.whitelist()
def scrap_asset_(asset_name):
    asset = frappe.get_doc("Asset", asset_name)
    
    if asset.docstatus != 1:
        frappe.throw(_("Asset {0} must be submitted").format(asset.name))
    elif asset.status in ("Cancelled", "Sold", "Scrapped"):
        frappe.throw(
            _("Asset {0} cannot be scrapped, as it is already {1}").format(asset.name, asset.status)
        )

    depreciation_series = frappe.get_cached_value(
        "Company", asset.company, "series_for_depreciation_entry"
    )

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.naming_series = depreciation_series
    je.user_remark = asset.remark
    je.location = asset.asset_branch
    je.posting_date = today()
    je.company = asset.company
    je.remark = "Scrap Entry for asset {0}".format(asset_name)

    for entry in get_gl_entries_on_asset_disposal(asset):
        entry.update({"reference_type": "Asset", "reference_name": asset_name})
        je.append("accounts", entry)

    je.flags.ignore_permissions = True
    je.submit()

    frappe.db.set_value("Asset", asset_name, "disposal_date", today())
    frappe.db.set_value("Asset", asset_name, "journal_entry_for_scrap", je.name)
    asset.set_status("Scrapped")

    frappe.msgprint(_("Asset scrapped via Journal Entry {0}").format(je.name))


