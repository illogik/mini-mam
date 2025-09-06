import json
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_eks as eks
import pulumi_kubernetes as kubernetes

#####################
### config values ###
#####################

config = pulumi.Config()
aws_region = config.get('region')  # revisit
cluster_name = config.get('clusterName')
min_cluster_size = config.get_int('minClusterSize')
max_cluster_size = config.get_int('maxClusterSize')
desired_cluster_size = config.get_int('desiredClusterSize')
eks_node_instance_type = config.get('eksNodeInstanceType')
vpc_network_cidr = config.get('vpcNetworkCidr')
db_user = config.require('dbUsername')
db_pass = config.require_secret('dbPassword')
delegated_subdomain = config.require('delegatedSubdomain')

aws_region = aws.config.region  # revisit

##########################################################
### route 53 zone and acm certificate - dns validation ###
##########################################################

# fqdn to use under your delegated subdomain
fqdn = f'mini-mam.{delegated_subdomain}'

# look up the hosted zone in account
zone = aws.route53.get_zone(name=delegated_subdomain, private_zone=False)

# authorize amazons ca at your delegated subdomain apex
caa_amazon = aws.route53.Record(
    'delegated-caa-issue-amazon',
    zone_id=zone.zone_id,
    name=delegated_subdomain,
    type='CAA',
    ttl=300,
    records=['0 issue "amazon.com"'],
    allow_overwrite=True,
)

# request a public acm cert - do i need to specify region?
cert = aws.acm.Certificate(
    'app-cert',
    domain_name=fqdn,
    validation_method='DNS',
    opts=pulumi.ResourceOptions(depends_on=[caa_amazon]),
)

# create dns validation records
validation_records = cert.domain_validation_options.apply(
    lambda dvos: [
        aws.route53.Record(
            f'app-cert-validation-{i}',
            zone_id=zone.zone_id,
            name=dvo.resource_record_name,
            type=dvo.resource_record_type,
            ttl=60,
            records=[dvo.resource_record_value],
        )
        for i, dvo in enumerate(dvos)
    ]
)

# finalize validation using the record fqdn
validated_cert = aws.acm.CertificateValidation(
    'app-cert-validated',
    certificate_arn=cert.arn,
    validation_record_fqdns=validation_records.apply(
        lambda recs: [r.fqdn for r in recs]
    ),
)

###########
### ecr ###
###########

services = [
    'api-gateway',
    'assets-service',
    'files-service',
    'transcode-service',
    'search-service',
    'frontend',
]

ecr_repos = {name: awsx.ecr.Repository(name, name=name) for name in services}

##########
### s3 ###
##########

s3_file_service = aws.s3.Bucket(
    'mini-mam-file-service',
    bucket='mini-mam-file-service',
)

###########
### vpc ###
###########

eks_vpc = awsx.ec2.Vpc(
    'eks-vpc', enable_dns_hostnames=True, cidr_block=vpc_network_cidr
)

###########
### eks ###
###########

eks_cluster = eks.Cluster(
    'eks-cluster',
    vpc_id=eks_vpc.vpc_id,
    authentication_mode=eks.AuthenticationMode.API,
    public_subnet_ids=eks_vpc.public_subnet_ids,
    private_subnet_ids=eks_vpc.private_subnet_ids,
    instance_type=eks_node_instance_type,
    desired_capacity=desired_cluster_size,
    min_size=min_cluster_size,
    max_size=max_cluster_size,
    node_associate_public_ip_address=False,
    endpoint_private_access=False,
    endpoint_public_access=True,
    create_oidc_provider=True,
    name=cluster_name,
)

###########
### rds ###
###########

rds_subnets = aws.rds.SubnetGroup(
    'mini-mam-rds-subnets',
    subnet_ids=eks_vpc.private_subnet_ids,
)

rds_sg = aws.ec2.SecurityGroup(
    'rds-sg',
    vpc_id=eks_vpc.vpc_id,
    description='Allow Postgres from EKS VPC',
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol='-1', from_port=0, to_port=0, cidr_blocks=['0.0.0.0/0']
        )
    ],
)

