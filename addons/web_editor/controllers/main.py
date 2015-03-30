# -*- coding: utf-8 -*-
from openerp.http import request, STATIC_CACHE
from openerp.addons.web import http
import json
import io
from PIL import Image, ImageFont, ImageDraw
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
import cStringIO
import werkzeug.wrappers
import time
import logging
logger = logging.getLogger(__name__)


class Web_Editor(http.Controller):
    #------------------------------------------------------
    # Backend snippet
    #------------------------------------------------------
    @http.route('/web_editor/snippets', type='json', auth="none")
    def snippets(self, **kwargs):
        return request.registry["ir.ui.view"].render(request.cr, request.uid, 'web_editor.snippets', None, context=request.context)

    #------------------------------------------------------
    # Backend html field
    #------------------------------------------------------
    @http.route('/web_editor/field/html', type='http', auth="none")
    def FieldTextHtml(self, model=None, res_id=None, field=None, callback=None, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        record = None
        if model and res_id:
            res_id = int(res_id)
            record = request.registry[model].browse(cr, uid, res_id, context)

        datarecord = json.loads(kwargs['datarecord'])
        kwargs.update({
            'content': record and getattr(record, field) or "",
            'model': model,
            'res_id': res_id,
            'field': field,
            'datarecord': datarecord,
            'debug': 'debug' in kwargs,
        })

        if not kwargs.get('languages'):
            langs = request.registry["res.lang"].search_read(cr, uid, [], ['code', 'name'], context=context)
            kwargs['languages'] = [(lg['code'], lg['name']) for lg in langs]

        return request.render(kwargs.get("template") or "web_editor.FieldTextHtml", kwargs, uid=request.uid)

    #------------------------------------------------------
    # Backend html field in inline mode
    #------------------------------------------------------
    @http.route('/web_editor/field/html/inline', type='http', auth="none")
    def FieldTextHtmlInline(self, model=None, res_id=None, field=None, callback=None, **kwargs):
        kwargs['inline_mode'] = True
        kwargs['dont_load_assets'] = not kwargs.get('enable_editor')
        return self.FieldTextHtml(model, res_id, field, callback, **kwargs)

    #------------------------------------------------------
    # convert font into picture
    #------------------------------------------------------
    @http.route([
        '/web_editor/font_to_img/<icon>',
        '/web_editor/font_to_img/<icon>/<color>',
        '/web_editor/font_to_img/<icon>/<color>/<int:size>',
        '/web_editor/font_to_img/<icon>/<color>/<int:size>/<int:alpha>',
        ], type='http', auth="none")
    def export_icon_to_png(self, icon, color='#000', size=100, alpha=255, font='/web/static/lib/fontawesome/fonts/fontawesome-webfont.ttf'):
        """ This method converts FontAwesom pictograms to Images and is Used only
            for mass mailing becuase custom fonts are not supported in mail.
            :param icon : character from FontAwesom cheatsheet
            :param color : RGB code of the color
            :param size : Pixels in integer
            :param alpha : transparency of the image from 0 to 255
            :param font : font path

            :returns PNG image converted from given font
        """
        # Initialize font
        addons_path = http.addons_manifest['web']['addons_path']
        font_obj = ImageFont.truetype(addons_path + font, size)

        # Determine the dimensions of the icon
        image = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        boxw, boxh = draw.textsize(icon, font=font_obj)
        draw.text((0, 0), icon, font=font_obj)
        left, top, right, bottom = image.getbbox()

        # Create an alpha mask
        imagemask = Image.new("L", (boxw, boxh), 0)
        drawmask = ImageDraw.Draw(imagemask)
        drawmask.text((-left, -top), icon, font=font_obj, fill=alpha)

        # Create a solid color image and apply the mask
        if color.startswith('rgba'):
            color = color.replace('rgba', 'rgb')
            color = ','.join(color.split(',')[:-1])+')'
        iconimage = Image.new("RGBA", (boxw, boxh), color)
        iconimage.putalpha(imagemask)

        # Create output image
        outimage = Image.new("RGBA", (boxw, size), (0, 0, 0, 0))
        outimage.paste(iconimage, (left, top))

        # output image
        output = io.BytesIO()
        outimage.save(output, format="PNG")
        response = werkzeug.wrappers.Response()
        response.mimetype = 'image/png'
        response.data = output.getvalue()
        response.headers['Cache-Control'] = 'public, max-age=604800'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
        response.headers['Connection'] = 'close'
        response.headers['Date'] = time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime())
        response.headers['Expires'] = time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(time.time()+604800*60))

        return response

    #------------------------------------------------------
    # image route for browse record
    #------------------------------------------------------
    def placeholder(self, response):
        return request.registry['ir.attachment']._image_placeholder(response)

    @http.route([
        '/web_editor/image',
        '/web_editor/image/<xmlid>',
        '/web_editor/image/<xmlid>/<field>',
        '/web_editor/image/<model>/<id>/<field>',
        '/web_editor/image/<model>/<id>/<field>/<int:max_width>x<int:max_height>'
        ], type='http', auth="public")
    def image(self, model=None, id=None, field=None, xmlid=None, max_width=None, max_height=None):
        """ Fetches the requested field and ensures it does not go above
        (max_width, max_height), resizing it if necessary.

        If the record is not found or does not have the requested field,
        returns a placeholder image via :meth:`~.placeholder`.

        Sets and checks conditional response parameters:
        * :mailheader:`ETag` is always set (and checked)
        * :mailheader:`Last-Modified is set iif the record has a concurrency
          field (``__last_update``)

        The requested field is assumed to be base64-encoded image data in
        all cases.

        xmlid can be used to load the image. But the field image must by base64-encoded
        """
        if xmlid and "." in xmlid:
            try:
                record = request.env.ref(xmlid)
                model, id = record._name, record.id
            except:
                raise werkzeug.exceptions.NotFound()
            if model == 'ir.attachment' and not field:
                if record.sudo().type == "url":
                    field = "url"
                else:
                    field = "datas"

        if not model or not id or not field:
            raise werkzeug.exceptions.NotFound()

        try:
            idsha = str(id).split('_')
            id = idsha[0]
            response = werkzeug.wrappers.Response()
            return request.registry['ir.attachment']._image(
                request.cr, request.uid, model, id, field, response, max_width, max_height,
                cache=STATIC_CACHE if len(idsha) > 1 else None)
        except Exception:
            logger.exception("Cannot render image field %r of record %s[%s] at size(%s,%s)",
                             field, model, id, max_width, max_height)
            response = werkzeug.wrappers.Response()
            return self.placeholder(response)

    #------------------------------------------------------
    # add attachment (images or link)
    #------------------------------------------------------
    @http.route('/web_editor/attachment/add', type='http', auth='user', methods=['POST'])
    def attach(self, func, upload=None, url=None, disable_optimization=None, **kwargs):
        # the upload argument doesn't allow us to access the files if more than
        # one file is uploaded, as upload references the first file
        # therefore we have to recover the files from the request object
        Attachments = request.registry['ir.attachment']  # registry for the attachment table

        uploads = []
        message = None
        # no image provided, storing the link and the image name
        if not upload:
            uploads.append({'local_url': url})
            name = url.split("/").pop()                       # recover filename
            attachment_id = Attachments.create(request.cr, request.uid, {
                'name': name,
                'type': 'url',
                'url': url,
                'res_model': 'ir.ui.view',
            }, request.context)
        else:                                                  # images provided
            try:
                attachment_ids = []
                for c_file in request.httprequest.files.getlist('upload'):
                    image_data = c_file.read()
                    image = Image.open(cStringIO.StringIO(image_data))
                    w, h = image.size
                    if w*h > 42e6: # Nokia Lumia 1020 photo resolution
                        raise ValueError(
                            u"Image size excessive, uploaded images must be smaller "
                            u"than 42 million pixel")

                    if not disable_optimization and image.format in ('PNG', 'JPEG'):
                        image_data = image_save_for_web(image)

                    attachment_id = Attachments.create(request.cr, request.uid, {
                        'name': c_file.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': c_file.filename,
                        'res_model': 'ir.ui.view',
                    }, request.context)
                    attachment_ids.append(attachment_id)

                uploads = Attachments.read(
                    request.cr, request.uid, attachment_ids, ['local_url'],
                    context=request.context)
            except Exception, e:
                logger.exception("Failed to upload image to attachment")
                message = unicode(e)

        return """<script type='text/javascript'>
            window.parent['%s'](%s, %s);
        </script>""" % (func, json.dumps(uploads), json.dumps(message))

    #------------------------------------------------------
    # remove attachment (images or link)
    #------------------------------------------------------
    @http.route('/web_editor/attachment/remove', type='json', auth='user')
    def remove(self, ids, **kwargs):
        """ Removes a web-based image attachment if it is used by no view (template)

        Returns a dict mapping attachments which would not be removed (if any)
        mapped to the views preventing their removal
        """
        cr, uid, context = request.cr, request.uid, request.context
        Attachment = request.registry['ir.attachment']
        Views = request.registry['ir.ui.view']

        attachments_to_remove = []
        # views blocking removal of the attachment
        removal_blocked_by = {}

        for attachment in Attachment.browse(cr, uid, ids, context=context):
            # in-document URLs are html-escaped, a straight search will not
            # find them
            url = escape(attachment.local_url)
            ids = Views.search(cr, uid, ["|", ('arch_db', 'like', '"%s"' % url), ('arch_db', 'like', "'%s'" % url)], context=context)

            if ids:
                removal_blocked_by[attachment.id] = Views.read(
                    cr, uid, ids, ['name'], context=context)
            else:
                attachments_to_remove.append(attachment.id)
        if attachments_to_remove:
            Attachment.unlink(cr, uid, attachments_to_remove, context=context)
        return removal_blocked_by

    #------------------------------------------------------
    # get translations from a view or a field
    #------------------------------------------------------
    @http.route('/web_editor/get_view_translations', type='json', auth='public', website=True)
    def get_view_translations(self, xml_id, lang=None):
        lang = lang or request.context.get('lang')
        return request.registry["ir.ui.view"].get_view_translations(
            request.cr, request.uid, xml_id, lang=lang, context=request.context)

    #------------------------------------------------------
    # set translations for a view or a field
    #------------------------------------------------------
    @http.route('/web_editor/set_translations', type='json', auth='public', website=True)
    def set_translations(self, data, lang):
        irt = request.registry.get('ir.translation')
        for trans in data:
            initial_content = trans['initial_content'].strip()
            new_content = trans['new_content'].strip()
            tid = trans['translation_id']
            if not tid:
                domain = [
                    ('res_id', '=', trans['id']),
                    ('lang', '=', lang),
                    ('src', '=', initial_content)]
                if trans['model'] == 'ir.ui.view':
                    domain += [
                        ('type', '=', 'view'),
                        ('name', '=', "website")]
                else:
                    domain += [
                        ('type', '=', 'model'),
                        ('name', '=', "%s,%s" % (trans['model'], trans['field']))]

                old_trans = irt.search_read(request.cr, request.uid, domain)
                if old_trans:
                    tid = old_trans[0]['id']

            if tid:
                vals = {'value': new_content}
                irt.write(request.cr, request.uid, [tid], vals)
            else:
                new_trans = {
                    'res_id': trans['id'],
                    'lang': lang,
                    'source': initial_content,
                    'value': new_content,
                }
                if trans['model'] == 'ir.ui.view':
                    new_trans['type'] = 'view'
                    new_trans['name'] = 'website'
                else:
                    new_trans['type'] = 'model'
                    new_trans['name'] = "%s,%s" % (trans['model'], trans['field'])

                if trans.get('gengo_translation'):
                    new_trans['gengo_translation'] = trans.get('gengo_translation')
                    new_trans['gengo_comment'] = trans.get('gengo_comment')
                irt.create(request.cr, request.uid, new_trans)
        return True
