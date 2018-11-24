# © 2013 Nicolas Bessi (Camptocamp SA)
# © 2014 Agile Business Group (<http://www.agilebg.com>)
# © 2015 Grupo ESOC (<http://www.grupoesoc.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, fields, models
from .. import exceptions


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Adds last name and first name; name becomes a stored function field."""
    _inherit = 'res.partner'

    lastname2 = fields.Char("A. Materno")
    lastname = fields.Char("A. Paterno")
    firstname2 = fields.Char("Segundo Nombre")
    firstname = fields.Char("Primer Nombre")
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True)

    @api.model
    def create(self, vals):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))

        if name is not None:
            # Calculate the splitted fields
            inverted = self._get_inverse_name(
                self._get_whitespace_cleaned_name(name),
                vals.get("is_company",
                         self.default_get(["is_company"])["is_company"]))

            for key, value in inverted.items():
                if not vals.get(key) or context.get("copy"):
                    vals[key] = value

            # Remove the combined fields
            if "name" in vals:
                del vals["name"]
            if "default_name" in context:
                del context["default_name"]

        return super(ResPartner, self.with_context(context)).create(vals)

    @api.multi
    def copy(self, default=None):
        """Ensure partners are copied right.

        Odoo adds ``(copy)`` to the end of :attr:`~.name`, but that would get
        ignored in :meth:`~.create` because it also copies explicitly firstname
        and lastname fields.
        """
        return super(ResPartner, self.with_context(copy=True)).copy(default)

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(ResPartner, self).default_get(fields_list)

        inverted = self._get_inverse_name(
            self._get_whitespace_cleaned_name(result.get("name", "")),
            result.get("is_company", False))

        for field in inverted.keys():
            if field in fields_list:
                result[field] = inverted.get(field)

        return result

    @api.model
    def _get_computed_name(self, lastname, lastname2, firstname, firstname2):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        return " ".join((p for p in (lastname, lastname2, firstname, firstname2) if p))

    @api.multi
    @api.depends("lastname2", "lastname", "firstname", "firstname2")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        for s in self:
            s.name = s._get_computed_name(s.lastname, s.lastname2, s.firstname, s.firstname2)

    @api.multi
    def _inverse_name_after_cleaning_whitespace(self):
        """Clean whitespace in :attr:`~.name` and split it.

        The splitting logic is stored separately in :meth:`~._inverse_name`, so
        submodules can extend that method and get whitespace cleaning for free.
        """
        for s in self:
            # Remove unneeded whitespace

            clean = self._get_whitespace_cleaned_name(s.name)

            # Clean name avoiding infinite recursion
            if s.name != clean:
                s.name = clean

            # Save name in the real fields
            else:
                s._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name):
        """Remove redundant whitespace from :param:`name`.

        Removes leading, trailing and duplicated whitespace.
        """
        return " ".join(name.split()) if name else name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        """Compute the inverted name.

        - If the partner is a company, save it in the lastname.
        - Otherwise, make a guess.

        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes

        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """
        # Company name goes to the lastname
        if is_company or not name:
            parts = [name or False, False, False, False]
            return {"lastname": False, "lastname2": False, "firstname": parts[0], "firstname2": False}
        # Guess name splitting
        else:
            parts = name.strip().split(" ", 3)
            if len(parts) == 1:
                return {"lastname": False, "lastname2": False, "firstname": parts[0], "firstname2": False}
            elif len(parts) == 2:
                return {"lastname": parts[0], "lastname2": False, "firstname": parts[1], "firstname2": False}
            elif len(parts) == 3:
                return {"lastname": parts[0], "lastname2": parts[1], "firstname": parts[2], "firstname2": False}
            elif len(parts) == 4:
                return {"lastname": parts[0], "lastname2": parts[1], "firstname": parts[2], "firstname2": parts[3]}

    @api.multi
    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        for s in self:
            parts = s._get_inverse_name(s.name, s.is_company)
            s.firstname =  parts["firstname"]
            s.lastname = parts["lastname"]
            s.lastname2 = parts["lastname2"]
            s.firstname2 = parts["firstname2"]

    @api.multi
    @api.constrains("firstname")
    def _check_name(self):
        """Ensure at least one name is set."""
        for s in self:
            if all((self.type == 'contact' or self.is_company,
                    not self.firstname)):
                raise exceptions.EmptyNamesError(self)


    @api.onchange("lastname2", "lastname", "firstname", "firstname2")
    def _onchange_subnames(self):
        """Avoid recursion when the user changes one of these fields.

        This forces to skip the :attr:`~.name` inversion when the user is
        setting it in a not-inverted way.
        """
        # Modify self's context without creating a new Environment.
        # See https://github.com/odoo/odoo/issues/7472#issuecomment-119503916.
        self.env.context = self.with_context(skip_onchange=True).env.context


    @api.onchange("name")
    def _onchange_name(self):
        """Ensure :attr:`~.name` is inverted in the UI."""
        if self.env.context.get("skip_onchange"):
            # Do not skip next onchange
            self.env.context = (
                self.with_context(skip_onchange=False).env.context)
        else:
            self._inverse_name_after_cleaning_whitespace()

    @api.model
    def _install_partner_firstname(self):
        """Save names correctly in the database.

        Before installing the module, field ``name`` contains all full names.
        When installing it, this method parses those names and saves them
        correctly into the database. This can be called later too if needed.
        """
        # Find records with empty firstname and lastname
        records = self.search([])

        # Force calculations there
        records._inverse_name()
        _logger.info("%d partners updated installing module.", len(records))

    # Disabling SQL constraint givint a more explicit error using a Python
    # contstraint
    _sql_constraints = [(
        'check_name',
        "CHECK( 1=1 )",
        'Contacts require a name.'
    )]
