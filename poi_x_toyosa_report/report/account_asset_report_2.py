
import time
from openerp import fields, models, api, _
from openerp.report import report_sxw
from openerp.addons.poi_account_reports.report.monto_a_texto_esp import amount_to_text


class ReportAccountInvoice(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.account_asset_report_document_2'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_x_toyosa_report.account_asset_report_document_2')
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)[0]
        invoice_id = self.env[report.model].browse(self.ids)

        rate = 0

        self.env.cr.execute("""
                SELECT round(1/rate,2) as rate
        from res_currency_rate rcr
        left join res_currency rc
        on rc.id = rcr.currency_id
        where rc.name = 'USD'
                """)

        rate = self.env.cr.fetchone()[0] or 0.0

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': invoice_id,
            'doc': invoice_id,
            'usd': usd_currency,
            'time': time,
            'rate': rate,
            'amount_to_text': amount_to_text,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'fecha_a_texto': self._fecha_a_texto,
            'cheque':   self._cheque,
            'glosai':   self._glosai,
            'get_lines_total': self._get_lines_total,
        }

        report_name =  'report.poi_x_toyosa_report.account_asset_report_document_2'

        return report_obj.render(report.report_name, docargs)

    @api.multi
    def _sum_debit(self, move_id=False):
        if not move_id:
            return 0.0

        self.env.cr.execute("""
            select sum(debit) as debit
            from account_move_line
            WHERE move_id = """+str(move_id)+"""
            """)
        return self.env.cr.fetchone()[0] or 0.0

    def _sum_credit(self, move_id=False):
        if not move_id:
            return 0.0

        self.env.cr.execute("""
            select sum(credit) as credit
            from account_move_line
            WHERE move_id = """+str(move_id)+"""
            """)
        return self.env.cr.fetchone()[0] or 0.0


    @api.multi
    def _cheque(self, move_id=False):
        if not move_id:
            return 0.0

        self.env.cr.execute(str("""
            select check_number as chequito
            from account_voucher
            WHERE move_id = """+str(move_id)+"""
            """))
        data = self.env.cr.fetchone()                             # FETCHONE devuelve la siguiente tupla del conjunto

        if data:                                              # SI LA VARIABLE DATA EXISTE  RETORNA  EL DATA
            return data[0]
        else:
            return ''

    @api.multi
    def _glosai(self, move_id=False):
        if not move_id:
            return 0.0

        self.env.cr.execute("""
        select ref as glosain
        from account_move_line
        WHERE move_id = """+str(move_id)+"""
""")
        return self.env.cr.fetchone()[0] or 0.0

    @api.multi
    def _fecha_a_texto(self, fecha_corta):
        dato = str(fecha_corta)
        year = dato[:4]                         # HASTA LA POSICION 4 DESDE LA IZQUIERDA
        dayi = dato[8:10]                       # DESDE LA POSICION 8  TOMAR EL 9 Y 10
        month = dato[5:7]

        if month=='01':                         # SE USA DOBLE IGUAL EN EL CASO DEL IF   PARA   CARACTERES TEXTO
            month = 'Enero'
        if month=='02':
            month = 'Febrero'
        if month=='03':
            month = 'Marzo'
        if month=='04':
            month = 'Abril'
        if month=='05':
            month = 'Mayo'
        if month=='06':
            month = 'Junio'
        if month=='07':
            month = 'Julio'
        if month=='08':
            month = 'Agosto'
        if month=='09':
            month = 'Septiembre'
        if month=='10':
            month = 'Octubre'
        if month=='11':
            month = 'Noviembre'
        if month=='12':
            month = 'Diciembre'

        fecha_texto = str(dayi) + ' de ' + str(month) + ' de ' + str(year)

        return fecha_texto

    @api.multi
    def _get_lines_total(self, move_id=False):
        res = []
        if not move_id:
            return res

        self.env.cr.execute("""SELECT t1.code as code,
                           t1.name as name,
                           t0.name as label,
                           sum(debit) as debit,
                           sum(credit) as credit,
                           aaa.full_name as analytic_account
                           FROM account_move_line t0
                           INNER JOIN account_account t1 on t1.id = t0.account_id
                           LEFT JOIN account_analytic_account aaa on aaa.id = t0.analytic_account_id
                            WHERE t0.move_id = %s
                            GROUP BY t1.code, t1.name, t0.name, aaa.full_name""", (move_id,))
        moves = self.env.cr.dictfetchall()
        for mov in moves:
            res.append(mov)
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
