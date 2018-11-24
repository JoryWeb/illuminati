# ©  2015 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'HR Holidays Advanced',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'author': "Poiesis Consulting, ",
    'summary': "Manage Holidays Advanced",
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
        'hr',
        'hr_holidays',
        'poi_hr_public_holidays',
    ],
    'data': [
        'data/data.xml',
    ],
    'installable': True,
}
