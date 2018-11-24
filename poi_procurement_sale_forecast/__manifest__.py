# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "MPS - Sale forecast",
    "version": "1.0",
    "depends": [
        "base",
        "product",
        "sale",
        "stock",
        "purchase",
        "mrp",
    ],
    "author": "OdooMRP team,"
              "AvanzOSC,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza",
    "contributors": [
        "Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>",
        "Ainara Galdona <ainaragaldona@avanzosc.es>",
        "Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>",
        "Ana Juaristi <anajuaristi@avanzosc.es>",
        "Daniel Campos <danielcampos@avanzosc.es>",
    ],
    "category": "MPS",
    "website": "http://www.odoomrp.com",
    "summary": "Sale forecast",
    "data": ["security/ir.model.access.csv",
             "wizard/sale_forecast_load_view.xml",
             "views/sale_view.xml",
             "data/procurement_cron_update.xml",
             "report/prevision_insumos_report_view.xml",
             "wizard/prevision_insumos_wizard_view.xml",
             "wizard/purchase_onstock_view.xml",
             ],
    'installable': False,
    "auto_install": False,
}
