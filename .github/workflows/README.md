# GitHub Actions Workflow Documentation

## Docker Build and Push Workflow

This workflow automatically builds and pushes Docker images to Docker Hub when code is pushed to the main branch or when tags are created.

### Prerequisites

1. **Docker Hub Account**: You need a Docker Hub account with the username `iconikio`
2. **GitHub Secrets**: Set up the following secrets in your GitHub repository settings

### Required GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, then add:

- `DOCKER_USERNAME`: Your Docker Hub username (`iconikio`)
- `DOCKER_PASSWORD`: Your Docker Hub access token (not your account password)

### How to Create Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com)
2. Go to Account Settings → Security
3. Click "New Access Token"
4. Give it a name (e.g., "GitHub Actions")
5. Copy the token and add it as `DOCKER_PASSWORD` in GitHub secrets

### Workflow Behavior

The workflow will:

- **On Push to main/master**: Build and push all images to Docker Hub
- **On Pull Requests**: Build images but don't push (for testing)
- **On Tags**: Build and push images with tag-based versioning

### Generated Images

The workflow builds and pushes these images to `iconikio/`:

- `iconikio/mini-mam-api-gateway`
- `iconikio/mini-mam-assets-service`
- `iconikio/mini-mam-files-service`
- `iconikio/mini-mam-transcode-service`
- `iconikio/mini-mam-search-service`
- `iconikio/mini-mam-frontend`

### Image Tags

Images are tagged with:
- Branch name (e.g., `main`)
- Commit SHA (e.g., `sha-abc123`)
- Semantic version tags (e.g., `v1.0.0`, `1.0`)

### Using the Images

After the workflow runs, you can use the images in your `docker-compose.yml`:

```yaml
services:
  api-gateway:
    image: iconikio/mini-mam-api-gateway:main
    # ... rest of config
  
  assets-service:
    image: iconikio/mini-mam-assets-service:main
    # ... rest of config
  
  # ... other services
```

### Multi-Platform Support

Images are built for both `linux/amd64` and `linux/arm64` architectures, making them compatible with:
- Intel/AMD servers and desktops
- Apple Silicon Macs
- ARM-based servers (AWS Graviton, etc.)

### Cache Optimization

The workflow uses GitHub Actions cache to speed up builds by caching Docker layers between runs. 