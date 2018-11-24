odoo.define('poi_pos_advanced.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');


    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_server_data: function () {
            var self = this;

            var partner_index = _.findIndex(this.models, function (model) {
                return model.model === "res.partner";
            });

            var partner_model = this.models[partner_index];
            partner_model.fields = $.merge(partner_model.fields, ['number_of_purchases', 'last_purchase', 'client_category', 'last_payment_method', 'total_purchases_amount']);

            return posmodel_super.load_server_data.apply(this, arguments);
        },
    });

});
