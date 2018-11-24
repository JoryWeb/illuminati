odoo.define('poi_pos_gift_card.pos_gift_card', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var utils = require('web.utils');
    var _t = core._t;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;


    // At POS Startup, load the floors, and add them to the pos model
    // Problem: TODO: A gift card will be loaded ONLY when POS loads. If it's not refreshed it won't be displayed;
    models.load_models({
        model: 'product.template.gift.card',
        fields: ['code', 'amount', 'remaining_amount', 'expiry_date'],
        domain: function (self) {
            return [];
        },
        loaded: function (self, giftcards) {
            self.giftcards = giftcards;
        },
    });

    /* MODELS */

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_server_data: function () {
            var self = this;

            var product_index = _.findIndex(this.models, function (model) {
                return model.model === "product.product";
            });

            var product_model = this.models[product_index];
            product_model.fields.push('is_gift_card');

            return posmodel_super.load_server_data.apply(this, arguments);
        },
    });

    /* MODELS */
    var OrderlineSuper = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            OrderlineSuper.prototype.initialize.call(this, attr, options);
            this.giftcard_code = false;
            this.giftcard_code_used = false;
        },
        set_quantity: function (quantity) {
            if (quantity === 'remove') {
                OrderlineSuper.prototype.set_quantity.apply(this, arguments);
            }
            else {
                var product_gift_card = this.pos.db.get_product_by_id(this.pos.config.giftcard_product_id[0]);
                if (this.product === product_gift_card) {
                    if (quantity > 1) {
                        this.quantity = 1;
                        this.quantityStr = '1';
                        this.trigger('change', this);
                    }
                    else {
                        OrderlineSuper.prototype.set_quantity.apply(this, arguments);
                    }
                }
                else {
                    OrderlineSuper.prototype.set_quantity.apply(this, arguments);
                }
            }
        },
        set_unit_price: function (price) {
            var self = this;
            var product_gift_card = this.pos.db.get_product_by_id(this.pos.config.giftcard_product_id[0]);
            if (this.product === product_gift_card) {
                this.order.assert_editable();
                var giftcards = this.pos.giftcards;

                var real_price = 0.0; // REAL PRICE APPLIED BASED ON HOW MUCH THEY HAVE ON GC

                $.each(giftcards, function (index, gc) {
                    if (self.get_giftcard_code_used()) {
                        if (self.get_giftcard_code_used() == gc.code) {
                            if (gc.remaining_amount == 0.0) {
                                console.log(gc);
                                alert(_t("The gift card doesn't have funds."))
                            }
                            else {
                                if (price > gc.remaining_amount) {
                                    real_price = gc.remaining_amount * (-1);
                                }
                                else {
                                    if (price > 0) {
                                        real_price = price * (-1);
                                    }
                                    else {
                                        real_price = price;
                                    }
                                }
                            }

                            return false;
                        }
                    }
                });
                this.price = round_di(parseFloat(real_price) || 0, this.pos.dp['Product Price']);
                this.trigger('change', this);
            }
            else {
                OrderlineSuper.prototype.set_unit_price.apply(this, arguments);
            }
        },
        set_giftcard_code: function (code) {
            this.giftcard_code = code;
        },
        get_giftcard_code: function () {
            return this.giftcard_code;
        },
        set_giftcard_code_used: function (code) {
            this.giftcard_code_used = code;
        },
        get_giftcard_code_used: function () {
            return this.giftcard_code_used;
        },
        export_as_JSON: function () {
            var data = OrderlineSuper.prototype.export_as_JSON.apply(this, arguments);
            data.giftcard_code = this.get_giftcard_code();
            data.giftcard_code_used = this.get_giftcard_code_used();
            return data;
        },
        export_for_printing: function () {
            var data = OrderlineSuper.prototype.export_for_printing.apply(this, arguments);
            data.giftcard_code = this.get_giftcard_code();
            data.giftcard_code_used = this.get_giftcard_code_used();
            return data;
        },

    });


    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (session, attributes) {
            _super_order.initialize.apply(this, arguments);
        },
        add_product: function (product, options) {

            if (product.is_gift_card) {
                if (options.giftcard_code) {
                    _super_order.add_product.apply(this, arguments);
                    var selected_orderline = this.get_selected_orderline();
                    selected_orderline.set_giftcard_code(options.giftcard_code);
                }
            }
            else {
                var product_gift_card = this.pos.db.get_product_by_id(this.pos.config.giftcard_product_id[0]);
                if (product === product_gift_card) {
                    if (options.giftcard_code_used) {
                        _super_order.add_product.apply(this, arguments);
                        var selected_orderline = this.get_selected_orderline();
                        selected_orderline.set_giftcard_code_used(options.giftcard_code_used);
                        selected_orderline.set_unit_price(options.price);
                    }
                }
                else {
                    _super_order.add_product.apply(this, arguments);
                }

            }

        }
    });


    /* SCREENS */

    var GiftCardPaymentButton = screens.ActionButtonWidget.extend({
        template: 'GiftCardPaymentButton',
        button_click: function () {
            var self = this;
            this.gui.show_popup('giftcardpayment-popup', {
                'order': self.pos.get_order(),
            });
        },
    });

    screens.define_action_button({
        'name': 'giftcardpaymentbutton',
        'widget': GiftCardPaymentButton,
        'condition': function () {
            return this.pos.config.iface_giftcard && this.pos.config.giftcard_product_id;
        },
    });

    var GiftCardPopupWidget = PopupWidget.extend({
        template: 'GiftCardPopupWidget',
        init: function (parent) {
            this.coupon_product = null;
            return this._super(parent);
        },
        show: function (options) {
            options = options || {};
            this._super(options);

            this.product = options['product'];

            this.renderElement();
            this.$('input').focus();
        },
        add_gift_card: function () {
            var value = this.$('input').val();
            if (!value) {
                alert("You have to fill a card code");
                return;
            }
            if (this.product) {
                this.pos.get_order().add_product(this.product, {'giftcard_code': value});
            }
            this.gui.close_popup();
        },
        renderElement: function () {
            this._super();
            var self = this;
            this.$(".confirm-giftcard").click(function () {
                self.add_gift_card();
            })

            //this.$(".confirm-giftcard").click(self.add_gift_card());
        },
    });

    gui.define_popup({name: 'giftcard-popup', widget: GiftCardPopupWidget});


    var GiftCardPaymentPopupWidget = PopupWidget.extend({
        template: 'GiftCardPaymentPopupWidget',
        init: function (parent) {
            this.coupon_product = null;
            return this._super(parent);
        },
        show: function (options) {
            options = options || {};
            this._super(options);

            this.order = options['order'];
            this.renderElement();
            this.$('input').focus();
        },
        apply_gift_card: function () {
            var value = this.$('input').val();
            if (!value) {
                //TODO: Add function.
                alert("You have to fill a card code");
                return;
            }
            if (this.validate_gift_card(value)) {
                this.gui.close_popup();
            }
        },
        validate_gift_card: function (code) {
            var self = this;
            var giftcards = this.pos.giftcards;
            var found = false;
            var product = this.pos.db.get_product_by_id(this.pos.config.giftcard_product_id[0]);

            $.each(giftcards, function (index, gc) {
                if (code == gc.code) {
                    console.log("GIFTCARD", gc);
                    self.order.add_product(product, {price: gc.remaining_amount, giftcard_code_used: code});
                    found = true;
                    return false;
                }
            });
            if (!found) {
                alert("Gift Card not found");
                return false;
            }
            else {
                return true;
            }
        },
        renderElement: function () {
            this._super();
            var self = this;
            this.$(".confirm-giftcardpayment").click(function () {
                self.apply_gift_card();
            })

            //this.$(".confirm-giftcard").click(self.add_gift_card());
        },
    });

    gui.define_popup({name: 'giftcardpayment-popup', widget: GiftCardPaymentPopupWidget});


    screens.PaymentScreenWidget.include({
        renderElement: function () {
            this._super();
            //this.giftcard_payment_button = new GiftCardPaymentWidget(this, {});
            //this.giftcard_payment_button.prependTo(this.$('.paymentmethods'));
        },
    });


    screens.ProductScreenWidget.include({
        start: function () {
            this._super();

        },
        click_product: function (product) {
            if (product.is_gift_card) {
                this.gui.show_popup('giftcard-popup', {'name': 'Coupon: ' + product.name, 'product': product});
                //this.gui.show_screen('scale',{product: product});
            } else {
                this._super(product);
            }
        },
    });
})
;
