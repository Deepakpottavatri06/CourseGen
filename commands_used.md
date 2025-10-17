Minikube commands to create the docker image locally in minikube VM

# Point Docker CLI to Minikube's Docker engine
minikube docker-env | Invoke-Expression OR eval $(minikube docker-env)

# Rebuild the image inside Minikube
docker build -t <image_name> <path>

# Restart your deployment to pick up the new image
kubectl rollout restart deployment <deployment.yaml>


# image policy in deployment.yaml
imagePullPolicy: IfNotPresent      # 👈 add this line
It ensures that the image is pulled only if it is not already present on the node.
### This is useful when you are building images locally and want to use them without pulling from a remote registry.

# secrets creation command
kubectl create secret generic <secret_name> --from-env-file=.env
## --from-env-file=.env  👈 this flag allows you to create a secret from a file containing key-value pairs.

# To view the created secret
kubectl get secrets

# service creation command 
### to expose your application to external traffic

kubectl apply -f service.yaml
kubectl get services

# To access the service
minikube service <service_name> --url
### This command retrieves the URL for accessing the specified service running in Minikube.