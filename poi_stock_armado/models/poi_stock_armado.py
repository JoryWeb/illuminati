# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


from openerp import models, fields, exceptions, api, _
# NOTE: In v9, this should be `from openerp.tools.misc import formatLang`


class PoiStockArmado(models.Model):
    _name = "poi.stock.armado"
    _description = "Purchase landed costs distribution"
    _order = 'name desc'

    name = fields.Char(string='Solicitud', required=True,
                       select=True, default='/')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'poi.stock.armado')))
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('confirmed', 'Confirmado'),
         ('done', 'Cerrado'),
         ('cancel', 'Cancelado')], string='Status', readonly=True,
        default='draft')
    user_id = fields.Many2one('res.users', string='Solicitante', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    date = fields.Date(string='Date', required=True, readonly=True, select=True,
                       states={'draft': [('readonly', False)]},
                       default=fields.Date.context_today)

    picking_id = fields.Many2one("stock.picking",string=u'Ingreso al Almacén')
    note = fields.Text("Notas")
    chasis_lines = fields.One2many(
        comodel_name='poi.stock.armado.line', ondelete="cascade",
        inverse_name='chasis', string='Chasis Motocicletas Disponibles')


    @api.multi
    def unlink(self):
        for c in self:
            if c.state not in ('draft', 'calculated'):
                raise exceptions.Warning(
                    _("You can't delete a confirmed cost distribution"))
        return super(PoiStockArmado, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'poi.stock.armado')
        return super(PoiStockArmado, self).create(vals)

    @api.onchange('picking_id')
    def onchange_pickign_id(self):
        lines = self.chasis_lines.browse([])
        if self.picking_id:
            for move in self.picking_id.move_lines:
                for quant in move.quant_ids:
                    if quant.location_id.usage == 'internal':
                        value_line = {
                            'lot_id': quant.lot_id.id,
                            'location_id': quant.location_id.id,
                            'product_qty': quant.qty,
                            'armado': quant.lot_id.mot_desarmada,
                        }
                        lines += lines.new(value_line)
                        self.chasis_lines = lines

    @api.multi
    def action_select_all(self):
        for lines in self.chasis_lines:
            lines.armado = True

    @api.multi
    def action_unselect_all(self):
        for lines in self.chasis_lines:
            lines.armado = False

    @api.multi
    def action_calculate(self):
        for armado in self:
            armado.state = 'confirmed'
        return True


    @api.one
    def action_done(self):
        for armado in self:
            for lines in armado.chasis_lines:
                lines.lot_id.mot_desarmada = lines.armado
            armado.state = 'done'
        self.state = 'done'

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.one
    def action_cancel(self):
        for armado in self:
            for lines in armado.chasis_lines:
                lines.lot_id.mot_desarmada = False
                lines.armado = False
            armado.state = 'draft'

class PoiStockArmadoLine(models.Model):
    _name = "poi.stock.armado.line"
    _description = "Lineas de Armado de Motocicletas"

    chasis = fields.Many2one(
        comodel_name='poi.stock.armado', string='Lineas de Armado',
        ondelete='cascade', required=True)
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot', string='Chasis', ondelete="restrict",
        required=True)
    location_id = fields.Many2one(
        comodel_name='stock.location', string='Ubicaciones')
    product_qty = fields.Float(string='Quantity')
    armado = fields.Boolean("Armado")
