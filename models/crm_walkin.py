from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class CrmLeadWalkin(models.Model):
    _name = 'crm.lead.walkin'
    _description = 'CRM Lead Walk-in Appointments'
    _order = 'scheduled_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", readonly=True, copy=False, default=lambda self: _('New'))
    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one(related='lead_id.partner_id', string='Partner', store=True, readonly=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", required=True, tracking=True)
    actual_date = fields.Datetime(string="Actual Visit Date", tracking=True)
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ], string='Status', default='scheduled', tracking=True)
    notes = fields.Text(string="Notes", tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    parent_walkin_id = fields.Many2one('crm.lead.walkin', string='Previous Appointment')
    child_walkin_ids = fields.One2many('crm.lead.walkin', 'parent_walkin_id', string='Rescheduled Appointments')
    reschedule_reason = fields.Selection([
        ('client_request', 'Client Request'),
        ('staff_unavailable', 'Staff Unavailable'),
        ('emergency', 'Emergency'),
        ('other', 'Other')
    ], string='Reschedule Reason', tracking=True)
    reschedule_note = fields.Text(string='Reschedule Notes', tracking=True)
    color = fields.Integer(string='Color Index')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('crm.lead.walkin') or _('New')
        return super().create(vals_list)
    
    def action_completed(self):
        self.ensure_one()
        self.write({
            'state': 'completed',
            'actual_date': fields.Datetime.now(),
        })
        # Create activity for follow-up
        self.lead_id.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_("Follow-up after walk-in"),
            note=_("Customer visited on %s. Follow-up with next steps.") % fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
            date_deadline=fields.Date.today() + timedelta(days=1),
        )
        return True
    
    def action_no_show(self):
        self.ensure_one()
        self.write({'state': 'no_show'})
        return True
    
    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        return True
    
    def action_reschedule(self):
        self.ensure_one()
        return {
            'name': _('Reschedule Walk-in'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.lead.walkin.reschedule.wizard',
            'target': 'new',
            'context': {
                'default_walkin_id': self.id,
                'default_lead_id': self.lead_id.id,
            },
        }
    
    def action_view_lead(self):
        """Navigate to the related lead form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
            'target': 'current',
        }

class CrmLeadWalkinRescheduleWizard(models.TransientModel):
    _name = 'crm.lead.walkin.reschedule.wizard'
    _description = 'Reschedule Walk-in Wizard'

    walkin_id = fields.Many2one('crm.lead.walkin', string='Walk-in', required=True)
    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    new_date = fields.Datetime(string="New Date", required=True)
    reschedule_reason = fields.Selection([
        ('client_request', 'Client Request'),
        ('staff_unavailable', 'Staff Unavailable'),
        ('emergency', 'Emergency'),
        ('other', 'Other')
    ], string='Reason', required=True)
    notes = fields.Text(string="Notes")

    def action_reschedule(self):
        self.ensure_one()
        if self.walkin_id:
            # Mark current walkin as rescheduled
            self.walkin_id.write({
                'state': 'rescheduled',
                'reschedule_reason': self.reschedule_reason,
                'reschedule_note': self.notes,
            })
            
            # Create new walkin appointment
            new_walkin = self.env['crm.lead.walkin'].create({
                'lead_id': self.lead_id.id,
                'scheduled_date': self.new_date,
                'notes': self.notes,
                'parent_walkin_id': self.walkin_id.id,
            })
            
            # Create activity for the rescheduled walkin
            self.lead_id.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Rescheduled Walk-in"),
                note=_("Walk-in rescheduled to %s. Reason: %s") % (
                    self.new_date.strftime('%Y-%m-%d %H:%M'),
                    dict(self._fields['reschedule_reason'].selection).get(self.reschedule_reason)
                ),
                date_deadline=fields.Date.context_today(self),
            )
            
            return {
                'type': 'ir.actions.act_window_close',
                'infos': {'success': True, 'message': _('Walk-in successfully rescheduled.')}
            }
        return {'type': 'ir.actions.act_window_close'}

class CrmLeadWalkinWizard(models.TransientModel):
    _name = 'crm.lead.walkin.wizard'
    _description = 'Schedule Walk-in Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    walkin_date = fields.Datetime(string="Walk-in Date", required=True, default=lambda self: fields.Datetime.now() + timedelta(days=1))
    notes = fields.Text(string="Notes", help="Additional notes about the walk-in")

    def action_schedule_walkin(self):
        self.ensure_one()
        if self.lead_id:
            try:
                # Create walkin record
                walkin = self.env['crm.lead.walkin'].create({
                    'lead_id': self.lead_id.id,
                    'scheduled_date': self.walkin_date,
                    'notes': self.notes,
                })
                
                # Create activity for the walkin
                activity_type = self.env.ref('cindrebay_crm_custom.mail_activity_type_walkin', raise_if_not_found=False)
                if not activity_type:
                    activity_type = self.env['mail.activity.type'].search([('name', '=', 'Meeting')], limit=1)
                if not activity_type:
                    activity_type = self.env['mail.activity.type'].search([], limit=1)
                
                if activity_type:
                    self.lead_id.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary=_("Walk-in Appointment"),
                        note=_("Walk-in scheduled for %s. Reference: %s. %s") % (
                            self.walkin_date.strftime('%Y-%m-%d %H:%M'),
                            walkin.name,
                            self.notes or ''
                        ),
                        date_deadline=self.walkin_date.date(),
                    )
                
                return {
                    'type': 'ir.actions.act_window_close'
                }
            except Exception as e:
                return {
                    'type': 'ir.actions.act_window_close'
                }
        return {'type': 'ir.actions.act_window_close'}

class CRMLead(models.Model):
    _inherit = 'crm.lead'
    
    walkin_ids = fields.One2many('crm.lead.walkin', 'lead_id', string='Walk-ins')
    walkin_count = fields.Integer(string='Walk-in Count', compute='_compute_walkin_count')
    next_walkin_id = fields.Many2one('crm.lead.walkin', string='Next Walk-in', compute='_compute_next_walkin')
    next_walkin_date = fields.Datetime(related='next_walkin_id.scheduled_date', string='Next Walk-in Date')
    walkin_state = fields.Selection(related='next_walkin_id.state', string='Walk-in Status')
    
    @api.depends('walkin_ids')
    def _compute_walkin_count(self):
        for record in self:
            record.walkin_count = len(record.walkin_ids)
    
    @api.depends('walkin_ids.scheduled_date', 'walkin_ids.state')
    def _compute_next_walkin(self):
        for record in self:
            next_walkin = self.env['crm.lead.walkin'].search([
                ('lead_id', '=', record.id),
                ('state', '=', 'scheduled'),
                ('scheduled_date', '>=', fields.Datetime.now())
            ], order='scheduled_date asc', limit=1)
            record.next_walkin_id = next_walkin.id if next_walkin else False
    
    def schedule_walkin(self):
        """Open the wizard to schedule a walk-in"""
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
    
    def action_view_walkins(self):
        """View all walk-ins for this lead"""
        self.ensure_one()
        return {
            'name': _('Walk-ins'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.walkin',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }
