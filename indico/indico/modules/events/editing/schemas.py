# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from markupsafe import escape
from marshmallow import ValidationError, fields, post_dump, validate, validates, validates_schema
from marshmallow_enum import EnumField
from sqlalchemy import func

from indico.core.marshmallow import mm
from indico.modules.categories.models.roles import CategoryRole
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.schemas import ContributionSchema
from indico.modules.events.editing.models.comments import EditingRevisionComment
from indico.modules.events.editing.models.editable import Editable, EditableState, EditableType
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.review_conditions import EditingReviewCondition
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, InitialRevisionState
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.events.util import get_all_user_roles
from indico.modules.users import User
from indico.util.caching import memoize_request
from indico.util.enum import IndicoEnum
from indico.util.i18n import _
from indico.util.marshmallow import PrincipalList, not_empty
from indico.util.string import natural_sort_key
from indico.web.flask.util import url_for
from indico.web.forms.colors import get_sui_colors


def _get_anonymous_user():
    return {
        'identifier': 'AnonymousUser',
        'avatar_url': url_for('assets.avatar'),
        'id': -1,
        'full_name': 'Someone',
        'anonymous': True,
    }


class RevisionStateSchema(mm.Schema):
    title = fields.String()
    name = fields.String()
    css_class = fields.String()


class EditableStateSchema(mm.Schema):
    title = fields.String()
    name = fields.String()
    css_class = fields.String()


class EditingUserSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'identifier', 'avatar_url', 'email')

    @post_dump
    def strip_emails(self, data, **kwargs):
        if not self.context.get('include_emails'):
            del data['email']
        return data


class EditingFileTypeSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingFileType
        fields = ('id', 'name', 'extensions', 'allow_multiple_files', 'required', 'publishable', 'is_used',
                  'filename_template', 'is_used_in_condition', 'url')

    is_used = fields.Function(lambda ft: EditingRevisionFile.query.with_parent(ft).has_rows())
    is_used_in_condition = fields.Function(lambda ft: EditingReviewCondition.query.with_parent(ft).has_rows())
    url = fields.Function(lambda ft: url_for('.api_edit_file_type',
                                             ft.event, type=ft.type.name,
                                             file_type_id=ft.id,
                                             _external=True))

    @post_dump(pass_many=True)
    def sort_list(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda ft: natural_sort_key(ft['name']))
        return data


class EditingTagSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingTag
        fields = (
            'id', 'code', 'title', 'color', 'system', 'verbose_title', 'is_used_in_revision', 'url'
        )

    is_used_in_revision = fields.Function(
        memoize_request(lambda tag: EditingRevision.query.with_parent(tag).has_rows())
    )
    url = fields.Function(lambda tag: url_for('.api_edit_tag', tag.event, tag_id=tag.id, _external=True))

    @post_dump(pass_many=True)
    def sort_list(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda e: natural_sort_key(e['verbose_title']))
        return data


class EditingRevisionFileSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingRevisionFile
        fields = ('uuid', 'filename', 'size', 'content_type', 'file_type', 'download_url', 'external_download_url')

    uuid = fields.String(attribute='file.uuid')
    filename = fields.String(attribute='file.filename')
    size = fields.Int(attribute='file.size')
    content_type = fields.String(attribute='file.content_type')
    download_url = fields.String()
    external_download_url = fields.String()


class EditingRevisionSignedFileSchema(EditingRevisionFileSchema):
    class Meta(EditingRevisionFileSchema.Meta):
        fields = ('uuid', 'filename', 'size', 'content_type', 'file_type', 'signed_download_url')

    signed_download_url = fields.String(attribute='file.signed_download_url')


class EditingRevisionCommentSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingRevisionComment
        fields = ('id', 'user', 'created_dt', 'modified_dt', 'internal', 'system', 'text', 'html', 'can_modify',
                  'modify_comment_url', 'revision_id')

    revision_id = fields.Int(attribute='revision.id')
    user = fields.Nested(EditingUserSchema)
    html = fields.Function(lambda comment: escape(comment.text))
    can_modify = fields.Function(lambda comment, ctx: comment.can_modify(ctx.get('user')))
    modify_comment_url = fields.Function(lambda comment: url_for('event_editing.api_edit_comment', comment))

    @post_dump(pass_original=True)
    def anonymize_user(self, data, orig, **kwargs):
        can_see_editor_names_fn = self.context.get('can_see_editor_names')
        if can_see_editor_names_fn and data['user'] and not can_see_editor_names_fn(self.context['user'], orig.user):
            data['user'] = _get_anonymous_user()
        return data


class EditingRevisionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingRevision
        fields = ('id', 'created_dt', 'reviewed_dt', 'submitter', 'editor', 'files', 'comment', 'comment_html',
                  'comments', 'initial_state', 'final_state', 'tags', 'create_comment_url', 'download_files_url',
                  'review_url', 'confirm_url', 'custom_actions', 'custom_action_url')

    comment_html = fields.Function(lambda rev: escape(rev.comment))
    submitter = fields.Nested(EditingUserSchema)
    editor = fields.Nested(EditingUserSchema)
    files = fields.List(fields.Nested(EditingRevisionFileSchema))
    tags = fields.List(fields.Nested(EditingTagSchema))
    comments = fields.Method('_get_comments')
    initial_state = fields.Nested(RevisionStateSchema)
    final_state = fields.Nested(RevisionStateSchema)
    create_comment_url = fields.Function(lambda revision: url_for('event_editing.api_create_comment', revision))
    download_files_url = fields.Function(lambda revision: url_for('event_editing.revision_files_export', revision))
    review_url = fields.Function(lambda revision: url_for('event_editing.api_review_editable', revision))
    confirm_url = fields.Method('_get_confirm_url')
    custom_action_url = fields.Function(lambda revision: url_for('event_editing.api_custom_action', revision))
    custom_actions = fields.Function(lambda revision, ctx: ctx.get('custom_actions', {}).get(revision, []))

    def _get_confirm_url(self, revision):
        if revision.initial_state == InitialRevisionState.needs_submitter_confirmation and not revision.final_state:
            return url_for('event_editing.api_confirm_changes', revision)

    def _get_comments(self, revision):
        comments = [comment for comment in revision.comments
                    if not comment.internal or revision.editable.can_use_internal_comments(self.context.get('user'))]
        return EditingRevisionCommentSchema(context=self.context).dump(comments, many=True)

    @post_dump()
    def sort_tags(self, data, **kwargs):
        data['tags'].sort(key=lambda tag: natural_sort_key(tag['verbose_title']))
        return data

    @post_dump(pass_original=True)
    def anonymize_users(self, data, orig, **kwargs):
        can_see_editor_names_fn = self.context.get('can_see_editor_names')
        if can_see_editor_names_fn:
            if data['editor'] and not can_see_editor_names_fn(self.context['user'], orig.editor):
                data['editor'] = _get_anonymous_user()
            if data['submitter'] and not can_see_editor_names_fn(self.context['user'], orig.submitter):
                data['submitter'] = _get_anonymous_user()
        return data


class EditingRevisionSignedSchema(EditingRevisionSchema):
    files = fields.List(fields.Nested(EditingRevisionSignedFileSchema))


class EditableSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Editable
        fields = ('id', 'type', 'editor', 'revisions', 'contribution', 'can_comment', 'review_conditions_valid',
                  'can_perform_editor_actions', 'can_perform_submitter_actions', 'can_create_internal_comments',
                  'can_unassign', 'can_assign_self', 'editing_enabled', 'state')

    contribution = fields.Nested(ContributionSchema)
    editor = fields.Nested(EditingUserSchema)
    revisions = fields.List(fields.Nested(EditingRevisionSchema))
    can_perform_editor_actions = fields.Function(
        lambda editable, ctx: editable.can_perform_editor_actions(ctx.get('user')))
    can_perform_submitter_actions = fields.Function(
        lambda editable, ctx: editable.can_perform_submitter_actions(ctx.get('user')))
    can_comment = fields.Function(lambda editable, ctx: editable.can_comment(ctx.get('user')))
    can_create_internal_comments = fields.Function(
        lambda editable, ctx: editable.can_use_internal_comments(ctx.get('user')))
    can_unassign = fields.Function(
        lambda editable, ctx: editable.can_unassign(ctx.get('user')))
    can_assign_self = fields.Function(
        lambda editable, ctx: editable.can_assign_self(ctx.get('user')))
    review_conditions_valid = fields.Boolean()
    editing_enabled = fields.Boolean()
    state = fields.Nested(EditableStateSchema)

    @post_dump(pass_original=True)
    def anonymize_editor(self, data, orig, **kwargs):
        can_see_editor_names_fn = self.context.get('can_see_editor_names')
        if can_see_editor_names_fn and data['editor'] and not can_see_editor_names_fn(self.context['user']):
            data['editor'] = _get_anonymous_user()
        return data


