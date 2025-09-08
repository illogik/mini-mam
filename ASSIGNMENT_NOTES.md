# Mini-mam High Level Deployment Strategy
- Pulumi used for infrastructure deployment and application bootstrap
- EKS used for running the application
  - AWS Load Balancer Controller used for ingress
  - ExternalDNS used for creation of DNS records
- Build and deploy of services via Makefile
  - This was a manual step with the intention of implementing this in a ci/cd pipeline

# Key Changes to Repo
- Added ci build/push to the Makefile
- Pulumi code stored in [pulumi](./pulumi)
- K8s manifests stored in [k8s](./k8s)

# General Notes
- This deployment *should* be reproducible. We can try it during the presentation!
- Ingress deployment for the currently running app used hard coded values due to an issue I had with my pulumi resource. I think that a full redeployment would fix whatever the problem was so we can find out if we decide to redeploy.
- Mini-mam download doesn't work - but it doesn't work on the demo installation either. It looked like this was an issue with the frontends download handler using a bare fetch which doesn't send the JWT.

# Things I Could Have Done Better
- Deployments
  - Helm for templatization in a CI/CD pipeline (ECR repo and GIT SHA)
- Autoscaling
  - Deployments would request minimal resources and be accompanied by a HorizontalPodAutoscaler
- Monitoring
- Metrics
  - Metrics ports already exposed
