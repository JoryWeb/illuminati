# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, models, fields, tools

# ---------------------------------------------------------
# Account Financial Report
# ---------------------------------------------------------


class poi_bancarizacion(models.Model):
    _name='poi.bol.bancarizacion.report'
    _description = "Reporte de Bancarizacion"
    _auto = False
    
    type = fields.Char('Type',size=3)
    modalidad = fields.Integer('Modalidad')
    fecha_doc = fields.Date('Fecha Documento', help=u'fecha del documento con el que se realizó la transacción. Igual o mayor 50 mil')
    tipo_transaccion = fields.Integer('Tipo transaccion')
    nit = fields.Char('NIT Cliente', size=11, help="NIT o CI del cliente.")
    razon = fields.Char(u'Razón Social', help=u"Nombre o Razón Social para la Factura.")
    cc_nro = fields.Char(u'Número factura')
    nro_contrato = fields.Char(u'Número Contrato')
    total_factura = fields.Float('Monto factura')
    cc_aut = fields.Char(u"Número de autorización")
    nro_cuenta = fields.Char('Número de cuenta', size=32)
    monto_pagado = fields.Float('Monto Pagado')
    monto_total_pagado = fields.Float('Monto acumulado')
    nit_banco = fields.Char('NIT Banco', size=12, help="NIT del banco.")
    nro_transaccion = fields.Char(u'Número de Transacción', size=16)
    tipo_doc_pago = fields.Integer('Tipo Documento')
    fecha_transaccion = fields.Date('Fecha de Transacción')
    
    def init(self, cr):

        function_query = """
        CREATE OR REPLACE FUNCTION get_amount_paid_in(date_end timestamp, function_invoice_id int) RETURNS float AS $$
    DECLARE
        total_paid float;
        BEGIN
        SELECT INTO total_paid( 
SELECT 
	sum(ap.amount / tcp.rate)
FROM account_invoice_payment_rel aipr
LEFT JOIN account_invoice ai
	ON ai.id = aipr.invoice_id
LEFT JOIN account_payment ap
	ON ap.id = aipr.payment_id
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tcp 
	on (ap.payment_date between tcp.from_date and tcp.to_date) and (ap.currency_id = tcp.currency_id)
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tci 
	on (ai.date_invoice between tci.from_date and tcp.to_date) and (ai.currency_id = tci.currency_id)
WHERE ap.state = 'posted'
AND ai.type = 'in_invoice'
AND ai.state in ('paid','open')
AND ap.payment_date<=date_end
AND ai.id=function_invoice_id);
        RETURN total_paid;
        END;
$$ LANGUAGE plpgsql;
        """
        cr.execute(function_query)
        
        function_query2 = """
        CREATE OR REPLACE FUNCTION get_amount_paid_out(date_end timestamp, function_invoice_id int) RETURNS float AS $$
    DECLARE
        total_paid float;
        BEGIN
        SELECT INTO total_paid( 
SELECT 
	sum(ap.amount / tcp.rate)
FROM account_invoice_payment_rel aipr
LEFT JOIN account_invoice ai
	ON ai.id = aipr.invoice_id
LEFT JOIN account_payment ap
	ON ap.id = aipr.payment_id
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tcp 
	on (ap.payment_date between tcp.from_date and tcp.to_date) and (ap.currency_id = tcp.currency_id)
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tci 
	on (ai.date_invoice between tci.from_date and tcp.to_date) and (ai.currency_id = tci.currency_id)
WHERE ap.state = 'posted'
AND ai.type = 'out_invoice'
AND ai.state in ('paid','open')
AND ap.payment_date<=date_end
AND ai.id=function_invoice_id);
        RETURN total_paid;
        END;
$$ LANGUAGE plpgsql;
        """
        cr.execute(function_query2)
        
        tools.sql.drop_view_if_exists(cr, 'poi_bol_bancarizacion_report')
        query_to_exe = """
            CREATE or replace view poi_bol_bancarizacion_report as (
(
SELECT 
	ap.id, 
	'in' as type,
	CASE WHEN ai.amount_total/tci.rate=ap.amount/tcp.rate THEN 1 ELSE 2 END as modalidad,
	ap.payment_date as fecha_doc,
	1 as tipo_transaccion, -- 1 compra con factura, 2 compra con retenciones, 3 compra de inmuebles
	coalesce(ai.nit,'0') as nit,
	coalesce(ai.razon,'') as razon,
	coalesce(ai.cc_nro,'0') as cc_nro,
	cast('0' as varchar) as nro_contrato,
	ai.amount_total/tci.rate as total_factura,
	coalesce(ai.cc_aut,'0') as cc_aut, -- 4 en retenciones
	ap.bank_account_number as nro_cuenta, -- No cuenta desde la que se pago
	ap.amount as monto_pagado,
	get_amount_paid_in(cast(ap.payment_date as timestamp), ai.id) as monto_total_pagado,
	rb.nit as nit_banco, 
	ap.transaction_number as nro_transaccion,
	bbpt.payment_document_type as tipo_doc_pago,
	ap.transaction_date as fecha_transaccion
FROM account_invoice_payment_rel aipr
LEFT JOIN account_invoice ai
	ON ai.id = aipr.invoice_id
LEFT JOIN account_payment ap
	ON ap.id = aipr.payment_id
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tcp 
	on (ap.payment_date between tcp.from_date and tcp.to_date) and (ap.currency_id = tcp.currency_id)
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tci 
	on (ai.date_invoice between tci.from_date and tcp.to_date) and (ai.currency_id = tci.currency_id)
LEFT JOIN res_bank rb
	ON ap.bank = rb.id
LEFT JOIN account_journal aj
	ON aj.id = ap.journal_id
LEFT JOIN bol_bank_payment_type bbpt
	ON bbpt.id = aj.bank_payment_type
WHERE ap.state = 'posted'
AND ai.type = 'in_invoice'
AND ai.state in ('paid','open')
AND ap.amount>0
AND bbpt.payment_document_type is not null
ORDER BY ai.id asc
)
UNION(
SELECT 
	ap.id, 
	'out' as type,
	CASE WHEN ai.amount_total/tci.rate=ap.amount/tcp.rate THEN 1 ELSE 2 END as modalidad,
	payment_date as fecha_doc,
	0 as tipo_transaccion, --no se usa
	-- aqui viene cc_nro
	-- aqui viene total_factura
	-- aqui viene nro_contrato
	-- aqui viene cc_aut
	coalesce(ai.nit,'0') as nit,
	coalesce(ai.razon,'') as razon,
	coalesce(ai.cc_nro,'0') as cc_nro, --NO es aqui
	cast('0' as varchar) as nro_contrato, -- no es aqui
	ai.amount_total/tci.rate as total_factura, -- no es aqui
	coalesce(ai.cc_aut,'0') as cc_aut, -- no es aqui
	ap.bank_account_number as nro_cuenta,
	ap.amount as monto_pagado,
	get_amount_paid_out(cast(ap.payment_date as timestamp), ai.id) as monto_total_pagado,
	rb.nit as nit_banco, 
	ap.transaction_number as nro_transaccion,
	bbpt.payment_document_type as tipo_doc_pago,
	ap.transaction_date as fecha_transaccion
FROM account_invoice_payment_rel aipr
LEFT JOIN account_invoice ai
	ON ai.id = aipr.invoice_id
LEFT JOIN account_payment ap
	ON ap.id = aipr.payment_id
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tcp 
	on (ap.payment_date between tcp.from_date and tcp.to_date) and (ap.currency_id = tcp.currency_id)
LEFT JOIN (
	select  cr.currency_id,
		cr.name::date as from_date,
		cr.rate,
		coalesce(((LAG(cr.name::date) over (PARTITION BY cr.currency_id order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
	from res_currency_rate cr
	where cr.currency_id is not null
	order by cr.name::date desc
) as tci 
	on (ai.date_invoice between tci.from_date and tcp.to_date) and (ai.currency_id = tci.currency_id)
LEFT JOIN res_bank rb
	ON ap.bank = rb.id
LEFT JOIN account_journal aj
	ON aj.id = ap.journal_id
LEFT JOIN bol_bank_payment_type bbpt
	ON bbpt.id = aj.bank_payment_type
WHERE ap.state = 'posted'
AND ai.type = 'out_invoice'
AND ai.state in ('paid','open')
AND ap.amount>0
AND bbpt.payment_document_type is not null
ORDER BY ai.id asc
)
            )"""
        
        cr.execute(query_to_exe)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}

        args.append(['total_factura', '>=', 50000])

        return super(poi_bancarizacion, self).search(args, offset, limit, order, count=count)

poi_bancarizacion()