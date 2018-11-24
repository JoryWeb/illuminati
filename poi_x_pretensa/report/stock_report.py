##############################################################################
#
#   Copyright (c) 2015 Poiesis Consulting (http://www.poiesisconsulting.com)
#   @author Miguel Angel Callisaya Mamani
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

import time
import logging
# from sale.report import sale_order
from openerp.report import report_sxw

_logger = logging.getLogger(__name__)


class stock_picking(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(stock_picking, self).__init__(cr, uid, name, context=context)

        sum_monto_losa = 0.0
        sum_monto_losa_m = 0.0
        sum_monto_premoldeados = 0.0
        sum_monto_premoldeados_m = 0.0
        sum_monto_viguetas = 0.0
        sum_monto_viguetas_m = 0.0
        sum_monto_casetones = 0.0
        sum_monto_casetones_m = 0.0
        sum_monto_materia_prima = 0.0
        sum_monto_materia_prima_m = 0.0
        sum_monto_otros = 0.0
        sum_monto_otros_m = 0.0
        sum_monto_plastobloq = 0.0
        sum_monto_plastobloq_m = 0.0
        sum_monto_tabiquerias = 0.0
        sum_monto_tabiquerias_m = 0.0
        sum_monto_tiras = 0.0
        sum_monto_tiras_m = 0.0
        sum_monto_paneles = 0.0
        sum_monto_paneles_m = 0.0
        sum_monto_techos = 0.0
        sum_monto_techos_m = 0.0

        for linea in self.pool.get('stock.picking').browse(cr, uid, context['active_ids'], context=context):
            for lineas in linea.move_lines:
                if (lineas.procurement_id.sale_line_id):
                    var_x = lineas.procurement_id.sale_line_id.product_dimension.var_x
                    var_y = lineas.procurement_id.sale_line_id.product_dimension.var_y
                    var_z = lineas.procurement_id.sale_line_id.product_dimension.var_z
                    try:
                        if (lineas.product_id.categ_id.name == 'Losas Huecas Pretensadas'):
                            sum_monto_losa += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_losa_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_losa_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_losa_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Premoldeados'):
                            sum_monto_premoldeados += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_premoldeados_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_premoldeados_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_premoldeados_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Viguetas Pretensadas'):
                            sum_monto_viguetas += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_viguetas_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_viguetas_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_viguetas_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Casetones'):
                            sum_monto_casetones += lineas.product_qty

                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_casetones_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_casetones_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_casetones_m += var_x * var_y * var_z * lineas.product_qty

                        if (lineas.product_id.categ_id.name == 'Plastobloq'):
                            sum_monto_plastobloq += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_plastobloq_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_plastobloq_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_plastobloq_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Tabiquerias'):
                            sum_monto_tabiquerias += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_tabiquerias_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_tabiquerias_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_tabiquerias_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Tiras'):
                            sum_monto_tiras += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_tiras_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_tiras_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_tiras_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Paneles'):
                            sum_monto_paneles += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_paneles_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_paneles_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_paneles_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Techos'):
                            sum_monto_techos += lineas.product_qty
                            if lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'lineal':
                                sum_monto_techos_m += var_x * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'area':
                                sum_monto_techos_m += var_x * var_y * lineas.product_qty
                            elif lineas.procurement_id.sale_line_id.product_dimension.metric_type == 'volume':
                                sum_monto_techos_m += var_x * var_y * var_z * lineas.product_qty
                    except Exception:
                        _logger.error('ERROR: Could not mark POS Order as Paid.', exc_info=True)
                else:
                    var_x = lineas.lot_creation_pack.dimension_id.var_x
                    var_y = lineas.lot_creation_pack.dimension_id.var_y
                    var_z = lineas.lot_creation_pack.dimension_id.var_z
                    try:
                        if (lineas.product_id.categ_id.name == 'Losas Huecas Pretensadas'):
                            sum_monto_losa += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_losa_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_losa_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_losa_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Premoldeados'):
                            sum_monto_premoldeados += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_premoldeados_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_premoldeados_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_premoldeados_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Viguetas Pretensadas'):
                            sum_monto_viguetas += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_viguetas_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_viguetas_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_viguetas_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Casetones'):
                            sum_monto_casetones += lineas.product_qty

                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_casetones_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_casetones_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_casetones_m += var_x * var_y * var_z * lineas.product_qty

                        if (lineas.product_id.categ_id.name == 'Plastobloq'):
                            sum_monto_plastobloq += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_plastobloq_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_plastobloq_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_plastobloq_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Tabiquerias'):
                            sum_monto_tabiquerias += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_tabiquerias_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_tabiquerias_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_tabiquerias_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Tiras'):
                            sum_monto_tiras += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_tiras_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_tiras_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_tiras_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Paneles'):
                            sum_monto_paneles += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_paneles_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_paneles_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_paneles_m += var_x * var_y * var_z * lineas.product_qty
                        if (lineas.product_id.categ_id.name == 'Techos'):
                            sum_monto_techos += lineas.product_qty
                            if lineas.lot_creation_pack.dimension_id.metric_type == 'lineal':
                                sum_monto_techos_m += var_x * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'area':
                                sum_monto_techos_m += var_x * var_y * lineas.product_qty
                            elif lineas.lot_creation_pack.dimension_id.metric_type == 'volume':
                                sum_monto_techos_m += var_x * var_y * var_z * lineas.product_qty
                    except Exception:
                        _logger.error('ERROR: Could not mark POS Order as Paid.', exc_info=True)
        self.localcontext.update({
            'time': time,
            'losas': sum_monto_losa,
            'losas_m': sum_monto_losa_m,
            'premoldeados': sum_monto_premoldeados,
            'premoldeados_m': sum_monto_premoldeados_m,
            'viguetas': sum_monto_viguetas,
            'viguetas_m': sum_monto_viguetas_m,
            'casetones': sum_monto_casetones,
            'casetones_m': sum_monto_casetones_m,
            'materia': sum_monto_materia_prima,
            'materia_m': sum_monto_materia_prima_m,
            'otros': sum_monto_otros,
            'otros_m': sum_monto_otros_m,
            'plastobloq': sum_monto_plastobloq,
            'plastobloq_m': sum_monto_plastobloq_m,
            'tabiquerias': sum_monto_tabiquerias,
            'tabiquerias_m': sum_monto_tabiquerias_m,
            'tiras': sum_monto_tiras,
            'tiras_m': sum_monto_tiras_m,
            'paneles': sum_monto_paneles,
            'paneles_m': sum_monto_paneles_m,
            'techos': sum_monto_techos,
            'techos_m': sum_monto_techos_m,

        })


report_sxw.report_sxw('report.stock.picking.pretensa', 'stock.picking', 'poi_x_pretensa/report/picking.rml',
                      parser=stock_picking, header="external")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
