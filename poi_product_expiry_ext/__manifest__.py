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
    "name": "Products Expiry Date - Extension",
    "version": "9.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "product_expiry",
        "mrp",
    ],
    "author": "OdooMRP team,"
              "AvanzOSC,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza",
    "contributors": [
        "Juan Ignacio Úbeda <juanignacioubeda@avanzosc.es>",
        "Pedro Manuel Baeza Romero <pedro.baeza@serviciosbaeza.com>",
        "Ana Juaristi Olalde <anajuaristi@avanzosc.es>",
        "Mikel Arregi <mikelarregi@avanzosc.es>"
        "Miguel Angel Callisaya Mamani <miguel.callisaya@poiesisconsulting.com>"
    ],
    "category": "Tools",
    "website": "http://www.odoomrp.com",
    "summary": "",
    "data": [
        "views/production_lot_ext_view.xml",
        "views/stock_quant_view.xml",
        "wizard/stock_pack_operation_lot_view.xml",
    ],
    "installable": False,
}
