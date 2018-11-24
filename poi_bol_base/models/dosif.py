##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
from datetime import datetime

from openerp import models, fields, api, _
from openerp import tools
from openerp.exceptions import UserError
from openerp.osv import expression


def check_mod_installed(cr, mod_name):
    cr.execute("SELECT state from ir_module_module where name = %s ", (mod_name,))
    rs = cr.fetchone()
    mod_state = rs and rs[0] or False

    if not mod_state:
        return False
    if mod_state == "installed":
        return True
    else:
        return False


class CcDosif(models.Model):
    _name = 'poi_bol_base.cc_dosif'
    _description = 'Dosificacion Facturas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre Serie', size=64, select=1, help=u"Serie de dosificación.")
    nro_orden = fields.Char(u'Número de autorización', size=15, digits=(15, 0), required=True,
                            help=u"Número de autorización provisto por el SIN.")  # Integer insuficiente para soportar el largo de este campo. Manejado como Char y restringido via Widget y via SQL Constraint.
    rango_ini = fields.Integer('Nro. de rango inicial', help="Nro. de rango inicial autorizado por el SIN.")
    rango_fin = fields.Integer('Nro. de rango final', help="Nro. de rango final autorizado por el SIN.")
    next_nro = fields.Integer(u'Siguiente número de factura', readonly=1, copy=False,
                              help="Campo interno para la asignación de numeración sin huecos.")
    fecha_ini = fields.Date('Fecha inicial', required=True, help="Fecha inicial autorizada por el SIN.")
    fecha_fin = fields.Date('Fecha final', required=True, help="Fecha final autorizada por el SIN.")
    activa = fields.Boolean('Activa', help=u"Dosificación activa para facturación.")
    auto_num = fields.Boolean('Auto numera', help=u"Numeración automatica al crear facturas.")
    warehouse_id = fields.Many2one('stock.warehouse', 'Sucursal (Almacen)')
    company_id = fields.Many2one('res.company', string='Company', related='warehouse_id.company_id', readonly=True)
    user_ids = fields.One2many('poi_bol_base.cc_dosif.users', 'dosif_id', 'Usuarios Autorizados')
    applies = fields.Selection([('out_invoice', 'Factura'), ('out_refund', u'Nota de crédito')], string="Aplica",
                               default='out_invoice')
    require_taxes = fields.Boolean(string='Requiere Impuestos', default=True)
    activity_id = fields.Many2one('company.activity', 'Actividad económica')
    multi_activity = fields.Boolean(related='company_id.multi_activity', string="Multiples actividades?", readonly=True)

    # @api.model_cr
    # def init(self):
    #    #NBA20120222. Fields definidos como integer_big no se muestran en form. Workaround para permitir bigint en cada instalación/actualización
    #    cr = self._cr
    #    cr.execute("ALTER TABLE poi_bol_base_cc_dosif ALTER nro_orden TYPE bigint USING nro_orden::bigint")
    _sql_constraints = [
        ('check_nro_orden', "CHECK (nro_orden ~ '^[0-9\.]+$')",
         u'Nro Autorización sólo acepta valores numéricos!'),
    ]

    @api.multi
    def get_valid_dosif(self):
        res = []
        users_allowed = self.env['poi_bol_base.cc_dosif.users']
        allowed_ids = users_allowed.search([('user_id', '=', self.env.uid)])
        res = [x.dosif_id.id for x in allowed_ids]
        return res

    @api.v7
    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        if not context:
            context = {}
        if not context.get('display_all'):
            valid_ids = self.get_valid_dosif(cr, user)

            new_ids = []

            for id in ids:
                if id in valid_ids:
                    new_ids.append(id)

            res = super(CcDosif, self).read(cr, user, new_ids, fields=fields, context=context, load=load)
        else:
            res = super(CcDosif, self).read(cr, user, ids, fields=fields, context=context, load=load)
        return res

    @api.v8
    def read(self, fields=None, load='_classic_read'):
        if not self.env.context.get('display_all'):
            valid_ids = self.get_valid_dosif()
            new_ids = []
            if self.ids:
                for id in self.ids:
                    if id in valid_ids:
                        new_ids.append(id)

            dosif_ids = self.search([('id', 'in', new_ids)])
            if dosif_ids:
                res = super(CcDosif, dosif_ids).read(fields=fields, load=load)
            else:
                res = super(CcDosif, self).read(fields=fields, load=load)
        else:
            res = super(CcDosif, self).read(fields=fields, load=load)
        return res

    def search(self, args, offset=0, limit=None, order=None, count=False):
        def check_if_id(arg):
            for argument in arg:
                if type(argument) is tuple:
                    if argument[0] == 'id':
                        return True
            else:
                return False

        if not self.env.context.get('display_all') and not check_if_id(args):
            dosif_ids = self.get_valid_dosif()
            args = expression.AND([args] + [[('id', 'in', dosif_ids)]])
        return super(CcDosif, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            ids = self.search([('name', operator, name)] + args, limit=limit)
        else:
            ids = self.search(args, limit=limit)
        return ids.name_get()

    @api.model
    def set_unique_numbering(self, set_id, dosif_id, case):
        # Simultaneamente busca y escribe la nueración correspondiente. Actualmente soporta sólo Invoice y PosOrder

        # This function only works when set_id is only a record
        if not isinstance(set_id, (int)):
            raise UserError(u'Asignación de numeración por Dosificación no aplica para múltiples documentos.')

        # Just in case that there is no dosif
        if not dosif_id or dosif_id == 0:
            raise UserError(u'No se especifico una Dosificación para la Asignación de numeración.')
        dosif = self.sudo().browse(dosif_id)

        # This is going to appear in case that a dosif doesn't exist
        if not dosif:
            raise UserError(u'No existe esta Serie de dosificación.')

        # This is going to check is dosif is active
        if not dosif.activa:
            raise UserError(u'Esta Serie de dosificación esta inactiva.')

        # First number or 1
        init_nro = dosif.rango_ini or 1

        # De manera atómica, leer y Actualizar la siguiente numeración para evitar errores de concurrencia
        cr = self.env.cr
        next_nro = dosif.next_nro
        if not next_nro or next_nro == 0:
            # Si es la primera vez que se usa una Dosificación, utilizar la numeración inicial
            next_nro = init_nro
            cr.execute("SELECT next_nro FROM poi_bol_base_cc_dosif WHERE id=%s FOR UPDATE NOWAIT", (dosif.id,))
            cr.execute("UPDATE poi_bol_base_cc_dosif SET next_nro=%s WHERE id=%s ", (init_nro + 1, dosif.id,))
        else:
            cr.execute("SELECT next_nro FROM poi_bol_base_cc_dosif WHERE id=%s FOR UPDATE NOWAIT", (dosif.id,))
            cr.execute("UPDATE poi_bol_base_cc_dosif SET next_nro=next_nro+1 WHERE id=%s ", (dosif.id,))
        self.invalidate_cache(['next_nro'], [dosif.id])

        if case == 'invoice':
            cr.execute("UPDATE account_invoice SET cc_nro = %s where id = %s RETURNING cc_nro", (next_nro, set_id,))
            self.env['account.invoice'].invalidate_cache(['cc_nro'], [set_id])
        elif case == 'pos':
            cr.execute("UPDATE pos_order SET cc_nro = %s where id = %s RETURNING cc_nro", (next_nro, set_id,))
            self.env['pos.order'].invalidate_cache(['cc_nro'], [set_id])
        else:
            raise UserError(u'Asignación de numeración por Dosificación no soportada para este Caso.')
        rs = cr.fetchone()
        check_nro = rs and rs[0] or False
        if int(check_nro) != int(next_nro):
            raise UserError(u'El número de factura asignado no es correcto (Nr. %s).' % str(check_nro))

        # TESTING IF PREV NUMBER EXISTS (UNLESS FIRST NUMBER OF DOSIFICATION)
        if next_nro and int(next_nro) != int(init_nro):
            prev_nro = int(next_nro) - 1
            if check_mod_installed(self.env.cr, 'poi_pos_bol'):
                prev_query = """
                select cast(cc_nro as int) as uni_nro
                from account_invoice
                where 
                  cc_dos = %s
                  and company_id = %s
                  and cc_nro IN (%s,%s) 
                  and type IN ('out_invoice','out_refund')
                  and estado_fac in ('A','V')
                  and id != %s 
                UNION
                select cast(cc_nro as int) as uni_nro
                from pos_order
                where state not in ('cancel')
                  and cc_dos = %s
                  and cc_nro IN (%s,%s) 
                  and estado_fac in ('A','V')
                """ % (
                str(dosif.id), str(dosif.company_id.id), str(prev_nro), str(next_nro), str(set_id), str(dosif.id),
                str(prev_nro), str(next_nro))
            else:
                prev_query = """
                select cast(cc_nro as int) as uni_nro
                from account_invoice
                where 
                  cc_dos = %s
                  and company_id = %s
                  and cc_nro IN (%s,%s) 
                  and type IN ('out_invoice','out_refund')
                  and estado_fac in ('A','V')
                  and id != %s 
                """ % (str(dosif.id), str(dosif.company_id.id), str(prev_nro), str(next_nro), str(set_id))

            self.env.cr.execute(prev_query)
            prev_found = False
            check = self.env.cr.fetchall()
            for reg in check:
                if reg[0] == prev_nro:
                    prev_found = True
                if reg[0] == next_nro:
                    raise UserError(
                        u'Se ha encontrado ya una factura con el mismo número (Nr. %s). Notifique al Administrador para regularizar.' % str(
                            next_nro))
            if not prev_found:
                raise UserError(
                    u'No se ha encontrado la factura previa (Nr. %s). Notifique al Administrador para regularizar.' % str(
                        prev_nro))

        if int(next_nro) > int(dosif.rango_fin):
            raise UserError(
                u'El rango superior de la Dosificación seleccionada ya ha sido alcanzado (Nr. %s). Debe seleccionar una nueva Dosificación.' % str(
                    dosif.rango_fin))
        elif int(next_nro) == int(dosif.rango_fin):
            pass  # ToDo. Enviar correo?

        # Logging dosif
        log_sql = """ INSERT INTO cc_dosif_log (cc_aut,cc_nro,user_id,date_request,res_case,res_id)
        VALUES ('%s', '%s', '%s', '%s', '%s', %s)
        """ % (
        dosif.nro_orden, next_nro, self._uid, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), case, str(set_id))
        try:
            self.env.cr.execute(log_sql)
        except:
            raise UserError(
                _("There is another invoice with '%s' as authorization number and '%s' as invoice number!") % (
                dosif.nro_orden, next_nro))

        # Retornar el respectivo Nro tal como se actualizó en la base de datos
        return int(next_nro)

    # ToDo: Reestablcer numeración - 1 cuando la factura última se marca como NO APLICA!!!!!


class CcDosifUsers(models.Model):
    _name = 'poi_bol_base.cc_dosif.users'

    dosif_id = fields.Many2one('poi_bol_base.cc_dosif', u'Dosificación', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', 'Usuario Autorizado', required=True)
    user_default = fields.Boolean('Por defecto', help=u"Esta dosificación se usara por defecto para este usuario.")


class CcDosifLog(models.Model):
    _name = 'cc.dosif.log'
    _log_access = False

    cc_nro = fields.Char(string='Nro. Factura')
    cc_aut = fields.Char(string='Nro. Autorizacion')
    user_id = fields.Many2one('res.users', string='User')
    date_request = fields.Datetime(string='Date Request')
    res_case = fields.Char(string='Case')
    res_id = fields.Integer('Case id')

    # ToDo: Enable this constraint. Is failing all the time
    _sql_constraints = [
        ('valid_cc_nro', 'unique(cc_nro, cc_aut, res_id)',
         'Number MUST BE UNIQUE!'),
    ]

    # ToDo: Still pending
    @api.cr_uid
    def delete_log(self, cc_nro, cc_aut):
        log_ids = self.search(['cc_nro', '=', cc_nro], ['cc_aut', '=', cc_aut])
        self.delete(log_ids)
        return True
