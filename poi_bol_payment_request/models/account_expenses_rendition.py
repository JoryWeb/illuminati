##############################################################################
#
#    Odoo Module
#    Copyright (C) 2015 Grover Menacho (<http://www.grovermenacho.com>).
#    Copyright (C) 2015 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Grover Menacho
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

from odoo import models, fields, api, _
# # FIXME: Descomentar y refactorizar segun el este acabado el libro de compras y ventas

# LCV_QUERY_INDIVIDUAL = """
# select *,(monto + descuento) as importe ,(monto + descuento - exento - ice) as subtotal_c,(monto + descuento - ice - exporta - exento) as subtotal_v,(ice + exento) as monto_nosujeto
# FROM
# (
#     select 'in' as case, '1' as spec,aeri.tipo_com,aeri.nit,coalesce(aeri.razon,'') as razon,cc_nro,(COALESCE(REGEXP_REPLACE(cc_nro, '[^0-9]+', '0', 'g'),'0'))::bigint as cc_nro_int,coalesce(imp_pol,'0') as imp_pol,cc_aut,to_char(cc_fecha,'DD/MM/YYYY') as cc_fecha,cc_fecha as date_invoice,Extract('year' from cc_fecha) as year_invoice,Extract('month' from cc_fecha) as month_invoice
#         ,round(monto,2) as monto,round(coalesce(ice,0),2) as ice,round(coalesce(exento,0),2) as exento, 0 as exporta,round(coalesce(descuento,0),2) as descuento,round(monto_neto,2) as monto_neto,round(monto_iva,2) as monto_iva,coalesce(cc_cod,'0') as cc_cod, 0 as cc_dos, '' as cc_dos_name
#         ,aer.state,coalesce(tipo_com,'1') as tipo_com_val,estado_fac,estado_fac as estado_fac_val,aer.company_id,aer.id as res_id,'account.expenses.rendition'::varchar as res_obj,aer.name as res_name,'Rendicion'::varchar as res_type,0 as shop_id
#         ,'' as origen_cc_fecha,NULL::DATE as origen_date_invoice,'0' as origen_cc_nro, '0' as origen_cc_aut, 0 as origen_monto, aeri.create_uid as user_id, aer.move_id as move_id
#     from account_expenses_rendition_invoice aeri
#         inner join account_expenses_rendition aer on aeri.rendition_id=aer.id
#         inner join account_expenses_rendition_invoice_taxes_rel it_rel on aeri.id=it_rel.rendition_invoice_id inner join account_tax at on it_rel.tax_id=at.id
#     where at.apply_lcv = True and aer.state='done'
#
# ) as lcv order by lcv.cc_nro_int,lcv.date_invoice
#             """


