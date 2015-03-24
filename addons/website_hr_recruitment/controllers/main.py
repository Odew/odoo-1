# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID, http, _
from openerp.http import request

from openerp.addons.website.models.website import slug

class WebsiteHrRecruitment(http.Controller):
    @http.route([
        '/jobs',
        '/jobs/country/<model("res.country"):country>',
        '/jobs/department/<model("hr.department"):department>',
        '/jobs/country/<model("res.country"):country>/department/<model("hr.department"):department>',
        '/jobs/office/<int:office_id>',
        '/jobs/country/<model("res.country"):country>/office/<int:office_id>',
        '/jobs/department/<model("hr.department"):department>/office/<int:office_id>',
        '/jobs/country/<model("res.country"):country>/department/<model("hr.department"):department>/office/<int:office_id>',
    ], type='http', auth="public", website=True)
    def jobs(self, country=None, department=None, office_id=None, **kwargs):
        env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))

        Country = env['res.country']
        HrJob = env['hr.job']

        # List jobs available to current UID and use sudo() because address is restricted
        jobs = HrJob.search([], order="website_published desc, no_of_recruitment desc").sudo()

        # Deduce departments and offices of those jobs
        departments = set(job.department_id for job in jobs if job.department_id)
        offices = set(job.address_id for job in jobs if job.address_id)
        countries = set(office.country_id for office in offices if office.country_id)

        # Default search by user country
        if not (country or department or office_id or kwargs.get('all_countries')):
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country = Country.search([('code', '=', country_code)], limit=1)
                if not any(job for job in jobs if job.address_id and job.address_id.country_id == country):
                    country = False

        # Filter the matching one
        if country and not kwargs.get('all_countries'):
            jobs = (job for job in jobs if job.address_id is None or job.address_id.country_id == country)
        if department:
            jobs = (job for job in jobs if job.department_id == department)
        if office_id:
            jobs = (job for job in jobs if job.address_id and job.address_id.id == office_id)

        # Render page
        return request.website.render("website_hr_recruitment.index", {
            'jobs': jobs,
            'countries': countries,
            'departments': departments,
            'offices': offices,
            'country_id': country,
            'department_id': department,
            'office_id': office_id,
        })

    @http.route('/jobs/add', type='http', auth="user", website=True)
    def jobs_add(self, **kwargs):
        job = request.env['hr.job'].create({
            'name': _('New Job Offer'),
        })
        return request.redirect("/jobs/detail/%s?enable_editor=1" % slug(job))

    @http.route('/jobs/detail/<model("hr.job"):job>', type='http', auth="public", website=True)
    def jobs_detail(self, job, **kwargs):
        return request.render("website_hr_recruitment.detail", {
            'job': job,
        })

    @http.route('/jobs/apply/<model("hr.job"):job>', type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        return request.render("website_hr_recruitment.apply", {
            'job': job,
            'error': error,
            'default': default,
        })

    @http.route('/jobs/thankyou', methods=['POST'], type='http', auth="public", website=True)
    def jobs_thankyou(self, **post):
        error = {}
        for field_name in ["partner_name", "phone", "email_from"]:
            if not post.get(field_name):
                error[field_name] = 'missing'
        if error:
            request.session['website_hr_recruitment_error'] = error
            ufile = post.pop('ufile')
            if ufile:
                error['ufile'] = 'reset'
            request.session['website_hr_recruitment_default'] = post
            return request.redirect('/jobs/apply/%s' % post.get("job_id"))

        # public user can't create applicants (duh)
        env = request.env(user=SUPERUSER_ID)
        value = {
            'name': '%s\'s Application' % post.get('partner_name'),
        }
        for f in ['email_from', 'partner_name', 'description']:
            value[f] = post.get(f)
        for f in ['department_id', 'job_id']:
            value[f] = int(post.get(f) or 0)
        # Retro-compatibility for saas-3. "phone" field should be replace by "partner_phone" in the template in trunk.
        value['partner_phone'] = post.pop('phone', False)

        # If the email is already known in our database, match it to the existing partner, else create a new one
        Partner = env['res.partner']
        existing_partner = Partner.name_search(name=post.get('email_from').strip(), args=[('is_company', '=', False)], limit=1)

        if not existing_partner:
            value_partner = {
                'name': post['partner_name'],
                'email': post['email_from'],
                'phone': value['partner_phone'],
            }
            partner = Partner.create(value_partner)
            value['partner_id'] = partner.id
        else:
            value['partner_id'] = existing_partner[0][0]

        # Create applicant
        applicant = env['hr.applicant'].create(value)
        if post['ufile']:
            name = applicant.partner_name if applicant.partner_name else applicant.name
            applicant.message_post(
                body = _("%s's Application \n From: %s \n\n %s \n") % (name, applicant.email_from or "", applicant.description or ""),
                attachments = [(post['ufile'].filename, post['ufile'].read())],
                content_subtype = 'plaintext',
                subtype = "hr_recruitment.mt_applicant_hired")

        return request.render("website_hr_recruitment.thankyou", {})