aws.ec2.SecurityGroupRule(
    'rds-ingress-from-vpc',
    type='ingress',
    security_group_id=rds_sg.id,
    protocol='tcp',
    from_port=5432,
    to_port=5432,
    cidr_blocks=[vpc_network_cidr],
)

rds_mini_mam = aws.rds.Instance(
    'mini-mam',
    allocated_storage=20,
    max_allocated_storage=50,
    db_name='minimam',
    engine='postgres',
    engine_version='15',
    instance_class=aws.rds.InstanceType.T3_MICRO,
    username=db_user,
    password=db_pass,
    db_subnet_group_name=rds_subnets.name,
    vpc_security_group_ids=[rds_sg.id],
    publicly_accessible=False,
    skip_final_snapshot=True,
)

####################################
### aws load balancer controller ###
####################################

albc_namespace = 'kube-system'
service_account_name = 'aws-load-balancer-controller'
service_account_full = f'system:serviceaccount:{albc_namespace}:{service_account_name}'
oidc_arn = eks_cluster.core.oidc_provider.arn
oidc_url = eks_cluster.core.oidc_provider.url

# iam role for lb controller service account
albc_iam_role = aws.iam.Role(
    'albc-iam-role',
    assume_role_policy=pulumi.Output.all(oidc_arn, oidc_url).apply(
        lambda args: json.dumps(
            {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {
                            'Federated': args[0],
                        },
                        'Action': 'sts:AssumeRoleWithWebIdentity',
                        'Condition': {
                            'StringEquals': {f'{args[1]}:sub': service_account_full},
                        },
                    }
                ],
            }
        )
    ),
)

# create iam policy
with open('files/iam_policy.json') as policy_file:
    albc_policy_doc = policy_file.read()

albc_iam_policy = aws.iam.Policy(
    'albc-iam-policy',
    name='AWSLoadBalancerControllerIAMPolicy',
    policy=albc_policy_doc,
    opts=pulumi.ResourceOptions(parent=albc_iam_role),
)

# attach iam policy to iam role
aws.iam.PolicyAttachment(
    'albc-attachment',
    policy_arn=albc_iam_policy.arn,
    roles=[albc_iam_role.name],
    opts=pulumi.ResourceOptions(parent=albc_iam_role),
)

# create k8s service account
provider = kubernetes.Provider(
    'provider',
    kubeconfig=eks_cluster.kubeconfig_json,
    opts=pulumi.ResourceOptions(depends_on=[eks_cluster]),
)

albc_service_account = kubernetes.core.v1.ServiceAccount(
    'albc-service-account',
    metadata={
        'name': service_account_name,
        'namespace': albc_namespace,
        'annotations': {
            'eks.amazonaws.com/role-arn': albc_iam_role.arn.apply(lambda arn: arn)
        },
    },
    opts=pulumi.ResourceOptions(provider=provider),
)

# helm deploy
helm = kubernetes.helm.v3.Release(
    'aws-load-balancer-controller',
    kubernetes.helm.v3.ReleaseArgs(
        name='aws-load-balancer-controller',
        chart='aws-load-balancer-controller',
        version='1.13.0',
        repository_opts=kubernetes.helm.v3.RepositoryOptsArgs(
            repo='https://aws.github.io/eks-charts',
        ),
        namespace='kube-system',  # your albc_namespace variable can go here
        create_namespace=False,  # kube-system already exists
        values={
            'clusterName': cluster_name,
            'serviceAccount': {
                'create': False,
                'name': service_account_name,
            },
        },
    ),
    opts=pulumi.ResourceOptions(provider=provider),
)

###############
### exports ###
###############

pulumi.export('app_fqdn', fqdn)
pulumi.export('certificatearn', validated_cert.certificate_arn)
pulumi.export('kubeconfig', eks_cluster.kubeconfig)
pulumi.export('rds_endpoint', rds_mini_mam.address)
pulumi.export('repo_urls', {name: repo.url for name, repo in ecr_repos.items()})
