deploy-api-gateway:
	kubectl apply -f api-gateway.yaml

delete-api-gateway:
	kubectl delete -f api-gateway.yaml

deploy-assets-service:
	kubectl apply -f assets-service.yaml

delete-assets-service:
	kubectl delete -f assets-service.yaml

deploy-files-service:
	kubectl apply -f files-service.yaml

delete-files-service:
	kubectl delete -f files-service.yaml

deploy-frontend:
	kubectl apply -f frontend.yaml

delete-frontend:
	kubectl delete -f frontend.yaml

deploy-search-service:
	kubectl apply -f search-service.yaml

delete-search-service:
	kubectl delete -f search-service.yaml

deploy-transcode-service:
	kubectl apply -f transcode-service.yaml

delete-transcode-service:
	kubectl delete -f transcode-service.yaml

deploy-ingress:
	kubectl apply -f ingress.yaml

delete-ingress:
	kubectl delete -f ingress.yaml

deploy-all: deploy-api-gateway deploy-assets-service deploy-files-service deploy-frontend deploy-search-service deploy-transcode-service

delete-all: delete-api-gateway delete-assets-service delete-files-service delete-frontend delete-search-service delete-transcode-service
