odoo.define('poi_pos_presale.presale', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Session = require('web.Session');
    var models = require('point_of_sale.models');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');
    var utils = require('web.utils');
    var _t = core._t;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    var framework = require('web.framework');


    /* MODELS */

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        //INVOICE ENGINE
        initialize: function (session, attributes) {
            this.synch_domain = [['state', '=', 'draft']]; // By default will be draft
            return posmodel_super.initialize.apply(this, arguments);
        },
        load_orders: function () { // Removing this.... Disabling because this won't help with Orders unpaid.
            //var jsons = this.db.get_unpaid_orders();

            if (this.config.pos_group_id)
            {
                this.synch_domain = [['state', '=', 'draft'],['pos_group_id','=',this.config.pos_group_id[0]]];
                this.pos_group_id = this.config.pos_group_id[0];
            }
            else {
                this.pos_group_id = false;
            }

            var jsons = [];
            var orders = [];
            var not_loaded_count = 0;

            for (var i = 0; i < jsons.length; i++) {
                var json = jsons[i];
                if (json.pos_session_id === this.pos_session.id) {
                    orders.push(new exports.Order({}, {
                        pos: this,
                        json: json,
                    }));
                } else {
                    not_loaded_count += 1;
                }
            }

            if (not_loaded_count) {
                console.info('There are ' + not_loaded_count + ' locally saved unpaid orders belonging to another session');
            }

            orders = orders.sort(function (a, b) {
                return a.sequence_number - b.sequence_number;
            });

            if (orders.length) {
                this.get('orders').add(orders);
            }
        },
        on_removed_order: function (removed_order, index, reason) { // OVERRIDE
            var order_list = this.get_order_list();
            if ((reason === 'abandon' || removed_order.temporary) && order_list.length > 0) {
                // when we intentionally remove an unfinished order, and there is another existing one
                removed_order.stop_synch();
                this.set_order(order_list[index] || order_list[order_list.length - 1]);
            } else {
                if (reason == 'synch') {
                    removed_order.stop_synch();
                }
                else {
                    // when the order was automatically removed after completion,
                    // or when we intentionally delete the only concurrent order
                    removed_order.stop_synch();
                    this.add_new_order();
                }
            }
        },
        build_order: function (order_id) {
            framework.blockUI({
                message: _t('Building order...'),
                css: {backgroundColor: '#f00', color: '#fff', 'font-family': 'Lato', 'font-size': '22px'}
            });
            var self = this;
            var order = false;
            var orderlines = false;

            var order_created = $.Deferred();

            $.when(self.get_order_sys(order_id)).then(function (orderrpc) {
                framework.blockUI({
                    message: _t('Getting order from Database...'),
                    css: {backgroundColor: '#f00', color: '#fff', 'font-family': 'Lato', 'font-size': '22px'}
                });
                order = orderrpc;
                return self.get_orderlines_sys(order.id);
            }).then(function (orderlinesrpc) {
                framework.blockUI({
                    message: _t('Getting orderlines from Database...'),
                    css: {backgroundColor: '#f00', color: '#fff', 'font-family': 'Lato', 'font-size': '22px'}
                });
                orderlines = orderlinesrpc;
            }).then(function () {
                framework.blockUI({
                    message: _t('Creating the new order...'),
                    css: {backgroundColor: '#f00', color: '#fff', 'font-family': 'Lato', 'font-size': '22px'}
                });
                self.create_order(order, orderlines);
            }).then(function () {
                framework.blockUI({
                    message: _t('The Order has been successfully created...'),
                    css: {backgroundColor: '#f00', color: '#fff', 'font-family': 'Lato', 'font-size': '22px'}
                });
                order_created.resolve();
                framework.unblockUI();
            });

            return order_created.promise();
        },
        create_order: function (order_data, orderlines_data) {
            var self = this;
            var order = new models.Order({}, {pos: this});

            this.synchorders.assign_values_to_order(order, order_data);

            order.lock_order();

            for (var j = 0, jlen = orderlines_data.length; j < jlen; j++) {
                var product = self.db.get_product_by_id(orderlines_data[j].product_id[0]);
                order.add_product(product);
                var last_orderline = order.get_last_orderline();
                self.synchorders.assign_values_to_orderline(last_orderline, orderlines_data[j]);
            }
            ;

            order.unlock_order();

            this.get('orders').add(order);
            this.set('selectedOrder', order);
            order.start_synch();
            return order;
        },
        get_order_sys: function (order_id) {
            return this.synchorders.connection.rpc('/poi_pos_presale/get_order_data', {'order_id': order_id});
        },
        get_orderlines_sys: function (order_id) {
            return this.synchorders.connection.rpc('/poi_pos_presale/get_orderline_data', {'order_id': order_id});
        },
        get_order_timestamp_sys: function (order_id) {
            return this.synchorders.connection.rpc('/poi_pos_presale/get_orders_timestamp', {'order_ids': [order_id]});
        },
        get_orders_timestamp_sys: function (order_ids) {
            return this.synchorders.connection.rpc('/poi_pos_presale/get_orders_timestamp', {'order_ids': order_ids});
        },
        get_order_by_id: function (order_id) {
            var self = this;
            var order_res = false;
            this.get('orders').chain().map(
                function (order) {
                    if (order.get('order_id') == order_id) {
                        order_res = order;
                    }
                    ;
                });
            return order_res;
        },
        get_order_data_by_id: function (order_id) {
            var self = this;
            var order_data = {
                'order_created': false,
                'timestamp': 0
            }
            this.get('orders').chain().map(
                function (order) {
                    if (order.get('order_id') == order_id) {
                        order_data = {
                            'order_created': true,
                            'timestamp': order.get_timestamp()
                        };
                    }
                    ;
                });
            return order_data;
        },
    });

    var _super_orderline = models.Orderline.prototype;

    models.Orderline = models.Orderline.extend({
        has_changes_to_save: function () {
            var self = this;
            if (this.old_orderline_resume) {
                if (JSON.stringify(this.export_as_JSON()) == JSON.stringify(this.old_orderline_resume)) {
                    return false;
                }
                else {
                    return true;
                }
            }
            return true;
        },
        save_changes: function () {
            var self = this;
            this.old_orderline_resume = this.export_as_JSON();
        },
        set_orderline_id: function (orderline_id) {
            this.set({'orderline_id': orderline_id});
        },
        get_orderline_id: function () {
            if (this.get('orderline_id')) {
                return this.get('orderline_id');
            }
            else {
                return false;
            }
        },
        set_unique_name: function (unique_name) {
            this.unique_name = unique_name;
        },
        get_unique_name: function () {
            if (this.unique_name) {
                return this.unique_name;
            }
            else {
                this.unique_name = 'Orderline_' + this.generateUniqueId() + this.get_product().id;
                return this.unique_name;
            }
        },
        generateUniqueId: function () {
            return new Date().getTime();
        },
        set_timestamp: function (timestamp) {
            this.set({'timestamp': timestamp});
        },
        get_timestamp: function () {
            if (this.get('timestamp')) {
                return this.get('timestamp');
            }
            else {
                return '';
            }
        },
        export_as_JSON: function () {
            var data = _super_orderline.export_as_JSON.apply(this, arguments);
            data.unique_name = this.get_unique_name();
            return data;
        },
        export_for_printing: function () {
            var data = _super_orderline.export_for_printing.apply(this, arguments);
            data.unique_name = this.get_unique_name();
            return data;
        },
    });


    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var res = _super_order.initialize.apply(this, arguments);
            this.locked = false;
            this.can_be_destroyed = true; //can_be_destroyed is going to allow orders screen to destroy the order in case that it's no longer available.
            //it's going to be false when we want it to see Receipts
            return res
        },
        //POS NEEDS A UNIQUE BASED ON TIME UNIQUE ID
        generateUniqueId: function () {
            var timestamp_unique = new Date().getTime();
            return this.pos.pos_session.id + '-' + timestamp_unique;
        },
        //
        mark_as_destroyable: function () {
            console.log('ORDER DESTROYABLE');
            this.can_be_destroyed = true;
        },
        mark_as_undestroyable: function () {
            console.log('ORDER UNDESTROYABLE');
            this.can_be_destroyed = false;
        },
        //lock_order and unlock_order are made to avoid pricelist changes.
        lock_order: function () {
            console.log('ORDER LOCKED');
            this.locked = true;
        },
        unlock_order: function () {
            console.log('ORDER UNLOCKED');
            this.locked = false;
        },
        /*
        This function intends to save all the orderlines, but we're not going to call this function from this module
        because this is a generic addon. This function needs to be called when the dependent addon wants to save all
        the orderline data on the db.
         */
        save_orderlines: function () {
            var self = this;
            if (this.get_order_id()) {
                var orderlines = this.orderlines.models;
                for (var i = 0; i < orderlines.length; i++) {
                    if (orderlines[i].has_changes_to_save()) {
                        (new instance.web.Model('pos.order')).get_func('save_orderline_from_ui')(self.get_order_id(), [orderlines[i].export_as_JSON()]).then(function () {
                            orderlines[i].save_changes();
                        });
                    }
                }
            }
        },
        start_synch: function () {
            var self = this;
            if (this.get_order_id()) {
                this.pos.synched_orders.push(this.get_order_id());
            }

            function synch_order() {
                if (self.get_order_id()) {
                    $.when(self.pos.get_order_timestamp_sys(self.get_order_id())).then(function (order_timestamp) {
                        if (order_timestamp[self.get_order_id()] > self.get_timestamp()) {
                            self.compare_order();
                        }
                        ;
                    }).always(function () {
                        if ($.inArray(self.get_order_id(), self.pos.synched_orders) >= 0) {
                            setTimeout(synch_order, 5000);
                        }
                    })
                }
            }

            synch_order();

        },
        stop_synch: function () {
            var self = this;
            this.pos.synched_orders.splice($.inArray(self.get_order_id(), this.pos.synched_orders), 1);
        },
        compare_order: function () {
            var self = this;
            var order = false;
            var orderlines = false;

            $.when(self.pos.get_order_sys(self.get_order_id())).then(function (orderrpc) {
                order = orderrpc;
                self.pos.synchorders.compare_order_data(self, order);
                return self.pos.get_orderlines_sys(order.id);
            }).then(function (orderlinesrpc) {

                var orderlinesrpc_un = []

                for (var i = 0; i < orderlinesrpc.length; i++) {
                    var orderline_sys = self.get_orderline_by_unique_name(orderlinesrpc[i].unique_name)
                    //Si se encontro dentro del sistema, hay que modificarlo, sino agregarlo
                    if (orderline_sys) {
                        self.pos.synchorders.compare_orderline_data(orderline_sys, orderlinesrpc[i]);
                    }
                    else {
                        self.pos.synchorders.add_new_orderline(self, orderlinesrpc[i]);
                    }
                    orderlinesrpc_un.push(orderlinesrpc[i].unique_name);
                }
                orderlines = orderlinesrpc;

                var unique_names = self.get_orderlines_unique_names();
                for (var j = 0; j < unique_names.length; j++) {
                    if ($.inArray(unique_names[j], orderlinesrpc_un) < 0) {
                        var line_to_remove = self.get_orderline_by_unique_name(unique_names[j]);
                        self.remove_orderline(line_to_remove);
                    }
                }
            });
        },
        set_order_id: function (order_id) {
            this.set({'order_id': order_id});
        },
        get_order_id: function () {
            if (this.get('order_id')) {
                return this.get('order_id');
            }
            else {
                return false;
            }
        },
        set_pos_group_id: function (pos_group_id) {
            this.set({'pos_group_id': pos_group_id});
        },
        get_pos_group_id: function () {
            if (this.get('pos_group_id')) {
                return this.get('pos_group_id');
            }
            else {
                return false;
            }
        },
        set_timestamp: function (timestamp) {
            this.set({'timestamp': timestamp});
        },
        get_timestamp: function () {
            if (this.get('timestamp')) {
                return this.get('timestamp');
            }
            else {
                return '';
            }
        },
        set_removal_flag: function () {
            this.to_be_removed = true;
        },
        get_orderline_by_unique_name: function (unique_name) {
            var orderline_selected = false;
            this.orderlines.each(function (orderline) {
                if (orderline.unique_name == unique_name) {
                    orderline_selected = orderline;
                }
            });
            return orderline_selected;
        },
        get_orderlines_unique_names: function () {
            var orderlines_un = [];
            this.orderlines.each(function (orderline) {
                orderlines_un.push(orderline.unique_name);
            });
            return orderlines_un;
        },
        mark_as_presale: function () {
            this.presale = true;
        },
        get_presale_status: function () {
            if (this.presale) {
                return true;
            }
            else {
                return false;
            }
        },
        export_as_JSON: function () {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.order_id = this.get_order_id();
            data.timestamp = this.get_timestamp();
            data.presale_order = this.get_presale_status();
            data.pos_group_id = this.pos.pos_group_id;
            return data;
        },
        export_for_printing: function () {
            var data = _super_order.export_for_printing.apply(this, arguments);
            data.order_id = this.get_order_id();
            data.timestamp = this.get_timestamp();
            data.presale_order = this.get_presale_status();
            data.pos_group_id = this.pos.pos_group_id;
            return data;
        },
    });


    /* SCREENS */

    var OrderSelectorPopupWidget = PopupWidget.extend({
        template: 'OrderSelectorPopupWidget',
        init: function (parent) {
            this.order_list_ids = [];
            this.orders_collection = [];
            this.connection = new Session(self, null, {use_cors: true});
            return this._super(parent);
        },
        show: function (options) {
            options = options || {};
            this._super(options);
            var self = this;

            this.order_list_ids = [];
            this.orders_collection = [];

            self.update_order_list();

            this.$('.back').click(function () {
                self.gui.show_screen(self.previous_screen);
            });

            this.$('.update-orders').click(function () {
                self.update_order_list();
            });
        },
        set_domain: function (domain) {
            this.pos.synch_domain = domain;
        },
        update_order_list: function () {
            var self = this;
            $.when(self.fetch_ids(self.pos.synch_domain, {})).then(function (orders) {
                var compare_result = self.compare_order_list(orders);

                var order_ids = [];

                for (var k = 0; k < orders.length; k++) {
                    order_ids.push(orders[k].id)
                }

                self.order_list_ids = order_ids;
                return compare_result;
            }).then(function (compare_result) {
                if (compare_result.to_add.length > 0) {
                    for (var i = 0; i < compare_result.to_add.length; i++) {
                        if (!self.find_order_button(compare_result.to_add[i])) {
                            self.add_order_button(compare_result.to_add[i]);
                        }
                    }
                }
                if (compare_result.to_remove.length > 0) {
                    for (var j = 0; j < compare_result.to_remove.length; j++) {
                        self.remove_order_button(compare_result.to_remove[j]);
                    }
                }
            })
        },
        compare_order_list: function (new_order_list) {

            var self = this;

            var order_ids = [];
            for (var k = 0; k < new_order_list.length; k++) {
                order_ids.push(new_order_list[k].id)
            }
            var new_order_list_ids = order_ids;

            var result = {
                'to_add': [],
                'to_remove': [],
            }

            var orders_to_check_update = [];

            if (new_order_list_ids) {
                var old_order_list = this.order_list_ids;
                for (var i = 0; i < new_order_list_ids.length; i++) {
                    if ($.inArray(new_order_list_ids[i], old_order_list) < 0) {
                        result.to_add.push(new_order_list_ids[i]);
                    }
                    else {
                        orders_to_check_update.push(new_order_list_ids[i]);
                    }
                }
                for (var i = 0; i < old_order_list.length; i++) {
                    if ($.inArray(old_order_list[i], new_order_list_ids) < 0) {
                        result.to_remove.push(old_order_list[i]);
                    }
                }

            }

            if (orders_to_check_update) {
                for (var i = 0; i < orders_to_check_update.length; i++) {
                    var order_button = self.find_order_button(orders_to_check_update[i]);
                    var new_timestamp = 0;
                    for (var k = 0; k < new_order_list.length; k++) {
                        if (new_order_list[k].id == orders_to_check_update[i]) {
                            new_timestamp = new_order_list[k].timestamp;
                        }
                    }
                    if (order_button.order != undefined) {
                        if (new_timestamp >= order_button.order.timestamp) {
                            self.update_order_button(orders_to_check_update[i]);
                        }
                    }

                }
            }
            return result;
        },
        fetch_ids: function (domain, context) {
            var result = [];
            context = context || {};
            return this.connection.rpc('/poi_pos_presale/get_order_ids', {
                'domain': domain,
                'context': context
            }).then(function (res) {
                return res.orders;
            });
        },
        add_order_button: function (order_id) {
            var self = this;
            this.pos.get_order_sys(order_id).then(function (order_data) {
                var new_order_button = new OrderButtonWidget(null, {
                    order: order_data,
                    pos: self.pos
                });
                self.orders_collection.push(new_order_button);
                new_order_button.appendTo(self.$('.order-list'));
            })

        },
        update_order_button: function (order_id) {
            var self = this;
            this.pos.get_order_sys(order_id).then(function (order_data) {
                var order_button = self.find_order_button(order_id);
                if (order_button) {
                    order_button.refresh_button(order_data);
                }
            })

        },
        remove_order_button: function (order_id) {
            var item = this.find_order_button(order_id);
            var position = $.inArray(item, this.orders_collection);
            this.orders_collection.splice(position, 1);
            item.destroy();
            /*
            if (item){
                item.parent().hide("puff", {}, 1000, function() {
                    $(this).remove();
                });
            }*/
        },
        find_order_button: function (order_id) {
            var self = this;
            for (var i = 0; i < this.orders_collection.length; i++) {
                if (self.orders_collection[i].order.id == order_id) {
                    return self.orders_collection[i];
                }
            }
            return false;
        },
        renderElement: function () {
            var self = this;
            this._super();
            for (var i = 0; i < this.order_list_ids.length; i++) {
                if (self.find_order_button(this.order_list_ids[i]).length == 0) {
                    self.add_order_button(this.order_list_ids[i]);
                }
            }
        },
    });

    gui.define_popup({name: 'orderselector-popup', widget: OrderSelectorPopupWidget});


    var OrderButtonWidget = PosBaseWidget.extend({
        template: 'OrderButtonWidget',
        init: function (parent, options) {
            this._super(parent, options);
            this.order = options.order;
        },
        refresh_button: function (order) {
            this.order = order;
            this.renderElement();
        },
        renderElement: function () {
            this._super();
            var self = this;
            this.$el.click(function () {
                self.selectOrder(self.order.id);
            });
        },
        selectOrder: function (order_id) {
            var self = this;
            //This intends to avoid miscreation
            var order_data = self.pos.get_order_data_by_id(order_id);
            if (order_data.order_created) {
                var order = self.pos.get_order_by_id(order_id);
                var actual_screen = order.get_screen_data('screen');

                self.pos.set('selectedOrder', order);

                if (actual_screen) {
                    order.set_screen_data({'screen': actual_screen});
                }
                else {
                    order.set_screen_data({'screen': 'products'});
                }

            }
            else {
                self.pos.build_order(order_id).done(function () {
                    self.on_order_built(order_id);
                });
            }
        },
        on_order_built: function (order_id) {
            // console.log('YA SE CREO LA ORDEN', order_id);
        },
        destroy: function () {
            var self = this;
            //This intends to avoid miscreation
            var order_data = self.pos.get_order_data_by_id(self.order.id);
            if (order_data.order_created) {
                var order = self.pos.get_order_by_id(self.order.id);
                console.log('THE ORDER CAN BE DESTROYED?', order.can_be_destroyed);
                if (order.can_be_destroyed) {
                    order.destroy();
                }
            }
            this._super();
        },
    });


    var OrderSelectorButtonWidget = PosBaseWidget.extend({
        template: 'OrderSelectorButtonWidget',
        init: function (parent, options) {
            options = options || {};
            this._super(parent, options);
            this.action = options.action;
            this.label = options.label;
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$el.click(function () {
                //self.gui.show_screen('orderselector', {});
                self.gui.show_popup('orderselector-popup', {})
            });
        },
        show: function () {
            this.$el.removeClass('oe_hidden');
        },
        hide: function () {
            this.$el.addClass('oe_hidden');
        },
    });


    var SynchOrdersWidget = PosBaseWidget.extend({
        init: function (parent, options) {
            var self = this;
            var options = options || {};
            this._super(parent, options);

            this.connection = new Session(self, null, {session_id: Session.session_id});
            this.synch_domain = [];

            this.pos.selected_order_id = false;
            this.pos.synched_orders = [];

            //This variable is to avoid duplicate connections
            this.connected = false;

        },
        save_actual_order: function () {
            var self = this;
            var actual_order = self.pos.get('selectedOrder');

            if (actual_order && actual_order.get_order_id()) {
                self.pos.selected_order_id = actual_order.get_order_id();
            }
            else {
                self.pos.selected_order_id = false;
            }
        },
        set_domain: function (domain) {
            this.synch_domain = domain;
        },
        fetch_ids: function (domain, context) {
            var result = [];
            this.save_actual_order();
            context = context || {};
            return this.connection.rpc('/poi_pos_presale/get_order_ids', {
                'domain': domain,
                'context': context
            }).then(function (res) {
                return res.orders;
            });
        },
        get_order: function (order_id) {
            return this.connection.rpc('/poi_pos_presale/get_order_data', {'order_id': order_id});
        },
        get_orderlines: function (order_id) {
            return this.connection.rpc('/poi_pos_presale/get_orderline_data', {'order_id': order_id});
        },
        get_order_timestamp: function (order_id) {
            return this.connection.rpc('/poi_pos_presale/get_orders_timestamp', {'order_ids': [order_id]});
        },
        assign_values_to_order: function (order, order_data) {
            order.set_order_id(order_data.id);
            order.set_timestamp(order_data.timestamp);
            //set_client
        },
        assign_values_to_orderline: function (orderline, orderline_data) {
            orderline.set_quantity(orderline_data.qty);
            orderline.set_discount(orderline_data.discount);
            orderline.set_unit_price(orderline_data.price_unit);
            orderline.set_orderline_id(orderline_data.id);
            orderline.set_unique_name(orderline_data.unique_name);
        },
        compare_order_data: function (order, order_data) {
            //We need some conditions to do this
            if (order.get_timestamp() != order_data.timestamp) {
                order.set_timestamp(order_data.timestamp);
            }
        },
        compare_orderline_data: function (orderline, orderline_data) {
            if (orderline.get_quantity() != orderline_data.qty) {
                orderline.set_quantity(orderline_data.qty);
            }
            if (orderline.get_discount() != orderline_data.discount) {
                orderline.set_discount(orderline_data.discount);
            }
            if (orderline.get_unit_price() != orderline_data.price_unit) {
                orderline.set_unit_price(orderline_data.price_unit);
            }
            if (orderline.get_orderline_id() != orderline_data.id) {
                orderline.set_orderline_id(orderline_data.id);
            }
            if (orderline.get_unique_name() != orderline_data.unique_name) {
                orderline.set_unique_name(orderline_data.unique_name);
            }
        },
        add_new_orderline: function (order, orderline_data) {
            order.lock_order();
            var product = this.pos.db.get_product_by_id(orderline_data.product_id[0]);
            var line = new models.Orderline({}, {pos: this.pos, order: order, product: product});
            this.assign_values_to_orderline(line, orderline_data);
            order.add_orderline(line);
            order.unlock_order();
        },
        set_flag_to_remove_all_orders: function () {
            this.pos.add_new_order();
            if (this.pos.get('orders').length > 1) {
                this.pos.get('orders').chain()
                    .map(function (new_order) {
                        new_order.set_removal_flag();
                    });
            }
        },
        set_flag_to_remove_nonused_orders: function (orders) {
            var self = this;
            var selectedOrder = this.pos.get('selectedOrder');

            if (this.pos.get('orders').length > 1) {
                this.pos.get('orders').chain()
                    .map(function (new_order) {
                        if (new_order.get_order_id()) {
                            if ($.inArray(new_order.get_order_id(), orders) == -1) {
                                new_order.set_removal_flag();
                            }
                            ;
                        }
                        else {
                            if (new_order.uid != selectedOrder.uid) {
                                new_order.set_removal_flag();
                            }
                        }
                    });
            }
        },
        set_flag_to_remove_order: function (order_id) {
            this.pos.get('orders').chain()
                .map(function (new_order) {
                    if (new_order.get_order_id() == order_id) {
                        new_order.set_removal_flag();
                    }
                });
        },
        set_flag_to_remove_other_orders: function (order_id) {
            this.pos.get('orders').chain()
                .map(function (new_order) {
                    if (new_order.get_order_id() != order_id) {
                        new_order.set_removal_flag();
                    }
                });
        },
        remove_orders: function () {
            /* REVERSING TO REMOVE, on_removed_order is having problems */
            for (var i = this.pos.get('orders').size() - 1, len = 0; i >= len; i--) {
                if (this.pos.get('orders').at(i).to_be_removed) {
                    this.pos.get('orders').at(i).destroy({'reason': 'abandon'});
                }
                ;
            }
            ;
        },
    });

    // BUTTONS


    var SendToPresaleButton = screens.ActionButtonWidget.extend({
        template: 'SendToPresaleButton',
        button_click: function () {
            var self = this;
            //alert("Send to Presale");
            //var order = this.pos.get_order();
            //console.log("ORDER", order);
            this.validate_order()
            //this.gui.show_popup('giftcardpayment-popup', {
            //    'order': self.pos.get_order(),
            //});
        },
        order_is_valid: function () {
            var self = this;
            var order = this.pos.get_order();

            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error', {
                    'title': _t('Empty Order'),
                    'body': _t('There must be at least one product in your order before it can be validated'),
                });
                return false;
            }

            // This was get from order_is_valid... Removed the other parts...

            return true;
        },

        finalize_validation: function () {
            var self = this;
            var order = this.pos.get_order();

            order.initialize_validation_date();

            this.pos.push_order(order);
            this.pos.get_order().finalize();
            //this.gui.show_screen('receipt');


        },

        // Check if the order is paid, then sends it to the backend,
        // and complete the sale process
        validate_order: function () {
            if (this.order_is_valid()) {
                this.finalize_validation();
            }
        },
    });

    screens.define_action_button({
        'name': 'sendtopresalebutton',
        'widget': SendToPresaleButton,
        'condition': function () {
            return this.pos.config.iface_presale;
        },
    });


    // Add the OrderSelector to the GUI, and set it as the default screen
    chrome.Chrome.include({
        build_widgets: function () {
            this._super();
            var w = new OrderSelectorButtonWidget(this, {});
            w.insertBefore(this.$('.header-button'));

            this.pos.synchorders = new SynchOrdersWidget(this, {});
        },
    });


    return {
        OrderSelectorPopupWidget: OrderSelectorPopupWidget,
    };

})
;
