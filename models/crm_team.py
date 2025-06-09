from odoo import models, fields, api, _

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    preferred_branches = fields.Char(
        string="Preferred Branches",
        help="Comma-separated list of branches this team is responsible for (e.g., 'kochi, calicut'). "
             "Used for automatic lead assignment based on the lead's preferred branch."
    )
    
    def _get_normalized_branches(self):
        """Returns a list of normalized branch names for this team."""
        if not self.preferred_branches:
            return []
        return [
            branch.strip().lower().rstrip('_') 
            for branch in self.preferred_branches.split(',')
            if branch.strip()
        ]
