from odoo import models, fields, api, _, tools

class payment_report(models.Model):
    _name = 'payment.report'
    _description = 'Reporte de Planificacion'
    _auto = False
    _order = "date_from desc, employee_id asc"

    employee_id = fields.Many2one('hr.employee', 'Empleado')
    # company_id = fields.Many2one('res.company', 'Compañia')
    amount = fields.Float('Monto Total')
    acc_number = fields.Char('Numero de Cuenta')
    bank_name = fields.Char('Entidad Financiera')
    date_from = fields.Date('Periodo')
    state = fields.Char('Estado')


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        self.env.cr.execute("REFRESH MATERIALIZED VIEW payment_report");

        res = super(payment_report, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        return res


    def _select(self):

        select_str ="""
            select
                e.id as employee_id,
                l.amount,
                b.acc_number,
                rb.name as bank_name,
                p.date_from,
                p.state
            from
                hr_employee e
                left join hr_payslip p on p.employee_id = e.id
                left join hr_payslip_line l on l.slip_id = p.id and code = 'NET'
                left join res_partner_bank b on b.id = e.bank_account_id
                left join res_bank rb on rb.id = b.bank_id
            where
                p.id is not null

        """
        return select_str


    @api.model_cr
    def init(self):
        table = "payment_report"
        self._cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'payment_report';
            """)
        vista = self._cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self._cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self._cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS payment_report;
            CREATE MATERIALIZED VIEW payment_report as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
