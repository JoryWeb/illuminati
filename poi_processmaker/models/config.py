# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _


class PmConfig(models.TransientModel):
    _name = 'pm.config.settings'
    _inherit = 'res.config.settings'

    pm_host = fields.Char('Host', help="The URL where Processmaker is hosted, including protocol, IP and Port (i.e. http://192.168.0.1:8080)")
    pm_token = fields.Char('Auth Token', help="Authorization token for API requests, as generated in http://[PM_IP]:8080/sysworkflow/en/neoclassic/oauth2/applications")
    pm_secret = fields.Char('Auth Secret', help="Authorization secret for API requests, as generated in http://[PM_IP]:8080/sysworkflow/en/neoclassic/oauth2/applications")
    pm_plugin = fields.Binary('PM Plugin for Odoo', readonly=True, help="Download this Plugin and deploy it to Processmaker. This will provide additional functionality on PM side.")   # .../processmaker-3.2.1-0/apps/processmaker/htdocs/workflow/engine/plugins
    pm_skin = fields.Binary('PM Skin for Odoo', readonly=True, help="Download this Skin and deploy it to Processmaker. This will provide a better look when viewing from within Odoo.")     # .../processmaker-3.2.1-0/apps/processmaker/htdocs/workflow/engine/skinEngine

    @api.model
    def get_pm_host(self, fields):
        pm_host = False
        if 'pm_host' in fields:
            pm_host = self.env['ir.config_parameter'].sudo().get_param(
                'poi_processmaker.pm_host')
        return {
            'pm_host': pm_host
        }

    @api.multi
    def set_pm_host(self):
        for wizard in self:
            self.env['ir.config_parameter'].sudo().set_param('poi_processmaker.pm_host', wizard.pm_host)

    @api.model
    def get_pm_token(self, fields):

        pm_token = self.env['ir.config_parameter'].sudo().get_param('poi_processmaker.pm_token')
        return {
            'pm_token': pm_token
        }

    @api.multi
    def set_pm_token(self):
        for wizard in self:
            self.env['ir.config_parameter'].sudo().set_param('poi_processmaker.pm_token', wizard.pm_token)

    @api.multi
    def get_pm_secret(self):

        pm_secret = self.env['ir.config_parameter'].sudo().get_param('poi_processmaker.pm_secret')
        return {
            'pm_secret': pm_secret
        }

    @api.multi
    def set_pm_secret(self):
        for wizard in self:
            self.env['ir.config_parameter'].sudo().set_param('poi_processmaker.pm_secret', wizard.pm_secret)
