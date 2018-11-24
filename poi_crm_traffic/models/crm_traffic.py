import logging
from odoo import models, fields, api, tools

class CrmTraffic(models.Model):
    _name = "crm.traffic"
    _description= "Trafico de Clientes"
    _inherit = ['mail.thread']


    name = fields.Char('Descripcion', default=lambda self: ('Nuevo'), readonly=True)
    partner_type_id = fields.Selection([
        ('new', 'Nuevo'),
        ('old', 'Antiguo'),
    ], "Tipo de Cliente", readonly=True, states={'draft':[('readonly',False)]},)
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen', default=lambda self:(self.env.user.shop_assigned and self.env.user.shop_assigned.id) or self.env['stock.warehouse'], readonly=True)
    reason_id = fields.Many2one('crm.traffic.reason', 'Motivo de Visita', readonly=True, states={'draft':[('readonly',False)]})
    # user_id = fields.Many2one('res.users', 'Vendedor Asignado(No usar)', default=lambda self:(self.env.user and self.env.user.id) or self.env['res.users'], readonly=True, states={'draft':[('readonly',False)]})
    user_id2 = fields.Many2one('res.users', 'Vendedor Asignado', readonly=True, states={'draft':[('readonly',False)]})
    date = fields.Datetime('Fecha y Hora', default=fields.Datetime.now(), readonly=True)
    tag_ids = fields.Many2many('crm.traffic.tag', 'traffic_tag_rel2',  'traffic_id', 'tag_id', string='Tags', readonly=True, states={'draft':[('readonly',False)]})
    lead_id = fields.Many2one('crm.lead', 'Iniciativas')
    lead_count = fields.Integer(string='# of Invoices', compute='_get_leads', readonly=True)
    lead_check = fields.Boolean('Iniciativa Creada', default=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Confirmado'),
    ], string="Estado", default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('crm.traffic') or 'Nuevo'
        traffic_id = super(CrmTraffic, self).create(vals)
        return traffic_id


    @api.multi
    def action_create_lead(self):
        lead_obj = self.env['crm.lead']
        lead_id = lead_obj.sudo().create({
            'name': self.name or self.create_date,
            'traffic_id': self.id,
            })
        self.lead_id = lead_id.id
        self.lead_check = True
        if self.user_id2:
            lead_id.user_id = self.user_id2.id
            lead_id.warehouse_id = (self.user_id2.shop_assigned and self.user_id2.shop_assigned.id) or False
        return {
            'name': "Iniciativas",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'context': {},
            'domain': [('traffic_id', '=', self.id)],
        }

    @api.multi
    def action_confirm(self):
        self.state = 'done'

    @api.onchange("reason_id")
    def _onchange_field(self):
        vals = {}


        vals['domain'] = {
            "tag_ids": [("id", "in", self.reason_id.tag_ids.ids)],
        }

        return vals


    @api.multi
    def _get_leads(self):
        for s in self:
            s.lead_count = self.env['crm.lead'].sudo().search_count([('traffic_id', '=', s.id)])

    @api.multi
    def action_view_leads(self):
        lead_id = self.mapped('lead_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('crm.crm_lead_all_leads')
        list_view_id = imd.xmlid_to_res_id('crm.crm_case_tree_view_leads')
        form_view_id = imd.xmlid_to_res_id('crm.crm_case_form_view_leads')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(lead_id) > 1:
            result['domain'] = "[('id','in',%s)]" % lead_id.ids
        elif len(lead_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = lead_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


class CustomerTraficTag(models.Model):
    _name = 'crm.traffic.tag'
    _description = 'Products Tag'

    name = fields.Char('Nombre', required=True)
    color = fields.Integer('Color Index')


class CustomerTraficReason(models.Model):
    _name = 'crm.traffic.reason'
    _description = 'Motivos de Visita'

    name = fields.Char('Nombre', required=True)
    report = fields.Boolean('Aparece en Reporte', help="Determina si el Motivo de Visita Aparece en el Reporte de Trafico de Clientes", default=False)
    type = fields.Selection([
        ('new', 'Nuevo'),
        ('old', 'Antiguo'),
        ('both', 'Ambos'),
    ], 'Tipo', default="both")

    tag_ids = fields.Many2many('crm.traffic.tag', 'traffic_tag_rel1',  'traffic_id', 'tag_id', string='Tags')
