odoo.define('aspl_pos_multi_currency.models', function (require) {
	var models = require('point_of_sale.models');
	var rpc = require('web.rpc');
	var utils = require('web.utils');
	var round_pr = utils.round_precision;

	models.PosModel.prototype.models.push({
		model:  'res.currency',
        fields: ['name','rate','rounding','symbol','position','accuracy'],
        domain:  function(self)
		{
			if (self.config.enable_multi_currency && self.config.fetch_master){
				return [];
			}
			else if (self.config.enable_multi_currency && !self.config.fetch_master) {
				var selected_ids = [];
				selected_ids=self.config.pos_currencies;
				return [['id','in',selected_ids]];
			}
		},
        loaded: function(self, currency_list) {
        	if (self.config.enable_multi_currency && self.config.fetch_master) {
        		self.currency_list = currency_list;
        		self.dict_curr_list = {};
        		for (i in currency_list){
        			self.dict_curr_list[currency_list[i].id] = currency_list[i];
        		}
	            var length = 0;
			    for(var prop in self.currency_list) {
			    	if(currency_list.hasOwnProperty(prop)) { 
			            ++length;
				        if (self.currency_list[prop].rounding > 0) 
			                self.currency_list[prop].decimals = Math.ceil(Math.log(1.0 /  self.currency_list[prop].rounding) / Math.log(10));
				        else 
				        	self.currency_list[prop].decimals = 0;
		        	}
			    }
			    self.currency_list.length=length;
    		}
        	else if(self.config.enable_multi_currency && !self.config.fetch_master) {
        		self.currency_list = [];
        		self.dict_curr_list = {};
        		for (i in currency_list){
        			self.dict_curr_list[currency_list[i].id] = currency_list[i];
        			for (j in self.config.pos_currencies){
        				if (currency_list[i].id == self.config.pos_currencies[j]) {
	        				self.currency_list.push(currency_list[i]);
	    				}
        			}
        		}
        		var length = 0;
			    for(var prop in self.currency_list) {
			        if(currency_list.hasOwnProperty(prop)) { 
			            ++length;
				        if (self.currency_list[prop].rounding > 0) 
			                self.currency_list[prop].decimals = Math.ceil(Math.log(1.0 /  self.currency_list[prop].rounding) / Math.log(10));
				        else 
				        	self.currency_list[prop].decimals = 0;
		        	}
			    }
			    self.currency_list.length=length;
    		}
        },
    });

	var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
    	initialize: function(attributes,options){
            var res = _super_order.initialize.apply(this, arguments);
            if (this.pos.config.enable_multi_currency){
	            if (this.pos.currency_list && this.pos.currency_list.length>0){
	            	this.foreign_currency = $.extend({}, this.pos.currency_list[0]);
	            }
	            else{
	            	this.foreign_currency = false;
	            }
	            this.multi_currency_checked = false;
	            this.currency_total = 0;
	            this.currency_change = 0;
	            this.currency_paid = 0;
	            this.curr_input_selected = false;
	            this.set({
	            	curr_receipt_mode:false,
	            })
        	}
            return res;
    	},
    	export_as_JSON: function() {
            var submitted_order = _super_order.export_as_JSON.call(this);
            var new_val = {
        		order_currency_id : this.get_currency_id() || false,
        		amount_currency : this.get_amount_currency() || false,
            	}
            $.extend(submitted_order, new_val);
            return submitted_order;
    	},
    	set_currency_id: function(currency) {
            this.set('order_currency_id', currency);
        },
        get_currency_id: function() {
            return this.get('order_currency_id');
        },
        set_currency_mode: function(mode) {
            this.set('currency_mode', mode);
        },
        get_currency_mode: function() {
            return this.get('currency_mode');
        },
        set_currency_receipt_mode: function(curr_receipt_mode) {
        	this.set('curr_receipt_mode', curr_receipt_mode);
        },
        get_currency_receipt_mode: function() {
        	return this.get('curr_receipt_mode');
        },
        set_amount_currency: function(amount) {
        	this.set('amount_currency', amount);
        },
        get_amount_currency: function() {
        	return this.get('amount_currency');
        },
        get_amount_currency_with_symbol: function() {
        	var self = this;
        	var order = self.pos.get_order();
        	var position_symbol = order.get_curr_symbol();
        	var amount = this.get('amount_currency');
        	if(amount){
        		return (position_symbol.symbol || '')+' '+amount;
        	}
        	return
        },
        get_currency_change: function(){
			var self = this;
        	var order = self.pos.get_order();
        	var position_symbol = order.get_curr_symbol();
        	if(position_symbol){
        		var amount_with_symbol = (order.get_change()*order.foreign_currency.rate).toFixed(2)
        		return (position_symbol.symbol || '')+' ' +amount_with_symbol;
        	}
        	return
		},
		get_curr_symbol:function(){
			self = this;
			var order = self.pos.get_order();
			var curr_id=parseInt($("#currency_selection").val());
			if(curr_id){
				var curr = self.pos.dict_curr_list[curr_id]
				return {
					'symbol':curr.symbol,
					'position':curr.position
				}
			}
			return
		},
        add_paymentline: function(cashregister) {
            var self = this;
            _super_order.add_paymentline.call(this,cashregister);
            if(self.pos.config.enable_multi_currency){
            	var selected_paymentline = self.pos.get_order().selected_paymentline;
            	if(selected_paymentline){
            		selected_paymentline.set_amount(0);
            	}
            }
        },
    });
    
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options){
            this.line_amount_currency;
            _super_orderline.initialize.call(this, attr, options);
        },
        set_line_amount_currency: function(line_amount_currency) {
            this.set('line_amount_currency', line_amount_currency);
        },
        get_line_amount_currency: function() {
            return this.get('line_amount_currency');
        },
        export_as_JSON: function() {
            var lines = _super_orderline.export_as_JSON.call(this);
            var new_attr = {
            		line_amount_currency: this.get_line_amount_currency() || false,
            }
            $.extend(lines, new_attr);
            return lines;
        },
        export_for_printing: function() {
            var lines = _super_orderline.export_for_printing.call(this);
            var new_attr = {
            		line_amount_currency: this.get_line_amount_currency() || false,
            }
            $.extend(lines, new_attr);
            return lines;
        },
    });
});