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

class ProductClass(models.Model):
    _name = 'product.class'

    name = fields.Char('Clase')

class ProductType(models.Model):
    _name = 'product.type'

    name = fields.Char('Tipo')

class ProductStype(models.Model):
    _name = 'product.stype'

    name = fields.Char('Sub-Tipo')

class ProductModel(models.Model):
    _name = 'product.model'

    name = fields.Char('Modelo')

class ProductSmodel(models.Model):
    _name = 'product.smodel'

    name = fields.Char('Sub-Model')

class ProductContainer(models.Model):
    _name = 'product.container'

    name = fields.Char('Tipo de Envase')

class ProductActivity(models.Model):
    _name = 'product.activity'

    name = fields.Char('Actividad Economica')



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    class_id = fields.Many2one('product.class', 'Clase')
    type_id = fields.Many2one('product.type', 'Tipo')
    stype_id = fields.Many2one('product.stype', 'Sub-Tipo')
    model_id = fields.Many2one('product.model', 'Modelo')
    smodel_id = fields.Many2one('product.smodel', 'Sub-Modelo')
    container_id = fields.Many2one('product.container', 'Tipo de Envase')
    activity_id = fields.Many2one('product.activity', 'Actividad Economica')
    min_sale_quantity = fields.Float('Cantidad Valida para la Venta')


class ProductProduct(models.Model):
    _inherit = 'product.product'


    @api.model
    def get_product(self, company_id=False, item_id=False):
        items = []
        domain = [('sale_ok', '=', True)]
        if item_id:
            domain.append(['id', '=', int(item_id)])
        pricelist_ids = self.env['product.pricelist'].search([('active', '=', True)])
        for p in self.search(domain):
            prices = []
            for pricelist in pricelist_ids:
                price_unit = False
                product = p.with_context(
                    # partner=self.order_id.partner_id.id,
                    quantity=1,
                    date_order=fields.Date.today(),
                    pricelist=pricelist.id,
                    uom=(p.uom_id and p.uom_id.id) or False,
                    # fiscal_position=self.env.context.get('fiscal_position')
                )
                price_unit = product.price
                if price_unit and price_unit > 0:
                    prices.append({
                        "ListaPrecioId": pricelist.id,
                        "ListaPrecio_Nombre": pricelist.name,
                        "Price": price_unit,
                        "ListaPrecio_Moneda": pricelist.currency_id.name,
                    })
            items.append({
                "ItemId": p.id,
                "Item_Nombre": p.name,
                "DivisionId": (p.categ_id and p.categ_id.id) or False,
                "Division": (p.categ_id and p.categ_id.name) or False,
                "ClaseId": (p.class_id and p.class_id.id) or False,
                "Clase": (p.class_id and p.class_id.name) or False,
                "TipoId": (p.type_id and p.type_id.id) or False,
                "Tipo": (p.type_id and p.type_id.name) or False,
                "SubTipoId": (p.stype_id and p.stype_id.id) or False,
                "Sub Tipo": (p.stype_id and p.stype_id.name) or False,
                "MarcaId": (p.segment_id and p.segment_id.id) or False,
                "Marca": (p.segment_id and p.segment_id.name) or False,
                "ModeloId": (p.model_id and p.model_id.id) or False,
                "Modelo": (p.model_id and p.model_id.name) or False,
                "SubModeloId": (p.smodel_id and p.smodel_id.id) or False,
                "Sub Modelo": (p.smodel_id and p.smodel_id.name) or False,
                "TipoEnvaseId": (p.container_id and p.container_id.id) or False,
                "TipoEnvase_Nombre": (p.container_id and p.container_id.name) or False,
                "UnidadMedidaVenta": (p.uom_id and p.uom_id.name) or False,
                "ActividadEconomicaId": (p.activity_id and p.activity_id.id) or False,
                "CantValidaParaVenta": p.min_sale_quantity,
                "Precios": prices,
            })
        res = {
            "Empresa" : "ALINA",
            "Error" : False,
            "Mensaje" : False,
            "Resultado" : False,
            "Items" : [items]
        }

        return res
