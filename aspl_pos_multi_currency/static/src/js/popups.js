odoo.define('aspl_pos_multi_currency.popups', function (require) {
	
	var gui = require('point_of_sale.gui');
	var PopupWidget = require('point_of_sale.popups');
	var rpc = require('web.rpc');
	
	var CurrencyRateUpdatePopup = PopupWidget.extend({
	    template: 'CurrencyRateUpdatePopup',
	    show: function(options){
	        var self = this;
	    	this.options = options || {};
	        this._super(options);
	        window.document.body.removeEventListener('keypress',self.pos.chrome.screens.payment.keyboard_handler);
            window.document.body.removeEventListener('keydown',self.pos.chrome.screens.payment.keyboard_keydown_handler);
            this.renderElement();
            self.$('#new_rate').focus();
            self.$('#new_rate').keypress(function(event) {
                if(event.which == 8 || event.which == 0){
                    return true;
                }
                if(event.which < 46 || event.which > 59) {
                    return false;
                    //event.preventDefault();
                } // prevent if not number/dot

                if(event.which == 46 && $(this).val().indexOf('.') != -1) {
                    return false;
                    //event.preventDefault();
                } // prevent if already dot
            });
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var currency_id = self.options.currency.id;
	    	var order = self.pos.get_order();
	    	var new_rate = self.$('#new_rate').val();
	    	if(new_rate && new_rate>0){
	    		var params = {
	    	    		model: 'res.currency.rate',
	    	    		method: 'currency_rate_update',
	    	    		args: [currency_id,new_rate],
	    	    	}
	    	    	rpc.query(params, {async: false}).then(function(new_currency){
	    	    		if(new_currency){
	    	    			var all_currencies = self.pos.dict_curr_list;
	    	    			_.each(all_currencies, function(key,currency){
	    	    				if(new_currency.currency_id[0] == currency){
	    	    					key.rate = new_currency.rate;
	    	    					self.pos.gui.screen_instances.payment.set_foreign_values(key.id);
	    	    					$("#curr_input").val(0);
	    	    					var line = order.selected_paymentline;
	    	    					if(line){
	    	    						line.set_amount(0);
	    	    					}
	    	    					self.pos.gui.screen_instances.payment.render_paymentlines();
	    	    				}
	    	    			});
	    	    			window.document.body.removeEventListener('keypress',self.pos.chrome.screens.payment.keyboard_handler);
	    	                window.document.body.removeEventListener('keydown',self.pos.chrome.screens.payment.keyboard_keydown_handler);
	    	    		}
	    	    	});
	    		self.gui.close_popup();
	    	} else{
	    		alert("Please enter new rate of currency in proper format");
	    		self.$('#new_rate').focus();
	    	}
	    },
	});
	gui.define_popup({name:'rate_update_popup', widget: CurrencyRateUpdatePopup});
});