
/* jshint undef: false  */

(function () {
'use strict';
var QWeb = openerp.web.qweb;
var _lt = openerp.web._lt;
var _t = openerp.web._t;

nv.dev = false;  // sets nvd3 library in production mode

openerp.web_graph.Graph = openerp.web_graph.Graph.extend({
    template: 'GraphWidget',

    // ----------------------------------------------------------------------
    // Init stuff
    // ----------------------------------------------------------------------
    init: function(parent, model,  domain, options) {
        this._super(parent, model,  domain, options);
    },

    draw_table: function () {
        this._super();
        //linea para quitar filas indefinidas del la visa
        this.table.find('.remove').parent('td').parent('tr').remove();
    },

    make_header_cell: function (header, frozen) {
        
        var cell = (_.has(header, 'cells') ? $('<td>') : $('<th>'))
                        .addClass('graph_border')
                        .attr('rowspan', header.height)
                        .attr('colspan', header.width);
        var $content = $('<span>').attr('href','#')
                                 .text(' ' + (header.title || _t('Undefined')))
                                 .css('margin-left', header.indent*30 + 'px')
                                 .attr('data-id', header.id);

        //check de filas indefinas dentro de la tabla
        if (header.title == 'Undefined' || header.title == 'Indefinido' ) {
            $content = $content.addClass('remove');
        };
        
        if (_.has(header, 'expanded')) {
            if (('indent' in header) && header.indent >= frozen) {
                $content.addClass(header.expanded ? 'fa fa-minus-square' : 'fa fa-plus-square');
                $content.addClass('web_graph_click');
            }
            if (!('indent' in header) && header.lvl >= frozen) {
                $content.addClass(header.expanded ? 'fa fa-minus-square' : 'fa fa-plus-square');
                $content.addClass('web_graph_click');
            }
        } else {
            $content.css('font-weight', 'bold');
        }
        return cell.append($content);

    },

    build_rows: function (headers, raw) {
        var self = this,
            pivot = this.pivot,
            m, i, j, k, cell, row;

        var rows = [];
        var cells, pivot_cells, values;

        var nbr_of_rows = headers.length;
        var col_headers = pivot.get_cols_leaves();

        for (i = 0; i < nbr_of_rows; i++) {
            row = headers[i];
            cells = [];
            pivot_cells = [];
            for (j = 0; j < pivot.cells.length; j++) {
                if (pivot.cells[j].x == row.id || pivot.cells[j].y == row.id) {
                    pivot_cells.push(pivot.cells[j]);
                }              
            }

            for (j = 0; j < col_headers.length; j++) {
                values = undefined;
                for (k = 0; k < pivot_cells.length; k++) {
                    if (pivot_cells[k].x == col_headers[j].id || pivot_cells[k].y == col_headers[j].id) {
                        values = pivot_cells[k].values;
                        break;
                    }               
                }
                if (!values) { values = new Array(pivot.measures.length);}
                for (m = 0; m < pivot.measures.length; m++) {
                    cells.push(self.make_cell(row,col_headers[j],values[m], m, raw));
                }
            }
            if (col_headers.length > 1) {
                var totals = pivot.get_total(row);
                for (m = 0; m < pivot.measures.length; m++) {
                    cell = self.make_cell(row, pivot.cols.headers[0], totals[m], m, raw);
                    cell.is_bold = 'true';
                    cells.push(cell);
                }
            }
            if (row.title != "Indefinido" && row.title != "Undefined") {
                rows.push({
                    id: row.id,
                    indent: row.path.length,
                    title: row.title,
                    expanded: row.expanded,
                    cells: cells,
                });
            };
        }

        return rows;
    },
});


})();
