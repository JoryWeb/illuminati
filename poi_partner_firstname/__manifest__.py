
{
    'name': 'Partner first name and last name',
    'summary': "Separa el primer nombre y segundo nombre para contactos que no sean compañias",
    'description': """
Partner First Name Poiesis
=============================
Añadido de nuevos campos al dato maestro de los contactos individuales para separar los nombres en:
    - Primer Nombre
    - Segundo Nombre
    - Apellido Paterno
    - Apellido Materno.
    """,
    'version': '11.0.1.0.0',
    'author': "Poiesis Consulting",
    'category': 'Extra Tools',
    'depends': ['base_setup'],
    'post_init_hook': 'post_init_hook',
    'data': [
        'views/res_partner.xml',
        'views/res_user.xml',
    ],
    'installable': True,
    'images': []
}
