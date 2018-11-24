#########################################################################
#                                                                       #
# Copyright (C) 2015  Agile Business Group                              #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU Affero General Public License as        #
# published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                       #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU Affero General Public Licensefor more details.                    #
#                                                                       #
# You should have received a copy of the                                #
# GNU Affero General Public License                                     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #
#########################################################################
import logging
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from lxml import etree
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.model
    def get_pricelist(self, company_id=False):
        pricelist = []
        for p in self.search([('active', '=', True)]):
            pricelist.append({
                "ListaPrecioId": p.id,
                "ListaPrecio": p.name,
                "EmpresaId": 1,

            })

        res = {
            "Empresa": "ALINA",
            "Error": False,
            "Mensaje": False,
            "Resultado": False,
            "Lista_de_Precio": pricelist
        }

        return res
