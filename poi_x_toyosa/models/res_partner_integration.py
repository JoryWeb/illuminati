from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    user_cod_barras = fields.Char(string='Usuario código barras')
    user_cod_localidad = fields.Char(string='Codigo Localidad')
    user_cod_cargo = fields.Char(string='Codigo Cargo')

    @api.multi
    def LeerUsuarios(self):
        user_list = []
        for user in self.env['res.users'].search([('active', '=', True)]):
            user = {
                'id': user.id,
                'user_cod_barras': user.partner_id.id,
                'password_crypt': user.password_crypt,
                'name': user.partner_id.name,
                'login': user.login,
                'cod_barras': user.partner_id.user_cod_barras or '',
                'cod_localidad': user.partner_id.user_cod_localidad or '',
                'cod_cargo': user.user_cod_cargo or '',
                'cod_sucursal': user.shop_assigned.name or '',
                'activo': user.active,
                'departamento': user.partner_id.state_id.name or '',
            }
            user_list.append(user)

        return user_list
