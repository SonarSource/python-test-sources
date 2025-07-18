# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from copy import deepcopy

from marshmallow import fields, pre_load, validate
from wtforms.validators import DataRequired, Optional

from indico.core.marshmallow import mm
from indico.modules.events.registration.models.registrations import RegistrationData


class BillableFieldDataSchema(mm.Schema):
    price = fields.Float(load_default=0)

    @pre_load
    def _remove_is_billable(self, data, **kwargs):
        # TODO remove this once the angular frontend is gone
        data = data.copy()
        data.pop('is_billable', None)
        return data


class LimitedPlacesBillableFieldDataSchema(BillableFieldDataSchema):
    places_limit = fields.Integer(load_default=0, validate=validate.Range(0))


class RegistrationFormFieldBase:
    """Base class for a registration form field definition."""

    #: unique name of the field type
    name = None
    #: wtform field class
    wtf_field_class = None
    #: additional options for the WTForm class
    wtf_field_kwargs = {}
    #: the validator to use when the field is required
    required_validator = DataRequired
    #: the validator to use when the field is not required
    not_required_validator = Optional
    #: the data fields that need to be versioned
    versioned_data_fields = frozenset({'price'})
    #: the marshmallow base schema for configuring the field
    setup_schema_base_cls = mm.Schema
    #: a dict with extra marshmallow fields to include in the setup schema
    setup_schema_fields = {}

    def __init__(self, form_item):
        self.form_item = form_item

    @property
    def default_value(self):
        return ''

    @property
    def validators(self):
        """Return a list of validators for this field."""
        return None

    @property
    def filter_choices(self):
        return None

    def calculate_price(self, reg_data, versioned_data):
        """Calculate the price of the field.

        :param reg_data: The user data for the field
        :param versioned_data: The versioned field data to use
        """
        return 0

    def create_sql_filter(self, data_list):
        """
        Create a SQL criterion to check whether the field's value is
        in `data_list`.  The function is expected to return an
        operation on ``Registrationdata.data``.
        """
        return RegistrationData.data.op('#>>')('{}').in_(data_list)

    def create_wtf_field(self):
        validators = list(self.validators) if self.validators is not None else []
        if self.form_item.is_required:
            validators.append(self.required_validator())
        elif self.not_required_validator:
            validators.append(self.not_required_validator())
        return self.wtf_field_class(self.form_item.title, validators, **self.wtf_field_kwargs)

    def create_setup_schema(self):
        name = f'{type(self).__name__}SetupDataSchema'
        schema = self.setup_schema_base_cls.from_dict(self.setup_schema_fields, name=name)
        return schema()

    def has_data_changed(self, value, old_data):
        return value != old_data.data

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False):
        """Convert form data into database-usable dictionary.

        :param registration: The registration the data is used for
        :param value: The value from the WTForm
        :param old_data: The existing `RegistrationData` in case a
                         registration is being modified.
        :param billable_items_locked: Whether modifications to any
                                      billable item should be ignored.
        """

        if old_data is not None and not self.has_data_changed(value, old_data):
            return {}
        else:
            return {
                'field_data': self.form_item.current_data,
                'data': value
            }

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        """Process the settings of the field.

        :param data: The field data from the client
        :param old_data: The old unversioned field data (if available)
        :param old_versioned_data: The old versioned field data (if
                                   available)
        :return: A ``(unversioned_data, versioned_data)`` tuple
        """
        data = dict(data)
        if 'places_limit' in data:
            data['places_limit'] = int(data['places_limit']) if data['places_limit'] else 0
        versioned_data = {k: v for k, v in data.items() if k in cls.versioned_data_fields}
        unversioned_data = {k: v for k, v in data.items() if k not in cls.versioned_data_fields}
        return unversioned_data, versioned_data

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        return versioned_data | unversioned_data

    @property
    def view_data(self):
        return self.unprocess_field_data(self.form_item.versioned_data, self.form_item.data)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        """Return the data contained in the field.

        If for_humans is True, return a human-readable string representation.
        If for_search is True, return a string suitable for comparison in search.
        """
        return registration_data.data

    def iter_placeholder_info(self):
        yield None, f'Value of "{self.form_item.title}" ({self.form_item.parent.title})'

    def render_placeholder(self, data, key=None):
        return self.get_friendly_data(data)

    def get_places_used(self):
        """Return the number of used places for the field."""
        return 0


class RegistrationFormBillableField(RegistrationFormFieldBase):
    setup_schema_base_cls = BillableFieldDataSchema

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        data = deepcopy(data)
        data['price'] = float(data['price']) if data.get('price') else 0
        return super().process_field_data(data, old_data, old_versioned_data)

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0)

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        data = versioned_data | unversioned_data
        data['is_billable'] = data['price'] > 0
        return data

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        if new_data_version is None:
            new_data_version = self.form_item.current_data
        if billable_items_locked and old_data.price != self.calculate_price(value, new_data_version.versioned_data):
            return {}
        return super().process_form_data(registration, value, old_data)


class RegistrationFormBillableItemsField(RegistrationFormBillableField):
    setup_schema_base_cls = mm.Schema

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super().process_field_data(
            data, old_data, old_versioned_data)
        # we don't have field-level billing data here
        del versioned_data['price']
        return unversioned_data, versioned_data

    def calculate_price(self, reg_data, versioned_data):
        # billable items need custom logic
        raise NotImplementedError
