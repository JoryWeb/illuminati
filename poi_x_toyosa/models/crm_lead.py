import logging
from odoo import api, fields, models
from lxml import etree
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    """Adds last name and first name; name becomes a stored function field."""
    _inherit = 'crm.lead'

    so_type_id = fields.Many2one('sale.order.type', 'Tipo de Cotizacion')
    current_car = fields.Boolean('Vehiculo Actual')
    brand = fields.Char('Marca')
    model = fields.Char('Modelo')
    year = fields.Char(u'Año')
    product_id = fields.Many2one('product.product' ,'Producto a Adquirir')
    price_list = fields.Float('Precio de Lista', related="product_id.list_price", readonly=True)
    price_sale = fields.Char('Precio de Venta')
    car_payment = fields.Boolean('Auto en Pago')
    credit_application = fields.Boolean('Solicitud de Credito')
    brand_model = fields.Char('Marca/Modelo')
    year2 = fields.Char(u'Año')
    km = fields.Char('Km')
    partner_price = fields.Char('Precio Esperado del Cliente')
    bank = fields.Boolean('Bancario')
    bank_name = fields.Char('Donde')
    direct = fields.Boolean('Directo')
    bank_eco = fields.Boolean('Banco Economico (%)')
    initial_fee = fields.Float('Cuota Inicial', digits=dp.get_precision('Product Price'), default=0)
    deadline = fields.Char('Plazo de Pago')
    interest_annual = fields.Char(u'Interés Anual')
    monthly_fee = fields.Float('Cuota Mensual', digits=dp.get_precision('Product Price'), default=0)
    insurance = fields.Boolean('Solicitud de Seguro')
    checklist_ids = fields.One2many('crm.lead.checklist', 'lead_id', 'Accesorios Ofrecidos')
    discount = fields.Float('Descuento', digits=dp.get_precision('Product Price'))
    chief_sale = fields.Char('Jefe de Ventas')

    currency_id =  fields.Many2one('res.currency', 'Moneda', default=lambda self: self.env.user.company_id.currency_id)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(CrmLead, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange('product_id')
    def _onchnage_product_id(self):
        self.checklist_ids = False
        lines = []
        for l in self.product_id.checklist_line:
            lines.append([0,0, {'item_id': l.item_id.id, 'imp': l.imp}])
        self.checklist_ids = lines

class CrmLeadChecklist(models.Model):
    _name = "crm.lead.checklist"

    lead_id = fields.Many2one('crm.lead', 'Oportunidad')
    item_id = fields.Many2one("check.list.toyosa.items", 'Items')
    activo = fields.Boolean("Aplica")
    imp = fields.Boolean('Importado', default=False)
    price = fields.Float('Precio', default=0)
