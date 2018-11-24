
import time
from odoo.osv import osv
from odoo.report import report_sxw
from odoo.addons.poi_account_reports.report.monto_a_texto_esp import amount_to_text


class account_asset_report_class(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(account_asset_report_class, self).__init__(cr, uid, name, context=context)
        rate = 0

        cr.execute("""
        SELECT round(1/rate,2) as rate
from res_currency_rate rcr
left join res_currency rc
on rc.id = rcr.currency_id
where rc.name = 'USD'
        """)


        rate = cr.fetchone()[0] or 0.0



        self.localcontext.update( {
            'time': time,
            'rate': rate,
            'amount_to_text': amount_to_text,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'fecha_a_texto': self._fecha_a_texto,
            'cheque':   self._cheque,
            'glosai':   self._glosai,
            'get_lines_total': self._get_lines_total,

        })

    def _sum_debit(self, move_id=False):
        if not move_id:
            return 0.0

        self.cr.execute("""
select sum(debit) as debit
from account_move_line
WHERE move_id = """+str(move_id)+"""
""")
        return self.cr.fetchone()[0] or 0.0

    def _sum_credit(self, move_id=False):
        if not move_id:
            return 0.0

        self.cr.execute("""
select sum(credit) as credit
from account_move_line
WHERE move_id = """+str(move_id)+"""
""")
        return self.cr.fetchone()[0] or 0.0


    def _cheque(self, move_id=False):
        if not move_id:
            return 0.0

        self.cr.execute(str("""
        select check_number as chequito
        from account_voucher
        WHERE move_id = """+str(move_id)+"""
        """))
        data = self.cr.fetchone()                             # FETCHONE devuelve la siguiente tupla del conjunto

        if data:                                              # SI LA VARIABLE DATA EXISTE  RETORNA  EL DATA
            return data[0]
        else:
            return ''

    def _glosai(self, move_id=False):
        if not move_id:
            return 0.0

        self.cr.execute("""
        select ref as glosain
        from account_move_line
        WHERE move_id = """+str(move_id)+"""
""")
        return self.cr.fetchone()[0] or 0.0

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

    def _get_lines_total(self, move_id=False):
        res = []
        if not move_id:
            return res

        self.cr.execute("""SELECT * FROM
                        (SELECT t1.code as code,
                           t1.name as name,
                           t0.name as label,
                           sum(debit) as debit,
                           sum(credit) as credit,
                           aaa.full_name as analytic_account,
                           t0.date,
                           t0.move_id,
 	                       t0.is_debit,
                           t0.id
                           FROM account_move_line t0
                           INNER JOIN account_account t1 on t1.id = t0.account_id
                           LEFT JOIN account_analytic_account aaa on aaa.id = t0.analytic_account_id
                            WHERE t0.move_id = %s
                            GROUP BY t1.code, t1.name, t0.name, aaa.full_name, t0.date, t0.move_id, t0.is_debit, t0.id) as aml
							order by date desc, move_id desc, is_debit desc, id""", (move_id,))
        moves = self.cr.dictfetchall()
        for mov in moves:
            res.append(mov)
        return res


class account_asset_report_document(osv.AbstractModel):
    _name = 'report.poi_account_reports.account_asset_report'
    _inherit = 'report.abstract_report'
    _template = 'poi_account_reports.account_asset_report'
    _wrapped_report_class = account_asset_report_class

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
