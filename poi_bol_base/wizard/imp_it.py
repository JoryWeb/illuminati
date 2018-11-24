#!/usr/bin/env python
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp.osv import fields, osv

import time
from openerp.tools.translate import _

class imp_it(osv.TransientModel):

    _name = "poi_bol_base.imp_it"
    _description = "Impuesto IT"
    
    _columns = {
       'date_from': fields.date('Desde Fecha', required=True),
       'date_to': fields.date('Hasta Fecha', required=True),
       'tax_id': fields.many2one('account.tax', 'Impuesto', required=True, help="Define la tasa a usar y las cuentas con las que se genera el asiento."),
       'state':fields.selection([('init','init'),('warning','warning'), ('done','done')], 'state'),
       'prev_move_id': fields.many2one('account.move', 'Asiento Anterior', help="Asiento que usa las mismas cuentas. Revisarlo antes de confirmar!"),
       'mode': fields.selection([('account','Global'),('analytic',u'Por Cuenta Analítica')], string="Nivel detalle", help="Especifica el nivel de detalle del cálculo del impuesto. Puede calcular un solo total 'Global', o puede generar el asiento desglosando subtotales 'Por Cuenta Analítica'"),
       'tocheck_analytic': fields.boolean('Ctas. Analiticas', help='Seleccione esta opcion si desea generar los asientos con cuentas analiticas'),
       'tocheck_account': fields.boolean('Ctas. Globales', help='Seleccione esta opcion si desea generar los asientos con cuentas generales'),
    }
    _defaults = {  
        'state': 'init',
        'mode': 'account',
    }

    def onchange_date_from(self, cr, uid, ids, date_from, tax_id,context=None):

        if date_from:
            last_id = False
            state = "init"

            tax = self.pool.get('account.tax').browse(cr, uid, tax_id, context=context)
            if not tax.account_collected_id:
                return {'value':{'date_from':False}, 'warning': {'title': u'Error de Configuración', 'message': u'No se ha configurado la cuenta Impuestos de facturas del Impuesto seleccionado!'}}
            acc_cred = tax.account_collected_id.id
            cr.execute('select max(ml.date),m.id as last_date from account_move_line ml inner join account_move m on ml.move_id=m.id ' \
                           'where tax_amount > 0 and credit > 0 and ml.state = %s and account_id = %s and account_tax_id = %s group by m.id', ('valid',acc_cred,tax_id,))
            res = cr.fetchone()
            last_date = res and res[0] or None
            if last_date:
                if int(last_date.replace('-','')) >= int(date_from.replace('-','')):
                    last_id = res and res[1] or ''
                    state = "warning"

            return {'value':{'prev_move_id':last_id, 'state': state}}

    def action_generate(self, cr, uid, ids, context=None):

        if context is None:
            context={}

        for data in  self.read(cr, uid, ids, context=context):
            tax_id = data['tax_id'][0]
            state = data['state']
            from_date = data['date_from']
            to_date = data['date_to']
            mode = data['mode']

            tax = self.pool.get('account.tax').browse(cr, uid, tax_id, context=context)
            if not tax.journal_id:
                raise osv.except_osv(_(u'Error de Configuración'), _('No se ha configurado un Diario contable para el Impuesto seleccionado!'))
            if not tax.account_collected_id:
                raise osv.except_osv(_(u'Error de Configuración'), _('No se ha configurado la cuenta Impuestos de facturas del Impuesto seleccionado!'))
            if not tax.account_counter_id:
                raise osv.except_osv(_(u'Error de Configuración'), _('No se ha configurado la Contra cuenta para el Impuesto seleccionado!'))
            acc_cred = tax.account_collected_id.id
            acc_deb = tax.account_counter_id.id
            app_tax_id = tax.apply_tax_id and tax.apply_tax_id.id
            perc = tax.amount

            if int(from_date.replace('-','')) > int(to_date.replace('-','')):
                raise osv.except_osv(_('Error !'), _('La fecha Desde es mayor que la fecha Hasta!!'))
            if tax.type != 'percent':
                raise osv.except_osv(_('Error !'), _("El Impuesto seleccionado no aplica. Este proceso sólo funciona con Impuestos de tipo 'Porcentaje'"))


            if mode == 'account':

                cr_query = """select sum(il.price_subtotal_with_tax)
                        from account_invoice_line il inner join account_account aa on il.account_id = aa.id
                            inner join account_account_type at on aa.user_type = at.id
                            inner join account_invoice inv on il.invoice_id = inv.id
                            inner join account_move mv on mv.id = inv.move_id
                            inner join account_invoice_line_tax ilt on ilt.invoice_line_id = il.id
                            left join account_tax atx on ilt.tax_id=atx.id
                        where mv.state = %s
                            and mv.date between %s and %s
                            and inv.type='out_invoice'
                            """
                if app_tax_id:
                    cr_query = cr_query + " and ilt.tax_id = " + str(app_tax_id)

                cr.execute(cr_query, ('posted',from_date,to_date,))
                res = cr.fetchone()

                cr_query2 = """select sum(il.price_subtotal_with_tax)
                        from account_invoice_line il inner join account_account aa on il.account_id = aa.id
                            inner join account_account_type at on aa.user_type = at.id
                            inner join account_invoice inv on il.invoice_id = inv.id
                            inner join account_move mv on mv.id = inv.move_id
                            inner join account_invoice_line_tax ilt on ilt.invoice_line_id = il.id
                            left join account_tax atx on ilt.tax_id=atx.id
                        where  mv.state = %s
                            and mv.date between %s and %s
                            and inv.type='out_refund'
                            """
                if app_tax_id:
                    cr_query2 = cr_query2 + " and ilt.tax_id = " + str(app_tax_id)

                cr.execute(cr_query2, ('posted',from_date,to_date,))
                res2 = cr.fetchone()

                sum_refund = res2 and res2[0] or 0.0
                sum_income = res and res[0] or 0.0

                sum_income = sum_income-sum_refund

                je_amount = sum_income * perc
                if je_amount > 0.0:
                    account_move_pool = self.pool.get('account.move')
                    account_move_line_pool = self.pool.get('account.move.line')
                    # ToDo: #FIX9: period_id ya no existe!
                    period_id = self.pool.get('account.period').find(cr, uid, to_date, context=context)[0]
                    journal = tax.journal_id
                    move_ins = {
                        "name": 'Registro Impuesto '+tax.description ,
                        "journal_id": journal.id,
                        "date": to_date,
                        "period_id": period_id,
                        }
                    je_id = account_move_pool.create(cr,uid,move_ins)

                    move_line_ins = {
                        "move_id": je_id,
                        "account_id": acc_deb,
                        "debit": je_amount,
                        "credit": 0,
                        "date": to_date,
                        "name": 'Gasto Impuesto '+tax.description,
                        "tax_amount": je_amount,
                        "journal_id": journal.id,
                        "period_id": period_id,
                        }
                    account_move_line_pool.create(cr,uid,move_line_ins)

                    move_line_ins = {
                        "move_id": je_id,
                        "account_id": acc_cred,
                        "debit": 0,
                        "date": to_date,
                        "credit": je_amount,
                        "name": 'Impuesto '+tax.description+' por pagar',
                        "tax_amount": je_amount,
                        "journal_id": journal.id,
                        "period_id": period_id,
                        }
                    account_move_line_pool.create(cr,uid,move_line_ins)

                    if journal.entry_posted:
                        account_move_pool.post(cr, uid, [je_id], context=context)
                    else:
                        self.log(cr, uid, ids, "El asiento generado esta en borrador y debe ser confirmado.")

                else:
                    self.log(cr, uid, ids, "La suma de Ingresos por la tasa de impuesto es cero. No se generó ningún asiento.")
                    raise osv.except_osv((u'Advertencia'), (u'El proceso no ha detectado montos relevantes a este Impuesto y no ha generado ningún Asiento. Proceda a cancelar el Asistente'))
                    return {'view_mode' : 'tree,form','type': 'ir.actions.act_window_close'}
            elif mode == 'analytic':
                #Si desglosa por cuenta analítica
                cr_query = """select sum(tot_inv.total), tot_inv.id
                            from
                            ((
                                select  sum(il.price_subtotal_with_tax) as total, move_analytic.analytic_id as id
                                from account_invoice_line il inner join account_account aa on il.account_id = aa.id
                                    inner join account_account_type at on aa.user_type = at.id
                                    inner join account_invoice inv on il.invoice_id = inv.id
                                    inner join account_move mv on mv.id = inv.move_id
                                    inner join account_invoice_line_tax ilt on ilt.invoice_line_id = il.id
                                    left join account_tax atx on ilt.tax_id=atx.id
                                    left join (
                                        select aml.move_id, max(aaa.id) as analytic_id
                                        from account_move_line aml
                                        left join account_analytic_line aal
                                        ON aal.move_id = aml.id
                                        left join account_analytic_account aaa
                                        on aal.account_id = aaa.id
                                        GROUP BY aml.move_id
                                    ) as move_analytic on move_analytic.move_id=mv.id
                                where  mv.state= %s and atx.apply_lcv = True
                                    and mv.date between %s and %s
                                    and inv.type='out_invoice'
                                    """
                if app_tax_id:
                    cr_query = cr_query + " and ilt.tax_id = " + str(app_tax_id)
                cr_query = cr_query + """
                                    GROUP BY move_analytic.analytic_id) UNION
                                    (
                                select  sum(il.price_subtotal_with_tax) * (-1) as total, move_analytic.analytic_id as id
                                from account_invoice_line il inner join account_account aa on il.account_id = aa.id
                                    inner join account_account_type at on aa.user_type = at.id
                                    inner join account_invoice inv on il.invoice_id = inv.id
                                    inner join account_move mv on mv.id = inv.move_id
                                    inner join account_invoice_line_tax ilt on ilt.invoice_line_id = il.id
                                    left join account_tax atx on ilt.tax_id=atx.id
                                    left join (
                                        select aml.move_id, max(aaa.id) as analytic_id
                                        from account_move_line aml
                                        left join account_analytic_line aal
                                        ON aal.move_id = aml.id
                                        left join account_analytic_account aaa
                                        on aal.account_id = aaa.id
                                        GROUP BY aml.move_id
                                    ) as move_analytic on move_analytic.move_id=mv.id
                                where  mv.state= %s and atx.apply_lcv = True
                                    and mv.date between %s and %s
                                    and inv.type='out_refund'
                                    """
                if app_tax_id:
                    cr_query = cr_query + " and ilt.tax_id = " + str(app_tax_id)
                cr_query = cr_query + """
                                    GROUP BY move_analytic.analytic_id
                                    )) as tot_inv
                                    group by tot_inv.id"""

                cr.execute(cr_query, ('posted',from_date,to_date,'posted',from_date,to_date,))
                move_ins=[]
                je_id=False
                res =cr.fetchall()
                for res_line in res:
                    sum_income = res_line and res_line[0] or 0.0
                    analytic_id=res_line[1]
                    je_amount = sum_income * perc
                    if je_amount > 0.0:
                        account_move_pool = self.pool.get('account.move')
                        account_move_line_pool = self.pool.get('account.move.line')
                        period_id = self.pool.get('account.period').find(cr, uid, to_date, context=context)[0]
                        journal = tax.journal_id
                        if not move_ins:
                            move_ins = {
                                "name": 'Registro Impuesto '+tax.description ,
                                "journal_id": journal.id,
                                "date": to_date,
                                "period_id": period_id,
                                }
                            je_id = account_move_pool.create(cr,uid,move_ins)

                        move_line_ins = {
                            "move_id": je_id,
                            "account_id": acc_deb,
                            "debit": je_amount,
                            "credit": 0,
                            "date": to_date,
                            "name": 'Gasto Impuesto '+tax.description,
                            "tax_amount": je_amount,
                            "journal_id": journal.id,
                            "period_id": period_id,
                            "analytic_account_id": analytic_id,
                            }
                        account_move_line_pool.create(cr,uid,move_line_ins)

                        move_line_ins = {
                            "move_id": je_id,
                            "account_id": acc_cred,
                            "debit": 0,
                            "date": to_date,
                            "credit": je_amount,
                            "name": 'Impuesto '+tax.description+' por pagar',
                            "tax_amount": je_amount,
                            "journal_id": journal.id,
                            "period_id": period_id,
                            "analytic_account_id": analytic_id,
                            }
                        account_move_line_pool.create(cr,uid,move_line_ins)


                    else:
                        self.log(cr, uid, ids, "La suma de Ingresos por la tasa de impuesto es cero. No se generó ningún asiento.")
                        #return {'view_mode' : 'tree,form','type': 'ir.actions.act_window_close'}

                if je_id:
                    if journal.entry_posted:
                        account_move_pool.post(cr, uid, [je_id], context=context)
                    else:
                        self.log(cr, uid, ids, "El asiento generado esta en borrador y debe ser confirmado.")
                else:
                    self.log(cr, uid, ids, "La suma de Ingresos por la tasa de impuesto es cero. No se generó ningún asiento.")
                    raise osv.except_osv((u'Advertencia'), (u'El proceso no ha detectado montos relevantes a este Impuesto y no ha generado ningún Asiento. Proceda a cancelar el Asistente'))

            else:
                raise osv.except_osv((u'Error de datos'), (u"Modalidad de Nivel detalle no reconocida"))

            if je_id:
                return {
                    'name': _('Journal Entries'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': False,
                    'res_model': 'account.move',
                    'domain': [],
                    'context': context,
                    'res_id': je_id,
                    'type': 'ir.actions.act_window',
                    }
            else:
                return {'view_mode' : 'tree,form','type': 'ir.actions.act_window_close'}
imp_it()