class EditableDumpSchema(EditableSchema):
    class Meta(EditableSchema.Meta):
        fields = [f for f in EditableSchema.Meta.fields if not f.startswith('can_')]


class EditableBasicSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Editable
        fields = ('id', 'type', 'state', 'editor', 'timeline_url', 'revision_count')

    state = EnumField(EditableState)
    editor = fields.Nested(EditingUserSchema)
    timeline_url = fields.String()


class EditingEditableListSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'friendly_id', 'title', 'code', 'editable')

    editable = fields.Method('_get_editable')

    def _get_editable(self, contribution):
        editable_type = self.context['editable_type']
        editable = contribution.get_editable(editable_type)
        if not editable:
            return None
        return EditableBasicSchema().dump(editable)


class FilteredEditableSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Editable
        fields = ('contribution_id', 'contribution_title', 'contribution_code', 'contribution_friendly_id',
                  'id', 'state', 'timeline_url', 'editor', 'can_assign_self')

    contribution_friendly_id = fields.String(attribute='contribution.friendly_id')
    contribution_code = fields.String(attribute='contribution.code')
    contribution_title = fields.String(attribute='contribution.title')
    state = EnumField(EditableState)
    timeline_url = fields.String()
    editor = fields.Nested(EditingUserSchema)
    can_assign_self = fields.Function(lambda editable, ctx: editable.can_assign_self(ctx.get('user')))

    @post_dump(pass_many=True)
    def sort_list(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda editable: (
                editable['editor'] is not None,
                editable['contribution_friendly_id'],
            ))
        return data


class EditingReviewAction(IndicoEnum):
    accept = 'accept'
    reject = 'reject'
    update = 'update'
    update_accept = 'update_accept'
    request_update = 'request_update'


class ReviewEditableArgs(mm.Schema):
    action = EnumField(EditingReviewAction, required=True)
    comment = fields.String(load_default='')

    @validates_schema(skip_on_field_errors=True)
    def validate_everything(self, data, **kwargs):
        if data['action'] != EditingReviewAction.accept and not data['comment']:
            raise ValidationError('This field is required', 'comment')


class EditingConfirmationAction(IndicoEnum):
    accept = 'accept'
    reject = 'reject'


class EditableTagArgs(mm.Schema):
    class Meta:
        rh_context = ('event', 'tag', 'is_service_call')

    code = fields.String(required=True, validate=not_empty)
    title = fields.String(required=True, validate=not_empty)
    color = fields.String(required=True, validate=validate.OneOf(get_sui_colors()))
    system = fields.Bool(load_default=False)

    @validates('code')
    def _check_for_unique_tag_code(self, code, **kwargs):
        event = self.context['event']
        tag = self.context['tag']
        query = EditingTag.query.with_parent(event).filter(func.lower(EditingTag.code) == code.lower())
        if tag:
            query = query.filter(EditingTag.id != tag.id)
        if query.has_rows():
            raise ValidationError(_('Tag code must be unique'))

    @validates('system')
    def _check_only_services_set_system_tags(self, value, **kwargs):
        if value and not self.context['is_service_call']:
            raise ValidationError('Only custom editing workflows can set system tags')


