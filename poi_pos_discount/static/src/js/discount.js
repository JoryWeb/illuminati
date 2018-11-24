odoo.define('pos_discount.pos_discount', function (require) {
    "use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var _t = core._t;

    var time = require('web.time');
    var utils = require('web.utils');

    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;


    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        get_total_without_discount: function() {
            return round_pr(this.orderlines.reduce((function(sum, orderLine) {
                return sum + (orderLine.get_unit_price() * orderLine.get_quantity());
            }), 0), this.pos.currency.rounding);
        },
        clearDiscounts: function () {
            //updating the discount total
            this.orderlines.each(function (orderline) {
                orderline.set_discount(0);
            });
        },
        applyDiscountsAmount: function (discount) {
            //updating the discount total
            var totaldiscount = this.get_total_discount();
            var totalorder = this.get_total_without_discount();
            var self = this;
            this.orderlines.each(function (orderline) {
                var nuevo_descuento = ((100 * (discount - totaldiscount)) / totalorder) + orderline.discount;
                orderline.set_discount(nuevo_descuento);
            });
        },
        applyDiscountsPercentage: function (discount) {
            //updating the discount percentage total
            this.orderlines.each(function (orderline) {
                orderline.set_discount(discount);
            });
        },
    })


    var DiscountPopupWidget = PopupWidget.extend({
        template: 'DiscountPopupWidget',
        init: function (parent) {
            this.coupon_product = null;
            return this._super(parent);
        },
        show: function (options) {
            options = options || {};
            this._super(options);

            this.renderElement();
            this.$('input').focus();
        },
        clear_discount: function () {
            this.pos.get_order().clearDiscounts();
        },
        apply_discount: function () {
            var amount = this.$('.discount_amount').val();
            var percentage = this.$('.discount_percentage').val();
            if (amount) {
                this.pos.get_order().applyDiscountsAmount(amount);
            }
            else {
                if (percentage) {
                    this.pos.get_order().applyDiscountsPercentage(percentage);
                }
            }
            this.gui.close_popup();
        },
        renderElement: function () {
            this._super();
            var self = this;
            this.$(".apply-discount").click(function () {
                self.apply_discount();
            });
            this.$(".clear-discount").click(function () {
                self.clear_discount();
            });

            //this.$(".confirm-giftcard").click(self.add_gift_card());
        },
    });

    gui.define_popup({name: 'discount-popup', widget: DiscountPopupWidget});


    var DiscountButton = screens.ActionButtonWidget.extend({
        template: 'DiscountButton',
        button_click: function () {
            var self = this;
            this.gui.show_popup('discount-popup', {});
        },

    });

    screens.define_action_button({
        'name': 'discount',
        'widget': DiscountButton,
    });


});
