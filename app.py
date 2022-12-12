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
        print("\n 1. Running bully")
        await asyncio.sleep(5) # wait for everything to be up
        
        # Get all pods doing bully
        print("\n 2. Making a DNS lookup to service")
        response = socket.getaddrinfo("bully-service",0,0,0,0)
        
        print("\n 3. Get response from DNS")
        ip_list = []
        for result in response:
            ip_list.append(result[-1][0])
        ip_list = list(set(ip_list))

        #Remove own POD ip from the list of pods
        ip_list.remove(POD_IP)
        print("\n 4. Got %d other pod ip's" % (len(ip_list)))
        
        # Get ID's of other pods by sending a GET request to them
        await asyncio.sleep(2)
        other_pods = dict()
        for pod_ip in ip_list:
            endpoint = '/pod_id'
            url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
        
            try:
                response = requests.get(url)
                print("\n 5. Got response from: %s,  %s" % (url, response))
            except:
                print("\n Could not connect to pod %s" % (pod_ip))
                continue

            other_pods[str(pod_ip)] = response.json()

        # Other pods in network
        print(other_pods)

        #parse the other_pods to recieve_election to start election        
        print("\n 6. Starting election")
        await receive_election(list(other_pods.values())[0]) #next(iter(other_pods[1])list(other_pods.values())[0]
        print("\n 7. Election completed")

        # Sleep a bit, then repeat
        await asyncio.sleep(2)
    
#GET /pod_id
async def pod_id(request):
    return web.json_response(POD_ID)

#POST /receive_election
#Receive election from other pod with lower id
async def receive_election(request):
    #Get pod ip of sender of election
    selected_id = request
    print("Received election for: ", selected_id)

    #get pod ip of sender of election
    await receive_answer(selected_id)

#POST /receive_answer
#Receive answer from other pod with higher id
async def receive_answer(request):
    print("Received answer")
    #get pod ip of sender of election
    selected_id = request
    
    #------------ Get list of pods in kubernetes network ------------
    response = socket.getaddrinfo("bully-service",0,0,0,0)        
    print("\n Get response from DNS")
    ip_list = []
    for result in response:
        ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))

    #Remove own POD ip from the list of pods
    ip_list.remove(POD_IP)
    #----------------------------------------------------------------

    #Get dictionary of pods_id's in kubenetes network
    #await asyncio.sleep(2)
    list_of_pods = dict()
    print("ip_list: ", ip_list)
    for pod_ip in ip_list:
        #Get pod id of pod_ip
        endpoint = '/pod_id'
        url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        pod_id = response.json()
        list_of_pods[str(pod_ip)] = pod_id

    pod_values = list(list_of_pods.values())
    print("list_of_pods: ", list_of_pods)

    isValid = True
    #compare pod id with own pod id
    for pod_id in pod_values:
        if(pod_id > selected_id):
            #Send election to new pod with higher id
            print("New election called for: ", pod_id)
            isValid = False
            await receive_election(pod_id)
        else:
            #Continue to next pod in list
            continue
    
    if(isValid):
        #Tell pod that sent election that it is the coordinator
        print("I am the coordinator", selected_id)
        #await asyncio.sleep(2)
        await receive_coordinator(selected_id)

#POST /receive_coordinator
#Receive coordinator from other pod with higher id
async def receive_coordinator(request):
    
    selected_id = request
    print("Received coordinator from pod:", selected_id)

    #------------ Get list of pods in kubernetes network ------------
    response = socket.getaddrinfo("bully-service",0,0,0,0)        
    print("\n Get response from DNS")
    ip_list = []
    for result in response:
        ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))

    #Remove own POD ip from the list of pods
    ip_list.remove(POD_IP)
    #----------------------------------------------------------------

    #Get dictionary of pods_id's in kubenetes network
    list_of_pods = dict()
    for pod_ip in ip_list:
        #Get pod id of pod_ip
        endpoint = '/pod_id'
        url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        pod_id = response.json()
        list_of_pods[str(pod_ip)] = pod_id
    
    pod_values = list(list_of_pods.values())

    #Send coordinator message to all pods with lower id
    isValid = True
    for pod_id in pod_values:
        if(pod_id < selected_id):
            #Send coordinator to new pod with lower id
            print("Pod: {0} New leader Is: {1}".format(pod_id, selected_id))
        else:
            #Continue to next pod in list
            print("ERROR: No leader was found", pod_id)
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