class AccountExpensesRenditionInvoice(models.Model):
    _inherit = 'account.expenses.rendition.invoice'

    # # FIXME: Descomentar y refactorizar segun el este acabado el libro de compras y ventas
    # def init(self, cr, select=False, mlc=False, mlr=False):
    #     #Al momento de iniciar el addon SOLO se crea una Vista SQL que contiene el query individual de este modulo unicamente. Esta vista no estara vinculada a este objeto. Sera incorporada a la vista general LCV desde el modulo poi_bol_base
    #     table = "poi_bol_lcv_report_rendition"
    #
    #     individual_query_to_exe = LCV_QUERY_INDIVIDUAL
    #
    #     cr.execute("""
    #
    #         DROP VIEW IF EXISTS %s CASCADE;
    #         CREATE VIEW %s as ((
    #         SELECT *
    #             FROM ((
    #                 %s
    #             )) as base
    #         ))""" % (table, table, individual_query_to_exe))

    @api.onchange('amount', 'taxes_ids', 'ice')
    def onchange_amount(self):
        # Ayuda a calcular los montos
        v = {}
        if self.amount:
            calc_neto = self.amount - (self.ice or 0.0)
            calc_iva = 0.0
            calc_exe = 0.0
            if self.taxes_ids:
                for tax in self.taxes_ids:
                    if tax.type_bol == 'iva':
                        temp_iva = tax.compute_all(calc_neto)['taxes'][0]['amount']
                        calc_iva += temp_iva
                    elif tax.amount_type == 'group':
                        tax_group = tax.compute_all(calc_neto)
                        for child in tax.children_tax_ids:
                            if child.type_bol == 'iva':
                                temp_iva = child.compute_all(calc_neto)['taxes'][0]['amount']
                                calc_iva += temp_iva
                            elif child.type_bol == 'exe':
                                calc_exe = child.compute_all(calc_neto)['taxes'][0]['amount']
                                calc_neto -= calc_exe

            self.monto_neto = calc_neto
            self.monto_iva = calc_iva
            self.exento = calc_exe

    amount = fields.Float('Amount')
    taxes_ids = fields.Many2many('account.tax', 'account_expenses_rendition_invoice_taxes_rel', 'rendition_invoice_id',
                                 'tax_id', 'Taxes', domain = [('type_tax_use', '=', 'purchase')])
    partner_id = fields.Many2one('res.partner', string='Proveedor', domain = [('supplier', '=', True)])
    nit = fields.Char('NIT', size=11, help="NIT o CI del cliente.")
    razon = fields.Char(u'Razón Social', size=124, help=u"Nombre o Razón Social para la Factura.")
    monto = fields.Float('Monto', digits=(16, 2), help="Monto de la Compra.", related='amount', store=True)
    monto_iva = fields.Float('IVA', digits=(16, 2))
    monto_neto = fields.Float('Neto', digits=(16, 2))
    tax_id = fields.Many2one('account.tax', 'Impuesto', domain = [('type_tax_use', '=', 'purchase')])
    cc_fecha = fields.Date('Fecha Factura', related='date_invoice', store=True)
    cc_nro = fields.Char('Nro. Factura', help=u"Número de factura.", related='invoice_number', store=True)
    cc_aut = fields.Char(u'Nro. Autorización', help=u"Número de autorización.")
    cc_cod = fields.Char(u'Código control', size=14,
                          help=u"Codigo de representación única para el SIN. Introducir manualmente para Compras.")
    # 'tipo_fac' a ser deprecado
    tipo_fac = fields.Selection(
        [('1', 'Compra'), ('2', 'Boleto BCP'), ('3', u'Importación'), ('4', 'Recibo de Alquiler'),
         ('5', u'Nota de débito proveedor'), ('6', u'Nota de crédito cliente'), ('7', 'Venta'),
         ('8', u'Nota de débito cliente'), ('9', u'Nota de crédito proveedor'), ('10', 'Sin Asignar')],
        'Tipo Factura', help=u"Tipificación de facturas según Impuestos Internos")
    tipo_com = fields.Selection(
        [('1', 'Mercado Interno'), ('2', 'Destino Exportaciones'), ('3', 'Interno y Exportaciones'),
         ('NA', 'No Aplica')], 'Tipo de Compra', help=u"Tipificación de facturas de Compra según Impuestos Internos", default="1")
    estado_fac = fields.Selection([('V', u'Válida'), ('A', 'Anulada'), ('E', 'Extraviada'), ('N', 'No Utilizada')],
                                   string='Estado Factura', default='V')
    ice = fields.Float('Importe ICE', digits=(16, 2))
    exento = fields.Float('Importe Exentos', digits=(16, 2))
    descuento = fields.Float('Descuentos obtenidos', digits=(16, 2),
                              help=u"Descuentos, Bonificaciones y Rebajas obtenidas. Es el descuento impositivo de factura que se hace visible en el Libro de Compras.")
    imp_pol = fields.Char(u'Nro. Poliza Import.', size=16,
                           help=u"Número de póliza de importaciÃ³n para Libro de compras")
    _sql_constraints = [
        ('check_nit', "CHECK (nit ~ '^[0-9\.]+$')",
         u'NIT sólo acepta valores numéricos y que no empiecen con cero!'),
        ('check_cc_aut', "CHECK (cc_aut ~ '^[0-9\.]+$')",
         u'Nro Autorización sólo acepta valores numéricos!'),
        ('check_cc_cod',
         "CHECK (cc_cod='' OR cc_cod ~ '[0-9A-F][0-9A-F][-][0-9A-F][0-9A-F][-][0-9A-F][0-9A-F][-][0-9A-F][0-9A-F]')",
         u'Formato de Codigo de control no valido! Debe tener la forma XX-XX-XX-XX (valores permitidos: 0-9 y A-F)'),
    ]

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.nit = (
                       self.partner_id.commercial_partner_id.nit != 0 and self.partner_id.commercial_partner_id.nit) or (
                       self.partner_id.commercial_partner_id.ci != 0 and self.partner_id.commercial_partner_id.ci) or ''
            self.razon = self.partner_id.commercial_partner_id.razon_invoice or self.partner_id.commercial_partner_id.razon or self.partner_id.commercial_partner_id.name or ''

    @api.multi
    def action_inverse_tax(self):
        self.env.context['active_ids'] = self.env.ids
        self.env.context['rendition_invoice_id'] = len(self.env.ids)>0 and self.env.ids[0] or False

        wizard_form = {
            'name': u"Cálculo precio inverso",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'poi_bol_rendition.tax_inverse.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return wizard_form
