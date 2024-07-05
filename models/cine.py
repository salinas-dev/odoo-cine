from odoo import models, fields, api, _
from odoo import models, fields, api
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from io import BytesIO  # Asegúrate de tener esta línea importada correctamente


class Cine(models.Model):
    _name = 'cine.movie'
    _description = 'Información de películas'

    name = fields.Char(string='Título', required=True)
    description = fields.Html(string='Descripción')
    release_date = fields.Date(string='Fecha de lanzamiento')
    image = fields.Binary(string='Imagen')
    image_filename = fields.Char(string='Nombre del archivo de imagen')
    clasificacion = fields.Selection([
        ('G', 'G'),
        ('PG', 'PG'),
        ('PG-13', 'PG-13'),
        ('R', 'R'),
        ('NC-17', 'NC-17'),
    ], string='Clasificación', required=True)
    genero = fields.Selection([
        ('accion', 'Acción'),
        ('aventura', 'Aventura'),
        ('comedia', 'Comedia'),
        ('drama', 'Drama'),
        ('terror', 'Terror'),
        ('romance', 'Romance'),
        ('ciencia_ficcion', 'Ciencia ficción'),
        ('animacion', 'Animación'),
        ('fantasia', 'Fantasía'),
        ('suspenso', 'Suspenso'),
        ('documental', 'Documental'),
        ('musical', 'Musical'),
        ('misterio', 'Misterio'),
    ], string='Género', required=True)
    funciones_ids = fields.One2many('cine.funcion', 'movie_id', string='Funciones')

class Sala(models.Model):
    _name = 'cine.sala'
    _description = 'Información de las salas de cine'

    name = fields.Char(string='Nombre', required=True)
    capacity = fields.Integer(string='Capacidad')
    precio_entrada_adulto = fields.Float(string='Precio de Entrada Adulto', default=0.0)
    precio_entrada_nino = fields.Float(string='Precio de Entrada Niño', default=0.0)
    existencias_boletos = fields.Integer(string='Existencias de Boletos', compute='_compute_existencias_boletos', store=True)
    funciones_ids = fields.One2many('cine.funcion', 'sala_id', string='Funciones')
    
    @api.depends('funciones_ids')
    def _compute_existencias_boletos(self):
        for sala in self:
            existencias = sala.capacity - sum(funcion.boletos_a_vender for funcion in sala.funciones_ids if funcion.state == 'activo')
            sala.existencias_boletos = existencias if existencias >= 0 else 0

    def actualizar_existencias_boletos(self, cantidad):
        self.existencias_boletos -= cantidad

