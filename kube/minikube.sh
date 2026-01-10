# Starts a node Kubernete cluster using Virtualbox/VMWareFusion
minikube start;
minikube addons enable registry;
minikube addons enable ingress;
echo "URL:: " + $(minikube  dashboard --url)

#LINKS
#https://richard.to/programming/hello-world-fast-api-kubenetes.html
#https://github.com/richard-to/kubernetes-experiments/blob/master/README.md
