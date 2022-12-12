#Remove old bully-app deployment and services
minikube kubectl -- delete deployment bully-app
minikube kubectl -- delete service bully-service
minikube kubectl -- delete service flask-web-service

# Build bully-app image
minikube image build -t bully-app .

# cd directory to flask_docker and build flask wep app 
Set-Location flask_docker 
minikube image build -t flask-web-app .

#docker build -t flask-wep-app:dev . 
#minikube image load flask-wep-app:dev

# cd directory to bully-in-kubernetes and deploy bully-app
Set-Location .. 

minikube kubectl -- apply -f .\k8s\flask-service.yaml
minikube kubectl -- apply -f .\k8s\headless-service.yaml
minikube kubectl -- apply -f .\k8s\deployment.yaml

Write-Host "------------------ View Kubernetes information ------------------"
minikube kubectl get all

Write-Host "------------------ View Kubernetes service URLs ------------------"
minikube service --all

#Yeet out the logs
#minikube kubectl -- logs -l bully-app

#Write-Host "------------------ View kubernetes active pods ------------------"
#minikube kubectl get pods
