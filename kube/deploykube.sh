eval $(minikube docker-env)
docker stop $(docker ps|grep kubefastapiapp| awk '{print $1}')
docker container rm $(docker container ls -a|grep kubefastapiapp| awk '{print $1}')
docker image rm $(docker images|grep kubefastapiapp| awk '{print $3}')
docker build --tag kubefastapiapp .
#deploy service
kubectl apply -f kube/deployment.yaml
kubectl apply -f kube/service.yaml
#kubectl apply -f ingress.yaml