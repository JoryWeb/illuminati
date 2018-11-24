from openerp import models, fields, api, _, tools
from lxml import etree


class poi_estado_resultados(models.Model):
    _name = 'poi.estado.resultados'
    _description = 'Estado de Resultados'
    _auto = False

    
    total = fields.Float('Balance Bs.')
    credit = fields.Float('Haber Bs.')
    debit = fields.Float('Debe Bs.')

    total_s = fields.Float('Balance $us.')
    credit_s = fields.Float('Haber $us.')
    debit_s = fields.Float('Debe Sus.')

    #fiscalyear_id = fields.Many2one('account.fiscalyear', 'Año Fiscal')
    fiscalyear_id = fields.Integer('Año Fiscal')
    date = fields.Date('Fecha')
    company_id = fields.Many2one('res.company', 'Company')
    segment_id = fields.Many2one('account.segment', 'Segmento')
    
    
    level1 = fields.Char('l1')
    level2 = fields.Char('l2')
    level3 = fields.Char('l3')
    level4 = fields.Char('l4')
    level5 = fields.Char('l5')
    level6 = fields.Char('l6')
    level7 = fields.Char('l7')
    level8 = fields.Char('l8')
    level9 = fields.Char('l9')
    level10 = fields.Char('l10')
    report_type0 = fields.Char('nivel0')
    report_type1 = fields.Char('nivel1')
    report_type2 = fields.Char('nivel2')
    report_type3 = fields.Char('nivel3')
    report_type4 = fields.Char('nivel4')
    report_type5 = fields.Char('nivel5')
    analitica1  = fields.Char('analitica1')
    analitica2 = fields.Char('analitica2')

       
    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
        select

            a.credit,
            a.debit,
            a.credit - a.debit as total,
            a.fiscalyear_id,
            case
                when a.level = 6 then a.name
                else null
            end as level1,
            case
                when a.level = 5 then a.name
                when aa.level = 5 then aa.name
                
                else null
            end as level2,
            case
                when a.level = 4 then a.name
                when aa.level = 4 then aa.name
                when aa1.level = 4 then aa1.name
                else null
            end as level3,
            case

                when a.level = 3 then a.name
                when aa.level = 3 then aa.name
                when aa1.level = 3 then aa1.name
                when aa2.level = 3 then aa2.name
                else null
            end as level4,
            case    
                when a.level = 2 then a.name
                when aa.level = 2 then aa.name
                when aa1.level = 2 then aa1.name
                when aa2.level = 2 then aa2.name
                when aa3.level = 2 then aa3.name
                else null
            end as level5,
            case
                when a.level = 1 then a.name
                when aa.level = 1 then aa.name
                when aa1.level = 1 then aa1.name
                when aa2.level = 1 then aa2.name
                when aa3.level = 1 then aa3.name
                when aa4.level = 1 then aa4.name
                else null
            end as level6,
            case
                when a.level = 0 then a.name
                when aa.level = 0 then aa.name
                when aa1.level = 0 then aa1.name
                when aa2.level = 0 then aa2.name
                when aa3.level = 0 then aa3.name
                when aa4.level = 0 then aa4.name
                when aa5.level = 0 then aa5.name
                else null
            end as level7

            
        from
            (select 
                
                aml.credit,
                        aml.debit,
                        --ap.fiscalyear_id,
                        to_char(aml.date,'YYYY')::INTEGER as fiscalyear_id,
                        aa.name,
                        aa.parent_id,
                        aa.level,
                        aaft.report_id,
                        aml.company_id
                        
                                  
                    from
                        account_move_line aml
                        inner join account_move am on am.id = aml.move_id
                        left join account_account aa on aa.id = aml.account_id
                        left join account_account_type aat on aat.id = aa.user_type_id
                        --left join account_period ap on ap.id = aml.period_id
                        left join account_account_financial_report_type aaft on aaft.account_type_id = aa.user_type_id
                        left join account_analytic_account aaa on aaa.id = aml.analytic_account_id 
                       
                        where am.state = 'posted'
                ) as a

            left join account_account aa on aa.id = a.parent_id
            left join account_account aa1 on aa1.id = aa.parent_id
            left join account_account aa2 on aa2.id = aa1.parent_id
            left join account_account aa3 on aa3.id = aa2.parent_id
            left join account_account aa4 on aa4.id = aa3.parent_id
            left join account_account aa5 on aa5.id = aa4.parent_id
        """
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "poi_estado_resultados"
        cr.execute("""
            SELECT table_type 
            FROM information_schema.tables 
            WHERE table_name = 'poi_estado_resultados';
            """)
        vista = cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        cr.execute("""
           
            DROP MATERIALIZED VIEW IF EXISTS %s;
            CREATE MATERIALIZED VIEW %s as ((
            SELECT row_number() over() as id, *
                FROM ((
                    %s
                )) as asd
            ))""" % (table, table, self._select(select)))




class poi_estado_resultados_wizzard(models.TransientModel):
    _name = "poi.estado.resultados_wizzard"

    char_account_id = fields.Many2one('account.account', 'Plan de Cuentas',help='Selecciona el Plan de Cuentas', required=True, domain = [('parent_id','=',False)], default=lambda self:  self.env['account.account'].search([('parent_id', '=', False), ('company_id', '=', self.env.user.company_id.id)], limit=1) )


    filter_1 = fields.Selection([
        ('fiscalyear', 'Año Fiscal'),
        ('fechas', 'Fechas desde Hasta')
        ], "Filtro de Fechas")

    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Año Fiscal', help='Mantener Vacio para poder Ver todos los Años Ficales')
    date_from = fields.Date('Desde')
    date_until = fields.Date('Hasta')
    account_report_id = fields.Many2one('account.financial.report', 'Informe de Cuentas', domain=[('parent_id','=',False)], required=True)

    target_move = fields.Selection([('posted', 'Todos los Asientos Asentados'),
                                         ('all', 'Todos los Asientos'),
                                        ], 'Movimientos', required=True, default="posted")

    filter2 = fields.Selection([
        ('nivel1', 'Cuenta Analitica nivel 1'),
        ('nivel2', 'Cuenta Analitica nivel 2')
        ], "Niveles")
        

    nivel1 = fields.Many2many("account.analytic.account","account_regiones_balance_rel","account_id","user_id","Agregar elementos")

    nivel2 = fields.Many2many("account.analytic.account","account_cuentas_balance_rel","account_id","user_id","Agregar elementos")

    @api.multi
    def open_table(self):

        data = self.read()[0]
        where_date = ""
        if data['date_from']:
            where_date =  "AND aml.date >= '" + data['date_from'] + "'"
            flag_date = True
        if data['date_until']:
            where_date = where_date + "AND aml.date <= '" + data['date_until']  + "'"
        id_rep = data['account_report_id'][0]
        if data['target_move']:
            if data['target_move'] == 'all':
                moves = "'draft', 'posted'"
                moves2 = ""
            else:
                moves = "'posted'"
                moves2 = "AND aml.state <> 'draft'"
        where_s = ""
        if data['fiscalyear_id']:
            id_fyear = data['fiscalyear_id'][0]
            self.env.cr.execute(
                """
                select 
                        date_stop
                from 
                        account_fiscalyear
                where id="""+ str(id_fyear) +"""  """)
            date_fyear = self.env.cr.fetchall()[0][0]

            self.env.cr.execute(
                """
                select 
                        max(rate)
                from 
                        res_currency_rate
                where currency_id=3 and name <= '"""+ str(date_fyear) +"""'   """)
            rate = self.env.cr.fetchall()[0][0]
            where_s = """ and fiscalyear_id = """+ str(id_fyear) +""" """
        else:
            self.env.cr.execute(
                """
                select 
                        max(rate)
                from 
                        res_currency_rate
                where currency_id=3  """)
            rate = self.env.cr.fetchall()[0][0]

        self.env.cr.execute(
            """
            select 
                    sign
            from 
                    account_financial_report
            where id="""+ str(id_rep) +"""  """)
        sign = (self.env.cr.fetchall())[0][0]

        self.env.cr.execute(
            """select max(level)
               from account_financial_report""")
        max_level_report = (self.env.cr.fetchall())[0][0]+3
        mlr = max_level_report
        self.env.cr.execute(
            """select max(level)
               from account_account""")
        max_level_account = 10
        mlc = 10

        rc_str = id_rep
        rep_xtras = {}
        while True:
            self.env.cr.execute(
                """
                select 
                        id,
                        account_report_id,
                        level

                from 
                        account_financial_report
                where parent_id in ("""+ str(rc_str) +""") """)
            report_child = self.env.cr.fetchall()
            rc_str = ""
            c = 0
            for rc in report_child:
                if rc[1]:
                    a = []
                    a.append(rc[1])
                    a.append(rc[2])
                    rep_xtras[rc[0]] = a
                if c > 0:
                    rc_str = rc_str + "," +str(rc[0])
                else:
                    rc_str = rc_str + str(rc[0])
                    c = c + 1
            if len(rc_str) < 1:
                break


        select_str = """
                case
                    when a""" + str(max_level_account) + """.level = """ + str(max_level_account) + """ then  a""" + str(max_level_account) + """.code ||' '|| a""" + str(max_level_account) + """.name
                    else null
                end as level"""+ str(max_level_account) +""" """
        
        select_p = ""
        select_xtra_rep = """  case 
                        when false then null
                        else null
                    end as level""" + str(max_level_account) + ""","""
        c = 0
        while ((max_level_account-1) >= 0):
            max_level_account = max_level_account - 1
            c = c + 1 
            p = "" 
            for x in xrange(1,c+1):
                if max_level_account == 0:
                    p =  """
                    when a""" + str(max_level_account+x) + """.level = """ + str(max_level_account) + """ then a""" + str(max_level_account+x) + """.id""" + p
                else:
                    p =  """
                    when a""" + str(max_level_account+x) + """.level = """ + str(max_level_account) + """ then a""" + str(max_level_account+x) + """.code ||' '|| a""" + str(max_level_account+x) + """.name""" + p

            if max_level_account == 0:
                select_p = """
                when a""" + str(max_level_account) + """.level = """ + str(max_level_account) + """ then a""" + str(max_level_account) + """.id"""
            else:
                select_p = """
                when a""" + str(max_level_account) + """.level = """ + str(max_level_account) + """ then a""" + str(max_level_account) + """.code ||''|| a""" + str(max_level_account) + """.name"""

            
            if max_level_account == 0:
                select_xtra_rep = select_xtra_rep 
            else:
                select_xtra_rep =   """  case 
                            when false then null
                            else null
                        end as level""" + str(max_level_account) + """,""" +select_xtra_rep 
            
            select_p =  p + select_p 
            select_str = select_str + """,
                case
                    """ + select_p + """
                    else null
                end as level""" + str(max_level_account) + """"""

        select_str2 = """, 
            case
                when afr"""+ str(max_level_report) +""".level = """+ str(max_level_report) +""" then COALESCE(cast(afr"""+ str(max_level_report) +""".sequence as varchar(32)), '') ||' '|| afr"""+ str(max_level_report) +""".name
                else null
            end as report_type"""+ str(max_level_report) +""""""
        c = 0

        select_rep = ""
        for  x in range(0, max_level_report+1):
            select_rep = """

                when afr"""+ str(x) +""".level = 0 then afr"""+ str(x) +""".id""" + select_rep

        select_rep = """,
                case
                    """+ select_rep +"""
                end as id_rep"""

        while ((max_level_report-1) >= 0):
            max_level_report = max_level_report - 1
            c = c + 1 
            p =  ""
            for x in xrange(1,c+1):
                p = """
                when afr"""+ str(max_level_report+x) +""".level = """+ str(max_level_report) +""" then COALESCE(cast(afr"""+ str(max_level_report+x) +""".sequence as varchar(32)), '') ||' '|| afr"""+ str(max_level_report+x) +""".name""" + p
            select_p = """
                when afr"""+ str(max_level_report) +""".level = """+ str(max_level_report) +""" then COALESCE(cast(afr"""+ str(max_level_report) +""".sequence as varchar(32)), '') ||' '|| afr"""+ str(max_level_report) +""".name"""
            select_p = p + select_p

            select_str2 = select_str2 + """,
                case
                    """ + select_p + """
                    else null
                end as report_type"""+ str(max_level_report) +""""""
        select = select_str + select_str2 + select_rep
        from_str = ""
        for x in xrange(0,mlc):
            from_str = """
                left join account_account a"""+str(x)+""" on a"""+str(x)+""".id = a"""+str(x+1)+""".parent_id    
            """ + from_str

        from_str2 = ""
        for x in xrange(0,mlr+1):
            if x == mlr:
                from_str2 = """
                left join account_account_financial_report_type aaft on aaft.account_type_id = a"""+ str(mlc) +""".user_type  
                left join account_financial_report afr"""+ str(x) +""" on afr"""+ str(x) +""".id = aaft.report_id   
                """ + from_str2
            else:
                from_str2 = """
                left join account_financial_report afr"""+ str(x) +""" on afr"""+ str(x) +""".id = afr"""+ str(x+1) +""".parent_id   
                """ + from_str2
            
        fr = from_str + from_str2

        
        if data['nivel2']:
            where_s = where_s + """ and sucursales_id in (""" +str(data['nivel2']).strip('[]') +""" ) """
        if data['nivel1']:
            where_s = where_s + """ and   region_id in (""" +str(data['nivel1']).strip('[]') +""" ) """


        sql = """
            select 
                *
            from
                (select 
                (a"""+ str(mlc) +""".debit - a"""+ str(mlc) +""" .credit) * """+ str(sign) +""" as total,
                a"""+ str(mlc) +""".credit,
                a"""+ str(mlc) +""".debit,
        
                ((a"""+ str(mlc) +""".debit - a"""+ str(mlc) +""" .credit) * """+ str(sign) +""") * """+ str(rate) +""" as total_s,
                a"""+ str(mlc) +""".credit * """+ str(rate) +""" as credit_s,
                a"""+ str(mlc) +""".debit * """+ str(rate) +""" as debit_s,
                a"""+ str(mlc) +""".fiscalyear_id,
                a"""+ str(mlc) +""".date,
                a"""+ str(mlc) +""".company_id,
                a"""+ str(mlc) +""".segment_id,
             
                """+ select +""",

                aaa1.name as analitica2,
                aaa1.id as sucursales_id,
                case
                    when aaa1.parent_id > 0 then aaa0.name
                end as analitica1,
                aaa0.id as region_id
                
                from
                    (select 
                        aa.id,
                        aml.credit,
                        aml.debit,
                        --ap.fiscalyear_id,
                        to_char(aml.date, 'YYYY')::INTEGER as fiscalyear_id,
                        aa.name,
                        aa.code,
                        aa.user_type_id,
                        aa.parent_id,
                        aa.level,
                        aaft.report_id,
                        aaa.id as sucursales,
                        aml.date,
                        aml.company_id,
                        case 
                            when aml.segment_id > 0 then aml.segment_id
                            when pt.segment_id > 0 then pt.segment_id
                            else null
                        end as segment_id
                        
                                  
                    from
                        account_move_line aml
                        inner join account_move am on am.id = aml.move_id
                        left join account_account aa on aa.id = aml.account_id
                        left join account_account_type aat on aat.id = aa.user_type_id
                        --left join account_period ap on ap.id = aml.period_id
                        left join account_account_financial_report_type aaft on aaft.account_type_id = aa.user_type_id
                        left join account_analytic_account aaa on aaa.id = aml.analytic_account_id 
                        left join product_product pp on pp.id = aml.product_id
                        left join product_template pt on pp.product_tmpl_id = pt.id
                        
                    
                    where am.state = in ("""+ moves +""") 
                   
            
                    
                    ) as a"""+ str(mlc) +""" 
                 """+ fr +"""
                left join account_analytic_account aaa1 on aaa1.id = a"""+ str(mlc) +""".sucursales
                left join account_analytic_account aaa0 on aaa0.id = aaa1.parent_id
                 ) as a
            where a.id_rep = """+str(data['account_report_id'][0])+""" """+ where_s +""" and level0 = """+ str(data['char_account_id'][0]) +"""
        """
        
     
        sql = """

        ( select
            p.report_p_id,
            p.report_type0,
            p.report_type1,
            p.report_type2,
            p.report_type3,
            p.report_type4,
            p.report_type5,
            p.level1,
            p.level2,
            p.level3,
            p.level4,
            p.level5,
            p.level6,
            p.level7,
            p.level8,
            p.level9,
            p.level10,
           
            p.credit,
            p.debit,               
            (p.debit - p.credit) * p.sign   as total,

            ((p.debit - p.credit) * p.sign ) * """+ str(rate) +""" as total_s,
            p.credit * """+ str(rate) +""" as credit_s,
            p.debit * """+ str(rate) +""" as debit_s,

            p.aml_date as date,
            p.aml_company_id as company_id,
            p.aml_segment_id as segment_id,
            p.ap_fiscalyear_id as fiscalyear_id,
            p.analitica2,
            p.sucursales_id,
            p.analitica1,
            p.region_id
           
        from
        (select
            aml.date as aml_date,
            aml.company_id as aml_company_id,
            case 
                when aml.segment_id > 0 then aml.segment_id
                when pt.segment_id > 0 then pt.segment_id
                else null
            end as aml_segment_id,
            --ap.fiscalyear_id as ap_fiscalyear_id,
            to_char(aml.date,'YYYY')::INTEGER as ap_fiscalyear_id,
            aaa0.name as analitica2,
            aaa0.id as sucursales_id,
            case
                  when aaa0.parent_id > 0 then aaa1.name
            end as analitica1,
            aaa1.id as region_id,
            *
        from
        (select 
            case
                when COALESCE(id9,0) > 0 then id9
                when COALESCE(id8,0) > 0 then id8
                when COALESCE(id7,0) > 0 then id7
                when COALESCE(id6,0) > 0 then id6
                when COALESCE(id5,0) > 0 then id5
                when COALESCE(id4,0) > 0 then id4
                when COALESCE(id3,0) > 0 then id3
                when COALESCE(id2,0) > 0 then id2
                when COALESCE(id1,0) > 0 then id1
            end as final_id,
                
            *
        from
        (select 
            
            
            case
                when r.aa_level = 1 then r.aa_id
                when aa0.level = 1 then aa0.id
                when aa1.level = 1 then aa1.id
                when aa2.level = 1 then aa2.id
                when aa3.level = 1 then aa3.id
                when aa4.level = 1 then aa4.id
                when aa5.level = 1 then aa5.id
                when aa6.level = 1 then aa6.id
                when aa7.level = 1 then aa7.id
                when aa8.level = 1 then aa8.id
                when aa9.level = 1 then aa9.id
            end as id1,
            case
                when r.aa_level = 2 then r.aa_id
                when aa0.level = 2 then aa0.id
                when aa1.level = 2 then aa1.id
                when aa2.level = 2 then aa2.id
                when aa3.level = 2 then aa3.id
                when aa4.level = 2 then aa4.id
                when aa5.level = 2 then aa5.id
                when aa6.level = 2 then aa6.id
                when aa7.level = 2 then aa7.id
                when aa8.level = 2 then aa8.id
                when aa9.level = 2 then aa9.id
            end as id2,
            case
                when r.aa_level = 3 then r.aa_id
                when aa0.level = 3 then aa0.id
                when aa1.level = 3 then aa1.id
                when aa2.level = 3 then aa2.id
                when aa3.level = 3 then aa3.id
                when aa4.level = 3 then aa4.id
                when aa5.level = 3 then aa5.id
                when aa6.level = 3 then aa6.id
                when aa7.level = 3 then aa7.id
                when aa8.level = 3 then aa8.id
                when aa9.level = 3 then aa9.id
            end as id3,
            case
                when r.aa_level = 4 then r.aa_id
                when aa0.level = 4 then aa0.id
                when aa1.level = 4 then aa1.id
                when aa2.level = 4 then aa2.id
                when aa3.level = 4 then aa3.id
                when aa4.level = 4 then aa4.id
                when aa5.level = 4 then aa5.id
                when aa6.level = 4 then aa6.id
                when aa7.level = 4 then aa7.id
                when aa8.level = 4 then aa8.id
                when aa9.level = 4 then aa9.id
            end as id4,
            case
                when r.aa_level = 5 then r.aa_id
                when aa0.level = 5 then aa0.id
                when aa1.level = 5 then aa1.id
                when aa2.level = 5 then aa2.id
                when aa3.level = 5 then aa3.id
                when aa4.level = 5 then aa4.id
                when aa5.level = 5 then aa5.id
                when aa6.level = 5 then aa6.id
                when aa7.level = 5 then aa7.id
                when aa8.level = 5 then aa8.id
                when aa9.level = 5 then aa9.id
            end as id5,
            case
                when r.aa_level = 6 then r.aa_id
                when aa0.level = 6 then aa0.id
                when aa1.level = 6 then aa1.id
                when aa2.level = 6 then aa2.id
                when aa3.level = 6 then aa3.id
                when aa4.level = 6 then aa4.id
                when aa5.level = 6 then aa5.id
                when aa6.level = 6 then aa6.id
                when aa7.level = 6 then aa7.id
                when aa8.level = 6 then aa8.id
                when aa9.level = 6 then aa9.id
            end as id6,
            case
                when r.aa_level = 7 then r.aa_id
                when aa0.level = 7 then aa0.id
                when aa1.level = 7 then aa1.id
                when aa2.level = 7 then aa2.id
                when aa3.level = 7 then aa3.id
                when aa4.level = 7 then aa4.id
                when aa5.level = 7 then aa5.id
                when aa6.level = 7 then aa6.id
                when aa7.level = 7 then aa7.id
                when aa8.level = 7 then aa8.id
                when aa9.level = 7 then aa9.id
            end as id7,
            case
                when r.aa_level = 8 then r.aa_id
                when aa0.level = 8 then aa0.id
                when aa1.level = 8 then aa1.id
                when aa2.level = 8 then aa2.id
                when aa3.level = 8 then aa3.id
                when aa4.level = 8 then aa4.id
                when aa5.level = 8 then aa5.id
                when aa6.level = 8 then aa6.id
                when aa7.level = 8 then aa7.id
                when aa8.level = 8 then aa8.id
                when aa9.level = 8 then aa9.id
            end as id8,
            case
                when r.aa_level = 9 then r.aa_id
                when aa0.level = 9 then aa0.id
                when aa1.level = 9 then aa1.id
                when aa2.level = 9 then aa2.id
                when aa3.level = 9 then aa3.id
                when aa4.level = 9 then aa4.id
                when aa5.level = 9 then aa5.id
                when aa6.level = 9 then aa6.id
                when aa7.level = 9 then aa7.id
                when aa8.level = 9 then aa8.id
                when aa9.level = 9 then aa9.id
            end as id9,
            r.sign,
            r.report_p_id,
            r.report_type0,
            r.report_type1,
            r.report_type2,
            r.report_type3,
            r.report_type4,
            r.report_type5,
            case
            when r.aa_level = 1    then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 1 then aa0.code ||' - '|| aa0.name 
                when aa1.level = 1 then aa1.code ||' - '|| aa1.name
                when aa2.level = 1 then aa2.code ||' - '|| aa2.name
                when aa3.level = 1 then aa3.code ||' - '|| aa3.name
                when aa4.level = 1 then aa4.code ||' - '|| aa4.name
                when aa5.level = 1 then aa5.code ||' - '|| aa5.name
                when aa6.level = 1 then aa6.code ||' - '|| aa6.name
                when aa7.level = 1 then aa7.code ||' - '|| aa7.name
                when aa8.level = 1 then aa8.code ||' - '|| aa8.name
                when aa9.level = 1 then aa9.code ||' - '|| aa9.name
            end as level1,
            case
                when r.aa_level = 2 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 2 then aa0.code ||' - '||  aa0.name
                when aa1.level = 2 then aa1.code ||' - '||  aa1.name
                when aa2.level = 2 then aa2.code ||' - '||  aa2.name
                when aa3.level = 2 then aa3.code ||' - '||  aa3.name
                when aa4.level = 2 then aa4.code ||' - '||  aa4.name
                when aa5.level = 2 then aa5.code ||' - '||  aa5.name
                when aa6.level = 2 then aa6.code ||' - '||  aa6.name
                when aa7.level = 2 then aa7.code ||' - '||  aa7.name
                when aa8.level = 2 then aa8.code ||' - '||  aa8.name
                when aa9.level = 2 then aa9.code ||' - '||  aa9.name
            end as level2,
            case
                when r.aa_level = 3 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 3 then aa0.code ||' - '||  aa0.name
                when aa1.level = 3 then aa1.code ||' - '||  aa1.name
                when aa2.level = 3 then aa2.code ||' - '||  aa2.name
                when aa3.level = 3 then aa3.code ||' - '||  aa3.name
                when aa4.level = 3 then aa4.code ||' - '||  aa4.name
                when aa5.level = 3 then aa5.code ||' - '||  aa5.name
                when aa6.level = 3 then aa6.code ||' - '||  aa6.name
                when aa7.level = 3 then aa7.code ||' - '||  aa7.name
                when aa8.level = 3 then aa8.code ||' - '||  aa8.name
                when aa9.level = 3 then aa9.code ||' - '||  aa9.name
            end as level3,
            case
                when r.aa_level = 4 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 4 then aa0.code ||' - '||  aa0.name
                when aa1.level = 4 then aa1.code ||' - '||  aa1.name
                when aa2.level = 4 then aa2.code ||' - '||  aa2.name
                when aa3.level = 4 then aa3.code ||' - '||  aa3.name
                when aa4.level = 4 then aa4.code ||' - '||  aa4.name
                when aa5.level = 4 then aa5.code ||' - '||  aa5.name
                when aa6.level = 4 then aa6.code ||' - '||  aa6.name
                when aa7.level = 4 then aa7.code ||' - '||  aa7.name
                when aa8.level = 4 then aa8.code ||' - '||  aa8.name
                when aa9.level = 4 then aa9.code ||' - '||  aa9.name
            end as level4,
            case
                when r.aa_level = 5 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 5 then aa0.code ||' - '||  aa0.name
                when aa1.level = 5 then aa1.code ||' - '||  aa1.name
                when aa2.level = 5 then aa2.code ||' - '||  aa2.name
                when aa3.level = 5 then aa3.code ||' - '||  aa3.name
                when aa4.level = 5 then aa4.code ||' - '||  aa4.name
                when aa5.level = 5 then aa5.code ||' - '||  aa5.name
                when aa6.level = 5 then aa6.code ||' - '||  aa6.name
                when aa7.level = 5 then aa7.code ||' - '||  aa7.name
                when aa8.level = 5 then aa8.code ||' - '||  aa8.name
                when aa9.level = 5 then aa9.code ||' - '||  aa9.name
            end as level5,
            case
                when r.aa_level = 6 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 6 then aa0.code ||' - '||  aa0.name
                when aa1.level = 6 then aa1.code ||' - '||  aa1.name
                when aa2.level = 6 then aa2.code ||' - '||  aa2.name
                when aa3.level = 6 then aa3.code ||' - '||  aa3.name
                when aa4.level = 6 then aa4.code ||' - '||  aa4.name
                when aa5.level = 6 then aa5.code ||' - '||  aa5.name
                when aa6.level = 6 then aa6.code ||' - '||  aa6.name
                when aa7.level = 6 then aa7.code ||' - '||  aa7.name
                when aa8.level = 6 then aa8.code ||' - '||  aa8.name
                when aa9.level = 6 then aa9.code ||' - '||  aa9.name
            end as level6,
            case
                when r.aa_level = 7 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 7 then aa0.code ||' - '||  aa0.name
                when aa1.level = 7 then aa1.code ||' - '||  aa1.name
                when aa2.level = 7 then aa2.code ||' - '||  aa2.name
                when aa3.level = 7 then aa3.code ||' - '||  aa3.name
                when aa4.level = 7 then aa4.code ||' - '||  aa4.name
                when aa5.level = 7 then aa5.code ||' - '||  aa5.name
                when aa6.level = 7 then aa6.code ||' - '||  aa6.name
                when aa7.level = 7 then aa7.code ||' - '||  aa7.name
                when aa8.level = 7 then aa8.code ||' - '||  aa8.name
                when aa9.level = 7 then aa9.code ||' - '||  aa9.name
            end as level7,
            case
                when r.aa_level = 8 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 8 then aa0.code ||' - '||  aa0.name
                when aa1.level = 8 then aa1.code ||' - '||  aa1.name
                when aa2.level = 8 then aa2.code ||' - '||  aa2.name
                when aa3.level = 8 then aa3.code ||' - '||  aa3.name
                when aa4.level = 8 then aa4.code ||' - '||  aa4.name
                when aa5.level = 8 then aa5.code ||' - '||  aa5.name
                when aa6.level = 8 then aa6.code ||' - '||  aa6.name
                when aa7.level = 8 then aa7.code ||' - '||  aa7.name
                when aa8.level = 8 then aa8.code ||' - '||  aa8.name
                when aa9.level = 8 then aa9.code ||' - '||  aa9.name
            end as level8,
            case
                when r.aa_level = 9 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 9 then aa0.code ||' - '||  aa0.name
                when aa1.level = 9 then aa1.code ||' - '||  aa1.name
                when aa2.level = 9 then aa2.code ||' - '||  aa2.name
                when aa3.level = 9 then aa3.code ||' - '||  aa3.name
                when aa4.level = 9 then aa4.code ||' - '||  aa4.name
                when aa5.level = 9 then aa5.code ||' - '||  aa5.name
                when aa6.level = 9 then aa6.code ||' - '||  aa6.name
                when aa7.level = 9 then aa7.code ||' - '||  aa7.name
                when aa8.level = 9 then aa8.code ||' - '||  aa8.name
                when aa9.level = 9 then aa9.code ||' - '||  aa9.name
            end as level9,
            case
                when r.aa_level = 10 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 10 then aa0.code ||' - '||  aa0.name
                when aa1.level = 10 then aa1.code ||' - '||  aa1.name
                when aa2.level = 10 then aa2.code ||' - '||  aa2.name
                when aa3.level = 10 then aa3.code ||' - '||  aa3.name
                when aa4.level = 10 then aa4.code ||' - '||  aa4.name
                when aa5.level = 10 then aa5.code ||' - '||  aa5.name
                when aa6.level = 10 then aa6.code ||' - '||  aa6.name
                when aa7.level = 10 then aa7.code ||' - '||  aa7.name
                when aa8.level = 10 then aa8.code ||' - '||  aa8.name
                when aa9.level = 10 then aa9.code ||' - '||  aa9.name
            end as level10
        from
        (select 
         aa.id  as aa_id,
         aa.level as aa_level,
         aa.name as aa_name,
         aa.code as aa_code,
        *

        from
        ((select
                 case
                         
                    when afr0.sign < 0 then afr0.sign
                    when afr1.sign < 0 then afr1.sign
                    when afr2.sign < 0 then afr2.sign
                    when afr3.sign < 0 then afr3.sign
                    when afr4.sign < 0 then afr4.sign
                    when afr5.sign < 0 then afr5.sign
                    else 1
                end as sign,
                afr0.id as report_p_id,
               
                case
                    when afr5.id > 0 then afr5.id 
                    when afr4.id > 0 then afr4.id 
                    when afr3.id > 0 then afr3.id
                    when afr2.id > 0 then afr2.id
                    when afr1.id > 0 then afr1.id
                    when afr0.id > 0 then afr0.id
                end as report_ids,
                afr0.name as report_type0,
                afr1.name as report_type1,
                afr2.name as report_type2,
                afr3.name as report_type3,
                afr4.name as report_type4,
                afr5.name as report_type5
                
            from
                account_financial_report afr0
                left join account_financial_report afr1 on afr0.id = afr1.parent_id
                left join account_financial_report afr2 on afr1.id = afr2.parent_id
                left join account_financial_report afr3 on afr2.id = afr3.parent_id
                left join account_financial_report afr4 on afr3.id = afr4.parent_id
                left join account_financial_report afr5 on afr4.id = afr5.parent_id
            where  COALESCE(afr0.parent_id, 0) = 0 
                and afr0.id = """+str(data['account_report_id'][0])+""") r
         left join account_account_financial_report_type aaft on aaft.report_id = r.report_ids
         left join account_account aa on aa.user_type_id = aaft.account_type_id )
         where aa.parent_id not in( (
             select aa.id as id

            from
            ((select
                afr0.id as report_p_id,
                
                case
                    when afr4.id > 0 then afr4.id 
                    when afr3.id > 0 then afr3.id
                    when afr2.id > 0 then afr2.id
                    when afr1.id > 0 then afr1.id
                    when afr0.id > 0 then afr0.id
                end as report_ids,
                afr0.name as report_type0,
                afr1.name as report_type1,
                afr2.name as report_type2,
                afr3.name as report_type3,
                afr4.name as report_type4
                
                from
                account_financial_report afr0
                left join account_financial_report afr1 on afr0.id = afr1.parent_id
                left join account_financial_report afr2 on afr1.id = afr2.parent_id
                left join account_financial_report afr3 on afr2.id = afr3.parent_id
                left join account_financial_report afr4 on afr3.id = afr4.parent_id
                where  COALESCE(afr0.parent_id, 0) = 0 
                and afr0.id = """+str(data['account_report_id'][0])+""") r
             left join account_account_financial_report_type aaft on aaft.report_id = r.report_ids
             left join account_account aa on aa.user_type_id = aaft.account_type_id )
             WHERE aa.parent_id IS NOT NULL
             order by aa.id))) r
             left join account_account aa0 on aa0.parent_id = r.aa_id 
             left join account_account aa1 on aa1.parent_id = aa0.id 
             left join account_account aa2 on aa2.parent_id = aa1.id 
             left join account_account aa3 on aa3.parent_id = aa2.id 
             left join account_account aa4 on aa4.parent_id = aa3.id 
             left join account_account aa5 on aa5.parent_id = aa4.id 
             left join account_account aa6 on aa6.parent_id = aa5.id 
             left join account_account aa7 on aa7.parent_id = aa6.id 
             left join account_account aa8 on aa8.parent_id = aa7.id 
             left join account_account aa9 on aa9.parent_id = aa8.id ) p) r

             left join account_move_line aml on aml.account_id = r.final_id
            
            """+ moves2 +""" 
            --AND aml.period_id IN (
            --    SELECT
            --        id
            --    FROM
            --        account_period
            --    )
            AND aml.move_id IN (
                SELECT 
                    id 
                FROM 
                    account_move 
                WHERE 
                    account_move.state in ("""+ moves +"""))
            """+ where_date +"""
            left join account_move am on am.id = aml.move_id
            --left join account_period ap on ap.id = aml.period_id
            left join account_analytic_account aaa0 on aaa0.id = aml.analytic_account_id 
            left join account_analytic_account aaa1 on aaa1.id = aaa0.parent_id
            left join product_product pp on pp.id = aml.product_id
            left join product_template pt on pp.product_tmpl_id = pt.id
             
            ) p
        where  report_p_id = """+str(data['account_report_id'][0])+""" """ +  where_s + """)
                      

        """
        sql2 = """
            ( select
            p.report_p_id,
            p.report_type0,
            p.report_type1,
            p.report_type2,
            p.report_type3,
            p.report_type4,
            p.report_type5,
            p.level1,
            p.level2,
            p.level3,
            p.level4,
            p.level5,
            p.level6,
            p.level7,
            p.level8,
            p.level9,
            p.level10,
           
            p.credit,
            p.debit,               
            (p.debit - p.credit) * p.sign   as total,

            ((p.debit - p.credit) * p.sign ) * """+ str(rate) +""" as total_s,
            p.credit * """+ str(rate) +""" as credit_s,
            p.debit * """+ str(rate) +""" as debit_s,

            p.aml_date as date,
            p.aml_company_id as company_id,
            p.aml_segment_id as segment_id,
            p.ap_fiscalyear_id as fiscalyear_id,
            p.analitica2,
            p.sucursales_id,
            p.analitica1,
            p.region_id
           
        from
        (select
            aml.date as aml_date,
            aml.company_id as aml_company_id,
            case 
                when aml.segment_id > 0 then aml.segment_id
                when pt.segment_id > 0 then pt.segment_id
                else null
            end as aml_segment_id,
            --ap.fiscalyear_id as ap_fiscalyear_id,
            to_char(aml.date, 'YYYY')::INTEGER as ap_fiscalyear_id,
            aaa0.name as analitica2,
            aaa0.id as sucursales_id,
            case
                  when aaa0.parent_id > 0 then aaa1.name
            end as analitica1,
            aaa1.id as region_id,
            *
        from
        (select 
            case
                when COALESCE(id9,0) > 0 then id9
                when COALESCE(id8,0) > 0 then id8
                when COALESCE(id7,0) > 0 then id7
                when COALESCE(id6,0) > 0 then id6
                when COALESCE(id5,0) > 0 then id5
                when COALESCE(id4,0) > 0 then id4
                when COALESCE(id3,0) > 0 then id3
                when COALESCE(id2,0) > 0 then id2
                when COALESCE(id1,0) > 0 then id1
            end as final_id,
                
            *
        from
        (select 
            
            
            case
                when r.aa_level = 1 then r.aa_id
                when aa0.level = 1 then aa0.id
                when aa1.level = 1 then aa1.id
                when aa2.level = 1 then aa2.id
                when aa3.level = 1 then aa3.id
                when aa4.level = 1 then aa4.id
                when aa5.level = 1 then aa5.id
                when aa6.level = 1 then aa6.id
                when aa7.level = 1 then aa7.id
                when aa8.level = 1 then aa8.id
                when aa9.level = 1 then aa9.id
            end as id1,
            case
                when r.aa_level = 2 then r.aa_id
                when aa0.level = 2 then aa0.id
                when aa1.level = 2 then aa1.id
                when aa2.level = 2 then aa2.id
                when aa3.level = 2 then aa3.id
                when aa4.level = 2 then aa4.id
                when aa5.level = 2 then aa5.id
                when aa6.level = 2 then aa6.id
                when aa7.level = 2 then aa7.id
                when aa8.level = 2 then aa8.id
                when aa9.level = 2 then aa9.id
            end as id2,
            case
                when r.aa_level = 3 then r.aa_id
                when aa0.level = 3 then aa0.id
                when aa1.level = 3 then aa1.id
                when aa2.level = 3 then aa2.id
                when aa3.level = 3 then aa3.id
                when aa4.level = 3 then aa4.id
                when aa5.level = 3 then aa5.id
                when aa6.level = 3 then aa6.id
                when aa7.level = 3 then aa7.id
                when aa8.level = 3 then aa8.id
                when aa9.level = 3 then aa9.id
            end as id3,
            case
                when r.aa_level = 4 then r.aa_id
                when aa0.level = 4 then aa0.id
                when aa1.level = 4 then aa1.id
                when aa2.level = 4 then aa2.id
                when aa3.level = 4 then aa3.id
                when aa4.level = 4 then aa4.id
                when aa5.level = 4 then aa5.id
                when aa6.level = 4 then aa6.id
                when aa7.level = 4 then aa7.id
                when aa8.level = 4 then aa8.id
                when aa9.level = 4 then aa9.id
            end as id4,
            case
                when r.aa_level = 5 then r.aa_id
                when aa0.level = 5 then aa0.id
                when aa1.level = 5 then aa1.id
                when aa2.level = 5 then aa2.id
                when aa3.level = 5 then aa3.id
                when aa4.level = 5 then aa4.id
                when aa5.level = 5 then aa5.id
                when aa6.level = 5 then aa6.id
                when aa7.level = 5 then aa7.id
                when aa8.level = 5 then aa8.id
                when aa9.level = 5 then aa9.id
            end as id5,
            case
                when r.aa_level = 6 then r.aa_id
                when aa0.level = 6 then aa0.id
                when aa1.level = 6 then aa1.id
                when aa2.level = 6 then aa2.id
                when aa3.level = 6 then aa3.id
                when aa4.level = 6 then aa4.id
                when aa5.level = 6 then aa5.id
                when aa6.level = 6 then aa6.id
                when aa7.level = 6 then aa7.id
                when aa8.level = 6 then aa8.id
                when aa9.level = 6 then aa9.id
            end as id6,
            case
                when r.aa_level = 7 then r.aa_id
                when aa0.level = 7 then aa0.id
                when aa1.level = 7 then aa1.id
                when aa2.level = 7 then aa2.id
                when aa3.level = 7 then aa3.id
                when aa4.level = 7 then aa4.id
                when aa5.level = 7 then aa5.id
                when aa6.level = 7 then aa6.id
                when aa7.level = 7 then aa7.id
                when aa8.level = 7 then aa8.id
                when aa9.level = 7 then aa9.id
            end as id7,
            case
                when r.aa_level = 8 then r.aa_id
                when aa0.level = 8 then aa0.id
                when aa1.level = 8 then aa1.id
                when aa2.level = 8 then aa2.id
                when aa3.level = 8 then aa3.id
                when aa4.level = 8 then aa4.id
                when aa5.level = 8 then aa5.id
                when aa6.level = 8 then aa6.id
                when aa7.level = 8 then aa7.id
                when aa8.level = 8 then aa8.id
                when aa9.level = 8 then aa9.id
            end as id8,
            case
                when r.aa_level = 9 then r.aa_id
                when aa0.level = 9 then aa0.id
                when aa1.level = 9 then aa1.id
                when aa2.level = 9 then aa2.id
                when aa3.level = 9 then aa3.id
                when aa4.level = 9 then aa4.id
                when aa5.level = 9 then aa5.id
                when aa6.level = 9 then aa6.id
                when aa7.level = 9 then aa7.id
                when aa8.level = 9 then aa8.id
                when aa9.level = 9 then aa9.id
            end as id9,
            r.sign,
            r.report_p_id,
            r.report_type0,
            r.report_type1,
            r.report_type2,
            r.report_type3,
            r.report_type4,
            r.report_type5,
            case
                when r.aa_level = 1 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 1 then aa0.code ||' - '||  aa0.name
                when aa1.level = 1 then aa1.code ||' - '||  aa1.name
                when aa2.level = 1 then aa2.code ||' - '||  aa2.name
                when aa3.level = 1 then aa3.code ||' - '||  aa3.name
                when aa4.level = 1 then aa4.code ||' - '||  aa4.name
                when aa5.level = 1 then aa5.code ||' - '||  aa5.name
                when aa6.level = 1 then aa6.code ||' - '||  aa6.name
                when aa7.level = 1 then aa7.code ||' - '||  aa7.name
                when aa8.level = 1 then aa8.code ||' - '||  aa8.name
                when aa9.level = 1 then aa9.code ||' - '||  aa9.name
            end as level1,
            case
                when r.aa_level = 2 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 2 then aa0.code ||' - '||  aa0.name
                when aa1.level = 2 then aa1.code ||' - '||  aa1.name
                when aa2.level = 2 then aa2.code ||' - '||  aa2.name
                when aa3.level = 2 then aa3.code ||' - '||  aa3.name
                when aa4.level = 2 then aa4.code ||' - '||  aa4.name
                when aa5.level = 2 then aa5.code ||' - '||  aa5.name
                when aa6.level = 2 then aa6.code ||' - '||  aa6.name
                when aa7.level = 2 then aa7.code ||' - '||  aa7.name
                when aa8.level = 2 then aa8.code ||' - '||  aa8.name
                when aa9.level = 2 then aa9.code ||' - '||  aa9.name
            end as level2,
            case
                when r.aa_level = 3 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 3 then aa0.code ||' - '||  aa0.name
                when aa1.level = 3 then aa1.code ||' - '||  aa1.name
                when aa2.level = 3 then aa2.code ||' - '||  aa2.name
                when aa3.level = 3 then aa3.code ||' - '||  aa3.name
                when aa4.level = 3 then aa4.code ||' - '||  aa4.name
                when aa5.level = 3 then aa5.code ||' - '||  aa5.name
                when aa6.level = 3 then aa6.code ||' - '||  aa6.name
                when aa7.level = 3 then aa7.code ||' - '||  aa7.name
                when aa8.level = 3 then aa8.code ||' - '||  aa8.name
                when aa9.level = 3 then aa9.code ||' - '||  aa9.name
            end as level3,
            case
                when r.aa_level = 4 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 4 then aa0.code ||' - '||  aa0.name
                when aa1.level = 4 then aa1.code ||' - '||  aa1.name
                when aa2.level = 4 then aa2.code ||' - '||  aa2.name
                when aa3.level = 4 then aa3.code ||' - '||  aa3.name
                when aa4.level = 4 then aa4.code ||' - '||  aa4.name
                when aa5.level = 4 then aa5.code ||' - '||  aa5.name
                when aa6.level = 4 then aa6.code ||' - '||  aa6.name
                when aa7.level = 4 then aa7.code ||' - '||  aa7.name
                when aa8.level = 4 then aa8.code ||' - '||  aa8.name
                when aa9.level = 4 then aa9.code ||' - '||  aa9.name
            end as level4,
            case
                when r.aa_level = 5 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 5 then aa0.code ||' - '||  aa0.name
                when aa1.level = 5 then aa1.code ||' - '||  aa1.name
                when aa2.level = 5 then aa2.code ||' - '||  aa2.name
                when aa3.level = 5 then aa3.code ||' - '||  aa3.name
                when aa4.level = 5 then aa4.code ||' - '||  aa4.name
                when aa5.level = 5 then aa5.code ||' - '||  aa5.name
                when aa6.level = 5 then aa6.code ||' - '||  aa6.name
                when aa7.level = 5 then aa7.code ||' - '||  aa7.name
                when aa8.level = 5 then aa8.code ||' - '||  aa8.name
                when aa9.level = 5 then aa9.code ||' - '||  aa9.name
            end as level5,
            case
                when r.aa_level = 6 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 6 then aa0.code ||' - '||  aa0.name
                when aa1.level = 6 then aa1.code ||' - '||  aa1.name
                when aa2.level = 6 then aa2.code ||' - '||  aa2.name
                when aa3.level = 6 then aa3.code ||' - '||  aa3.name
                when aa4.level = 6 then aa4.code ||' - '||  aa4.name
                when aa5.level = 6 then aa5.code ||' - '||  aa5.name
                when aa6.level = 6 then aa6.code ||' - '||  aa6.name
                when aa7.level = 6 then aa7.code ||' - '||  aa7.name
                when aa8.level = 6 then aa8.code ||' - '||  aa8.name
                when aa9.level = 6 then aa9.code ||' - '||  aa9.name
            end as level6,
            case
                when r.aa_level = 7 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 7 then aa0.code ||' - '||  aa0.name
                when aa1.level = 7 then aa1.code ||' - '||  aa1.name
                when aa2.level = 7 then aa2.code ||' - '||  aa2.name
                when aa3.level = 7 then aa3.code ||' - '||  aa3.name
                when aa4.level = 7 then aa4.code ||' - '||  aa4.name
                when aa5.level = 7 then aa5.code ||' - '||  aa5.name
                when aa6.level = 7 then aa6.code ||' - '||  aa6.name
                when aa7.level = 7 then aa7.code ||' - '||  aa7.name
                when aa8.level = 7 then aa8.code ||' - '||  aa8.name
                when aa9.level = 7 then aa9.code ||' - '||  aa9.name
            end as level7,
            case
                when r.aa_level = 8 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 8 then aa0.code ||' - '||  aa0.name
                when aa1.level = 8 then aa1.code ||' - '||  aa1.name
                when aa2.level = 8 then aa2.code ||' - '||  aa2.name
                when aa3.level = 8 then aa3.code ||' - '||  aa3.name
                when aa4.level = 8 then aa4.code ||' - '||  aa4.name
                when aa5.level = 8 then aa5.code ||' - '||  aa5.name
                when aa6.level = 8 then aa6.code ||' - '||  aa6.name
                when aa7.level = 8 then aa7.code ||' - '||  aa7.name
                when aa8.level = 8 then aa8.code ||' - '||  aa8.name
                when aa9.level = 8 then aa9.code ||' - '||  aa9.name
            end as level8,
            case
                when r.aa_level = 9 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 9 then aa0.code ||' - '||  aa0.name
                when aa1.level = 9 then aa1.code ||' - '||  aa1.name
                when aa2.level = 9 then aa2.code ||' - '||  aa2.name
                when aa3.level = 9 then aa3.code ||' - '||  aa3.name
                when aa4.level = 9 then aa4.code ||' - '||  aa4.name
                when aa5.level = 9 then aa5.code ||' - '||  aa5.name
                when aa6.level = 9 then aa6.code ||' - '||  aa6.name
                when aa7.level = 9 then aa7.code ||' - '||  aa7.name
                when aa8.level = 9 then aa8.code ||' - '||  aa8.name
                when aa9.level = 9 then aa9.code ||' - '||  aa9.name
            end as level9,
            case
                when r.aa_level = 10 then r.aa_code ||' - '|| r.aa_name
                when aa0.level = 10 then aa0.code ||' - '||  aa0.name
                when aa1.level = 10 then aa1.code ||' - '||  aa1.name
                when aa2.level = 10 then aa2.code ||' - '||  aa2.name
                when aa3.level = 10 then aa3.code ||' - '||  aa3.name
                when aa4.level = 10 then aa4.code ||' - '||  aa4.name
                when aa5.level = 10 then aa5.code ||' - '||  aa5.name
                when aa6.level = 10 then aa6.code ||' - '||  aa6.name
                when aa7.level = 10 then aa7.code ||' - '||  aa7.name
                when aa8.level = 10 then aa8.code ||' - '||  aa8.name
                when aa9.level = 10 then aa9.code ||' - '||  aa9.name
            end as level10
        from
        (select 
         aa.id  as aa_id,
         aa.level as aa_level,
         aa.name as aa_name,
         aa.code as aa_code,
        *

        from
        ((select
                afr0.id as report_p_id,
                case
                     
                    when afr0.sign < 0 then afr0.sign
                    when afr1.sign < 0 then afr1.sign
                    when afr2.sign < 0 then afr2.sign
                    when afr3.sign < 0 then afr3.sign
                    when afr4.sign < 0 then afr4.sign
                    when afr5.sign < 0 then afr5.sign
                    else 1
                end as sign,
                case
                    when afr5.id > 0 then afr5.id 
                    when afr4.id > 0 then afr4.id 
                    when afr3.id > 0 then afr3.id
                    when afr2.id > 0 then afr2.id
                    when afr1.id > 0 then afr1.id
                    when afr0.id > 0 then afr0.id
                end as report_ids,
                afr0.name as report_type0,
                afr1.name as report_type1,
                afr2.name as report_type2,
                afr3.name as report_type3,
                afr4.name as report_type4,
                afr5.name as report_type5
                
            from
                account_financial_report afr0
                left join account_financial_report afr1 on afr0.id = afr1.parent_id
                left join account_financial_report afr2 on afr1.id = afr2.parent_id
                left join account_financial_report afr3 on afr2.id = afr3.parent_id
                left join account_financial_report afr4 on afr3.id = afr4.parent_id
                left join account_financial_report afr5 on afr4.id = afr5.parent_id
            where  COALESCE(afr0.parent_id, 0) = 0 
                and afr0.id = """+str(data['account_report_id'][0])+""") r
         left join account_account_financial_report aafr on aafr.report_line_id = r.report_ids
         left join account_account aa on aa.id = aafr.account_id )
         where aa.parent_id not in( (
             select aa.id as id

            from
            ((select
                afr0.id as report_p_id,
                case
                    when afr4.id > 0 then afr4.id 
                    when afr3.id > 0 then afr3.id
                    when afr2.id > 0 then afr2.id
                    when afr1.id > 0 then afr1.id
                    when afr0.id > 0 then afr0.id
                end as report_ids,
                afr0.name as report_type0,
                afr1.name as report_type1,
                afr2.name as report_type2,
                afr3.name as report_type3,
                afr4.name as report_type4
                
                from
                account_financial_report afr0
                left join account_financial_report afr1 on afr0.id = afr1.parent_id
                left join account_financial_report afr2 on afr1.id = afr2.parent_id
                left join account_financial_report afr3 on afr2.id = afr3.parent_id
                left join account_financial_report afr4 on afr3.id = afr4.parent_id
                where  COALESCE(afr0.parent_id, 0) = 0 
                and afr0.id = """+str(data['account_report_id'][0])+""") r
             left join account_account_financial_report aafr on aafr.report_line_id = r.report_ids
             left join account_account aa on aa.id = aafr.account_id )
             WHERE aa.parent_id IS NOT NULL
             order by aa.id))) r
             left join account_account aa0 on aa0.parent_id = r.aa_id 
             left join account_account aa1 on aa1.parent_id = aa0.id 
             left join account_account aa2 on aa2.parent_id = aa1.id 
             left join account_account aa3 on aa3.parent_id = aa2.id 
             left join account_account aa4 on aa4.parent_id = aa3.id 
             left join account_account aa5 on aa5.parent_id = aa4.id 
             left join account_account aa6 on aa6.parent_id = aa5.id 
             left join account_account aa7 on aa7.parent_id = aa6.id 
             left join account_account aa8 on aa8.parent_id = aa7.id 
             left join account_account aa9 on aa9.parent_id = aa8.id ) p) r

             left join account_move_line aml on aml.account_id = r.final_id
            
            """+ moves2 +"""
            AND aml.period_id IN (
                SELECT 
                    id 
                FROM 
                    account_period 
                )  
            AND aml.move_id IN (
                SELECT 
                    id 
                FROM 
                    account_move 
                WHERE 
                    account_move.state in ("""+ moves +"""))
             """+ where_date +"""
            left join account_move am on am.id = aml.move_id
            left join account_period ap on ap.id = aml.period_id
            left join account_analytic_account aaa0 on aaa0.id = aml.analytic_account_id 
            left join account_analytic_account aaa1 on aaa1.id = aaa0.parent_id
            left join product_product pp on pp.id = aml.product_id
            left join product_template pt on pp.product_tmpl_id = pt.id
        
            ) p
        where  report_p_id = """+str(data['account_report_id'][0])+""" """ +  where_s + """)
        """

        sql = sql + "UNION ALL " + sql2
        list_sql =[]
        for rx in rep_xtras:
            rep_id = rx
            select_str3 = ""
            jerarquia = []
            flag = False
            while True:
                self.env.cr.execute(
                    """
                    select 
                            
                            COALESCE(cast(sequence as varchar(32)), '') ||''|| name,
                            parent_id

                    from 
                            account_financial_report
                    where id = ("""+ str(rep_id) +""") """)
                report_child = self.env.cr.fetchall()
                
                for rc in report_child:
                    jerarquia.append(rc[0])
                    if rc[1] > 0:
                        rep_id = rc[1]
                    else:
                        flag = True
                if flag:
                    break
            
            jerarquia.reverse()
            for n in xrange(1,7):
                if  n < len(jerarquia) :
                    select_str3 = select_str3 +  """
                        case 
                            when true then '"""+ str(jerarquia[n]) +"""'
                        end as report_type"""+ str(n) +""",
                    """ 
                else:
                     select_str3 = select_str3 + """
                        case 
                            when true then null
                        end as report_type"""+ str(n) +""",
                    """ 
               

           
            sql2 = """
               select 
                    case
                        when true then """+ str(data['account_report_id'][0]) +"""
                    end as id_rep, 
                    """+ select_str3 +"""
                    """+ select_xtra_rep +"""
                  
                    sum(a.credit) as credit, 
                    sum(a.debit) as debit,
                    sum(a.total) as total, 
                    sum(a.total_s) as total_s, 
                    sum(a.credit_s) as credit_s, 
                    sum(a.debit_s) as debit_s,
                    
                    max(a.date) as date,
                    max(a.company_id) as company_id,
                    max(a.segment_id) as segment_id,
                    max(a.fiscalyear_id) as fiscalyear_id,
                    
                    

                    max(sucursales) as analitica2,
                    sucursales_id,
                    max(region) as analitica1,
                    max(region_id) as region_id

                from
                    (select 
                    (a"""+ str(mlc) +""".debit - a"""+ str(mlc) +""" .credit) * """+ str(sign) +""" as total,
                    a"""+ str(mlc) +""".credit,
                    a"""+ str(mlc) +""".debit,
            
                    ((a"""+ str(mlc) +""".debit - a"""+ str(mlc) +""" .credit) * """+ str(sign) +""") * """+ str(rate) +""" as total_s,
                    a"""+ str(mlc) +""".credit * """+ str(rate) +""" as credit_s,
                    a"""+ str(mlc) +""".debit * """+ str(rate) +""" as debit_s,

                    a"""+ str(mlc) +""".fiscalyear_id,
                    a"""+ str(mlc) +""".date,
                    a"""+ str(mlc) +""".company_id,
                    a"""+ str(mlc) +""".segment_id,
                    
                    """+ select +""",


                    aaa1.name as sucursales,
                    aaa1.id as sucursales_id,
                    case
                        when aaa1.parent_id > 0 then aaa0.name
                    end as region,
                    aaa0.id as region_id
                    
                    from
                        (select 
                            aa.id,
                            aml.credit,
                            aml.debit,
                            --ap.fiscalyear_id,
                            to_char(aml.date,'YYYY')::INTEGER as fiscalyear_id,
                            aa.name,
                            aa.code,
                            aa.user_type_id,
                            aa.parent_id,
                            aa.level,
                            aaft.report_id,
                            aaa.id as sucursales,
                            aml.date,
                            aml.company_id,
                            case
                                when aml.segment_id > 0 then aml.segment_id
                                when pt.segment_id > 0 then pt.segment_id
                                else null
                            end as segment_id
                            
                                      
                        from
                            account_move_line aml
                            inner join account_move am on am.id = aml.move_id
                            left join account_account aa on aa.id = aml.account_id
                            left join account_account_type aat on aat.id = aa.user_type_id
                            --left join account_period ap on ap.id = aml.period_id
                            left join account_account_financial_report_type aaft on aaft.account_type_id = aa.user_type_id
                            left join account_analytic_account aaa on aaa.id = aml.analytic_account_id 
                            left join product_product pp on pp.id = aml.product_id
                            left join product_template pt on pp.product_tmpl_id = pt.id

                            
                        
                        where 
                       
                        --aml.period_id IN (
                        --    SELECT
                        --        id
                        --    FROM
                        --        account_period
                        --    )
                        AND aml.move_id IN (
                            SELECT 
                                id 
                            FROM 
                                account_move 
                            WHERE 
                                account_move.state in ("""+ moves +"""))
                        """+ moves2 +"""
                        """+ where_date +"""
                       
                
                        
                        ) as a"""+ str(mlc) +""" 
                     """+ fr +"""
                    left join account_analytic_account aaa1 on aaa1.id = a"""+ str(mlc) +""".sucursales
                    left join account_analytic_account aaa0 on aaa0.id = aaa1.parent_id
                     ) as a
                where a.id_rep = """+str(rep_xtras[rx][0])+""" """+ where_s +""" and level0 = """+ str(data['char_account_id'][0]) +"""
                group by 
                    report_type0,
                    sucursales_id,
                    date
            """
            list_sql.append(sql2)
        if len(list_sql) > 0:
            sql = """ (""" + sql + """)""" 
            for consulta in list_sql:
                sql =  """"""+ sql +"""UNION ALL ("""+ consulta +""") """


        self.env['poi.estado.resultados'].init(select=sql, mlc=mlc, mlr=mlr)
        ctx = {}
        ctx['search_default_group_report'] = 1
        
        date = ""
        if data['date_from']:
            date = """('date', '>=', '"""+ data['date_from']+ """')"""
        if data['date_until'] and data['date_from']:
            date = date + """,('date', '<=', '"""+ data['date_until'] +"""') """ 
        elif data['date_until']:
            date = """('date', '<=', '"""+ data['date_until'] +"""') """
        if len(date) > 3:
            date = """[""" + date + """] """ 
        return {
            #'domain': date,
            'name': data['account_report_id'][1],
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'poi.estado.resultados',
            'type': 'ir.actions.act_window',
            'context': ctx
        }