!#/bin/bash

mkdir kube-prometheus
cd kube-prometheus
git clone https://github.com/prometheus-operator/kube-prometheus
git checkout main
kubectl apply --server-side -f manifests/setup
kubectl wait \
	--for condition=Established \
	--all CustomResourceDefinition \
	--namespace=monitoring
kubectl apply -f manifests/
