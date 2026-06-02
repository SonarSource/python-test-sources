import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3

no_config = s3.Bucket(self, "bucket")  # Noncompliant [S6249]

ssl_false = s3.Bucket(self, "bucket", enforce_ssl=False)  # Noncompliant [S6249]


with_config = s3.Bucket(self, "bucket")  # S6281: Compliant (missing block_public_access is no longer flagged)

result = with_config.add_to_resource_policy(iam.PolicyStatement(  # Noncompliant [S6249]
        effect=iam.Effect.DENY,
        resources=[bucket.bucket_arn],
        actions=["s3:SomeAction"],
        principals=[roles],
        conditions=[{"Bool": {"aws:SecureTransport": False}}],
    )
)

empty_policy_call = s3.Bucket(self, "bucket")  # Noncompliant [S6249]
result = empty_policy_call.add_to_resource_policy()

no_policy_added = s3.Bucket(self, "bucket")  # Noncompliant [S6249]
result = no_policy_added.foo(
    iam.PolicyStatement(
        effect=iam.Effect.DENY,
        resources=["*"],
        actions=["s3:*"],
        principals=["*"],
        conditions=["SecureTransport:False"],
    )
)

not_policy_statement = s3.Bucket(self, "bucket")  # Noncompliant [S6249]
result = not_policy_statement.add_to_resource_policy(
    iam.Foo(
        effect=iam.Effect.DENY,
        resources=["*"],
        actions=["s3:*"],
        principals=["*"],
        conditions=["SecureTransport:False"],
    )
)
from module import foo

ssl_true = s3.Bucket(self, "bucket", enforce_ssl=True)  # Compliant [S6249]
ssl_unknown = s3.Bucket(self, "bucket", enforce_ssl=foo())  # Compliant [S6249]

correct_policy = s3.Bucket(self, "bucket")  # S6281: Compliant (missing block_public_access is no longer flagged)
result = correct_policy.add_to_resource_policy(
    iam.PolicyStatement(  # Compliant [S6249]
        effect=iam.Effect.DENY,
        resources=["*"],
        actions=["s3:*"],
        principals=["*"],
        conditions=["SecureTransport:False"],
    )
)

compliant_policy = s3.Bucket(self, "bucket")  # S6281: Compliant (missing block_public_access is no longer flagged)
result = compliant_policy.add_to_resource_policy(
    iam.PolicyStatement(  # Compliant [S6249]
        effect=iam.Effect.DENY,
        resources=["foo", "*"],
        actions=["s3:*", "foo:foo"],
        principals=[
            "role",
            "other_role",
            "*",
        ],
        conditions=["condition_a", "SecureTransport:False"],
    )
)
