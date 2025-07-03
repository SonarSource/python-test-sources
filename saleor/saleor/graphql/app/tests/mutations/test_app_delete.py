import graphene

from .....app.error_codes import AppErrorCode
from .....app.models import App
from ....tests.utils import get_graphql_content

APP_DELETE_MUTATION = """
    mutation appDelete($id: ID!){
      appDelete(id: $id){
        errors{
          field
          message
          code
        }
        app{
          name
        }
      }
    }
"""


def test_app_delete(
    staff_api_client,
    staff_user,
    app,
    permission_manage_orders,
    permission_manage_apps,
):
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    staff_user.user_permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["errors"]
    assert not App.objects.filter(id=app.id)


def test_app_delete_for_app(
    app_api_client,
    permission_manage_orders,
    permission_manage_apps,
):
    requestor = app_api_client.app
    app = App.objects.create(name="New_app")
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    requestor.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["errors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_out_of_scope_app(
    staff_api_client,
    staff_user,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure user can't delete app with wider scope of permissions."""
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"


def test_app_delete_superuser_can_delete_any_app(
    superuser_api_client,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    """Ensure superuser can delete app with any scope of permissions."""
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}

    response = superuser_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    assert data["app"]
    assert not data["errors"]
    assert not App.objects.filter(id=app.id).exists()


def test_app_delete_for_app_out_of_scope_app(
    app_api_client,
    permission_manage_orders,
    permission_manage_apps,
):
    app = App.objects.create(name="New_app")
    query = APP_DELETE_MUTATION
    app.permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("App", app.id)

    variables = {"id": id}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=(permission_manage_apps,)
    )
    content = get_graphql_content(response)

    data = content["data"]["appDelete"]
    errors = data["errors"]
    assert not data["app"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == AppErrorCode.OUT_OF_SCOPE_APP.name
    assert error["field"] == "id"
