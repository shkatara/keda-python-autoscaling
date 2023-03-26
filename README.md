
![Logo](https://raw.githubusercontent.com/kedacore/keda/main/images/logos/keda-word-colour.png)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![MIT License](https://img.shields.io/docker/pulls/shkatara/python-custom-metrics-prometheus
)](https://hubgw.docker.com/r/shkatara/python-custom-metrics-prometheus)


# Kubernetes Event Driven Autoscaler ( KEDA )

This git repository is for anyone who is looking to get their hands on on a working Kubernetes Driven Autoscaling Demo.

About KEDA: In easy words, lets your application pods, or rather any resource in Kubernetes that has a scale subresource, automatically scale out (including to/from zero) on your defined metrics. With the modern applications being put on Kubernetes, scaling out only on the basis of CPU Utilization or Memory Utilization are almost never enough. 

With KEDA, you can not define what do you want to scale on, precisely, on which event do you want to scale out. With KEDA, you can be as flexible as scaling on your own terms like:

- Scale out automatically if your KAFKA queue has more messages than a defined threshold.
- Scale out automatically on the number of HTTP requests to your application. 

The applications and options of scaling out on these custom metrics are limitless. 


## Testing Environment:

This demo / repository has been tested with the following stack:

| Component  | Name | Version |
| ------------- | ------------- | ------------- |
| Container Platform  | Upstream Kubernetes (Standard Kubeadm Installation) | 1.25.0|
| Operating System | Centos   |7.9 |
|Autoscaler | Kubernetes Driven Auto Scaler (KEDA)| 2.10.0|
|Prometheus | Kube-Prometheus Stack |v0.12.0 / git main branch |
|Container Runtime| containerd | 1.6.19|
|Kubernetes Client| kubectl| 1.25.0|

Note: Please make sure you are using the correct versions from above as there is a version-skew and version dependency between kube-prometheus and Kubernetes.

NOTE: It is expected that you will have a working Infrastructure given as above before proceeding for the demo. 
## Background of the Demo:

In this demo, we will be:

- Installing the kube-prometheus server. This will give us kube-state-metrics, a prometheus server, and a prometheus operator.
- Installing Keda operator
- Deploying a sample flask based python application that will expose custom metrics for prometheus to scrape on /metrics endpoint on port 5000
- Creating a ServiceMonitor for allowing prometheus to scrape custom metrics from our application.
- Creating a KEDA custom resource called ScaledObject where we will define our scaling definition based on the custom metrics.

The metrics that the application will expose is a Counter type metrics from prometheus that counts the number of HTTP requests to the '/' endpoint of the application. This metrics is exposed by the application on /metrics endpoint for prometheus to scrape using the ServiceMonitor custom resource.


## Flask Application Background:

The application is a simple flask based application that implements prometheus libraries to expose metrics of type Counter on the /metrics endpoint named "python_request_operations_total", that counts the number of http requests that has been made to the / of the application. Each time you curl on the / of the application, this metrics is increased by 1. 

The application is already built and pushed to docker hub at docker.io/shkatara/python-custom-metrics-prometheus:latest
## Getting started with the project
- ## Installing kube-prometheus in monitoring namespace
```bash
  [root@host ~]# git clone github.com/shkatara/keda-python-autoscaling.git
  [root@host ~]# cd keda-python-autoscaling
  [root@host ~]# ./deploy-kube-prometheus.sh
  [root@host ~]# kubectl get pods -n monitoring
```
Once all the pods in monitoring namespace are running, edit the prometheus-k8s service in monitoring namespace for type NodePort to open the prometheus console. 

- ## Installing Kubernetes Driven Auto Scaler Operator

```bash
[root@host ~]# ./deploy-keda.sh
```

- ## Deploy the sample application in the 'test' namespace:

```bash
[root@host ~]# kubectl  -f app.yaml create
```

- ## Test the application for sample metrics:

```bash
[root@host ~]# curl localhost:30115
Hello World!
[root@host ~]# curl localhost:30115/metrics
# HELP python_request_operations_total The total number of processed requests
# TYPE python_request_operations_total counter
python_request_operations_total 1.0  
# HELP python_request_operations_created The total number of processed requests
# TYPE python_request_operations_created gauge
python_request_operations_created 1.6798341744646277e+09
# HELP python_request_duration_seconds Histogram for the duration in seconds.
# TYPE python_request_duration_seconds histogram
python_request_duration_seconds_bucket{le="1.0"} 1.0
python_request_duration_seconds_bucket{le="2.0"} 1.0
python_request_duration_seconds_bucket{le="5.0"} 1.0
python_request_duration_seconds_bucket{le="6.0"} 1.0
python_request_duration_seconds_bucket{le="10.0"} 1.0
python_request_duration_seconds_bucket{le="+Inf"} 1.0
python_request_duration_seconds_count 1.0
python_request_duration_seconds_sum 0.600651741027832
# HELP python_request_duration_seconds_created Histogram for the duration in seconds.
# TYPE python_request_duration_seconds_created gauge
python_request_duration_seconds_created 1.6798341744646492e+09
```
As you can see, there are many metrics available that the application is exposing. The one we are going to use for scaling on is "python_request_operations_total" 

- ## Configure Prometheus to scrape custom metrics from our application

``` bash
[root@host ~]# kubectl create rolebinding prometheus-test-namespace-scrape --clusterrole=edit --serviceaccount=monitoring:prometheus-k8s -n test\
[root@host ~]# kubectl  -f service-monitor.yaml create
```
In the above step, we create a rolebinding, allowing the prometheus service account to look into our namespace for querying the pods and to query the /metrics endpoint of the application, where the metrics are exposed.

Let us now create the ScaledObject resouce from KEDA. This is the Custom Resource where we define our auto scaling parameters. We are using prometheus as the data source of KEDA and a prometheus related query on which KEDA will be scaling out. KEDA under the hood creates a Horizontal Pod Autoscaler that does the scaling of our pods, based on the telemetry that has been given by KEDA. 

- ### Create ScaledObject to scale out on custom metrics threshold

```bash
[root@host ~]# kubectl  -f scaled-object.yaml create
[root@host ~]# kubectl get scaledobject,hpa -n test
NAME                                   SCALETARGETKIND      SCALETARGETNAME   MIN   MAX   TRIGGERS     AUTHENTICATION   READY   ACTIVE   FALLBACK   AGE
scaledobject.keda.sh/scaledobject-py   apps/v1.Deployment   test                          prometheus                    True    False    False      96m

NAME                                                           REFERENCE         TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/keda-hpa-scaledobject-py   Deployment/test   11/25 (avg)   1         100       2          96m
```

The scaledobject has created a HPA where the target is our custom metrics "python_request_operations_total" threshold, rather than CPU and Memory. Also, the scaledObject is Ready as it is listening on the threshold but not active as the threshold condition is not met / crossed. 

- ## Conclusion:

Your numbers on Targets and Age will be different. Basically, we are saying that we need to scale out on the number of pods, when the metrics "python_request_operations_total" goes beyond 25. In other words, once we hit our application endpoint / 25 times, we will start up a new pod because the threshold that is 25 has been crossed, and this proves that on an event, that was crossing the 25th HTTP request, we were able to scale out our pods, irrespective to their CPU and Memory Utilization

## Screenshots

![App Screenshot](https://via.placeholder.com/468x300?text=App+Screenshot+Here)


## Acknowledgements

 - [Kubernetes Driven Auto Scaler](https://keda,sh)
 - [Kube-Prometheus](https://github.com/prometheus-operator/kube-prometheus)
 - [Write a Good readme](https://readme.so)
 - [A Pretty Good DevOps Channel](https://www.youtube.com/channel/UCFe9-V_rN9nLqVNiI8Yof3w)


## Authors

- [shkatara](https://www.github.com/shkatara)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/shubhamkatara)




## Feedback

If you have any feedback, please reach out to me at shubham.katara59@gmail.com

