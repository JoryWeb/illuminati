odoo.define('poi_bol_pos.main', function (require) {
    "use strict";

    var main = require('point_of_sale.main');
    var core = require('web.core');

    var PosDB = require('point_of_sale.DB');

    PosDB.include({
        init: function (options) {
            this._super.apply(this, arguments);
            this.partner_by_nit_ci = {};
        },
        add_partners: function (partners) {

            var res = this._super.apply(this, arguments);


            var updated_count = 0;
            var new_write_date = '';
            var partner;
            var self = this;

            // If there were updates, we need to completely
            // rebuild the search string and the barcode indexing

            this.partner_by_nit_ci = {};

            for (var id in this.partner_by_id) {
                partner = this.partner_by_id[id];
                var nit_ci = false;

                if (partner.nit) {
                    nit_ci = partner.nit;
                }
                else {
                    if (partner.ci) {
                        nit_ci = partner.ci;
                    }
                }

                if (nit_ci) {
                    self.partner_by_nit_ci[nit_ci] = partner;
                }
            }

            return res;
        },
        get_partner_by_nit_ci: function (nit_ci) {
            return this.partner_by_nit_ci[nit_ci];
        },

    });
    return PosDB;

});
