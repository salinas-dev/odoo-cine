from odoo import models, fields, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    funcion_id = fields.Many2one('cine.funcion', string='Función')

    def action_open_funciones(self):
        domain = [('state', '=', 'activo')]
        if self.funcion_id and self.funcion_id.sala_id:
            domain.append(('sala_id', '=', self.funcion_id.sala_id.id))
        
        return {
            'name': _('Funciones de Cine'),
            'type': 'ir.actions.act_window',
            'res_model': 'cine.funcion',
            'view_mode': 'tree,form',
            'target': 'new',
            'domain': domain,
        }