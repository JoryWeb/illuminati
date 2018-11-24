odoo.define('poi_pos_bol.screens', function (require) {
    "use strict";


    var screens = require('point_of_sale.screens');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var PopupWidget = require('point_of_sale.popups');
    var utils = require('web.utils');
    var core = require('web.core');
    var pos_model = require('point_of_sale.models');
    var gui = require('point_of_sale.gui');

    var QWeb = core.qweb;
    var _t = core._t;
    var Mutex = utils.Mutex;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;
    var Backbone = window.Backbone;


    pos_model.load_fields("account.journal",["payment_model"]);

    PosBaseWidget.include({
        format_decimals: function (amount, precision) {
            var currency = (this.pos && this.pos.currency) ? this.pos.currency : {
                symbol: '$',
                position: 'after',
                rounding: 0.01,
                decimals: 2
            };
            var decimals = currency.decimals;

            if (precision && (typeof this.pos.dp[precision]) !== undefined) {
                decimals = this.pos.dp[precision];
            }

            if (typeof amount === 'number') {
                amount = round_di(amount, decimals).toFixed(decimals);
            }

            return amount + ''
        },
        get_literal_amount: function (amount) {
            var decimals = Math.max(0, Math.ceil(Math.log(1.0 / this.pos.currency.rounding) / Math.log(10)));
            if (typeof amount === 'number') {
                amount = Math.round(amount * 100) / 100;
                amount = amount.toFixed(decimals);
            }
            else {
                amount = 0.0;
            }

            function Unidades(num) {

                switch (num) {
                    case 1:
                        return "UN";
                    case 2:
                        return "DOS";
                    case 3:
                        return "TRES";
                    case 4:
                        return "CUATRO";
                    case 5:
                        return "CINCO";
                    case 6:
                        return "SEIS";
                    case 7:
                        return "SIETE";
                    case 8:
                        return "OCHO";
                    case 9:
                        return "NUEVE";
                }

                return "";
            }

            function Decenas(num) {

                var decena = Math.floor(num / 10);
                var unidad = num - (decena * 10);

                switch (decena) {
                    case 1:
                        switch (unidad) {
                            case 0:
                                return "DIEZ";
                            case 1:
                                return "ONCE";
                            case 2:
                                return "DOCE";
                            case 3:
                                return "TRECE";
                            case 4:
                                return "CATORCE";
                            case 5:
                                return "QUINCE";
                            default:
                                return "DIECI" + Unidades(unidad);
                        }
                    case 2:
                        switch (unidad) {
                            case 0:
                                return "VEINTE";
                            default:
                                return "VEINTI" + Unidades(unidad);
                        }
                    case 3:
                        return DecenasY("TREINTA", unidad);
                    case 4:
                        return DecenasY("CUARENTA", unidad);
                    case 5:
                        return DecenasY("CINCUENTA", unidad);
                    case 6:
                        return DecenasY("SESENTA", unidad);
                    case 7:
                        return DecenasY("SETENTA", unidad);
                    case 8:
                        return DecenasY("OCHENTA", unidad);
                    case 9:
                        return DecenasY("NOVENTA", unidad);
                    case 0:
                        return Unidades(unidad);
                }
            }//Unidades()

            function DecenasY(strSin, numUnidades) {
                if (numUnidades > 0)
                    return strSin + " Y " + Unidades(numUnidades)

                return strSin;
            }//DecenasY()

            function Centenas(num) {

                var centenas = Math.floor(num / 100);
                var decenas = num - (centenas * 100);

                switch (centenas) {
                    case 1:
                        if (decenas > 0)
                            return "CIENTO " + Decenas(decenas);
                        return "CIEN";
                    case 2:
                        return "DOSCIENTOS " + Decenas(decenas);
                    case 3:
                        return "TRESCIENTOS " + Decenas(decenas);
                    case 4:
                        return "CUATROCIENTOS " + Decenas(decenas);
                    case 5:
                        return "QUINIENTOS " + Decenas(decenas);
                    case 6:
                        return "SEISCIENTOS " + Decenas(decenas);
                    case 7:
                        return "SETECIENTOS " + Decenas(decenas);
                    case 8:
                        return "OCHOCIENTOS " + Decenas(decenas);
                    case 9:
                        return "NOVECIENTOS " + Decenas(decenas);
                }

                return Decenas(decenas);
            }//Centenas()

            function Seccion(num, divisor, strSingular, strPlural) {
                var cientos = Math.floor(num / divisor)
                var resto = num - (cientos * divisor)

                var letras = "";

                if (cientos > 0)
                    if (cientos > 1)
                        letras = Centenas(cientos) + " " + strPlural;
                    else
                        letras = strSingular;

                if (resto > 0)
                    letras += "";

                return letras;
            }//Seccion()

            function Miles(num) {
                var divisor = 1000;
                var cientos = Math.floor(num / divisor)
                var resto = num - (cientos * divisor)

                var strMiles = Seccion(num, divisor, "UN MIL", "MIL");
                var strCentenas = Centenas(resto);

                if (strMiles == "")
                    return strCentenas;

                return strMiles + " " + strCentenas;

                //return Seccion(num, divisor, "UN MIL", "MIL") + " " + Centenas(resto);
            }//Miles()

            function Millones(num) {
                var divisor = 1000000;
                var cientos = Math.floor(num / divisor)
                var resto = num - (cientos * divisor)

                var strMillones = Seccion(num, divisor, "UN MILLON", "MILLONES");
                var strMiles = Miles(resto);

                if (strMillones == "")
                    return strMiles;

                return strMillones + " " + strMiles;

                //return Seccion(num, divisor, "UN MILLON", "MILLONES") + " " + Miles(resto);
            }//Millones()

            function NumeroALetras(num) {
                var data = {
                    numero: num,
                    enteros: Math.floor(num),
                    centavos: (((Math.round(num * 100)) - (Math.floor(num) * 100))),
                    letrasCentavos: "",
                    letrasMonedaPlural: "BOLIVIANOS",
                    letrasMonedaSingular: "BOLIVIANOS"
                };

                if (data.centavos > 0)
                    data.letrasCentavos = "" + data.centavos + "/100";

                if (data.centavos == 0) {
                    data.letrasCentavos = "00/100";
                }

                if (data.enteros == 0)
                    return "CERO " + " " + data.letrasCentavos + " " + data.letrasMonedaPlural;
                if (data.enteros == 1)
                    return Millones(data.enteros) + " " + data.letrasCentavos + " " + data.letrasMonedaSingular;
                else
                    return Millones(data.enteros) + " " + data.letrasCentavos + " " + data.letrasMonedaPlural;
            }//NumeroALetras()

            return NumeroALetras(amount);
        },
        build_currency_template: function () {
            this._super();

            var decimals = Math.max(0, Math.ceil(Math.log(1.0 / this.currency.rounding) / Math.log(10)));
            this.get_literal_amount = function (amount) {
                if (typeof amount === 'number') {
                    amount = Math.round(amount * 100) / 100;
                    amount = amount.toFixed(decimals);
                }
                else {
                    amount = 0.0;
                }

                function Unidades(num) {

                    switch (num) {
                        case 1:
                            return "UN";
                        case 2:
                            return "DOS";
                        case 3:
                            return "TRES";
                        case 4:
                            return "CUATRO";
                        case 5:
                            return "CINCO";
                        case 6:
                            return "SEIS";
                        case 7:
                            return "SIETE";
                        case 8:
                            return "OCHO";
                        case 9:
                            return "NUEVE";
                    }

                    return "";
                }

                function Decenas(num) {

                    var decena = Math.floor(num / 10);
                    var unidad = num - (decena * 10);

                    switch (decena) {
                        case 1:
                            switch (unidad) {
                                case 0:
                                    return "DIEZ";
                                case 1:
                                    return "ONCE";
                                case 2:
                                    return "DOCE";
                                case 3:
                                    return "TRECE";
                                case 4:
                                    return "CATORCE";
                                case 5:
                                    return "QUINCE";
                                default:
                                    return "DIECI" + Unidades(unidad);
                            }
                        case 2:
                            switch (unidad) {
                                case 0:
                                    return "VEINTE";
                                default:
                                    return "VEINTI" + Unidades(unidad);
                            }
                        case 3:
                            return DecenasY("TREINTA", unidad);
                        case 4:
                            return DecenasY("CUARENTA", unidad);
                        case 5:
                            return DecenasY("CINCUENTA", unidad);
                        case 6:
                            return DecenasY("SESENTA", unidad);
                        case 7:
                            return DecenasY("SETENTA", unidad);
                        case 8:
                            return DecenasY("OCHENTA", unidad);
                        case 9:
                            return DecenasY("NOVENTA", unidad);
                        case 0:
                            return Unidades(unidad);
                    }
                }//Unidades()

                function DecenasY(strSin, numUnidades) {
                    if (numUnidades > 0)
                        return strSin + " Y " + Unidades(numUnidades)

                    return strSin;
                }//DecenasY()

                function Centenas(num) {

                    var centenas = Math.floor(num / 100);
                    var decenas = num - (centenas * 100);

                    switch (centenas) {
                        case 1:
                            if (decenas > 0)
                                return "CIENTO " + Decenas(decenas);
                            return "CIEN";
                        case 2:
                            return "DOSCIENTOS " + Decenas(decenas);
                        case 3:
                            return "TRESCIENTOS " + Decenas(decenas);
                        case 4:
                            return "CUATROCIENTOS " + Decenas(decenas);
                        case 5:
                            return "QUINIENTOS " + Decenas(decenas);
                        case 6:
                            return "SEISCIENTOS " + Decenas(decenas);
                        case 7:
                            return "SETECIENTOS " + Decenas(decenas);
                        case 8:
                            return "OCHOCIENTOS " + Decenas(decenas);
                        case 9:
                            return "NOVECIENTOS " + Decenas(decenas);
                    }

                    return Decenas(decenas);
                }//Centenas()

                function Seccion(num, divisor, strSingular, strPlural) {
                    var cientos = Math.floor(num / divisor)
                    var resto = num - (cientos * divisor)

                    var letras = "";

                    if (cientos > 0)
                        if (cientos > 1)
                            letras = Centenas(cientos) + " " + strPlural;
                        else
                            letras = strSingular;

                    if (resto > 0)
                        letras += "";

                    return letras;
                }//Seccion()

                function Miles(num) {
                    var divisor = 1000;
                    var cientos = Math.floor(num / divisor)
                    var resto = num - (cientos * divisor)

                    var strMiles = Seccion(num, divisor, "UN MIL", "MIL");
                    var strCentenas = Centenas(resto);

                    if (strMiles == "")
                        return strCentenas;

                    return strMiles + " " + strCentenas;

                    //return Seccion(num, divisor, "UN MIL", "MIL") + " " + Centenas(resto);
                }//Miles()

                function Millones(num) {
                    var divisor = 1000000;
                    var cientos = Math.floor(num / divisor)
                    var resto = num - (cientos * divisor)

                    var strMillones = Seccion(num, divisor, "UN MILLON", "MILLONES");
                    var strMiles = Miles(resto);

                    if (strMillones == "")
                        return strMiles;

                    return strMillones + " " + strMiles;

                    //return Seccion(num, divisor, "UN MILLON", "MILLONES") + " " + Miles(resto);
                }//Millones()

                function NumeroALetras(num) {
                    var data = {
                        numero: num,
                        enteros: Math.floor(num),
                        centavos: (((Math.round(num * 100)) - (Math.floor(num) * 100))),
                        letrasCentavos: "",
                        letrasMonedaPlural: "BOLIVIANOS",
                        letrasMonedaSingular: "BOLIVIANOS"
                    };

                    if (data.centavos > 0) {
                        data.letrasCentavos = "" + data.centavos + "/100";
                    }
                    if (data.centavos == 0) {
                        data.letrasCentavos = "00/100";
                    }
                    if (data.enteros == 0)
                        return "CERO " + " " + data.letrasCentavos + " " + data.letrasMonedaPlural;
                    if (data.enteros == 1)
                        return Millones(data.enteros) + " " + data.letrasCentavos + " " + data.letrasMonedaSingular;
                    else
                        return Millones(data.enteros) + " " + data.letrasCentavos + " " + data.letrasMonedaPlural;
                }//NumeroALetras()

                return NumeroALetras(amount);

            }

        },
    });

    var InvoiceDataWidget = PosBaseWidget.extend({
        template: 'InvoiceDataWidget',
        init: function (parent) {
            this._super(parent);
            var self = this;
            this.pos.bind('change:selectedOrder', function () {
                self.renderElement();
                self.watch_order_changes();
            }, this);
            this.watch_order_changes();
        },
        start: function () {
            this._super();

        },
        renderElement: function () {
            var self = this;
            this._super();
            var self = this;
            this.$el.find('#customer_nit').keyup(function () {
                var nit_value = this.value;
                self.set_nit_to_order(nit_value)
                var razon_found = false;
                razon_found = self.pos.get_razon(nit_value);
                if (razon_found) {
                    self.set_razon_to_order(razon_found);
                    self.$el.find('#customer_razon').val(razon_found);
                }
                self.$el.find('#customer_nit').focus();
            });
            this.$el.find('#customer_razon').keyup(function () {
                var razon_value = this.value;
                self.set_razon_to_order(razon_value)
                self.$el.find('#customer_razon').focus();
            });


            var order = this.pos.get_order();
            if (!order) {
                return;
            }
            else {
                self.$el.find('#customer_nit').val(order.get_nit())
                self.$el.find('#customer_razon').val(order.get_razon())
            }
        },
        set_nit_to_order: function (nit) {
            var order = this.pos.get_order();
            if (!order) {
                return;
            }
            else {
                order.set_nit(nit);
            }
        },
        set_razon_to_order: function (razon) {
            var order = this.pos.get_order();
            if (!order) {
                return;
            }
            else {
                order.set_razon(razon);
            }
        },

        // sets up listeners to watch for order changes
        watch_order_changes: function () {
            var self = this;
            var order = this.pos.get_order();

            if (this.old_order) {
                this.old_order.unbind(null, null, this);
            }
            order.bind('change:nit', function () {
                self.renderElement();
            });
            order.bind('change:razon', function () {
                self.renderElement();
            });
            this.old_order = order;
        },
    });


    screens.ProductScreenWidget.include({
        start: function () {
            this._super();
            this.invoicedata = new InvoiceDataWidget(this, {});
            this.invoicedata.prependTo(this.$('.rightpane-footer'));

        }
    });

    var CardPaymentPopupWidget = PopupWidget.extend({
        template: 'CardPaymentPopupWidget',
        init: function (parent) {
            this.card_code = '';
            this.card_bank_owner = '';
            return this._super(parent);
        },
        show: function (options) {
            options = options || {};
            this._super(options);

            this.paymentline = options['paymentline'];
            this.paymentscreen = options['paymentscreen'];
            this.order = options['order'];

            this.renderElement();
            this.gui.unlock_keyboard();
            this.$('.card_code').focus();
        },
        set_cardpayment_data: function () {
            var card_code = this.$('.card_code').val();
            var card_bank_owner = this.$('.card_bank_owner').val();
            if (!card_code || !card_bank_owner) {
                alert("Please fill both fields");
                return;
            }
            if (this.paymentline) {
                this.paymentline.set_card_data_from_JSON({'card_code': card_code, 'card_bank_owner': card_bank_owner});
                this.paymentscreen.render_paymentlines();
                this.order.trigger('change', this.order);
            }
            this.gui.lock_keyboard();
            this.gui.close_popup();
        },
        renderElement: function () {
            this._super();
            var self = this;
            this.$(".confirm-cardpayment").click(function () {
                self.set_cardpayment_data();
            })

            //this.$(".confirm-giftcard").click(self.add_gift_card());
        },
    });

    gui.define_popup({name: 'cardpayment-popup', widget: CardPaymentPopupWidget});


    screens.PaymentScreenWidget.include({
        renderElement: function () {
            this._super();
            //TODO: SYSTEM DOESN'T ALLOW THAT!
            //this.invoicedata = new InvoiceDataWidget(this, {});
            //this.invoicedata.prependTo(this.$('.right-content'));
        },
        finalize_validation: function () {
            var self = this;
            var _super = this._super;
            var order = this.pos.get_order();

            var invoice_data = this.pos.get_unique_numbering();

            order.set_cc_dos(invoice_data.cc_dos);
            order.set_cc_aut(invoice_data.cc_aut);
            order.set_cc_nro(invoice_data.cc_nro);
            order.set_leyenda(invoice_data.leyenda);
            order.set_limit_date(invoice_data.limit_date);
            order.set_cc_key(invoice_data.llave);
            order.assign_cc_code();

            this.pos.add_razon(order.get_nit(), order.get_razon());

            this._super();
        },
        click_paymentmethods: function (id) {
            var i;
            var order = this.pos.get_order();
            var cashregister = null;
            for (i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal_id[0] === id) {
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }

            if (cashregister.journal.type === "bank" && cashregister.journal.payment_model === "bank_card"){
                this._super(id);
                this.gui.show_popup('cardpayment-popup', {'paymentline': order.selected_paymentline, 'paymentscreen': this, 'order': order});
            } else {
                this._super(id);
            }
        },
    });

});

