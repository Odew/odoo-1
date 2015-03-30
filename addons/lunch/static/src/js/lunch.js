odoo.define('lunch.form_widgets', function (require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');
var Model = require('web.Model');
var form_widgets = require('web.form_widgets');
var form_relational = require('web.form_relational');
var _t = core._t;
var QWeb = core.qweb;
var lunch = {};

lunch.lunch_order_widget_previous_orders = form_relational.FieldOne2Many.extend(form_common.ReinitializeWidgetMixin, {
    template : 'lunch_order_widget_previous_orders',
    events: {
        'click span.add_button': 'set_order_line',
    },
    init: function(field_manager, node){
        this._super.apply(this, arguments);
        this.lunch_data = {};
        this.fields_to_read = ['product_id', 'supplier', 'note', 'price', 'category_id', 'currency_id'];
        this.monetary = new form_widgets.FieldMonetary(field_manager, node); // create instance to use format_value
        this.monetary.__edispatcherRegisteredEvents = []; // remove all bind events
    },
    // set_lunchbox_value: function(data){
    //     var self = this;
    //     _.each(data, function(datum){
    //         self.lunch_data[datum['id']] = datum;
    //     });
    // },
    // fetch_value: function(){
    //     var self = this;
    //     return this.dataset.call('read',[this.get('value'), this.fields_to_read])
    //         .done(function(data){
    //           self.set_lunchbox_value(data);
    //         });
    // },
    fetch_value: function(){
        var self = this;
        return this.dataset.call('read',[this.get('value'), this.fields_to_read])
            .done(function(data){
                _.each(data, function(order){
                    self.lunch_data[order['id']] = order;
            })})
    },
    get_line_value: function (id) {
        var data = _.clone(this.lunch_data[id]);
        if (typeof this.lunch_data[id]['product_id'][0] != 'undefined'){
            data['product_id'] = this.lunch_data[id]['product_id'][0];
        }
        if (typeof this.lunch_data[id]['supplier'][0] != 'undefined'){
            data['supplier'] = this.lunch_data[id]['supplier'][0];
        }
        if (typeof this.lunch_data[id]['category_id'][0] != 'undefined'){
            data['category_id'] = this.lunch_data[id]['category_id'][0];
        }
        return data;
    },
    set_order_line: function(event){
        var id = parseInt($(event.currentTarget).attr('id'));

        // Add the selection to the order lines
        var records = this.field_manager.get_field_value('order_line_ids');
        records.push([0, 0, this.get_line_value(id)]);

        this.field_manager.set_values({'order_line_ids': records});
        this.getParent().fields.order_line_ids.trigger_on_change();

        // If a previous order is selected several time, then the note is modified for one
        // order line, this note is applied to all lines. Forcing to render prevents this bug.
        this.render_value();
    },
    render_value: function() {
        var self = this;
        return this.fetch_value().done(function(data) {
            if (_.isEmpty(data)) {
              return self.$el.html(QWeb.render("lunch_order_widget_no_previous_order"));
            }
            var categories = _.groupBy(data,function(data1){return data1['supplier'][1];});
            return self.$el.html(QWeb.render("lunch_order_widget_previous_orders_list", {'widget': self, 'categories': categories}
            ));
        });
    },
    destroy: function () {
      this.monetary.destroy();
      this._super();
    }
});
core.form_widget_registry.add('previous_order', lunch.lunch_order_widget_previous_orders);

return lunch;

});



// odoo.define('lunch.form_widgets', function (require) {
// "use strict";
//
// var core = require('web.core');
// var form_common = require('web.form_common');
// var Model = require('web.Model');
// var form_widgets = require('web.form_widgets');
// var form_relational = require('web.form_relational');
// var _t = core._t;
// var QWeb = core.qweb;
// var lunch = {};
//
// lunch.lunch_order_widget_previous_orders = form_relational.AbstractManyField.extend(form_common.ReinitializeWidgetMixin, {
//     template : 'lunch_order_widget_previous_orders',
//     events: {
//          'click span.add_button': 'set_order_line',
//     },
//     init: function(field_manager, node){
//         this._super.apply(this, arguments);
//         this.lunch_data = {};
//         this.fields_to_read = ['product_id', 'supplier', 'note', 'price', 'category_id', 'currency_id'];
//         this.monetary = new form_widgets.FieldMonetary(field_manager, node); // create instance to use format_value
//         this.monetary.__edispatcherRegisteredEvents = []; // remove all bind events
//         // this.on("change:effective_readonly", this, this.reinitialize);
//     },
// //     set_lunchbox_value: function(data){
// //         var self = this;
// //         _.each(data, function(datum){
// //             self.lunch_data[datum['id']] = datum;
// //         });
// //     },
// //     fetch_value: function(){
// //         var self = this;
// //         return this.dataset.call('read',[this.get('value'), this.fields_to_read])
// //             .done(function(data){
// //               self.set_lunchbox_value(data);
// //             });
// //     },
//        fetch_value: function(){
//            var self = this;
//            return this.dataset.call('read',[this.get('value'), this.fields_to_read])
//                .done(function(data){
//                    _.each(data, function(order){
//                        self.lunch_data[order['id']] = order;
//                })})
//        },
//     get_line_value: function (id) {
//         var data = _.clone(this.lunch_data[id]);
//         if (typeof this.lunch_data[id]['product_id'][0] != 'undefined'){
//             data['product_id'] = this.lunch_data[id]['product_id'][0];
//         }
//         if (typeof this.lunch_data[id]['supplier'][0] != 'undefined'){
//             data['supplier'] = this.lunch_data[id]['supplier'][0];
//         }
//         if (typeof this.lunch_data[id]['category_id'][0] != 'undefined'){
//             data['category_id'] = this.lunch_data[id]['category_id'][0];
//         }
//         return data;
//     },
//     set_order_line: function(event){
//         var id = parseInt($(event.currentTarget).attr('id'));
//
//         // Add the selection to the order lines
//         var records = this.field_manager.get_field_value('order_line_ids');
//         records.push([0, 0, this.get_line_value(id)]);
//
//         this.field_manager.set_values({'order_line_ids': records});
//         this.getParent().fields.order_line_ids.dataset_changed();
//
//         // If a previous order is selected several time, then the note is modified for one
//         // order line, this note is applied to all lines. Forcing to render prevents this bug.
//         this.render_value();
//     },
//     render_value: function() {
//         var self = this;
//         return this.fetch_value().done(function(data) {
//             if (_.isEmpty(data)) {
//               return self.$el.html(QWeb.render("lunch_order_widget_no_previous_order"));
//             }
//             var categories = _.groupBy(data,function(data1){return data1['supplier'][1];});
//             return self.$el.html(QWeb.render("lunch_order_widget_previous_orders_list", {'widget': self, 'categories': categories}
//             ));
//         });
//     },
//     destroy: function () {
//       this.monetary.destroy();
//       this._super();
//     }
// });
// core.form_widget_registry.add('previous_order', lunch.lunch_order_widget_previous_orders);
//
// return lunch;
//
// });
