from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bo = fields.Integer(string=u'% B2O3')
    ho = fields.Integer(string=u'% H2O')
    dry_base = fields.Integer(string=u'Base seca')
    sampling_date = fields.Date(string=u'Fecha de Muestreo')
    date_analisys = fields.Date(string=u'Fecha de Análisis')
    exa = fields.Integer(string=u'Base seca')
    delivery_type_alv = fields.Selection([('parcial', 'Parcial'),
                                          ('todo', 'Todo junto')],
                                         string=u'Método de entrega', default='')

    priority_type_alv = fields.Selection([('normal', 'Normal'),
                                          ('urgente', 'Urgente'),
                                          ('muyurgente', 'Muy Urgente')],
                                         string=u'Prioridad', default='')

    location_origin = fields.Char(string=u'Ubicación origen')
    reference_client = fields.Char(string=u'Referencia cliente')
    loading_order = fields.Char(string=u'Orden de carga OC')
    expiration_invoice = fields.Char(string=u'Nro Lote/factura exp:')
    responsable = fields.Char(string=u'Responsable')
    type_transp = fields.Selection([('barco', 'Barco'),
                                    ('barco', 'Barco'),
                                    ('tren', 'Tren')],
                                   string=u'Tipo de Transporte', default='')
    cellar = fields.Char(string=u'Bodega')
    date_send_cellar_trasp = fields.Date(string=u'Fecha entrega de bodega')
    cant_coat_cellar_trasp = fields.Integer(string=u'Cantidad Sacos en Bodega')
    shipment_trasp = fields.Char(string=u'Nro. Embarque')
    reference_trasp = fields.Char(string=u'Referencia PO')
    carga_manifest = fields.Char(string=u'Manifesto Internacional de Carga')
    formlol_sealed = fields.Boolean(string=u'Gobernación Formulario 101 Sellado')
    inter_rail_transport = fields.Char(string=u'Transporte Internacional Ferroviario')
    send_metod_trasp = fields.Selection([('parcial', 'Parcial'),
                                         ('todojunto', 'Todo unto')],
                                        string=u'Método de entrega', default='')
    priority_trasp = fields.Selection([('nourgente', 'No urgente'),
                                       ('normal', 'Normal'),
                                       ('urgente', 'Urgente'),
                                       ('muyurgente', 'Muy urgente')],
                                      string=u'Prioridad', default='')
