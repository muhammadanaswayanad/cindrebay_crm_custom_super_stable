from odoo import models, fields, api, _
import random
from datetime import datetime

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    date_closed_editable = fields.Boolean('Allow Editing Date Closed', default=False)
    date_closed = fields.Datetime('Closed Date', readonly=True, copy=False, tracking=True)

    def set_date_closed_editable(self):
        """Method to toggle date_closed editability"""
        for record in self:
            record.date_closed_editable = not record.date_closed_editable
        return True

    def write(self, vals):
        # Override write to handle date_closed field editability
        if 'date_closed' in vals and not self.date_closed_editable:
            vals.pop('date_closed')
        result = super(CrmLead, self).write(vals)

        # If preferred_branch was updated, try to reassign the team
        if 'preferred_branch' in vals:
            for lead in self:
                # Only reassign if no team or if lead was updated intentionally 
                if not lead.team_id or 'team_id' not in vals:
                    lead._assign_team_from_branch()
                    
        return result

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        # Override to dynamically set readonly status
        res = super(CrmLead, self).fields_get(allfields, attributes)
        if 'date_closed' in res:
            res['date_closed']['readonly'] = False
        return res
    
    def _find_duplicate_leads(self):
        """
        Find potential duplicate leads based on phone number or email.
        Returns the first found duplicate lead or False if none found.
        """
        self.ensure_one()
        duplicates = False
        
        if self.phone:  # Try to find duplicate by phone
            duplicates = self.env['crm.lead'].search([
                ('id', '!=', self.id),  # Exclude current lead
                ('phone', '=', self.phone),  # Match exact phone
                ('user_id', '!=', False),  # Has a salesperson assigned
                ('create_date', '<', self.create_date),  # Only older leads
            ], order='create_date DESC', limit=1)
            
        if not duplicates and self.email_from:  # Try to find duplicate by email
            duplicates = self.env['crm.lead'].search([
                ('id', '!=', self.id),
                ('email_from', '=', self.email_from),
                ('user_id', '!=', False),
                ('create_date', '<', self.create_date),
            ], order='create_date DESC', limit=1)
            
        return duplicates[0] if duplicates else False

    @api.model
    def _get_team_by_preferred_branch(self, branch):
        """
        Find a sales team that handles the specified branch.
        
        Args:
            branch: The preferred branch value from the lead
            
        Returns:
            crm.team record if found, False otherwise
        """
        if not branch:
            return False
            
        # Normalize branch name (lowercase, strip spaces, remove trailing underscore)
        normalized_branch = branch.strip().lower().rstrip('_')
        
        # Find teams that include this branch in their preferred_branches
        teams = self.env['crm.team'].search([
            ('preferred_branches', '!=', False)
        ])
        
        for team in teams:
            team_branches = team._get_normalized_branches()
            if normalized_branch in team_branches:
                return team
                
        return False
    
    def _assign_team_from_branch(self):
        """
        Assign the lead to a team based on the preferred_branch field.
        Returns True if successfully assigned, False if no team found.
        """
        self.ensure_one()
        # First check for duplicates
        duplicate_lead = self._find_duplicate_leads()
        if duplicate_lead and duplicate_lead.user_id:
            # If duplicate found, assign to the same salesperson
            self.user_id = duplicate_lead.user_id.id
            self.team_id = duplicate_lead.team_id.id if duplicate_lead.team_id else False
            return True
            
        # If no duplicates, proceed with branch-based assignment
        team = self._get_team_by_preferred_branch(self.preferred_branch)
        if team:
            self.team_id = team.id
            return True
        return False
    
    @api.model_create_multi
    def create(self, vals_list):
        leads = super(CrmLead, self).create(vals_list)
        
        for lead in leads:
            # Try to assign based on preferred branch first
            if not lead._assign_team_from_branch():
                # Fall back to the existing random assignment logic if no branch match
                # ... existing random assignment code here ...
                pass
                
        return leads
