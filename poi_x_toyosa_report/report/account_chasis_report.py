
import time
from openerp import fields, models, api, _
from openerp.report import report_sxw
from openerp.addons.poi_account_reports.report.monto_a_texto_esp import amount_to_text


class ReportAccountChasisReport(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.account_chasis_report'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_x_toyosa_report.account_chasis_report')
        move_id = self.env[report.model].browse(self.ids)
        rate = 0

        self.env.cr.execute("""
        SELECT round(1/rate,2) as rate
from res_currency_rate rcr
left join res_currency rc
on rc.id = rcr.currency_id
where rc.name = 'USD'
        """)


        rate = self.env.cr.fetchone()[0] or 0.0
        mline = move_id.line_ids
        for ml in mline:
            if ml.src and not ml.lot_id:
                model, lot_id = ml.src.split(',')
                ml.lot_id = int(lot_id)

        docargs = {

            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': move_id,
            'doc': move_id,
            'time': time,
            'rate': rate,
            'amount_to_text': amount_to_text,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'fecha_a_texto': self._fecha_a_texto,
            'cheque':   self._cheque,
            'glosai':   self._glosai,
            'get_lines_total': self._get_lines_total,
            'chasises': self._get_chasises,
            'get_lots': self._get_lots,
        }

        report_name =  'report.poi_x_toyosa_report.account_chasis_report'

        return report_obj.render(report.report_name, docargs)

    @api.multi
    def _get_lots(self, line_id):
        lot_obj = self.env['stock.production.lot']
        quant_obj = self.env['stock.quant']
        invoice_obj = self.env['account.invoice']
        line_id = self.env['account.move.line'].browse(int(line_id))
        lots = []
        if line_id.src:
            model, lot_id = line_id.src.split(",")
            if model == 'stock.production.lot':
                lot_id = lot_obj.browse(int(lot_id))
                quant_id = quant_obj.search([('lot_id', '=', lot_id.id)], limit=1, order="id desc")
                if quant_id:
                    lots.append([lot_id.name, quant_id[0].cost])
                else:
                    lots.append([lot_id.name, 0])
        elif line_id.move_id.src:
            model, invoice_id = line_id.move_id.src.split(",")
            if model == 'account.invoice':
                lot_ids  = lot_obj.search([('invoice_purchase_id', '=', int(invoice_id)), ('product_id', '=',  line_id.product_id.id)])
                for l in lot_ids:
                    quant_id = quant_obj.search([('lot_id', '=', l.id)], limit=1, order="id desc")
                    if quant_id:
                        lots.append([l.name, quant_id[0].cost])
                    else:
                        lots.append([l.name, 0]) 
                if not lot_ids:
                    inv_id = invoice_obj.browse(int(invoice_id))
                    if inv_id.lot_id and inv_id.lot_id.product_id and inv_id.lot_id.product_id.id == line_id.product_id.id:
                        quant_id = quant_obj.search([('lot_id', '=', inv_id.lot_id.id)], limit=1, order="id desc")
                        if quant_id:
                            lots.append([inv_id.lot_id.name, quant_id[0].cost])
                        else:
                            lots.append([inv_id.lot_id.name, 0]) 
        return lots


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

    @api.multi
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
                           aaa.full_name as analytic_account,
                           t0.id as line_id
                           FROM account_move_line t0
                           INNER JOIN account_account t1 on t1.id = t0.account_id
                           LEFT JOIN account_analytic_account aaa on aaa.id = t0.analytic_account_id
                            WHERE t0.move_id = %s
                            GROUP BY t1.code, t1.name, t0.name, aaa.full_name, t0.id
                            order by t0.name,  aaa.full_name""", (move_id,))
        moves = self.env.cr.dictfetchall()
        for mov in moves:
            res.append(mov)
        return res



    @api.multi
    def _get_chasises(self, move_id=False):
        res = []
        if not move_id:
            return res

        self.env.cr.execute("SELECT SPLIT_PART(am.src,',','1'),aj.type FROM account_move am inner join account_journal aj on aj.id=am.journal_id WHERE am.id=%s " % (move_id,))
        cr_fetch = self.env.cr.fetchone()
        move_case = cr_fetch[0]
        journal_case = cr_fetch[1]

        if move_case == "stock.move":
            self.env.cr.execute("""SELECT spl.name as chasis, sq.cost,sq.qty,pp.name_template 
                                FROM account_move_line aml inner join account_move am on aml.move_id=am.id
                                    inner join stock_move sm on sm.id=SPLIT_PART(am.src,',','2')::integer
                                    right join stock_quant sq on sq.id = am.src_quant::integer
                                    inner join stock_production_lot spl on spl.id=sq.lot_id
                                    inner join product_product pp on pp.id=sq.product_id
                                WHERE SPLIT_PART(am.src,',','1')='stock.move' AND am.id=%s AND aml.debit > 0.0""", (move_id,))

        if move_case == "account.invoice":
            if journal_case == "purchase":
                self.env.cr.execute("""SELECT spl.name  as chasis, sq.cost,sq.qty,pp.name_template 
                                    FROM stock_move sm inner join stock_picking sp on sm.picking_id=sp.id
                                        right join stock_quant_move_rel sqmr on sqmr.move_id=sm.id
                                        right join stock_quant sq on sq.id=sqmr.quant_id
                                        inner join stock_production_lot spl on spl.id=sq.lot_id
                                        inner join product_product pp on pp.id=sq.product_id
                                    WHERE sp.embarque = (select ai.n_embarque from account_invoice ai where ai.id = (select SPLIT_PART(am.src,',','2')::integer from account_move am where am.id = %s ))""", (move_id,))
            if journal_case == "sale":
                self.env.cr.execute("""SELECT spl.name  as chasis, ail.price_subtotal as cost,ail.quantity as qty,pp.name_template 
                                    FROM account_move_line aml inner join account_move am on aml.move_id=am.id
                                        inner join account_invoice ai on ai.id=SPLIT_PART(src,',','2')::integer
                                        right join account_invoice_line ail on ail.invoice_id=ai.id 
                                        inner join stock_production_lot spl on spl.id=ail.lot_id
                                        inner join product_product pp on pp.id=aml.product_id
                                    WHERE coalesce(aml.product_id,0) !=0 and aml.credit>0 and  am.id = %s """, (move_id,))

        if move_case == "stock.landed.cost":
            self.env.cr.execute("""SELECT spl.name  as chasis, (sval.additional_landed_cost / sval.quantity) as cost,sq.qty,pp.name_template
                                FROM stock_move sm inner join stock_picking sp on sm.picking_id=sp.id
                                    right join stock_quant_move_rel sqmr on sqmr.move_id=sm.id
                                    right join stock_quant sq on sq.id=sqmr.quant_id
                                    inner join stock_production_lot spl on spl.id=sq.lot_id
                                    inner join product_product pp on pp.id=sq.product_id
                                    right join stock_valuation_adjustment_lines sval on sval.move_id=sm.id
                                WHERE sval.cost_id = (select SPLIT_PART(am.src,',','2')::integer from account_move am where am.id = %s )""", (move_id,))

        moves = self.env.cr.dictfetchall()
        for mov in moves:
            res.append(mov)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
