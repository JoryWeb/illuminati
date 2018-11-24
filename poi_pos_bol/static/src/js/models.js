odoo.define('poi_pos_bol.models', function (require) {
    "use strict";

    var BarcodeParser = require('barcodes.BarcodeParser');
    var PosDB = require('point_of_sale.DB');
    var devices = require('point_of_sale.devices');
    var core = require('web.core');
    var session = require('web.session');
    var time = require('web.time');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;
    var Mutex = utils.Mutex;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;
    var Backbone = window.Backbone;

    var models = require('point_of_sale.models');

    var exports = {};


    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        //INVOICE ENGINE
        initialize: function (session, attributes) {
            this.bol_customers = {};
            return posmodel_super.initialize.apply(this, arguments);
        },
        initialize_dosif: function (dosif) {
            console.log('INITIALIZING DOSIF', dosif);
            console.log("TIENDA", this.shop);
            this.dosif = dosif;
            var self = this;
            var fecha_ini = new Date(dosif.fecha_ini);
            var fecha_fin = new Date(dosif.fecha_fin);
            var fecha_actual = new Date();
            console.log(fecha_ini, fecha_actual, fecha_fin);

            if (fecha_actual < fecha_ini || fecha_actual > fecha_fin) {
                alert(_t('Dosification error. Date invalid.'));
                this.init_localstorage_dosif(dosif.id, false);
                this.cc_aut = '';
                this.leyenda = '';
                this.limit_date = '';
                this.llave = ''
            }
            else {
                this.cc_aut = dosif.nro_orden;
                this.last_cc_nro = dosif.rango_fin;
                this.leyenda = dosif.leyenda_id[1];
                this.cc_dos = dosif.id;
                this.limit_date = fecha_fin;
                this.llave = dosif.llave;
                this.init_localstorage_dosif(dosif.id, dosif.last_pos_cc_nro);
            }


        },
        get_unique_numbering: function () {
            var cc_nro_to_assign = this.get_localstorage_dosif(this.cc_dos);
            if (cc_nro_to_assign == false) {
                return false;
            }
            ;
            if (cc_nro_to_assign > this.last_cc_nro) {
                alert(_t("Error: Last number of dosification was reached. Please select other dosification and restart the POS"));
                return false;
            }
            return {
                'cc_aut': this.cc_aut,
                'cc_nro': cc_nro_to_assign,
                'leyenda': this.leyenda,
                'cc_dos': this.cc_dos,
                'limit_date': this.limit_date,
                'llave': this.llave,
            }
        },
        /* saves the dosif to the database */
        init_localstorage_dosif: function (cc_dos, cc_nro) {
            localStorage['dosif_' + cc_dos] = cc_nro;
        },
        get_localstorage_dosif: function (cc_dos) {
            var cc_nro = localStorage['dosif_' + cc_dos];
            if (cc_nro !== undefined && cc_nro !== "") {
                var data = parseInt(cc_nro) + 1;
                localStorage['dosif_' + cc_dos] = data; //The localstorage will use always the last number assigned.
                return data;
            }
            else {
                alert(_t("The dosification was not loaded properly. Please refresh the page"));
                return false;
            }
        },
        load_server_data: function () {
            var self = this;

            var partner_index = _.findIndex(this.models, function (model) {
                return model.model === "res.partner";
            });

            var partner_model = this.models[partner_index];
            partner_model.fields = $.merge(partner_model.fields, ['ci', 'nit', 'razon', 'razon_invoice']);


            var company_index = _.findIndex(this.models, function (model) {
                return model.model === "res.company";
            });

            var company_model = this.models[company_index];
            company_model.fields = $.merge(company_model.fields, ['nit', 'razon', 'actividad', 'street', 'street2', 'city', 'country_id', 'phone']);

            return posmodel_super.load_server_data.apply(this, arguments);
        },
        initialize_bol_customers: function (bol_customers) {
            var customers = {};
            $.each(bol_customers, function (index, bc) {
                console.log('BC'.bc);
                customers[bc.nit] = bc.razon;
            })
            this.bol_customers = customers;
        },
        get_razon: function (nit) {
            var partner_found = this.db.get_partner_by_nit_ci(nit);
            if (partner_found) {
                this.get_order().set_client(partner_found);
                return false;
            }
            if (this.bol_customers[nit]) {
                return this.bol_customers[nit];
            }
            else {
                return false;
            }
        },
        add_razon: function (nit, razon) {
            this.bol_customers[nit] = razon;
        }
    });


    // At POS Startup, load the dosifications, and add them to the pos model
    models.load_models({
        model: 'poi_bol_base.cc_dosif',
        fields: [],
        domain: function (self) {
            return [['id', '=', self.config.dosif_id[0]]];
        },
        context: function (self) {
            return {display_all: true};
        },
        loaded: function (self, dosifs) {
            if (dosifs.length) {
                self.initialize_dosif(dosifs[0])
            }
        },
    });

    models.load_models({
        model: 'bol.customer',
        fields: [],
        domain: function (self) {
            return [];
        },
        context: function (self) {
            return {};
        },
        loaded: function (self, bol_customers) {
            if (bol_customers.length) {
                self.initialize_bol_customers(bol_customers)
            }
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (session, attributes) {
            _super_order.initialize.apply(this, arguments);
            console.log('INITIALIZING ORDERS');
            this.set({
                nit: '0',
                razon: _t('No Name'),
                cc_aut: null,
                cc_nro: null,
                limit_date: null,
                date_order: null,
                date_fac: null,
                time_fac: null,
                leyenda: ''
            });
        },
        set_client: function (client) {
            _super_order.set_client.apply(this, arguments);
            this.assert_editable();
            if (client) {
                if (client.nit) {
                    this.set_nit(client.nit);
                }
                else {
                    if (client.ci) {
                        this.set_nit(client.ci);
                    }
                }
                if (client.razon_invoice) {
                    this.set_razon(client.razon_invoice);
                }
                else {
                    if (client.razon) {
                        this.set_razon(client.razon);
                    }
                    else {
                        if (client.name) {
                            this.set_razon(client.name);
                        }
                    }
                }
            }
        },
        /* ---- Bolivian Invoice Data --- */
        // NIT
        set_nit: function (nit) {
            this.assert_editable();
            this.set('nit', nit);
        },
        get_nit: function () {
            return this.get('nit');
        },
        // RAZON
        set_razon: function (razon) {
            this.assert_editable();
            this.set('razon', razon);
        },
        get_razon: function () {
            return this.get('razon');
        },
        // ID DE DOSIF
        set_cc_dos: function (cc_dos) {
            this.assert_editable();
            this.set({'cc_dos': cc_dos});
        },
        get_cc_dos: function () {
            return this.get('cc_dos');
        },
        // NUMERO DE AUT
        set_cc_aut: function (cc_aut) {
            this.assert_editable();
            this.set({'cc_aut': cc_aut});
        },
        get_cc_aut: function () {
            return this.get('cc_aut');
        },
        // LLAVE
        set_cc_key: function (cc_key) {
            this.assert_editable();
            this.set({'cc_key': cc_key});
        },
        get_cc_key: function () {
            return this.get('cc_key');
        },
        // NUMERO DE FACTURA
        set_cc_nro: function (cc_nro) {
            this.assert_editable();
            this.set({'cc_nro': cc_nro});
        },
        get_cc_nro: function () {
            console.log('NRO', this.get('cc_nro'));
            return this.get('cc_nro');
        },
        // FECHA LIMITE DE EMISION
        set_limit_date: function (limit_date) { // LIMIT DATE IN FORMAT DATE
            this.assert_editable();
            var dd = limit_date.getDate();
            var mm = limit_date.getMonth() + 1; //January is 0!
            var yyyy = limit_date.getFullYear();


            this.set({'limit_date': dd + "-" + mm + '-' + yyyy});
        },
        get_limit_date: function () {
            return this.get('limit_date');
        },
        // FECHA DE LA ORDER en formato YYYYMMDD
        set_date_order: function (date_order) {
            this.assert_editable();
            this.set({'date_order': date_order});
        },
        get_date_order: function () {
            return this.get('date_order');
        },
        // FECHA PARA FACTURA
        set_date_fac: function (date_fac) {
            this.assert_editable();
            this.set({'date_fac': date_fac});
        },
        get_date_fac: function () {
            return this.get('date_fac');
        },
        // HORA PARA FACTURA
        set_time_fac: function (time_fac) {
            this.assert_editable();
            this.set({'time_fac': time_fac});
        },
        get_time_fac: function () {
            return this.get('time_fac');
        },
        // LEYENDA DE DOSIFICACION
        set_leyenda: function (leyenda) {
            this.assert_editable();
            this.set({'leyenda': leyenda});
        },
        get_leyenda: function () {
            return this.get('leyenda');
        },
        generate_qr: function () {
            var qr_literal = "0" + "|" + // NIT emisor
                this.get_cc_nro() + "|" + // Numero de factura
                this.get_cc_aut() + "|" + // Numero de autorizacion
                this.get_date_fac() + "|" + // Fecha de emision DD/MM/AA
                this.get_total_with_tax() + "|" + // Monto total
                this.get_total_with_tax() + "|" + // Monto valido para Credito Fiscal
                this.get_cc_cod() + "|" + // Codigo de control
                this.get_nit() + "|" + // NIT Cliente
                "0" + "|" + // TODO: Importe ICE/IEHD/TASAS
                "0" + "|" + // TODO: Importe por ventas no gravadas o gravadas a tasa cero
                "0" + "|" + // TODO: Importe no sujeto a credito fiscal
                "0"; // TODO: Descuentos, bonificaciones y rebajas obtenidas
            var el = kjua({text: qr_literal, ecLevel: 'M',});
            var qr = $(el)[0].src.replace('data:image/png;base64,', '');
            this.set_qr_img(qr);
        },
        set_qr_img: function (qr_img) {
            var self = this;
            self.qr_code = new Image();
            self.qr_code.src = 'data:image/png;base64,' + qr_img;
            self.qr_img = qr_img;
        },
        get_qr_img: function () {
            if (this.qr_code) {
                return this.qr_code.src;
            }
            else {
                return false;
            }

        },
        get_qr_img_invoice: function () {
            if (this.qr_img) {
                return this.qr_img;
            }
            else {
                return false;
            }

        },
        set_cc_cod: function (cc_cod) {
            console.log('cc_cod', cc_cod);
            this.set({'cc_cod': cc_cod});
        },
        get_cc_cod: function () {
            if (this.get('cc_cod')) {
                return this.get('cc_cod');
            }
            else {
                return ''
            }
        },
        assign_validate_date: function () {
            var date = new Date();
            var dd = date.getDate();
            var mm = date.getMonth() + 1; //January is 0!
            var yyyy = date.getFullYear();

            var seconds = date.getSeconds();
            var minutes = date.getMinutes();
            var hour = date.getHours();

            if (dd < 10) {
                dd = '0' + dd;
            }
            if (mm < 10) {
                mm = '0' + mm;
            }

            var date_order = yyyy + "" + mm + "" + dd;
            this.set_date_order(date_order)

            var date_fac = dd + "/" + mm + "/" + yyyy;
            var time_fac = hour + ":" + minutes + ":" + seconds;
            this.set_date_fac(date_fac)
            this.set_time_fac(time_fac)
        },
        assign_cc_code: function () {
            this.assign_validate_date(); // Let's assign dates when cc code is validated;
            var cc_code = generateControlCode(this.get_cc_aut(),//Numero de autorizacion
                this.get_cc_nro(),//Numero de factura
                this.get_nit(),//Número de Identificación Tributaria o Carnet de Identidad
                this.get_date_order(),//fecha de transaccion de la forma AAAAMMDD
                this.get_total_with_tax(),//Monto de la transacción
                this.get_cc_key()//Llave de dosificación
            );
            this.set_cc_cod(cc_code);
            this.generate_qr(); //TODO: Evaluate position
        },
        export_as_JSON: function () {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.nit = this.get_nit();
            data.razon = this.get_razon();
            data.cc_dos = this.get_cc_dos();
            data.cc_aut = this.get_cc_aut();
            data.cc_nro = this.get_cc_nro();
            data.limit_date = this.get_limit_date();
            data.leyenda = this.get_leyenda();

            data.date_fac = this.get_date_fac();
            data.time_fac = this.get_time_fac();

            data.cc_cod = this.get_cc_cod();
            data.qr_img = this.get_qr_img_invoice();
            //var tot_val = this.get_tot_val();

            return data;
        },
        export_for_printing: function () {
            var data = _super_order.export_for_printing.apply(this, arguments);
            data.nit = this.get_nit();
            data.razon = this.get_razon();
            data.cc_dos = this.get_cc_dos();
            data.cc_aut = this.get_cc_aut();
            data.cc_nro = this.get_cc_nro();
            data.limit_date = this.get_limit_date();
            data.leyenda = this.get_leyenda();
            data.date_order = this.get_date_order() + " " + this.get_time_fac();
            return data;
        },
    });


    models.Orderline = models.Orderline.extend({
        get_display_price_without_discount: function () {
            var rounding = this.pos.currency.rounding;
            return round_pr(round_pr(this.get_unit_price() * this.get_quantity(), rounding), rounding);
        },
    });


    var _paylineproto = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options) {
            _paylineproto.initialize.apply(this, arguments);
            this.card_code = '';
            this.card_bank_owner = '';
        },
        init_from_JSON: function (json) {
            _paylineproto.init_from_JSON.apply(this, arguments);

            this.card_code = json.card_code;
            this.card_bank_owner = json.card_bank_owner;

        },
        export_as_JSON: function () {
            return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {
                card_code: this.card_code,
                card_bank_owner: this.card_bank_owner,
            });
        },
        set_card_data_from_JSON: function (json) {
            this.order.assert_editable();
            this.card_code = json.card_code;
            this.card_bank_owner = json.card_bank_owner;
            this.name = this.name + " (" + this.card_bank_owner + ": " + this.card_code + ")";
        },
    });


// exports = {
//     PosModel: PosModel,
//     NumpadState: NumpadState,
//     load_fields: load_fields,
//     load_models: load_models,
//     Orderline: Orderline,
//     Order: Order,
// };
    return exports;

});
