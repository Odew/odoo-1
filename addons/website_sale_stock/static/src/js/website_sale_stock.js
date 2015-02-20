odoo.define('website_sale_stock.website_sale_stock', function(require) {
    "use strict";
    $(document).ready(function() {
        $('input.js_check_stock').change(function() {
            var available_qty = parseInt($(this).data('max'));
            if (parseInt($(this).val()) > available_qty) {
                var stock_alert = $('#add_to_cart').parent().find('#stock_warning');
                if (stock_alert.length == 0) {
                    $('#add_to_cart').parent().prepend('<p class="bg-warning" style="padding: 15px;" id="stock_warning">Sorry ! Only ' + available_qty + ' units are still in stock');
                } else {
                    stock_alert.html('Sorry ! Only' + available_qty + ' units are still in stock');
                }
                $(this).val(available_qty);
            }
        })
    });

});
