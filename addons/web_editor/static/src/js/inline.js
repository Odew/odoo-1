(function () {
    'use strict';

    var web_editor = openerp.web_editor;
    
    web_editor['style-inline'] = true;
    
    web_editor.EditorBar.include({
        start: function () {
            var self = this;
            if (location.search.indexOf("enable_editor") !== -1) {
                this.on('rte:ready', this, function () {
                    // move the caret at the end of the text when click after all content
                    $("#wrapwrap").on('click', function (event) {
                        if ($(event.target).is("#wrapwrap") || $(event.target).is("#wrapwrap .o_editable:first:empty")) {
                            setTimeout(function () {
                                var node = $("#wrapwrap .o_editable:first *")
                                    .filter(function () { return this.textContent.match(/\S|\u00A0/); })
                                    .add($("#wrapwrap .o_editable:first"))
                                    .last()[0];
                                $.summernote.core.range.create(node, $.summernote.core.dom.nodeLength(node)).select();
                            },0);
                        }
                    });
                });
            }
            return this._super.apply(this, arguments);
        },
    });

    web_editor.snippet.BuildingBlock.include({
        start: function () {
            var self = this;
            this._super();
            setTimeout(function () {
                var $editable = $("#wrapwrap .o_editable:first");
                web_editor.img_to_font($editable);
                web_editor.style_to_class($editable);
            });
        },
        clean_for_save: function () {
            this._super();
            var $editable = $("#wrapwrap .o_editable:first");
            web_editor.class_to_style($editable);
            web_editor.font_to_img($editable);
        },

    });

    window.top.openerp[callback+"_updown"] = function (value, fields_values) {
        var $editable = $("#wrapwrap .o_editable:first");
        value = value || "";
        if (value.indexOf('on_change_model_and_list') === -1 && value !== $editable.html()) {
            web_editor.editor_bar.rte.historyRecordUndo($editable, true);
            web_editor.editor_bar.snippets.make_active(false);
            
            $editable.html(value);

            web_editor.img_to_font($editable);
            web_editor.style_to_class($editable);
        } else {
            $editable.trigger("content_changed");
        }
    };

})();