odoo.define('aspl_pos_multi_currency.screens', function (require) {
	
	var models = require('point_of_sale.models');
	var gui = require('point_of_sale.gui');
	var screens = require('point_of_sale.screens');
	var utils = require('web.utils');
	var round_pr = utils.round_precision;
	var round_di = utils.round_decimals;
	
	var core = require('web.core');
	var QWeb = core.qweb;
	var _t = core._t;
	var ReceiptScreenWidget = screens.ReceiptScreenWidget;
	
	screens.PaymentScreenWidget.include ({
		init: function(parent, options) {
	        var self = this;
	        this._super(parent, options);
		},
		click_paymentline: function(cid) {
			var self = this;
			this._super(cid);
			var order = self.pos.get_order();
			order.curr_input_selected=false;
		},
		findWithAttr: function(array, attr, value) {
		    for(var i = 0; i < array.length; i += 1) 
		    {
		        if(array[i][attr] === value) 
		            return i;
		    }
		},
		convert_currency: function(currency_id,amount){
			var self = this;
			if(!currency_id && !amount){
				return 
			}
			var order = self.pos.get_order();
			var currency = self.pos.dict_curr_list[currency_id];
			if(currency){
				var decimals = currency.decimals;
				var currency_total = round_di(amount*currency.rate,decimals).toFixed(decimals);
				return currency_total;
			} else{
				return false
			}
		},
		format_foreign: function(amount,currency,precision) {
            if(!amount && !currency){
            	return
            }
			var decimals = currency.decimals;
            if (precision && (typeof this.pos.dp[precision]) !== undefined) {
                decimals = this.pos.dp[precision];
            }
            if (typeof amount === 'number') {
                amount = round_di(amount,decimals).toFixed(decimals);
//                amount = openerp.instances[this.session.name].web.format_value(round_di(amount, decimals), { type: 'float', digits: [69, decimals]});
            }
            if (currency.position === 'after') {
                return amount + ' ' + (currency.symbol || '');
            } else {
                return (currency.symbol || '') + ' ' + amount;
            }
        },
        set_foreign_values: function(currency_id){
			var self=this;
			var currentOrder=self.pos.get_order();
			var currency_id = currency_id;
			var currency = self.pos.dict_curr_list[currency_id];
			if (currency){
				var name = currency.name;
				var rate_silent = currency.rate;
				var decimals = currency.decimals;
				var currency_total = round_di(currentOrder.get_total_with_tax()*currency.rate,decimals).toFixed(decimals);
				if (self.pos.config.display_conversion)
					self.$('#conversion_rate').html('1 '+self.pos.currency.name+' = '+
							rate_silent + ' ' + name);
				self.$('#currency_value_label').html(_t('Total in ')+name + ':');
				self.$('#foreign_input_label').html(_t('Paid in ')+name + ':');
				self.$('#receipt_currency_label').html(_t('Receipt in ')+name + ':');
				self.$('#currency_value').html(self.format_foreign(currency_total,currency));
				self.$('#foreign_change_label').html(_t('Change in ') + name + ':');
				self.$('#foreign_change_value').html(self.format_foreign(0,currency));
			}
		},
		show: function(){
            var self = this;
            this._super();
            currentOrder = self.pos.get_order();
            currentOrder.set_currency_receipt_mode(false);
            self.$("#curr_input").focus(function() {
            	$('body').off('keypress',self.keyboard_handler);
               	$('body').off('keydown',self.keyboard_keydown_handler);
	           	window.document.body.removeEventListener('keypress',self.keyboard_handler);
	           	window.document.body.removeEventListener('keydown',self.keyboard_keydown_handler);
            });
            self.$("#curr_input").focusout(function() {
                window.document.body.addEventListener('keypress',self.keyboard_handler);
                window.document.body.addEventListener('keydown',self.keyboard_keydown_handler);
            });
            if (self.pos.config.enable_multi_currency) {
            	self.$('#curr_input').focus(function(e){
            		if (this.value!=''){
            			$(this).select();
            		}
            		if(self.numpad_state){
                        self.numpad_state.reset();
                    }
            		currentOrder.curr_input_selected=true;
        		});
            	self.$('#curr_receipt').change(function(e) {
	            	if($('#curr_receipt').prop("checked") == true){
	            		currentOrder.set_currency_receipt_mode(true);
	            	} else{
	            		currentOrder.set_currency_receipt_mode(false);
	            	}
            	});
	            self.$('#toggle_multi_currency').change(function(e) {
	            	if (self.pos.currency_list.length==0) {
		            	alert("Add Currency from pos configuration.");
		            	return false;
	        		}
	            	currentOrder.multi_currency_checked=self.$('#toggle_multi_currency').prop("checked");
	            	currentOrder.set_currency_mode(true);
	            	if (currentOrder.multi_currency_checked) {
	    				self.$('.section_currency').show();
	    				self.$('#curr_input').focus();
	    				if (self.$('#curr_input').val()!='')
	    					self.$('#curr_input').select();
	    				currentOrder.curr_input_selected=true;
	    				if(self.numpad_state){
	    					self.numpad_state.reset();
	                    }
    				} else{
	    				self.$('.section_currency').hide();
	    				currentOrder.set_currency_mode(false);
	            		currentOrder.curr_input_selected=false;
    				}
	    		});
	            self.$('#toggle_multi_currency').prop("checked",currentOrder.multi_currency_checked);
	            var foreign_decimals=currentOrder.foreign_currency.decimals;
	            var foreign_currency_rate=currentOrder.foreign_currency.rate;
				currentOrder.currency_total=round_di(currentOrder.get_total_with_tax()*foreign_currency_rate,foreign_decimals).toFixed(foreign_decimals);
				var curr_id = parseInt(self.$("#currency_selection").val());
	            self.set_foreign_values(curr_id);
	            if (currentOrder.currency_paid==0){
	            	self.$('#curr_input').val('');
	            }
	            else{
	            	self.$('#curr_input').val(currentOrder.currency_paid);
	            }
	            this.$('#curr_input').keyup(function(e){
	            	currentOrder = self.pos.get_order();
	            	currentOrder.currency_paid = $(this).val();
					var line = currentOrder.selected_paymentline;
					if (line==undefined){
						self.gui.show_popup('error',{
			                title: _t('Error'),
			                body:  _t('No Payment Line selected !'),
			            });
						self.$('#curr_input').val(0);
						return false;
					}
					var curr_id = self.$("#currency_selection").val();
					var currency = self.pos.dict_curr_list[curr_id];
					if(currency){
						converted_value=round_di(this.value/currency.rate,self.pos.currency.decimals).toFixed(self.pos.currency.decimals);
						line.set_amount(converted_value);
						self.render_paymentlines();
						self.$('.paymentline.selected .edit').text(converted_value);
					}
				});
	            self.$("#currency_selection").change(function(e){
					var currentOrder = self.pos.get_order();
					self.$('#curr_input').focus();
					var selected_currency = parseInt($(this).val());
					selected_id = self.findWithAttr(self.pos.currency_list, 'id', selected_currency);
					currentOrder.set_currency_id(selected_currency);
					currentOrder.foreign_currency = $.extend({}, self.pos.currency_list[selected_id]);
					var foreign_currency_rate = currentOrder.foreign_currency.rate;
					currentOrder.currency_total = round_di(currentOrder.get_total_with_tax()*foreign_currency_rate,foreign_decimals).toFixed(foreign_decimals);
					self.set_foreign_values(selected_currency);
					self.$('#curr_input').val(0);
					var p_line = currentOrder.selected_paymentline;
					if (p_line==undefined || p_line==""){
						self.$('.paymentline input').val(0);
						return false;
					}
					p_line.set_amount(0);
					self.render_paymentlines();
				});
	            self.$("#currency_selection").val(currentOrder.foreign_currency.id);
	            self.$('#toggle_multi_currency').trigger('change');
	            self.$('#btn_rate_update').click(function(){
	            	var currency_id = parseInt(self.$("#currency_selection").val());
	            	var currency = self.pos.dict_curr_list[currency_id];
	            	if(currency){
	            		self.gui.show_popup("rate_update_popup",{'currency':currency});
	            	} else{
	            		alert("Currency not found.");
	            	}
	            })
        	}
		},
		set_value: function(val) {
        	var self=this;
        	var curr_input_selected=this.pos.get('selectedOrder').curr_input_selected;
        	if (curr_input_selected){
        		var foreign_decimals=currentOrder.foreign_currency.decimals;
        		value=round_di(val,foreign_decimals).toFixed(foreign_decimals);
        		self.$('#curr_input').val(value);
        		self.$('#curr_input').trigger('keyup');
        	}
        	else{
	            var selected_line = this.pos.get_order().selected_paymentline;
	            if(selected_line){
	                selected_line.set_amount(val);
	                selected_line.node.querySelector('input').value = selected_line.amount.toFixed(2);
	            }
        	}
        },
		add_paymentline: function(line){
			this._super(line);
			this.pos.get_order().curr_input_selected=false;
		},
		get_currency_selection:function(){
			var self = this
			return self.pos.currency_list[0];
		},
		finalize_validation: function() {
			var self = this;
	        var order = this.pos.get_order();
	        var value = self.$('#curr_input').val();
	        order.set_currency_id(false);
	        if(order.get_currency_mode() && Number(value)>0){
	        	var foreign_decimals = order.foreign_currency.decimals;
            	var selected_currency = parseInt($('#currency_selection').val());
            	var currency = self.pos.dict_curr_list[selected_currency];
	            order.set_currency_id(selected_currency);
	            order.set_amount_currency(value);
	            var orderlines = order.get_orderlines();
		        if(orderlines){
		        	var curr_receipt_lines = [];
		        	_.each(orderlines, function(line){
			            var line_amount_currency = round_di(line.get_display_price()*currency.rate,foreign_decimals).toFixed(foreign_decimals);
			            line.set_line_amount_currency(line_amount_currency);
			            curr_receipt_lines.push(self.format_foreign(line_amount_currency,currency));
		        	})
		        }
            }
	        self._super();
		},
	});

	ReceiptScreenWidget.include({
		print_xml: function() {
			var self = this;
			self._super();
			var order = self.pos.get_order();
			if(self.pos.config.enable_multi_currency && order.get_currency_receipt_mode() && order.get_currency_id()){
    			var orderlines = self.pos.get_order().get_orderlines();
                var receipt_order_lines = []
                if (orderlines){
                	_.each(orderlines, function(line){
                		receipt_order_lines.push(line.export_for_printing())
                	})
                	var param = {
                        widget:self,
                        orderlines: receipt_order_lines,
                        order: order,
                        receipt: order.export_for_printing(),
                        pos: self.pos,
                    }
                    var currency_receipt = QWeb.render('CurrencyReceipt', param);
                    self.pos.proxy.print_receipt(currency_receipt);
                }
	        }
		},
		render_receipt: function() {
	        var self = this;
	        var order = self.pos.get_order();
	        self._super();
	        if(self.pos.config.enable_multi_currency && order.get_currency_receipt_mode() && order.get_currency_id()){
    			var orderlines = self.pos.get_order().get_orderlines();
                var receipt_order_lines = []
                if (orderlines){
                	var param = {
                        widget:self,
                        orderlines: orderlines,
                        order: order,
                        receipt: order.export_for_printing(),
                        pos: self.pos,
                    }
                	this.$('.pos-currency_receipt-container').html(QWeb.render('CurrencyPosTicket', param));
                }
	        } else {
	        	this.$('.pos-currency_receipt-container').html('');
	        }
	    },
	});
});