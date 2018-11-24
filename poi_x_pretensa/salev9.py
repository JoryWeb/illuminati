
from openerp import fields, models, api, _
from openerp.exceptions import Warning

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_total_metric(self):
        res = {}
        for order in self:
            # res[order.id] = {}
            sum_metric = 0.0
            sum_metric_m2 = 0.0
            sum_metric_m3 = 0.0
            sum_weight = 0.0
            top_uom = ''
            for line in order.order_line:
                tot_dim = line.total_dimension or 0.0
                metric_type = line.product_dimension.metric_type
                if metric_type == 'lineal':
                    sum_metric += tot_dim
                    sum_metric_m2 += 0.0
                    sum_metric_m3 += 0.0
                else:
                    if metric_type == 'area':
                        sum_metric_m2 += tot_dim
                        sum_metric += 0.0
                        sum_metric_m3 += 0.0
                    else:
                        if metric_type == 'volume':
                            sum_metric_m3 += tot_dim
                            sum_metric_m2 += 0.0
                            sum_metric += 0.0
                        else:
                            sum_metric += 0.0
                            sum_metric_m2 += 0.0
                            sum_metric_m3 += 0.0
                sum_weight += (
                                  line.product_id and line.product_id.weight or 0.0) * tot_dim  # * (line.product_uom_qty or 0.0)
                top_uom = line.product_dimension and line.product_dimension.uom_id.name or ''

            order.total_metric = str(sum_metric) + ' ' + top_uom

            order.total_metric_m2 = str(sum_metric_m2) + ' ' + top_uom + u"²"

            order.total_metric_m3 = str(sum_metric_m3) + ' ' + top_uom + u"³"

            order.total_weight = sum_weight / 46


    state = fields.Selection([
        ('draft', 'Cotización'),
        ('sent', 'Cotización Enviada'),
        ('sale', 'Pedido de Venta'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado'),
        ], string='Estado', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    invoice_status = fields.Selection([
        ('upselling', 'Oportunidad de venta'),
        ('invoiced', 'Totalmente Facturado'),
        ('to invoice', 'Para facturar'),
        ('no', 'Nada Facturado')
    ], string='Estado Facturación', compute='_get_invoiced', store=True, readonly=True, default='no')

    picking_policy = fields.Selection([
        ('direct', u'Entregar cada producto cuando esté disponible'),
        ('one', u'Entregar todos los productos a la vez')],
        string=u'Política de entrega', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    user_id = fields.Many2one('res.users', string='Responsable', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    total_metric = fields.Char(string=u'Total métrica (m)', compute='_get_total_metric', readonly=True)
    total_metric_m2 = fields.Char(compute='_get_total_metric', string=u'Total métrica (m²)', readonly=True)
    total_metric_m3 = fields.Char(compute='_get_total_metric', string=u'Total métrica (m³)', readonly=True)
    total_weight = fields.Float(compute='_get_total_metric', string=u'Total quintales', readonly=True)



    @api.onchange('pricelist_id')
    def change_shop_id(self):
        ids_d = sorted(self.user_id.shop_option_ids.ids + [self.user_id.shop_assigned.id] + self.user_id.shop_ids.ids)
        # Actualizar domain dinamicamente para no tener que aplicar restricción de almacenes
        res = {}
        res.setdefault('domain', {})
        res['domain'] = {'warehouse_id': [('id', 'in', ids_d)]}
        return res

    @api.onchange('warehouse_id')
    def change_warehouse_id(self):
        for sale in self:
            sale.project_id = sale.warehouse_id.analytic_account_id.id,
            sale.pricelist_id = sale.warehouse_id.pricelist_id.id
    #
    # @api.onchange('warehouse_alt_id')
    # def change_warehouse_alt(self):
    #     self.warehouse_id = self.warehouse_alt_id.id

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
                'warehouse_id': self.env.user.shop_assigned.id,
                'vendedor': self._uid,
                'user_id': self._uid,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        if self.warehouse_id:
            values = {
                'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'vendedor': self._uid,
                'user_id': self._uid,
            }
        else:
            values = {
                'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
                'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'vendedor': self._uid,
                'user_id': self._uid,
            }
        if self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.user_id:
            values['user_id'] = self.partner_id.user_id.id
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

    @api.multi
    def action_confirm(self):
        if not self.partner_id.nit or not self.partner_id.nit:
            raise Warning(_('El cliente seleccionado no tiene NIT o CI'))
        group = self.env.user.has_group('poi_warehouse_sale.group_sale_salesman_shop_leads')
        if not group:
            raise Warning(_('Usted no es un usuario autorizado'))
        res = super(SaleOrder, self).action_confirm()
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        # Desahabilitado no aplica al proceso general de pretensa la alerta
        return {}