class EditableFileTypeArgs(mm.Schema):
    class Meta:
        rh_context = ('event', 'file_type', 'editable_type')

    name = fields.String(required=True, validate=not_empty)
    filename_template = fields.String(validate=not_empty, allow_none=True)
    extensions = fields.List(fields.String(validate=not_empty))
    allow_multiple_files = fields.Boolean()
    required = fields.Boolean()
    publishable = fields.Boolean()

    @validates('name')
    def _check_for_unique_file_type_name(self, name, **kwargs):
        event = self.context['event']
        file_type = self.context['file_type']
        editable_type = self.context['editable_type']
        query = EditingFileType.query.with_parent(event).filter(
            func.lower(EditingFileType.name) == name.lower(), EditingFileType.type == editable_type
        )
        if file_type:
            query = query.filter(EditingFileType.id != file_type.id)
        if query.has_rows():
            raise ValidationError(_('Name must be unique'))

    @validates('filename_template')
    def _check_for_correct_filename_template(self, template, **kwargs):
        if template is not None and '.' in template:
            raise ValidationError(_('Filename template cannot include dots'))

    @validates('extensions')
    def _check_for_correct_extensions_format(self, extensions, **kwargs):
        for extension in extensions:
            if re.match(r'^[*.]+', extension):
                raise ValidationError(_('Extensions cannot have leading dots'))

    @validates('publishable')
    def _check_if_can_unset_or_delete(self, publishable, **kwargs):
        event = self.context['event']
        file_type = self.context['file_type']
        editable_type = self.context['editable_type']
        if file_type and not publishable:
            is_last = not (EditingFileType.query
                           .with_parent(event)
                           .filter(EditingFileType.publishable,
                                   EditingFileType.id != file_type.id,
                                   EditingFileType.type == editable_type)
                           .has_rows())
            if is_last:
                raise ValidationError(_('Cannot unset the only publishable file type'))


class EditingReviewConditionArgs(mm.Schema):
    class Meta:
        rh_context = ('event', 'editable_type')

    file_types = fields.List(fields.Int(), required=True, validate=not_empty)

    @validates('file_types')
    def _validate_file_types(self, file_types, **kwargs):
        editable_type = self.context['editable_type']
        event = self.context['event']
        event_file_types = {ft.id for ft in event.editing_file_types}
        condition_types = set(file_types)

        if condition_types - event_file_types:
            raise ValidationError(_('Invalid file type used'))

        event_conditions = EditingReviewCondition.query.with_parent(event).filter_by(type=editable_type).all()
        if any(condition_types == {ft.id for ft in cond.file_types} for cond in event_conditions):
            raise ValidationError(_('Conditions have to be unique'))


class EditingMenuItemSchema(mm.Schema):
    name = fields.String(required=True)
    title = fields.String(required=True)
    url = fields.String(required=True)
    icon = fields.String()


class EditableTypeArgs(mm.Schema):
    editable_types = fields.List(EnumField(EditableType), required=True)


class EditableTypePrincipalsSchema(mm.Schema):
    class Meta:
        rh_context = ('event',)

    principals = PrincipalList(allow_event_roles=True, allow_category_roles=True)


class ReviewCommentSchema(mm.Schema):
    text = fields.String(required=True)
    internal = fields.Boolean(load_default=False)


class RoleSchema(mm.Schema):
    name = fields.String()
    code = fields.String()
    source = fields.Method('_get_source')

    def _get_source(self, role):
        return 'category' if isinstance(role, CategoryRole) else 'event'


class ServiceUserSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'roles', 'manager', 'submitter', 'editor')

    roles = fields.Method('_get_roles')
    manager = fields.Function(lambda user, ctx: ctx['editable'].event.can_manage(user, 'editing_manager'))
    submitter = fields.Function(lambda user, ctx: ctx['editable'].can_perform_submitter_actions(user))
    editor = fields.Function(lambda user, ctx: ctx['editable'].can_perform_editor_actions(user))

    def _get_roles(self, user):
        event = self.context['editable'].event
        event_roles, category_roles = get_all_user_roles(event, user)
        roles = RoleSchema(many=True).dump(event_roles | category_roles)
        return sorted(roles, key=lambda r: (r['source'], r['code']))


class ServiceReviewEditableSchema(mm.Schema):
    publish = fields.Boolean(load_default=True)
    comment = fields.String()
    comments = fields.List(fields.Nested(ReviewCommentSchema))
    tags = fields.List(fields.Int())


class ServiceActionSchema(mm.Schema):
    name = fields.String(required=True)
    title = fields.String(required=True)
    color = fields.String(load_default=None)
    icon = fields.String(load_default=None)
    confirm = fields.String(load_default=None)


class ServiceActionResultSchema(mm.Schema):
    publish = fields.Boolean()
    comments = fields.List(fields.Nested(ReviewCommentSchema))
    tags = fields.List(fields.Int())
    redirect = fields.String()
