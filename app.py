import asyncio
import os
import os
import socket
import random
import aiohttp
import requests
import json
from aiohttp import web
from kubernetes import config, client
from kubernetes.client.api import core_v1_api

POD_IP = str(os.environ['POD_IP'])
WEB_PORT = int(os.environ['WEB_PORT'])
POD_ID = random.randint(0, 100)
v1 = core_v1_api.CoreV1Api()

async def setup_k8s():
    # If you need to do setup of Kubernetes, i.e. if using Kubernetes Python client
    config.load_incluster_config()
    print("K8S setup completed")


async def run_bully():
    while True:
        print("Running bully")
        await asyncio.sleep(5) # wait for everything to be up
        
        # Get all pods doing bully
        print("Making a DNS lookup to service")
        response = socket.getaddrinfo("bully-service",0,0,0,0)
        #pods = v1.list_namespaced_pod("default", watch=False)

        #for i in pods.items:
        #    if i.status.pod_ip == POD_IP:
        #        continue
        #    print(i.status.pod_ip)
        #    ip_list.append(i.status.pod_ip)
        
        print("Get response from DNS")
        #print(response)
        ip_list = []
        for result in response:
            print(result[-1][0])
            ip_list.append(result[-1][0])
        #print(ip_list)
        ip_list = list(set(ip_list))

        #Remove own POD ip from the list of pods
        #ip_list.remove(POD_IP)
        print("Got %d other pod ip's" % (len(ip_list)))
        
        # Get ID's of other pods by sending a GET request to them
        await asyncio.sleep(2)
        other_pods = dict()
        for pod_ip in ip_list:
            endpoint = '/pod_id'
            url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
            
            try:
                response = requests.get(url)
            except:
                print("Could not connect to pod %s" % (pod_ip))
                continue

            other_pods[str(pod_ip)] = response.json()
            

        # Other pods in network
        print(other_pods)
        
        # Sleep a bit, then repeat
        await asyncio.sleep(2)
    
#GET /pod_id
async def pod_id(request):
    return web.json_response(POD_ID)
    
#POST /receive_answer
#Receive answer from other pod with higher id
async def receive_answer(request):
    print("Received answer")
    #get pod ip of sender of election
    #selected_id = request.json()
    selected_id = pod_id(request)

    #Get dictionary of pods_id's in kubenetes network
    list_of_pods = dict()
    for pod_ip in ip_list:
        #Get pod id of pod_ip
        endpoint = '/pod_id'
        url = 'http://' + str(POD_IP) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        pod_id = response.json()
        list_of_pods[str(pod_ip)] = pod_id

    isValid = True
    #compare pod id with own pod id
    for pod_id in list_of_pods:
        if(pod_id > selected_id):
            #Send election to new pod with higher id
            print("New election called for: ", pod_id)
            isValid = False
            receive_election(pod_id)
        else:
            #Continue to next pod in list
            pass
    
    if(isValid):
        #Tell pod that sent election that it is the coordinator
        print("I am the coordinator")
        receive_coordinator(pod_id)
    
            
    
    #print("I am the coordinator")
    #receive_coordinator(pod_id)

#POST /receive_election
#Receive election from other pod with lower id
async def receive_election(request):
    #Get pod ip of sender of election
    selected_id = pod_id(request)
    print("Received election for: ", selected_id)
    
    #get pod ip of sender of election
    receive_answer(selected_id)
        

#POST /receive_coordinator
#Receive coordinator from other pod with higher id
async def receive_coordinator(request):
    selected_id = pod_id(request)
    print(f"Received coordinator from pod {selected_id['Coordinator']}")

    #Get dictionary of pods_id's in kubenetes network
    list_of_pods = dict()
    for pod_ip in ip_list:
        #Get pod id of pod_ip
        endpoint = '/pod_id'
        url = 'http://' + str(POD_IP) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        pod_id = response.json()
        list_of_pods[str(pod_ip)] = pod_id

    #Send coordinator message to all pods with lower id
    isValid = True
    for pod_id in list_of_pods:
        if(pod_id < selected_id):
            #Send coordinator to new pod with lower id
            print("New leader Is: ", pod_id)
        else:
            #Continue to next pod in list
            print("ERROR: No leader was found")
            isValid = False
    if(isValid):
        v1.patch_namespaced_pod(selected_id, "default", {"metadata": {"labels": {"leader": "true"}}})
    

async def background_tasks(app):
    task = asyncio.create_task(run_bully())
    yield
    task.cancel()
    await task

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/pod_id', pod_id)
    app.router.add_post('/receive_answer', receive_answer)
    app.router.add_post('/receive_election', receive_election)
    app.router.add_post('/receive_coordinator', receive_coordinator)
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, host='0.0.0.0', port=WEB_PORT)