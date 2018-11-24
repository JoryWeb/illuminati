import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class SaleType(models.Model):
    _name = 'sale.type'
    _description = 'Tipos de Venta para Toyosa'

    name = fields.Char('Descripcion')
    active = fields.Boolean("Activo",  default=True, help="Dertermina si el tipo de Venta esta activo en el sistema")
    #Cotizacion
    chasis_flag = fields.Boolean('Chasis Requerido', help="Al estar marcado el campo chasis siempre sera requerido para poder crear la cotizacion.")
    booking = fields.Selection(
        string="Reserva",
        selection=[
            ('discount', 'A partir de la Aprobacion del Descuento.'),
            ('sale', 'A partir de la confirmacion de la Venta.'),
            ('advanced', 'A partir del Primer Adelanto se Habilita el boton de Reserva.'),
            ('without', 'Sin Reserva.'),
        ], help="En que momento se lleva a cabo la reserva del chasis."
    )

    partner_id = fields.Many2one('res.partner', 'Cliente')
    discount_flag = fields.Boolean('Descuento', help=u"Entrar al circuito de Autorización")
    auth_id = fields.Many2one('poi.auth.auth', 'Circuito de Autorizacion', domain=[('model_id.model', '=', 'sale.order')])
    print_order = fields.Many2one('ir.actions.report', u'Impresion de Cotización', domain=[('model','in',['sale.order']),], help=u"Template(reporte) de la Cotización a imprimir")
    print_invoice = fields.Many2one('ir.actions.report', u'Impresion de Factura', domain=[('model','in',['account.invoice']), ],  help=u"Template(reporte) de la Factura a imprimir.")
    edit_discount = fields.Boolean('Descuento Editable', help=u"Permite la edición del Campo 'Descuento'.", default=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Tarifa de Venta Sin Seguro')
    pricelist_insurance_id = fields.Many2one('product.pricelist', 'Tarifa de Venta Con Seguro')
    dealsheet_flag = fields.Boolean('Dealsheet', help="Se agregara el dealsheet a la cotizacion")
    contract_type_id = fields.Many2one('sale.contract', 'Contrato')
    booking_type_id = fields.Many2one('stock.reserve.type' ,'Tipo de Reserva')
    edit_price = fields.Boolean('Precio Editable')
    bidding_sale = fields.Boolean('Licitacion', help="El tipo de Venta es de licitaciones.")
    #Para facturacion
    pay_invoice = fields.Boolean('Pago del 100%', help='Pago al 100%, Para la entrega del albaran')
    nationalized_car = fields.Boolean('Vehiculo Nacionalizado')
    edit_nit = fields.Boolean('Bloquear Edicion de Nit', default=True)
    edit_razon = fields.Boolean('Bloquear Edicion de Razon', default=True)
    car_released = fields.Boolean('Vehiculo Liberado')
    # amount_min = fields.Float('Monto Minimo para la Reserva', related="booking_type_id.monto_minimo", readonly=True)
    percent_min = fields.Float('Porcentaje Minimo', help="Porcentaje minimo adelantado para la validacion de la factura.")
    check_chasis = fields.Boolean('Validar Chasis', help="Si esta marcado se realizara la comprabacion del chasis en caso contrario se omitira.")
    check_chasis_pre = fields.Boolean('Validar Chasis pre-facturacion', help="Si esta marcado se realizara la comprabacion del chasis para hacer la correspondiente facturacion desde la orden de venta.")
    paymemt_term_ids = fields.Many2many('account.payment.term', 'sale_type_payment_term_rel', 'sale_type_id', 'term_id', string='Terminos de Pago')

    sale_cif = fields.Boolean('Venta Cif Zona Franca', default=False, help="Determina si la venta es en zona Franca")

    invoice_type = fields.Selection(
        string="Tipo de Facturacion",
        selection=[
            ('invoice_type_1', 'Facturacion Normal'),
            ('invoice_type_2', 'Facturacion de Automotores'),

        ], default="invoice_type_1", help="Al Crear la Factura se lo hara a travez de uno de estos dos metodos. El primero es una facturacion normal donde se muestran todos los productos. El segundo Facturacion de Automotores crea la factura Agrupando todo en una sola linea."
    )


    plate_procesing = fields.Selection(
        string="Tramite de Placas",
        selection=[
            ('valid_invoice', 'Realizar al Validar la Factura.'),
            ('without_plate', 'Sin tramite.'),

        ], default="without_plate", help="Cuando se realiza el tramite de placas."
    )


class SaleOrderType(models.Model):
    _name = 'sale.order.type'
    _description = 'Tipos de Cotizacion para Toyosa'

    name = fields.Char('Descripcion')
    sale_type_ids = fields.Many2many('sale.type', 'sale_order_type_rel',  'sale_type_id', 'sale_order_type_id', string='Tipos de Venta')
