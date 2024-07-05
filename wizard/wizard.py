from odoo import models, fields

class SimpleWizard(models.TransientModel):
    _name = 'simple.wizard'
    _description = 'Simple Wizard'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')

    def action_confirm(self):
        return {
            'type': 'ir.actions.act_window_close',
            'info': {
                'title': 'Éxito',
                'message': 'Wizard ejecutado correctamente.',
                'type': 'success'
            }
        }
