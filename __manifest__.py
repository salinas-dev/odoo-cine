{
    'name': 'Gestión de Cine',
    'version': '1.0',
    'category': 'Entertainment',
    'summary': 'Módulo para gestionar un cine, incluyendo películas, salas y funciones',
    'description': """
        Este módulo permite gestionar un cine, proporcionando funcionalidades para la administración de películas, 
        salas y funciones. Incluye vistas personalizadas y seguridad.
    """,
    'author': 'Nora Salinas',
    'website': '',
    'depends': ['base', 'sale', 'account', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/cine_sala_views.xml',
        'views/cine_views.xml',
        'views/cine_funcion_views.xml',
        'views/cine_menu.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'report/account_move_report.xml'
    ],
    'installable': True,
    'application': True,
    'icon': "static/description/odoo_icon.png",  # Ruta al archivo de icono del módulo
}
