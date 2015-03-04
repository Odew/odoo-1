(function() {
    "use strict";
    var web_editor = openerp.web_editor;

    web_editor.snippet.animationRegistry.visitor = web_editor.snippet.Animation.extend({
        selector: ".oe_country_events",
        start: function () {
            var self = this;
            $.post( "/event/get_country_event_list", function( data ) {
                if(data){
                    $( ".country_events_list" ).replaceWith( data );
                }
            });
        }
    });
})();