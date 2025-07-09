from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import base64
import csv
from io import StringIO

class CrmLeadImportWizard(models.TransientModel):
    _name = 'crm.lead.import.wizard'
    _description = 'Import Leads Wizard'

    csv_file = fields.Binary(string="CSV File", required=True)
    csv_filename = fields.Char(string="CSV Filename")

    def action_import(self):
        if not self.csv_file:
            raise ValidationError(_("Please upload a CSV file."))

        csv_data = base64.b64decode(self.csv_file).decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))

        required_columns = ["City/Town", "Customer", "Email", "Opportunity", "Phone", "Referred By", "Sales Team", "Source"]
        for column in required_columns:
            if column not in csv_reader.fieldnames:
                raise ValidationError(_("The CSV file is missing the required column: %s") % column)

        # Use importing_leads context
        ctx = {'importing_leads': True}
        for row in csv_reader:
            partner = self.env['res.partner'].search([('name', '=', row['Customer'])], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': row['Customer']})

            team = self.env['crm.team'].search([('name', '=', row['Sales Team'])], limit=1)
            source = self.env['utm.source'].search([('name', '=', row['Source'])], limit=1)
            referred_by = self.env['hr.employee'].search([('name', '=', row['Referred By'])], limit=1)

            self.env['crm.lead'].with_context(ctx).sudo().create({
                'name': row['Opportunity'],
                'partner_id': partner.id,
                'email_from': row['Email'],
                'phone': row['Phone'],
                'city': row['City/Town'],
                'source_id': source.id if source else False,
                'team_id': team.id if team else False,
                'referred_by': referred_by.id if referred_by else False,
                'type': 'lead',
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class CrmStage(models.Model):
    _inherit = "crm.stage"
    probability = fields.Float(string="Probability")

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    # Add a computed field to display contact name more prominently
    display_name = fields.Char(string="Contact Name", compute="_compute_display_name", store=True)
    
    @api.depends('partner_id', 'contact_name', 'partner_name')
    def _compute_display_name(self):
        for lead in self:
            if lead.partner_id:
                lead.display_name = lead.partner_id.name
            elif lead.contact_name:
                lead.display_name = lead.contact_name
            elif lead.partner_name:
                lead.display_name = lead.partner_name
            else:
                lead.display_name = lead.name

    date_closed = fields.Datetime(
        string='Closed Date',
        tracking=True,
        readonly=False,
        copy=False,
        help="Date this lead/opportunity was closed."
    )

    # Selection field for Mode of Study
    mode_of_study = fields.Selection([
        ('offline', 'Offline'),
        ('online', 'Online')
    ], string="Mode of Study", default='offline')

    # New fields - adding copy=True to ensure they persist during lead conversion
    estimated_joining_date = fields.Char(
        string="Estimated Joining Date", 
        copy=True,
        help="When the student plans to join"
    )
    course_preferred = fields.Char(
        string="Course Preferred", 
        copy=True,
        help="What course the lead is interested in"
    )
    preferred_branch = fields.Char(
        string="Preferred Branch", 
        copy=True,
        help="Which branch location the lead prefers"
    )
    
    # Add back the field but set it as deprecated
    malayalee_status = fields.Selection([
        ('malayalee', 'Malayalee'),
        ('non_malayalee', 'Non-Malayalee')
    ], string="Malayalee Status", tracking=True, help="This field is deprecated and will be removed in future versions.")

    avatar_128 = fields.Binary(string="Avatar 128", related='partner_id.avatar_128', store=True, readonly=False)
    image_1920 = fields.Binary(string="Image", related="partner_id.image_1920", store=True, readonly=False)

    whatsapp_number = fields.Char(string="WhatsApp Number", related="partner_id.whatsapp_number", store=True, readonly=False)
    date_of_birth = fields.Date(string="Date of Birth", related="partner_id.date_of_birth", store=True, readonly=False)
    age = fields.Integer(string="Age", related="partner_id.age", store=True, readonly=False)
    father_guardian = fields.Char(string="Father/Guardian", related="partner_id.father_guardian", store=True, readonly=False)
    qualification = fields.Char(string="Qualification", related="partner_id.qualification", store=True, readonly=False)
    street = fields.Char(string="Address 1", related='partner_id.street', store=True, readonly=False)
    street2 = fields.Char(string="Address 2", related='partner_id.street2', store=True, readonly=False)
    city = fields.Char(string="City/Town", related='partner_id.city', store=True, readonly=False)
    district = fields.Char(string="District", store=True, readonly=False)
    country_id = fields.Many2one('res.country',string="Country", related='partner_id.country_id', store=True, readonly=False, default=lambda self: self.env.company.country_id.id)
    state_id = fields.Many2one('res.country.state',string="State", related='partner_id.state_id', store=True, readonly=False, default=lambda self: self.env.company.state_id.id)
    mobile_alt = fields.Char(string="Mobile (Alt)", related='partner_id.mobile_alt', store=True, readonly=False)

    aadhaar_no = fields.Char(string="Student Aadhaar No", related='partner_id.aadhaar_no', store=True, readonly=False)
    # Bank Details
    bank_account_name = fields.Char(string="Account Holder Name", related='partner_id.bank_account_name', store=True, readonly=False)
    bank_account_no = fields.Char(string="Account No", related='partner_id.bank_account_no', store=True, readonly=False)
    bank_ifsc_code = fields.Char(string="IFSC Code", related='partner_id.bank_ifsc_code', store=True, readonly=False)
    bank_name = fields.Char(string="Bank Name", related='partner_id.bank_name', store=True, readonly=False)
    relation_with_bank_acc_holder = fields.Selection(
        selection=[('self', 'Self/Own'),('spouse', 'Spouse'),
            ('mother', 'Mother'),('father', 'Father'),('grand_father', 'Grand Father'),
            ('grand_mother', 'Grand Mother'),('uncle', 'Uncle'),
            ('aunt', 'Aunt'),('brother', 'Brother'),
            ('sister', 'Sister'),('son', 'Son'),
            ('daughter', 'Daughter'),('other', 'Other (Specify)')
        ],
        string="Relationship with Account Holder", default="self", related='partner_id.relation_with_bank_acc_holder', store=True, readonly=False
    )

    categ_id = fields.Many2one('product.category',string='Product Category',compute='_compute_category', store=True)
    @api.depends('course_id')
    def _compute_category(self):
        for rec in self:
            rec.categ_id = rec.course_id.categ_id.id if rec.course_id else False
    relation_with_bank_acc_holder_manual = fields.Char(string="Specify Relation", related='partner_id.relation_with_bank_acc_holder_manual', store=True, readonly=False)

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    course_id = fields.Many2one('product.product', string="Course", required=False)
    enrollment_number = fields.Char(string="Enrollment No", )

    expected_revenue = fields.Monetary(compute="_compute_expected_revenue", store=True, readonly=False, required=False)  # Changed from required=True to required=False
    
    referred_by = fields.Many2one('hr.employee', string="Referred By")
    @api.depends('course_id')
    def _compute_expected_revenue(self):
        for record in self:
            if record.course_id:
                record.expected_revenue = record.course_id.list_price
            else:
                # Set a default value when there's no course_id
                record.expected_revenue = 0.0

    # Override the built-in probability compute method
    probability = fields.Float(compute="_compute_probability")

    @api.depends('stage_id')
    def _compute_probabilities(self):
        for lead in self:
            if lead.stage_id:
                lead.probability = lead.stage_id.probability

    invoice_status = fields.Selection(
        selection=lambda self: self.env["sale.order"]._fields["invoice_status"].selection,
        related="sale_order_id.invoice_status",
        string="Invoice Status",
        readonly=True, copy=False,
        )
    
    is_won = fields.Boolean(related='stage_id.is_won')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    def action_create_sale_order(self):
        if not self.partner_id:
            raise ValidationError(f'You need to set a Customer before confirming the Sale!')
        if not self.course_id:
            raise ValidationError(f'You need to selecte a Course before confirming the Sale!')

        if not self.aadhaar_no or not self.bank_account_name or not self.bank_account_no or not self.bank_ifsc_code or not self.bank_name or not self.relation_with_bank_acc_holder:
            raise ValidationError(f'You have to fill the following fields before confirming Sale:\n Aadhaar No, Account Holder Name, Account No, IFSC Code, Bank Name, Relationship with Account Holder')
        sale_order_data = {
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'origin': self.name,
            'source_id': self.source_id.id,
            'company_id': self.company_id.id or self.env.company.id,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
            'order_line': [
                (0,0, {
                    'product_id': self.course_id.id,
                })
                ]
        }
        if self.team_id:
            sale_order_data['team_id'] = self.team_id.id
        if self.user_id:
            sale_order_data['user_id'] = self.user_id.id

        sale_order = self.env['sale.order'].create(sale_order_data)
        sale_order.action_confirm()
        self.sale_order_id = sale_order.id

    def action_create_invoice(self):
        if self.sale_order_id:
            return {
                'name': _('Create Invoice'),
                'res_model': 'sale.advance.payment.inv',
                'view_mode': 'form',
                'context': {
                    'active_model': 'sale.order',
                    'active_ids': [self.sale_order_id.id],
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
    invoice_count = fields.Integer(related="sale_order_id.invoice_count")
        
    def action_view_invoice(self):
        if self.sale_order_id:
            if self.invoice_count > 0:
                return self.sale_order_id.action_view_invoice()

    @api.model_create_multi
    def create(self, vals):
        res = super(CRMLead, self).create(vals)
        if not self.env.context.get('importing_leads'):
            for record in res:
                record.set_lead_queue()
                if record.type == 'opportunity':
                    record._check_course_id_required()
                    record._check_source_id_required()
        return res
    
    def write(self, vals):
        # Store old user_id before write
        old_user_ids = {record.id: record.user_id.id for record in self}
        
        # First check if we're already in a set_lead_queue operation to prevent recursion
        if self.env.context.get('setting_lead_queue'):
            res = super(CRMLead, self).write(vals)
            return res
        
        res = super(CRMLead, self).write(vals)
        
        # If user_id (salesperson) changed, reassign pending activities
        if 'user_id' in vals:
            for record in self:
                old_user_id = old_user_ids[record.id]
                new_user_id = vals['user_id']
                if old_user_id != new_user_id:
                    # Get all pending activities for this lead
                    activities = self.env['mail.activity'].search([
                        ('res_id', '=', record.id),
                        ('res_model', '=', 'crm.lead'),
                        ('user_id', '=', old_user_id),
                        ('state', '!=', 'done')
                    ])
                    # Reassign activities to new user
                    if activities:
                        activities.write({'user_id': new_user_id})
        
        # Add check for type change (lead to opportunity conversion)
        converting_to_opportunity = vals.get('type') == 'opportunity'
        
        # Don't call set_lead_queue again if we're already importing leads or
        # if we're in the set_lead_queue process to prevent infinite recursion
        if not self.env.context.get('importing_leads') and not self.env.context.get('setting_lead_queue'):
            for record in self:
                record.set_lead_queue()
                # Only check source and course if converting to opportunity or updating specific fields
                if converting_to_opportunity or any(f in vals for f in ['stage_id', 'source_id', 'course_id']):
                    if record.type == 'opportunity':
                        record._check_course_id_required()
                        record._check_source_id_required()
        return res

    def set_lead_queue(self):
        for record in self:
            if record.type == 'lead' and not record.user_id:
                # First check for duplicate leads by phone or email
                duplicates = False
                
                # Check by phone
                if record.phone:
                    duplicates = self.env['crm.lead'].search([
                        ('id', '!=', record.id),
                        ('phone', '=', record.phone),
                        ('user_id', '!=', False),
                        ('create_date', '<', record.create_date)
                    ], order='create_date DESC', limit=1)
                
                # If no duplicates found by phone, check by email
                if not duplicates and record.email_from:
                    duplicates = self.env['crm.lead'].search([
                        ('id', '!=', record.id),
                        ('email_from', '=', record.email_from),
                        ('user_id', '!=', False), 
                        ('create_date', '<', record.create_date)
                    ], order='create_date DESC', limit=1)
                
                # If duplicate found, assign to the same salesperson
                if duplicates:
                    record.with_context(setting_lead_queue=True).user_id = duplicates[0].user_id.id
                    if duplicates[0].team_id:
                        record.with_context(setting_lead_queue=True).team_id = duplicates[0].team_id.id
                    return
                
                # If no duplicates, continue with the regular assignment process
                # First try to assign based on preferred branch
                if record.preferred_branch:
                    team = self.env['crm.team'].search([
                        ('name', 'ilike', record.preferred_branch)
                    ], limit=1)
                    if team:
                        # Use context to prevent recursion
                        record.with_context(setting_lead_queue=True).team_id = team.id
                
                # If no team assigned by preferred branch, try city
                if not record.team_id and record.city:
                    team = self.env['crm.team'].search([
                        ('name', 'ilike', record.city)
                    ], limit=1)
                    if team:
                        # Use context to prevent recursion
                        record.with_context(setting_lead_queue=True).team_id = team.id
                
                # Now proceed with queue-based assignment if we have a team
                if record.team_id and record.team_id.queue_line_ids:
                    all_users_assigned_lead = len(record.team_id.queue_line_ids.mapped('current_lead')) == len(record.team_id.queue_line_ids)
                    # Reset current lead of all salespersons to False, to allow allocating new leads to them in next round
                    if all_users_assigned_lead:
                        record.team_id.queue_line_ids[0].write({'current_lead': record.id})
                        # Use context to prevent recursion
                        record.with_context(setting_lead_queue=True).user_id = record.team_id.queue_line_ids[0].salesperson_id.id
                        for queue_line in record.team_id.queue_line_ids[1:]:
                            queue_line.write({'current_lead': False})
                    else:
                        for queue_line in record.team_id.queue_line_ids:
                            # If no lead is assigned to this salesperson in current round
                            if not queue_line.current_lead:
                                queue_line.write({'current_lead': record.id})
                                # Use context to prevent recursion
                                record.with_context(setting_lead_queue=True).user_id = queue_line.salesperson_id.id
                                break

    date_deadline = fields.Date(string="Deadline", required=False)

    def _check_course_id_required(self):
        # Skip all validations if importing leads
        if self.env.context.get('importing_leads'):
            return
        required_stages = ['Prospect (P)', 'Hot Prospect (HP)']
        
        for record in self:
            if record.type == 'opportunity':
                # Existing validations
                if record.stage_id.name in required_stages:
                    if not record.course_id:
                        raise ValidationError(_('You need to select a Course when the lead is in stage: %s') % record.stage_id.name)
                    if not record.date_deadline:
                        raise ValidationError(_('You need to set a Deadline when the lead is in stage: %s') % record.stage_id.name)

    def _check_source_id_required(self):
        # Skip validation if importing leads
        if self.env.context.get('importing_leads'):
            return
        for record in self:
            # Only validate if it's an opportunity and in a relevant stage
            if record.type == 'opportunity' and record.stage_id.name not in ['Lost', 'Won']:
                if not record.source_id:
                    raise ValidationError(_('You need to select a Source for the lead.'))

    def action_import_lead(self):
        # Logic to handle lead import
        self.ensure_one()
        if not self.source_id:
            raise ValidationError(_('You need to select a Source for the lead.'))
        if not self.date_deadline:
            raise ValidationError(_('You need to set a Deadline for the lead.'))
        # Additional import logic here
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_change_expected_revenue(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Expected Revenue',
            'res_model': 'crm.lead.change.revenue.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_currency_id': self.currency_id.id},
        }

    def action_open_collection_form(self):
        collection = self.env['crm.lead.collection'].search([('lead_id', '=', self.id), ('state', '=', 'pending')], limit=1)
        if collection:
            view_id = self.env.ref('tijus_crm_custom.view_crm_lead_collection_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Collect Payment',
                'res_model': 'crm.lead.collection',
                'view_mode': 'form',
                'view_id': view_id,
                'res_id': collection.id,
                'target': 'new',
            }
        else:
            raise ValidationError(_('No pending collections found for this lead.'))

    sales_objection = fields.Selection([
        ('trust', 'Trust'),
        ('fees', 'Fees'),
        ('need', 'Need'),
        ('stall', 'Stall')
    ], string="Sales Objection", tracking=True)

    date_closed_editable = fields.Boolean('Allow Editing Date Closed', default=False)

    def edit_date_closed(self):
        """Toggle editability of date_closed field"""
        self.ensure_one()
        self.date_closed_editable = not self.date_closed_editable
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # Update the call_status field to include 'not_connected'
    call_status = fields.Selection([
        ('not_called', 'Not Called'),
        ('not_connected', 'Call not connected'), # New status
        ('call_1', '1st Call'),
        ('followup_1', 'Followup 1'),
        ('followup_2', 'Followup 2'),
        ('followup_3', 'Followup 3'),
        ('followup_4', 'Followup 4'),
        ('followup_5', 'Followup 5'),
        ('followup_6', 'Followup 6'),
        ('followup_7', 'Followup 7'),
        ('followup_8', 'Followup 8'),
        ('followup_9', 'Followup 9'),
        ('followup_10', 'Followup 10'),
    ], string="Call Status", default='not_called', tracking=True)
    
    call_remarks = fields.Text(string="Call Remarks")
    call_history_ids = fields.One2many('crm.lead.call.history', 'lead_id', string='Call History')

    def log_call(self):
        """Log the current call status and remarks to history"""
        self.ensure_one()
        if self.call_status and self.call_status != 'not_called':
            # Create the call history record with the current server time
            self.env['crm.lead.call.history'].create({
                'lead_id': self.id,
                'call_status': self.call_status,
                'remarks': self.call_remarks,
                'user_id': self.env.user.id,
                'call_date': fields.Datetime.now(),  # Explicitly set call_date to now
            })
            
            # Force update the lead's write_date by writing an empty dict
            # This updates the "Last Updated" field on the lead
            self.write({})
            
            # Clear remarks field after logging
            self.call_remarks = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Call Logged'),
                    'message': _('Call status and remarks have been saved to history.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Warning'),
                'message': _('Please select a call status before logging.'),
                'sticky': False,
                'type': 'warning',
            }
        }

    def schedule_walkin(self):
        """Open the wizard to schedule a walk-in activity"""
        self.ensure_one()
        return {
            'name': _('Schedule Walk-in'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.lead.walkin.wizard',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            },
        }

class CrmLeadChangeRevenueWizard(models.TransientModel):
    _name = 'crm.lead.change.revenue.wizard'
    _description = 'Change Expected Revenue Wizard'

    new_expected_revenue = fields.Monetary(string="New Expected Revenue", required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    next_collection_date = fields.Date(string="Next Collection Date", required=True)

    def action_change_revenue(self):
        lead = self.env['crm.lead'].browse(self.env.context.get('active_id'))
        if not lead:
            raise ValidationError(_('No active lead found.'))
        lead.expected_revenue = self.new_expected_revenue
        lead.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=self.next_collection_date,
            summary=_('Collect Pending Fee'),
            note=_('Please collect the pending fee from the customer.')
        )
        self.env['crm.lead.collection'].create({
            'lead_id': lead.id,
            'collection_date': self.next_collection_date,
            'amount': self.new_expected_revenue,
        })

class CrmLeadCallHistory(models.Model):
    _name = 'crm.lead.call.history'
    _description = 'CRM Lead Call History'
    _order = 'create_date desc'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    call_status = fields.Selection([
        ('not_called', 'Not Called'),
        ('not_connected', 'Call not connected'), # New status
        ('call_1', '1st Call'),
        ('followup_1', 'Followup 1'),
        ('followup_2', 'Followup 2'),
        ('followup_3', 'Followup 3'),
        ('followup_4', 'Followup 4'),
        ('followup_5', 'Followup 5'),
        ('followup_6', 'Followup 6'),
        ('followup_7', 'Followup 7'),
        ('followup_8', 'Followup 8'),
        ('followup_9', 'Followup 9'),
        ('followup_10', 'Followup 10'),
    ], string="Call Status", required=True)
    remarks = fields.Text(string="Remarks")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    create_date = fields.Datetime(string='System Date', readonly=True)
    call_date = fields.Datetime(string='Call Date', default=lambda self: fields.Datetime.now(), required=True)
    
    @api.model
    def create(self, vals):
        # Ensure call_date is set to current time in create
        if not vals.get('call_date'):
            vals['call_date'] = fields.Datetime.now()
        return super(CrmLeadCallHistory, self).create(vals)

class CrmTeam(models.Model):
    _inherit = "crm.team"
    queue_line_ids = fields.One2many('crm.lead.queueing.line', 'team_id', store=True)

    def create(self, vals):
        res = super().create(vals)
        self.set_queue_line_ids(res)
        return res
    
    def write(self, vals):
        res = super().write(vals)
        self.set_queue_line_ids(self)
        return res
    
    def set_queue_line_ids(self, recs):
        for record in recs:
            queue_line_users = record.queue_line_ids.mapped('salesperson_id.id')
            for member in record.member_ids:
                # Create queue line for the new member
                if member.id not in queue_line_users:
                    self.env['crm.lead.queueing.line'].create({
                        'salesperson_id': member.id,
                        'current_lead': False,
                        'team_id': record.id
                    })
            # Remove queue lines for non existing members
            record.queue_line_ids.filtered(lambda line: line.salesperson_id.id not in record.member_ids.ids).unlink()

class CrmLeadQueueingLine(models.Model):
    _name = "crm.lead.queueing.line"
    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    current_lead = fields.Many2one('crm.lead', domain=[('type','=','lead')])
    team_id = fields.Many2one('crm.team', check_company=True)

class CrmLeadCollection(models.Model):
    _name = 'crm.lead.collection'
    _description = 'CRM Lead Collection'

    lead_id = fields.Many2one('crm.lead', string="Lead", required=True)
    collection_date = fields.Date(string="Collection Date", required=True)
    amount = fields.Monetary(string="Amount", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    collected_amount = fields.Monetary(string="Collected Amount", default=0.0)
    balance = fields.Monetary(string="Balance", compute="_compute_balance", store=True)
    state = fields.Selection([('pending', 'Pending'), ('collected', 'Collected')], string="State", default='pending')

    @api.depends('amount', 'collected_amount')
    def _compute_balance(self):
        for record in self:
            record.balance = record.amount - record.collected_amount
            if record.balance <= 0:
                record.state = 'collected'
            else:
                record.state = 'pending'

    def action_enter_collected_amount(self):
        view_id = self.env.ref('tijus_crm_custom.view_enter_collected_amount_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enter Collected Amount',
            'res_model': 'crm.lead.collection.enter.amount',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_collection_id': self.id},
        }

class CrmLeadCollectionEnterAmount(models.TransientModel):
    _name = 'crm.lead.collection.enter.amount'
    _description = 'Enter Collected Amount for Lead Collection'

    collection_id = fields.Many2one('crm.lead.collection', string="Collection", required=True)
    collected_amount = fields.Monetary(string="Collected Amount", required=True)
    currency_id = fields.Many2one('res.currency', related='collection_id.currency_id', readonly=True)

    def action_confirm(self):
        if not self.collection_id:
            raise ValidationError(_('No collection specified.'))
        
        # Update the collected amount
        new_collected_amount = self.collection_id.collected_amount + self.collected_amount
        self.collection_id.write({
            'collected_amount': new_collected_amount
        })
        
        # Create activity for the lead
        if self.collection_id.lead_id:
            lead = self.collection_id.lead_id
            lead.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Payment Collection'),
                note=_('Payment of %s collected. Balance: %s') % (
                    format(self.collected_amount, '.2f'),
                    format(self.collection_id.balance, '.2f')
                ),
                user_id=lead.user_id.id if lead.user_id else self.env.user.id
            )
        
        # Return success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Payment collected successfully'),
                'sticky': False,
                'type': 'success',
            }
        }

class CrmLeadWalkinWizard(models.TransientModel):
    _name = 'crm.lead.walkin.wizard'
    _description = 'Schedule Walk-in Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    walkin_date = fields.Date(string="Walk-in Date", required=True, default=fields.Date.today)
    notes = fields.Text(string="Notes", help="Additional notes about the walk-in")

    def action_schedule_walkin(self):
        self.ensure_one()
        if self.lead_id:
            try:
                # Try to find the walk-in activity type
                activity_type = self.env.ref('cindrebay_crm_custom.mail_activity_type_walkin', raise_if_not_found=False)
                if not activity_type:
                    # Fallback to a standard activity type if custom one not found
                    activity_type = self.env['mail.activity.type'].search([('name', '=', 'Meeting')], limit=1)
                
                if not activity_type:
                    # Further fallback to any activity type if no Meeting type
                    activity_type = self.env['mail.activity.type'].search([], limit=1)
                    
                if activity_type:
                    note = _("Customer will visit the center on %s. %s") % (
                        self.walkin_date.strftime('%d/%m/%Y'),
                        self.notes or ''
                    )
                    
                    self.lead_id.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary=_("Walk-in Visit"),
                        note=note.strip(),
                        date_deadline=self.walkin_date
                    )
                    
                # Show success notification
                return {
                    'type': 'ir.actions.act_window_close',
                }
                
            except Exception as e:
                # Show error notification
                return {
                    'type': 'ir.actions.act_window_close',
                }
        
        return {'type': 'ir.actions.act_window_close'}