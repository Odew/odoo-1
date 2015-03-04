(function () {
    'use strict';

    var web_editor = openerp.web_editor;

    window.top.openerp[callback+"_updown"] = function (value, fields_values, field_name) {
        var $editable = $("#wrapwrap .o_editable:first");
        if(value !== $editable.prop("innerHTML")) {
            if ($('body').hasClass('editor_enable')) {
                if (value !== fields_values[field_name]) {
                    web_editor.editor_bar.rte.historyRecordUndo($editable);
                }
                web_editor.editor_bar.snippets.make_active(false);
            }
            
            $editable.html(value);

            if ($('body').hasClass('editor_enable') && value !== fields_values[field_name]) {
                $editable.trigger("content_changed");
            }
        }
    };

    web_editor.EditorBar.include({
        start: function () {
            if (location.search.indexOf("enable_editor") !== -1) {
                this.on('rte:ready', this, function () {
                    this.$('form').hide();

                    if (window.top.openerp[callback+"_editor"]) {
                        window.top.openerp[callback+"_editor"](this);
                    }

                    var $editable = $("#wrapwrap .o_editable:first");
                    setTimeout(function () {
                        $($editable.find("*").filter(function () {return !this.children.length;}).first()[0] || $editable)
                            .focusIn().trigger("mousedown").trigger("keyup");
                    },0);

                    $editable.on('content_changed', this, function () {
                        if (window.top.openerp[callback+"_downup"]) {
                            window.top.openerp[callback+"_downup"]($editable.prop('innerHTML'));
                        }
                    });
                });

                this.on("snippets:ready", this, function () {
                    $(window.top).trigger("resize");
                });

            } else if (window.top.openerp[callback+"_editor"]) {
                window.top.openerp[callback+"_editor"](this);
            }
            return this._super();
        }
    });

    web_editor.snippet.BuildingBlock.include({
        _get_snippet_url: function () {
            return snippets_url;
        }
    });
        
})();