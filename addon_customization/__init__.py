# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

from addon_customization.misc_methods import scrap_asset_
from erpnext.assets.doctype.asset import depreciation


depreciation.scrap_asset = scrap_asset_