class Funcion(models.Model):
    _name = 'cine.funcion'
    _description = 'Información de las funciones de películas'

    name = fields.Char(string='Nombre', required=True)
    movie_id = fields.Many2one('cine.movie', string='Película', required=True, ondelete='restrict')
    sala_id = fields.Many2one('cine.sala', string='Sala', required=True)
    start_time = fields.Datetime(string='Hora de inicio', required=True)
    state = fields.Selection([
        ('activo', 'Activo'),
        ('pendiente', 'Pendiente'),
        ('ocupado', 'Ocupado'),
    ], string='Estado', default='pendiente', required=True)
    image = fields.Binary(string='Imagen', compute='_compute_movie_image')
    image_filename = fields.Char(string='Nombre del archivo de imagen', compute='_compute_movie_image')
    capacidad = fields.Integer(string='Capacidad', related='sala_id.capacity', store=True)
    boletos_a_vender = fields.Integer(string='Boletos a vender')
    tipo_boleto = fields.Selection([
        ('adulto', 'Adulto'),
        ('nino', 'Niño'),
    ], string='Tipo de Boleto', required=True)
    invoice_ids = fields.Many2many('account.move', string='Historial de Facturas', readonly=True)
    current_invoice_id = fields.Many2one('account.move', string='Factura Relacional')
    boletos_vendidos = fields.Integer(string="Boletos Vendidos", compute="_compute_boletos_vendidos")

    @api.depends('sale_order_ids')
    def _compute_boletos_vendidos(self):
        for funcion in self:
            funcion.boletos_vendidos = sum(funcion.sale_order_ids.mapped('boletos_vendidos'))

    def view_invoice_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historial de Facturas',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_partner_id': self.env.user.partner_id.id},
            'target': 'new',
        }

    @api.onchange('sala_id')
    def _onchange_sala_id(self):
        if self.sala_id:
            self.capacidad = self.sala_id.capacity

    @api.constrains('capacidad')
    def _check_capacidad(self):
        for funcion in self:
            if funcion.capacidad > funcion.sala_id.capacity:
                raise ValidationError('La capacidad de la función no puede exceder la capacidad de la sala.')

    @api.depends('movie_id.image', 'movie_id.image_filename')
    def _compute_movie_image(self):
        for funcion in self:
            funcion.image = funcion.movie_id.image
            funcion.image_filename = funcion.movie_id.image_filename

    def action_activo(self):
        self.state = 'activo'

    def action_pendiente(self):
        self.state = 'pendiente'

    def action_ocupado(self):
        self.state = 'ocupado'
        
    @api.depends('invoice_ids.state')
    def _compute_boletos_vendidos(self):
        for funcion in self:
            funcion.boletos_vendidos = sum(funcion.invoice_ids.mapped('invoice_line_ids.quantity'))

    def create_sale_order(self):
        self.ensure_one()
        if self.state != 'activo':
            raise ValidationError('Solo se puede generar una venta si la función está en estado Activo.')

        if self.movie_id.clasificacion in ['R', 'NC-17'] and self.tipo_boleto == 'nino':
            raise ValidationError('No se pueden vender boletos de niño para películas con clasificación para adultos.')

        tipo_boleto_name = dict(self._fields['tipo_boleto'].selection).get(self.tipo_boleto)

        if self.tipo_boleto == 'adulto':
            list_price = self.sala_id.precio_entrada_adulto
        elif self.tipo_boleto == 'nino':
            list_price = self.sala_id.precio_entrada_nino
        else:
            list_price = 0.0

        product = self.env['product.product'].create({
            'name': _('%s - %s') % (self.movie_id.name, tipo_boleto_name),
            'type': 'service',
            'list_price': list_price,
        })

        taxes = product.taxes_id.filtered(lambda r: r.company_id.id == self.env.company.id)
        taxes_ids = taxes.ids

        # Crear la orden de venta
        sale_order_vals = {
            'partner_id': 1,  # Ajusta el partner_id según tu caso
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'product_uom_qty': self.boletos_a_vender,
                'price_unit': list_price,
                'tax_id': [(6, 0, taxes_ids)],
            })],
            'funcion_id': self.id
        }

        sale_order = self.env['sale.order'].create(sale_order_vals)

        # Crear la factura desde la orden de venta
        sale_order.action_confirm()
        invoice = sale_order._create_invoices()

        # Actualizar existencias de boletos en la sala
        self.sala_id.actualizar_existencias_boletos(self.boletos_a_vender)

        # Devolver la acción para mostrar la orden de venta
        return {
            'name': 'Orden de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
        }

    def create_invoice(self):
        if self.state != 'activo':
            raise ValidationError('Solo se puede generar una factura si la función está en estado Activo.')

        if self.movie_id.clasificacion in ['R', 'NC-17'] and self.tipo_boleto == 'nino':
            raise ValidationError('No se pueden vender boletos de niño para películas con clasificación para adultos.')

        tipo_boleto_name = dict(self._fields['tipo_boleto'].selection).get(self.tipo_boleto)

        if self.tipo_boleto == 'adulto':
            list_price = self.sala_id.precio_entrada_adulto
        elif self.tipo_boleto == 'nino':
            list_price = self.sala_id.precio_entrada_nino
        else:
            list_price = 0.0

        product = self.env['product.product'].create({
            'name': _('%s - %s') % (self.movie_id.name, tipo_boleto_name),
            'type': 'service',
            'list_price': list_price,
        })

        # Crear la factura
        invoice_vals = {
            'partner_id': 1,  # Ajusta el partner_id según tu caso
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': self.boletos_a_vender,  # Asegurarse de que se utiliza la cantidad correcta
                'price_unit': list_price,
            })],
            #'funcion_id': self.id
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Confirmar la factura
        invoice.action_post()

        # Actualizar existencias de boletos en la sala
        self.sala_id.actualizar_existencias_boletos(self.boletos_a_vender)

        # Agregar la factura al historial de facturas de la función
        self.write({
            'invoice_ids': [(4, invoice.id)]  # Añadir la factura al Many2many campo invoice_ids
        })


        return {
            'name': 'Factura',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }

    def create_invoice_from_sale_order(self, sale_order):
        invoice_lines = []
        for line in sale_order.order_line:
            invoice_lines.append((0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': sale_order.partner_id.id,
            'invoice_line_ids': invoice_lines,
            'funcion_id': self.id,  # Asignar la función actual a la factura
        })

        # Confirmar la factura
        invoice.action_post()

        # Agregar la factura al historial de facturas de la función
        self.write({
            'invoice_ids': [(4, invoice.id)]  # Añadir la factura al Many2many campo invoice_ids
        })

        return invoice
    
    

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
    

from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    funcion_id = fields.Many2one('cine.funcion', string='Función')

    def generate_ticket(self):
        return self.env.ref('cine.funcion_cine_account_move').report_action(self)


