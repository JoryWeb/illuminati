# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class WebEnvironmentRibbonBackend(models.Model):

    _name = 'web.environment.ribbon.backend'
    _description = 'Web Environment Ribbon Backend'

    @api.model
    def _prepare_ribbon_name(self):
        db_name = self.env.cr.dbname
        name = self.env['ir.config_parameter'].sudo().get_param('ribbon.name')
        if name:
            name = name.format(db_name=db_name)
        return name

    @api.model
    def get_environment_ribbon(self):
        """
        This method returns the ribbon data from ir config parameters
        :return: dictionary
        """
        ir_config_model = self.env['ir.config_parameter']
        production_uuid = ir_config_model.sudo().get_param('database.production.uuid')
        if production_uuid == '0':
            return {'name': 'False'}
        database_uuid = ir_config_model.sudo().get_param('database.uuid')
        if database_uuid == production_uuid:
            return {'name': 'False'}
        name = self._prepare_ribbon_name()
        return {
            'name': name,
            'color': ir_config_model.sudo().get_param('ribbon.color'),
            'background_color': ir_config_model.sudo().get_param(
                'ribbon.background.color'),
        }
