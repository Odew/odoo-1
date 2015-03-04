(function () {
    'use strict';

if (openerp.web_editor) {
    return;
}

var web_editor = openerp.web_editor = {};
openerp.web_editor_ = web_editor;

//////////////////////////////////////////////////////////////////////////////////////////////////////////

web_editor.get_context = function (dict) {
    var html = document.documentElement;
    return _.extend({
        'lang': (html.getAttribute('lang') || '').replace('-', '_'),
    }, dict);
};

//////////////////////////////////////////////////////////////////////////////////////////////////////////
/* ----------------------------------------------------
   Async Ready and Template loading
   ---------------------------------------------------- */

var templates_def = $.Deferred().resolve();
web_editor.add_template_file = function(template) {
    var def = $.Deferred();
    templates_def = templates_def.then(function() {
        openerp.qweb.add_template(template, function(err) {
            if (err) {
                def.reject(err);
            } else {
                def.resolve();
            }
        });
        return def;
    });
    return def;
};

web_editor.dom_ready = $.Deferred();
$(document).ready(function () {
    web_editor.dom_ready.resolve();
    // fix for ie
    if($.fn.placeholder) $('input, textarea').placeholder();
});

var all_ready;
web_editor.ready = function() {
    if (!all_ready) {
        all_ready = web_editor.dom_ready.then(function () {
            return templates_def;
        }).promise();
    }
    return all_ready;
};

})();
