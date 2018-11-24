##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models, _
import time


class poi_vehicle(models.Model):
    _name = 'poi.vehicle'
    _inherit = 'poi.vehicle'

    def _workshop_count(self):
        maintenance = self.env['workshop.order']
        for asset in self:
            self.workshop_count = maintenance.search_count([('asset_id', '=', asset.id)])

    def _workshop_prev_count(self):
        maintenance = self.env['workshop.order']
        for asset in self:
            self.workshop_prev_count = maintenance.search_count(
                [('asset_id', '=', asset.id), ('date_execution', '>=', time.strftime('%Y-%m-%d %H:%M:%S')),
                 ('state', 'not in', ('cancel', 'done'))])

    def _next_maintenance(self):
        maintenance = self.env['workshop.order']
        for asset in self:
            order_ids = maintenance.search(
                [('asset_id', '=', asset.id),
                 ('state', 'not in', ('done', 'cancel', 'invoiced', 'stop'))],
                limit=1, order='date_execution')
            if len(order_ids) > 0:
                self.maintenance_date = order_ids[0].date_execution

    workshop_count = fields.Integer(compute='_workshop_count', string='# Maintenance')
    workshop_prev_count = fields.Integer(compute='_workshop_prev_count', string='# Maintenance Preview')
    maintenance_date = fields.Date(compute='_next_maintenance', string='Maintenance Date')

    @api.multi
    def action_view_maintenance(self):
        return {
            'domain': "[('asset_id','in',[" + ','.join(map(str, self.ids)) + "])]",
            'name': _('Maintenance Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'workshop.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.multi
    def action_view_prev_maintenance(self):
        return {
            'domain': "[('asset_id','in',[" + ','.join(map(str, self.ids)) + "]),('date_execution', '>=', time.strftime('%Y-%m-%d %H:%M:%S')),('state', 'not in', ('cancel', 'done'))]",
            'name': _('Maintenance Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'workshop.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.multi
    def action_view_kilomentraje(self):
        dummy, view_id = self.env['ir.model.data'].get_object_reference('poi_workshop', 'workshop_kilometraje_order_tree_view')
        return {
            'name': _('Kilometraje'),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view_id,
            'domain': "[('asset_id','in',[" + ','.join(map(str, self.ids)) + "])]",
            'context': {'group_by': 'asset_id'},
            'res_model': 'workshop.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.multi
    def action_view_historial(self):
        return {
            'domain': "[('asset_id','in',[" + ','.join(map(str, self.ids)) + "])]",
            'name': _('Historial'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'poi.vehicle.history',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
