(function () {
    'use strict';

var web_editor = openerp.web_editor || (openerp.web_editor = {});
var _t = openerp._t;

//////////////////////////////////////////////////////////////////////////////////////////////////////////

web_editor.no_editor = !!$(document.documentElement).data('editable-no-editor');

web_editor.add_template_file('/web_editor/static/src/xml/editor.xml');

web_editor.dom_ready.done(function () {
    $(document).on('click', '.note-editable', function (ev) {
        ev.preventDefault();
    });

    $(document).on('submit', '.note-editable form .btn', function (ev) {
        // Disable form submition in editable mode
        ev.preventDefault();
    });

    $(document).on('hide.bs.dropdown', '.dropdown', function (ev) {
        // Prevent dropdown closing when a contenteditable children is focused
        if (ev.originalEvent
                && $(ev.target).has(ev.originalEvent.target).length
                && $(ev.originalEvent.target).is('[contenteditable]')) {
            ev.preventDefault();
        }
    });
});
web_editor.reload = function () {
    location.hash = "scrollTop=" + window.document.body.scrollTop;
    if (location.search.indexOf("enable_editor") > -1) {
        window.location.href = window.location.href.replace(/enable_editor(=[^&]*)?/g, '');
    } else {
        window.location.reload();
    }
};

//////////////////////////////////////////////////////////////////////////////////////////////////////////

/* ----- TOP EDITOR BAR FOR ADMIN ---- */

web_editor.ready().then(function () {
    if (location.search.indexOf("enable_editor") >= 0 && !web_editor.no_editor) {
        web_editor.editor_bar = new web_editor.EditorBar();
        web_editor.editor_bar.prependTo(document.body);
    }
});

web_editor.EditorBar = openerp.Widget.extend({
    template: 'web_editor.editorbar',
    events: {
        'click button[data-action=save]': 'save',
        'click a[data-action=cancel]': 'cancel',
    },
    init: function(parent) {
        var self = this;
        var res = this._super.apply(this, arguments);
        this.parent = parent;
        this.rte = new web_editor.RTE(this);
        this.rte.on('rte:ready', this, function () {
            self.trigger('rte:ready');
        });
        return res;
    },
    start: function() {
        var self = this;
        this.saving_mutex = new openerp.Mutex();

        this.$('button[data-action=save]').prop('disabled', true);
        $('.dropdown-toggle').dropdown();

        this.display_placeholder();

        this.rte.on('change', this, this.proxy('rte_changed'));
        this.rte.start();
        this.rte.start_edition();

        var flag = false;
        window.onbeforeunload = function(event) {
            if ($('.o_editable.o_dirty').length && !flag) {
                flag = true;
                setTimeout(function () {flag=false;},0);
                return _t('This document is not saved!');
            }
        };
        return this._super();
    },
    display_placeholder: function () {
        var $area = $("#wrapwrap").find("[data-oe-model] .oe_structure.oe_empty, [data-oe-model].oe_structure.oe_empty, [data-oe-type=html]")
            .addClass("oe_empty")
            .attr("data-oe-placeholder", _t("Press The Top-Left Edit Button"));

        this.on('rte:ready', this, function () {
            $area.attr("data-oe-placeholder", _t("Write Your Text Here"));
        });
        this.on("snippets:ready", this, function () {
            if ($("body").hasClass("editor_has_snippets")) {
                $area.attr("data-oe-placeholder", _t("Write Your Text or Drag a Block Here"));
            }
        });

        $(document).on("keyup", function (event) {
            if((event.keyCode === 8 || event.keyCode === 46)) {
                var $target = $(event.target).closest(".o_editable");
                if(!$target.is(":has(*:not(p):not(br))") && !$target.text().match(/\S/)) {
                    $target.empty();
                }
            }
        });
    },
    rte_changed: function () {
        this.$('button[data-action=save]').prop('disabled', false);
    },
    _save: function () {
        var self = this;

        var saved = {}; // list of allready saved views and data

        var defs = $('.o_editable')
            .filter('.o_dirty')
            .removeAttr('contentEditable')
            .removeClass('o_dirty oe_carlos_danger o_is_inline_editable')
            .map(function () {
                var $el = $(this);

                $el.find('[class]').filter(function () {
                    if (!this.className.match(/\S/)) {
                        this.removeAttribute("class");
                    }
                });

                // remove multi edition
                var key =  $el.data('oe-model')+":"+$el.data('oe-id')+":"+$el.data('oe-field')+":"+$el.data('oe-type')+":"+$el.data('oe-expression');
                if (saved[key]) return true;
                saved[key] = true;

                // TODO: Add a queue with concurrency limit in webclient
                // https://github.com/medikoo/deferred/blob/master/lib/ext/function/gate.js
                return self.saving_mutex.exec(function () {
                    return self.saveElement($el)
                        .then(undefined, function (thing, response) {
                            // because ckeditor regenerates all the dom,
                            // we can't just setup the popover here as
                            // everything will be destroyed by the DOM
                            // regeneration. Add markings instead, and
                            // returns a new rejection with all relevant
                            // info
                            var id = _.uniqueId('carlos_danger_');
                            $el.addClass('o_dirty oe_carlos_danger ' + id);
                            return $.Deferred().reject({
                                id: id,
                                error: response.data,
                            });
                        });
                });
            }).get();
        return $.when.apply(null, defs).then(function () {
            window.onbeforeunload = null;
        }, function (failed) {
            // If there were errors, re-enable edition
            self.rte.start_edition(true);
            // jquery's deferred being a pain in the ass
            if (!_.isArray(failed)) { failed = [failed]; }

            _(failed).each(function (failure) {
                var html = failure.error.exception_type === "except_osv";
                if (html) {
                    var msg = $("<div/>").text(failure.error.message).html();
                    var data = msg.substring(3,msg.length-2).split(/', u'/);
                    failure.error.message = '<b>' + data[0] + '</b>' + data[1];
                }
                $('.o_editable.' + failure.id)
                    .removeClass(failure.id)
                    .popover({
                        html: html,
                        trigger: 'hover',
                        content: failure.error.message,
                        placement: 'auto top',
                    })
                    // Force-show popovers so users will notice them.
                    .popover('show');
            });
        });
    },
    save: function () {
        return this._save().then(function () {
            web_editor.reload();
        });
    },
    /**
     * Saves an RTE content, which always corresponds to a view section (?).
     */
    save_without_reload: function () {
        return this._save();
    },
    saveElement: function ($el) {
        var markup = $el.prop('outerHTML');
        return openerp.jsonRpc('/web/dataset/call', 'call', {
            model: 'ir.ui.view',
            method: 'save',
            args: [$el.data('oe-id'), markup,
                   $el.data('oe-xpath') || null,
                   web_editor.get_context()],
        });
    },
    cancel: function () {
        new $.Deferred(function (d) {
            var $dialog = $(openerp.qweb.render('web_editor.discard')).appendTo(document.body);
            $dialog.on('click', '.btn-danger', function () {
                d.resolve();
            }).on('hidden.bs.modal', function () {
                d.reject();
            });
            d.always(function () {
                $dialog.remove();
            });
            $dialog.modal('show');
        }).then(function () {
            window.onbeforeunload = null;
            web_editor.reload();
        });
    },
});

})();

