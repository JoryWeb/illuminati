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

class ResPartner(models.Model):
    _inherit = 'res.partner'

    dposid = fields.Char('DPoSId')
    nit_ext = fields.Char('NIT Extension')
    pricelist_eco_id = fields.Many2one('product.pricelist', 'Lista de Precio Linea Eco')



    @api.model
    def get_partner(self, company_id=False):
        customers = []
        for p in self.search([('customer', '=', True)]):
            if p.company_type == 'person':
                customers.append({
                    'ClienteId': p.id,
                    'DPoSId': p.dposid,
                    'Cliente_Nombre': p.name,
                    'Cliente_AParterno': False,
                    'Cliente_AMaterno': False,
                    "Cliente_Tipo": "Natural",
                    "Cliente_NombreComercial": False,
                    'NIT': p.ci,
                    'Cliente_NIT_Extension': p.ci_dept,
                    'LienaCredito_Saldo': p.credit,
                    "LineaCredito_Moneda": "USD",
                    "M20001": (p.pricelist_eco_id and  p.pricelist_eco_id.id) or False,
                    "Estado": p.active,
                })
            else:
                customers.append({
                    'ClienteId': p.id,
                    'DPoSId': p.dposid,
                    'Cliente_Nombre': False,
                    'Cliente_AParterno': False,
                    'Cliente_AMaterno': False,
                    "Cliente_Tipo": "Empresa",
                    "Cliente_NombreComercial": p.name,
                    'NIT': p.nit,
                    'Cliente_NIT_Extension': p.nit_ext,
                    'LienaCredito_Saldo': p.credit,
                    "LineaCredito_Moneda" : "USD",
                    "M20001" : (p.pricelist_eco_id and  p.pricelist_eco_id.id) or False,
                    "Estado" : p.active,
                })


        res = {
            'Empresa': 'Alina',
            'Error': False,
            'Mensaje': False,
            'Resultado': False,
            'Clientes': customers,

        }
        return res
