##############################################################################
# For copyright and license notices, see __odoo__.py file in root directory
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError, Warning
import odoo.addons.decimal_precision as dp
import calendar
import unicodedata
import operator

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    n_produccion = fields.Char(u"Número de Producción", readonly=False, states={'done': [('readonly', True)]})
    barco = fields.Char(string=u"Barco", states={'done': [('readonly', True)]}, copy=False)
    transportista = fields.Many2one("res.partner", string=u"Transportista")
    placa = fields.Char(string=u"Placa", states={'done': [('readonly', True)]})
    tipo = fields.Selection(string=u"Tipo", related='picking_type_id.code', readonly=True)
    n_guia = fields.Char(string=u"N° de Guia", states={'done': [('readonly', True)]})
    #order_id = fields.Many2one('sale.order', 'Orden de Venta', compute="_compute_order_id", store=True)
    #order_check = fields.Boolean('Orden de Venta?', compute="_compute_order_id", store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Cuenta Analitica')

    # Refactorizar funcion, ya no existe el campo procurement_ids
    # @api.multi
    # @api.depends("group_id")
    # def _compute_order_id(self):
    #     for s in self:
    #         if s.picking_type_code == 'outgoing':
    #             if s.group_id and s.group_id.procurement_ids:
    #                 for p in s.group_id.procurement_ids:
    #                     if p.sale_line_id and p.sale_line_id.order_id:
    #                         s.order_id = p.sale_line_id.order_id.id
    #                         s.order_check = True

    @api.multi
    def action_view_quant(self):
        '''
        Funcion necesaria para obtener los quants asignados a este chasis
        '''
        lot_ids = []
        for move in self.move_lines:
            for move_l in move.move_line_ids:
                lot_ids.append(move_l.lot_id.id)
        action = self.env.ref('poi_x_toyosa.action_poi_stock_reservation_lot_tree')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.view_poi_stock_reservation_lot_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        # result['context'] = "{'default_imports': %d}" % imports.id
        result['domain'] = "[('id','in',[" + ','.join(map(str, lot_ids)) + "])]"
        return result

    @api.multi
    def action_view_incidence(self):
        '''
        Funcion necesaria para obtener las incidencias registradas por Chasis
        '''
        incidence_ids = []
        # Obtener los ids de lotes registrados en el picking
        for move in self.move_lines:
            for move_l in move.move_line_ids:
                incidence_ids += move_l.lot_id.incidencia.ids
                # incidence_ids += inci.ids
        action = self.env.ref('poi_x_toyosa.stock_lot_incidence_action')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.view_stock_lot_incidence_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['domain'] = "[('id','in',[" + ','.join(map(str, incidence_ids)) + "])]"
        return result

    @api.multi
    def action_view_chasis(self):
        '''
        Funcion necesaria para obtener los quants asignados a este chasis
        '''
        quant_ids = []
        lot_ids = []
        for move in self.move_lines:
            for quant in move.quant_ids:
                lot_ids.append(quant.lot_id.id)
        action = self.env.ref('poi_x_toyosa.action_estado_importaciones_albaran')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.view_estado_importaciones_albaran', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['domain'] = "[('id','in',[" + ','.join(map(str, lot_ids)) + "])]"
        return result


    @api.multi
    def LeerAlbaranes(self, location_id, state=''):
        picking_operation_list = []
        # Albaranes de entrada
        pickings = self.search([('location_dest_id', '=', location_id), ('state', '=', state)])
        for picking in pickings:
            dest_seg_albaran_id = 0
            for move in picking.move_lines:
                if move.move_orig_ids:
                    dest_seg_albaran_id = move.move_orig_ids.location_dest_id.id

            for pack_lot in picking.move_line_ids:
                unicode_char = pack_lot.location_id.complete_name
                output1 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
                unicode_char = pack_lot.location_dest_id.complete_name
                output2 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')

                list_pack = {
                    'anio_modelo': pack_lot.lot_id.anio_modelo.name or '',
                    'chasis': pack_lot.lot_id.name or '',
                    'cod_ant_destino': pack_lot.location_dest_id.cod_antiguo or '',
                    'cod_ant_origen': pack_lot.location_id.cod_antiguo or '',
                    'cod_master': pack_lot.lot_id.product_id.default_code or '',
                    'destino_2do_albaran': dest_seg_albaran_id,
                    'destino_id': pack_lot.location_dest_id.id,
                    'estado_albaran': picking.state,
                    'id_transaccion_odoo': picking.id,
                    'marca': pack_lot.lot_id.product_id.modelo.marca.name or '',
                    'origen_id': pack_lot.location_id.id,
                    'pack_lot_id': pack_lot.id,
                    'tipo_albaran': picking.picking_type_id.code,
                    'tipo_ubicacion_destino': pack_lot.location_dest_id.usage or '',
                    'tipo_ubicacion_origen': pack_lot.location_id.usage or '',
                }
                picking_operation_list.append(list_pack)

        # Albaranes de Salida
        pickings = self.search([('location_id', '=', location_id), ('state', '=', state)])
        for picking in pickings:
            dest_seg_albaran_id = 0
            for move in picking.move_lines:
                if move.move_orig_ids:
                    dest_seg_albaran_id = move.move_orig_ids.location_dest_id.id
                for pack_lot in move.move_line_ids:
                    unicode_char = pack_lot.location_id.complete_name
                    output1 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
                    unicode_char = pack_lot.location_dest_id.complete_name
                    output2 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')

                    list_pack = {
                        'anio_modelo': pack_lot.lot_id.anio_modelo.name or '',
                        'chasis': pack_lot.lot_id.name or '',
                        'cod_ant_destino': pack_lot.location_dest_id.cod_antiguo or '',
                        'cod_ant_origen': pack_lot.location_id.cod_antiguo or '',
                        'cod_master': pack_lot.lot_id.product_id.default_code or '',
                        'destino_2do_albaran': dest_seg_albaran_id,
                        'destino_id': pack_lot.location_dest_id.id,
                        'estado_albaran': picking.state,
                        'id_transaccion_odoo': picking.id,
                        'marca': pack_lot.lot_id.product_id.modelo.marca.name or '',
                        'origen_id': pack_lot.location_id.id,
                        'pack_lot_id': pack_lot.id,
                        'tipo_albaran': picking.picking_type_id.code,
                        'tipo_ubicacion_origen': pack_lot.location_id.usage or '',
                        'tipo_ubicacion_destino': pack_lot.location_dest_id.usage or '',
                    }
                    picking_operation_list.append(list_pack)
        return picking_operation_list

    @api.multi
    def LeerStock(self, location_id):
        stock_list = []
        # Stock de picking según picking_id
        quants = self.env['stock.quant'].search(
            [('location_id', '=', location_id), ('location_id.usage', 'in', ('internal', 'transit'))])
        for quant in quants:
            if quant.location_id:
                stock_quant = {
                    'anio_modelo': quant.lot_id.anio_modelo.name or '',
                    'chasis': quant.lot_id.name or '',
                    'chasis_id': quant.lot_id.id,
                    'cod_antiguo': quant.location_id.cod_antiguo or '',
                    'cod_master': quant.lot_id.product_id.default_code or '',
                    'marca': quant.lot_id.product_id.modelo.marca.name or '',
                    'ubicacion_stock': quant.location_id.name or '',

                }
                stock_list.append(stock_quant)
        return stock_list

    @api.multi
    def LeerChasis(self):
        lot_list = []
        # Stock de picking según picking_id
        lots = self.env['stock.production.lot'].search([('product_id.tracking', '=', 'serial')])
        for lot in lots:
            if lot.location_id:
                unicode_char = lot.location_id.complete_name
                output = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
                cod_antiguo = lot.location_id.cod_antiguo
            else:
                output = ''
                cod_antiguo = ''
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', lot.location_id.id)])
            cod_localidad = ''
            for ware in warehouse:
                cod_localidad = ware.city
            lot_data = {
                'anio_modelo': lot.anio_modelo.name or '',
                'chasis': lot.name or '',
                'chasis_id': lot.id,
                'cod_antiguo_ubicacion': cod_antiguo or '',
                'codigo_master': lot.product_id.default_code or '',
                'codigo_modelo': lot.product_id.katashiki.name or '',
                'codigo_ubicacion': lot.location_id.id or '',
                'color_externo': lot.colorexterno.name or '',
                'color_interno': lot.colorinterno.name or '',
                'estado': lot.state or '',
                'liberado': lot.state_finanzas or '',
                'marca': lot.product_id.modelo.marca.name or '',
                'master': lot.product_id.name or '',
                'modelo': lot.product_id.modelo.name or '',
                'modelo_generico': lot.product_id.categ_id.name or '',
                'nacionalizado': lot.state_importaciones or '',
                'nombre_localidad': cod_localidad or '',
                'nombre_ubicacion': output or '',
            }
            lot_list.append(lot_data)
        return lot_list

    @api.multi
    def LeerUsuarios(self):
        usuario_list = []
        # Stock de picking según picking_id
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('poi_x_toyosa.group_codigobarras'):
                usuario = {
                    'id_usuario': user.id,
                    'usuario': user.partner_id.user_cod_barras or '',
                    'password': user.password_crypt or '',
                    'nombre': user.name or '',
                    'correo': user.partner_id.email or '',
                    'cod_localidad': user.partner_id.city or '',
                    'cod_cargo': user.partner_id.user_cod_cargo or '',
                    'cod_sucursal': user.shop_assigned.other_info or '',
                    'activo': user.active,
                    'departamento': user.partner_id.state_id.name or '',
                }
                usuario_list.append(usuario)
        return usuario_list

    @api.multi
    def ConfirmarChasis(self, pack_lot_id):
        pack_lot = self.env['stock.move.line'].browse(pack_lot_id)
        if pack_lot.product_uom_qty > pack_lot.qty_done:
            pack_lot.qty_done = 1
            return [{'chasis_confirmado': pack_lot.lot_id.name}]
        else:
            return [{'chasis_confirmado': 'Ya se confirmo:' + str(pack_lot.lot_id.name)}]

    @api.multi
    def ValidarChasis(self, chasis):
        chasis = self.env['stock.production.lot'].search([('name', '=', chasis)])
        if len(chasis) > 0:
            return [{'chasis_id': chasis[0].id,
                     'cod_master': chasis[0].product_id.default_code,
                     'anio_modelo': chasis[0].anio_modelo.name,
                     'existe': True}]
        else:
            return [{'chasis_id': 0,
                     'cod_master': '',
                     'anio_modelo': '',
                     'existe': False}]

    @api.multi
    def ObtenerChasisId(self, chasis):
        chasis = self.env['stock.production.lot'].search([('name', '=', chasis)])
        if len(chasis) > 0:
            return chasis[0].id
        else:
            return 0

    @api.multi
    def LeerAlbaranesWeb(self, chasis_id, location_id, state=''):
        picking_operation_list = []
        # Albaranes de entrada
        pickings = self.search([('location_dest_id', '=', location_id), ('state', '=', state)])
        for picking in pickings:
            dest_seg_albaran_id = 0
            for move in picking.move_lines:
                if move.move_orig_ids:
                    dest_seg_albaran_id = move.move_orig_ids.location_dest_id.id

                for pack_lot in move.move_line_ids:
                    if chasis_id == pack_lot.lot_id.id:
                        unicode_char = pack_lot.location_id.complete_name
                        output1 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
                        unicode_char = pack_lot.location_dest_id.complete_name
                        output2 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')

                        list_pack = {
                            'chasis': pack_lot.lot_id.name or '',
                            'cod_master': pack_lot.lot_id.product_id.default_code or '',
                            'anio_modelo': pack_lot.lot_id.anio_modelo.name or '',
                            'marca': pack_lot.lot_id.product_id.modelo.marca.name or '',
                            'origen_id': pack_lot.location_id.id,
                            'cod_ant_origen': pack_lot.location_id.cod_antiguo or '',
                            'tipo_ubicacion_origen': pack_lot.location_id.usage or '',
                            'destino_id': pack_lot.location_dest_id.id,
                            'cod_ant_destino': pack_lot.location_dest_id.cod_antiguo or '',
                            'tipo_ubicacion_destino': pack_lot.location_dest_id.usage or '',
                            'id_transaccion_odoo': picking.id,
                            'tipo_albaran': picking.picking_type_id.code,
                            'estado_albaran': picking.state,
                            'pack_lot_id': pack_lot.id,
                            'destino_2do_albaran': dest_seg_albaran_id,
                        }
                        picking_operation_list.append(list_pack)

        # Albaranes de Salida
        pickings = self.search([('location_id', '=', location_id), ('state', '=', state)])
        for picking in pickings:
            dest_seg_albaran_id = 0
            for move in picking.move_lines:
                if move.move_orig_ids:
                    dest_seg_albaran_id = move.move_orig_ids.location_dest_id.id
                for pack_lot in move.move_line_ids:
                    if chasis_id == pack_lot.lot_id.id:
                        unicode_char = pack_lot.location_id.complete_name
                        output1 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
                        unicode_char = pack_lot.location_dest_id.complete_name
                        output2 = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
                        list_pack = {
                            'chasis': pack_lot.lot_id.name or '',
                            'cod_master': pack_lot.lot_id.product_id.default_code or '',
                            'anio_modelo': pack_lot.lot_id.anio_modelo.name or '',
                            'marca': pack_lot.lot_id.product_id.modelo.marca.name or '',
                            'origen_id': pack_lot.location_id.id,
                            'cod_ant_origen': pack_lot.location_id.cod_antiguo or '',
                            'tipo_ubicacion_origen': pack_lot.location_id.usage or '',
                            'destino_id': pack_lot.location_dest_id.id,
                            'cod_ant_destino': pack_lot.location_dest_id.cod_antiguo or '',
                            'tipo_ubicacion_destino': pack_lot.location_dest_id.usage or '',
                            'id_transaccion_odoo': picking.id,
                            'tipo_albaran': picking.picking_type_id.code,
                            'estado_albaran': picking.state,
                            'pack_lot_id': pack_lot.id,
                            'destino_2do_albaran': dest_seg_albaran_id,
                        }
                        picking_operation_list.append(list_pack)
        return picking_operation_list

    @api.multi
    def CancelarConfirmacionChasis(self, pack_lot_id):
        pack_lot = self.env['stock.pack.operation.lot'].browse(pack_lot_id)
        pack_lot.do_minus()
        return [{'chasis_no_confirmado': pack_lot.lot_id.name}]

    @api.multi
    def RegistrarIncidencias(self, pack_lot_id, incidencias):
        pack_lot = self.env['stock.move.line'].browse(pack_lot_id)
        for incidencia_array in incidencias:
            type = self.env['stock.lot.incidence.type'].search([('name', '=', incidencia_array['tipo'])])
            if not type:
                type = self.env['stock.lot.incidence.type'].create({'name': incidencia_array['tipo']})

            if incidencia_array['user_id']:
                val_incidence = {
                    'name': incidencia_array['name'],
                    'tipo': type[0].id,
                    'recordatorio': incidencia_array['user_id'],
                    'cantidad_fabrica': incidencia_array['cantidad_fabrica'],
                    'cantidad_revisada': incidencia_array['cantidad_revisada'],
                    'posicion': incidencia_array['posicion'],
                    'clasificacion': incidencia_array['clasificacion'],
                    'observaciones': incidencia_array['observaciones'],
                }
                incidencia = self.env['stock.lot.incidence'].create(val_incidence)
                self._cr.execute(
                    "insert into  stock_lot_incidence_stock_move_line_rel (stock_move_line_id, stock_lot_incidence_id) values(%s,%s)",
                    (pack_lot.id, incidencia.id))
                for file in incidencia_array['files']:
                    imagen = file['imagen']
                    attach_vals = {'res_model': 'stock.lot.incidence',
                                   'name': file['name'],
                                   'res_id': incidencia.id,
                                   'datas': imagen,
                                   'datas_fname': file['name_file']}
                    file_id = self.env['ir.attachment'].create(attach_vals)
                    self._cr.execute("insert into stock_lot_attachment_ir_rel (hr_id, attachment_id) values(%s,%s)",
                                     (incidencia.id, file_id.id))
                return "Incidencia Registrada"
            else:
                return "El usuario seleccionado no existe"

    @api.multi
    def RegistrarIncidenciasLote(self, lot_id, incidencias):
        lot = self.env['stock.production.lot'].browse(lot_id)
        for incidencia_array in incidencias:
            type = self.env['stock.lot.incidence.type'].search([('name', '=', incidencia_array['tipo'])])
            if not type:
                type = self.env['stock.lot.incidence.type'].create({'name': incidencia_array['tipo']})

            if incidencia_array['user_id']:
                val_incidence = {
                    'name': incidencia_array['name'],
                    'tipo': type[0].id,
                    'recordatorio': incidencia_array['user_id'],
                    'cantidad_fabrica': incidencia_array['cantidad_fabrica'],
                    'cantidad_revisada': incidencia_array['cantidad_revisada'],
                    'posicion': incidencia_array['posicion'],
                    'clasificacion': incidencia_array['clasificacion'],
                    'observaciones': incidencia_array['observaciones'],
                }
                incidencia = self.env['stock.lot.incidence'].create(val_incidence)
                self._cr.execute(
                    "insert into stock_lot_incidence_stock_production_lot_rel (stock_production_lot_id, stock_lot_incidence_id) values(%s,%s)",
                    (lot.id, incidencia.id))
                for file in incidencia_array['files']:
                    imagen = file['imagen']
                    attach_vals = {'res_model': 'stock.lot.incidence',
                                   'name': file['name'],
                                   'res_id': incidencia.id,
                                   'datas': imagen,
                                   'datas_fname': file['name_file']}
                    file_id = self.env['ir.attachment'].create(attach_vals)
                    self._cr.execute("insert into stock_lot_attachment_ir_rel (hr_id, attachment_id) values(%s,%s)",
                                     (incidencia.id, file_id.id))
                return "Clasificacion Registrada"
            else:
                return "El usuario seleccionado no existe"

    # Enviar los picking a procesar en forma de array
    @api.multi
    def ConfirmarAlbaran(self, picking):
        if picking:
            pick_process = self.browse(picking)
            pick_process.ensure_one()
            if pick_process.state in ('assigned', 'partially_available'):
                pick_process.action_done()
                # for pack in pick_process.pack_operation_ids:
                #     if pack.qty_done > 0:
                #         pack.product_qty = pack.qty_done
                #     else:
                #         pack.unlink()
                # pick_process.do_transfer()
                # if pick_process.sale_id.procurement_group_id:
                #     order_obj = self.env['sale.order']
                #     order_ids = order_obj.search(
                #         [('procurement_group_id', '=', pick_process.sale_id.procurement_group_id.id)])
                #     if order_ids and order_ids[0].lot_id:
                #         order_ids[0].lot_id.state = 'done'
        return "Realizado"

    @api.multi
    def ConfirmarAlbaran_no_back(self, picking):
        if picking:
            pick_process = self.browse(picking)
            pick_process.ensure_one()
            if pick_process.state in ('assigned', 'partially_available'):
                pick_process.action_done()
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', pick_process.id)])
                backorder_pick.action_cancel()
                pick_process.message_post(body=_("Transferencia restante <em>%s</em> <b>Cancelado</b>.") % (backorder_pick.name))
            ## El objetivo es obtener el
            ## Id del picking que empujo el stock a almacenes
            # move_dest_id = 0
            # picking_origin_id = 0
            # for move in pick_process.move_lines:
            #     if move.state != 'cancel':
            #         move_dest_id = move.id
            # move_d = self.env['stock.move'].search([('move_dest_id', '=', move_dest_id)])
            # if move_d:
            #     picking_origin_id = move_d[0].picking_id.id
            #
            # pick_process.ensure_one()
            # if pick_process.state in ('assigned', 'partially_available'):
            #     for pack in pick_process.pack_operation_ids:
            #         if pack.qty_done > 0:
            #             pack.product_qty = pack.qty_done
            #         else:
            #             pack.unlink()
            #     pick_process.do_transfer()
            #     if pick_process.sale_id.procurement_group_id:
            #         order_obj = self.env['sale.order']
            #         order_ids = order_obj.search(
            #             [('procurement_group_id', '=', pick_process.sale_id.procurement_group_id.id)])
            #         if order_ids and order_ids[0].lot_id:
            #             order_ids[0].lot_id.state = 'done'
            #
            # backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', pick_process.id)])
            # if backorder_pick:
            #     if picking_origin_id:
            #         picking_ingreso = self.RevertirAlbaran(picking_origin_id)
            #         backorder_pick.action_cancel()
            #         pick_process.message_post(
            #             body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))
            #         return "Realizado picking Devolucion Id = " + str(picking_ingreso)
            #     else:
            #         backorder_pick.action_cancel()
            #         pick_process.message_post(
            #             body=_("Albarán <em>%s</em> <b>Cancelado</b>.") % (backorder_pick.name))
            #         return "Realizado"
            return "Realizado"

    # Enviar los picking a procesar en forma de array
    @api.multi
    def RevertirAlbaran(self, picking):
        PickingReturn = self.env['stock.return.picking']
        picking_return = PickingReturn.with_context({'active_ids': [picking], 'active_id': picking}).create(
            {'location_id': 0})
        valor = picking_return.create_returns()
        return valor['res_id']

    # Deprecated
    @api.multi
    def create_lots_for_picking(self):
        res = super(StockPicking, self).create_lots_for_picking()
        lot_obj = self.env['stock.production.lot']
        opslot_obj = self.env['stock.pack.operation.lot']
        for picking in self:
            for ops in picking.pack_operation_ids:
                if ops.product_id.tracking in ('serial'):
                    for opslot in ops.pack_lot_ids:
                        if opslot.name_lot != opslot.name_lot_repeat and opslot.name_lot == '':
                            raise ValidationError(_(
                                'Por favor verifique el chasis "%s" No coinciden o no a registrado los chasis') % opslot.name_lot)
                        if not opslot.lot_id:
                            lot_id = lot_obj.create({'name': opslot.lot_name, 'product_id': ops.product_id.id})
                            opslot_obj.write([opslot.id], {'lot_id': lot_id})
                        else:
                            # Controlar que la ubicación entre internos no modifique el nombre del lote
                            # Creado
                            if opslot.operation_id.location_id.usage not in (
                                    'internal', 'transit',
                                    'customer') and opslot.operation_id.location_dest_id.usage in (
                                    'internal', 'transit'):
                                if not opslot.name_lot:
                                    raise ValidationError(_(
                                        'No ha digitado el número de chasis para el lote "%s"') % opslot.lot_name)
                                opslot.lot_id.n_produccion = opslot.n_produccion
                                opslot.lot_id.edicion = opslot.edicion
                                opslot.lot_id.colorinterno = opslot.colorinterno.id
                                opslot.lot_id.colorexterno = opslot.colorexterno.id
                                opslot.lot_id.n_llaves = opslot.n_llaves
                                opslot.lot_id.cant_llaves = opslot.cant_llaves
                                opslot.lot_id.n_caja = opslot.n_caja
                                # opslot.lot_id.name_lot_chasis = opslot.lot_name
                                opslot.lot_id.name = opslot.name_lot
                                opslot.lot_id.n_motor = opslot.n_motor
                                opslot.lot_id.embarque = picking.embarque
                                for incidence in opslot.incidencia:
                                    opslot.lot_id.incidencia = [(4, incidence.id)]

                            else:
                                opslot.lot_id.mot_desarmada = opslot.mot_desarmada
                                for incidence in opslot.incidencia:
                                    opslot.lot_id.incidencia = [(4, incidence.id)]

    @api.multi
    def do_new_transfer(self):
        if self.sale_id.procurement_group_id:
            order_obj = self.env['sale.order']
            order_ids = order_obj.search([('procurement_group_id', '=', self.sale_id.procurement_group_id.id)])
            if order_ids:
                for ov in order_ids:
                    if ov.sale_type_id.pay_invoice:
                        if not ov.invoice_ids.filtered(lambda r: r.state == 'paid' and r.estado_fac == 'V'):
                            raise Warning(
                                'Se debe Tener almenos una Factura en Estado Valido y Totalmente Pagado para validar la transferencia.')
        res = super(StockPicking, self).do_new_transfer()
        if self.sale_id.procurement_group_id:
            order_obj = self.env['sale.order']
            order_ids = order_obj.search([('procurement_group_id', '=', self.sale_id.procurement_group_id.id)])
            if order_ids and order_ids[0].lot_id:
                order_ids[0].lot_id.state = 'done'
        return res

    # Las funciones son requeridas para calcular de
    # nueva forma las cantidades a transferir en funcion de los colores de chasis
    def picking_recompute_remaining_quantities(self, cr, uid, picking, done_qtys=False, context=None):
        need_rereserve = False
        all_op_processed = True
        if picking.pack_operation_ids:
            need_rereserve, all_op_processed = self.recompute_remaining_qty(cr, uid, picking, done_qtys=done_qtys,
                                                                            context=context)
        # Esta validación solo tiene que aplicar a compras
        # Internamente ya el sistema ara la validación de los chasis o lotes
        if picking.location_id.usage == 'supplier':
            picking.picking_recompute_qty_chasis()
        elif picking.location_dest_id.usage != 'customer' and picking.request_id:
            picking.picking_recompute_qty_chasis_transit()
        return need_rereserve, all_op_processed

    @api.cr_uid_ids_context
    def do_recompute_remaining_quantities(self, cr, uid, picking_ids, done_qtys=False, context=None):
        for picking in self.browse(cr, uid, picking_ids, context=context):
            if picking.pack_operation_ids:
                self.recompute_remaining_qty(cr, uid, picking, done_qtys=done_qtys, context=context)

        if picking.location_id.usage in ('supplier'):
            picking.picking_recompute_qty_chasis()
        elif picking.location_dest_id.usage != 'customer' and picking.request_id:
            picking.picking_recompute_qty_chasis_transit()

    @api.multi
    def picking_recompute_qty_chasis(self):
        picking = self

        for pack in picking.pack_operation_product_ids:
            if pack.pack_lot_ids:
                stock_link = self.env["stock.move.operation.link"].search([('operation_id', '=', pack.id)])
                stock_link.unlink()

        for pack in picking.pack_operation_product_ids:
            if pack.pack_lot_ids:
                for move in picking.move_lines:
                    if pack.product_id.id == move.product_id.id and pack.colorinterno.id == move.colorinterno.id and pack.colorexterno.id == move.colorexterno.id and pack.edicion == move.edicion:
                        self.env['stock.move.operation.link'].create({'move_id': move.id,
                                                                      'operation_id': pack.id,
                                                                      'qty': pack.qty_done,
                                                                      })

    # se requiere calcular correctamente los chasis asignados a los moves

    @api.multi
    def picking_recompute_qty_chasis_transit(self):
        picking = self
        # borrar los links actualmente creados
        for pack in picking.pack_operation_product_ids:
            if pack.pack_lot_ids:
                stock_link = self.env["stock.move.operation.link"].search([('operation_id', '=', pack.id)])
                stock_link.unlink()

        for pack in picking.pack_operation_product_ids:
            for move in picking.move_lines:
                for pack_lot in pack.pack_lot_ids:
                    if pack_lot.qty > 0:
                        if pack.product_id.id == move.product_id.id and pack_lot.lot_id.id == move.restrict_lot_id.id:
                            quant_res = 0
                            for quant in move.reserved_quant_ids:
                                quant_res = quant.id
                            if quant_res > 0:
                                self.env['stock.move.operation.link'].create({'move_id': move.id,
                                                                              'operation_id': pack.id,
                                                                              'qty': move.product_qty,
                                                                              'reserved_quant_id': quant_res,
                                                                              })
                            else:
                                self.env['stock.move.operation.link'].create({'move_id': move.id,
                                                                              'operation_id': pack.id,
                                                                              'qty': move.product_qty,
                                                                              })

    # @api.model
    # def _create_backorder(self, picking, backorder_moves=None):
    #     res = super(StockPicking, self)._create_backorder(
    #         picking, backorder_moves=backorder_moves)
    #
    #     ## Corregir los pack Operations generados y utilizar nuevos
    #     ## que corrigan el error de agrupar por color
    #     if picking.location_id.usage == 'supplier':
    #         pickingd = self.env["stock.picking"].browse(res)
    #         for pack in pickingd.pack_operation_product_ids:
    #             if pack.product_id.tracking in ('serial') and pack.product_id.cost_method in ('real'):
    #                 stock_link = self.env["stock.move.operation.link"].search([('operation_id', '=', pack.id)])
    #                 stock_link.unlink()
    #                 pack.unlink()
    #
    #         # for pack_p in pickingd.pack_operation_product_ids:
    #         #    if pack_p.product_id.tracking in ('serial') and pack.product_id.cost_method in ('real'):
    #         # pickingd.pack_operation_product_ids.unlink()
    #
    #         for move_line in pickingd.move_lines_related:
    #             if move_line.product_id.tracking in ('serial') and move_line.product_id.cost_method in ('real'):
    #                 valor_pack = {'location_dest_id': move_line.location_dest_id.id,
    #                               'product_id': move_line.product_id.id,
    #                               'product_qty': move_line.product_qty,
    #                               'product_uom_id': move_line.product_uom.id,
    #                               'location_id': move_line.location_id.id,
    #                               'picking_id': move_line.picking_id.id,
    #                               'colorinterno': move_line.colorinterno.id,
    #                               'colorexterno': move_line.colorexterno.id,
    #                               'edicion': move_line.edicion,
    #                               'price_unit': move_line.price_unit,
    #                               'owner_id': False}
    #                 pack_id = self.env["stock.pack.operation"].create(valor_pack)
    #                 self.env['stock.move.operation.link'].create({'move_id': move_line.id,
    #                                                               'operation_id': pack_id.id,
    #                                                               'qty': move_line.product_qty,
    #                                                               })
    #     return res