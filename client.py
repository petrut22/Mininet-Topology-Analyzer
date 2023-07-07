#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import requests     # http(s) requests
import argparse     # argument parsing
import asyncio
import aiohttp
from timeit import default_timer as timer
from datetime import timedelta
from multiprocessing.dummy import Pool as ThreadPool
from queue import Queue
from collections import OrderedDict
from random import randrange

# ANSI color escape codes
ANSI_RED     = '\033[31m'
ANSI_GREEN   = '\033[32m'
ANSI_YELLOW  = '\033[33m'
ANSI_BLUE    = '\033[34m'
ANSI_MAGENTA = '\033[35m'
ANSI_CLR     = '\033[0m'
ANSI_BOLD    = '\033[1m'
ANSI_UNBOLD  = '\033[2m'

################################################################################
############################### CLIENT BACKENDS ################################
################################################################################

# http_get - performs an HTTP(S) GET and returns relevant info
#   @url : the URL; must start with http:// or https://
#
#   @return : list of (url, status__code, elapsed_time [μs]) tuples
#             one for each redirect
def http_get(url: str):
    ret = [ ]

    # follow redirects and measure them independently
    while True:
        req = requests.get(url, allow_redirects=False)
        ret.append((url, req.status_code, req.elapsed.microseconds))

        # if server answer is a redirect, try again
        if req.is_redirect and req.next.url != None:
            url = req.next.url
        else:
            break

    return ret

################################################################################
########################### RESPONSE PRETTY PRINTERS ###########################
################################################################################

# disp_http - display http responses
#   @resp_list : value returned by http_get()
def disp_http(resp_list):
    for resp in resp_list:
        # select color for status message depending on class
        sm_color = ANSI_MAGENTA     # this signifies an invalid code
        if 100 <= resp[1] < 200:    # Informational Response
            sm_color = ANSI_BLUE
        if 200 <= resp[1] < 300:    # Successful Response
            sm_color = ANSI_GREEN
        if 300 <= resp[1] < 400:    # Redirection Response
            sm_color = ANSI_YELLOW
        if 400 <= resp[1] < 500:    # Client Error Response
            sm_color = ANSI_RED
        if 500 <= resp[1] < 600:    # Server Error Response
            sm_color = ANSI_RED

        # print the info
        logfile = open('client_log.txt', 'w+')
        # print('%sURL :%s %s%s' % \
        #       (ANSI_BOLD, ANSI_UNBOLD, resp[0], ANSI_CLR), file = logfile)
        print('URL:', resp[0])
        # print('%sCODE:%s %s%d%s' % \
        #       (ANSI_BOLD, ANSI_UNBOLD, sm_color, resp[1], ANSI_CLR), file = logfile)
        print('CODE:', resp[1])
        # print('%sTIME:%s %d [μs]%s' % \
        #       (ANSI_BOLD, ANSI_UNBOLD, resp[2], ANSI_CLR), file = logfile)
        print('TIME:', resp[2])
        # print("\n", file = logfile)
        logfile.close()


################################################################################
############################## SCRIPT ENTRY POINT ##############################
################################################################################

dictionaryURL = dict()

def urlDictionaryCreate(protocol):
    #for each host -> latency
    dictionaryURL[protocol + "10.10.101.2:9000"] = 29.7865
    dictionaryURL[protocol + "10.10.101.3:9000"] = 23.9725
    dictionaryURL[protocol + "10.10.102.2:9000"] = 33.835
    dictionaryURL[protocol + "10.10.102.3:9000"] = 21.52
    dictionaryURL[protocol + "10.10.103.2:9000"] = 18.8285
    dictionaryURL[protocol + "10.10.103.3:9000"] = 26.976

def threadFunction(url):
    response = http_get(url)
    print(url, response)
    return

#the thread policy
def threadPolicy(numberReq, hostsURList):
    N = len(hostsURList)

    pool = ThreadPool(processes = N)

    for i in range(int(numberReq / N)):
        pool.map(threadFunction, hostsURList)

    if((numberReq % N) != 0):
        poolNew = ThreadPool(numberReq % N)
        poolNew.map(threadFunction, hostsURList[: numberReq % N])

#start asynchronous http request and wait the response
async def getResponse(session, url):
    async with session.get(url) as response:
        print(response.status)
        result = await response
        return 

#function with Round Robin using asynchronous http requests
async def roundRobin(numberReq, hostsURList):
    N = len(hostsURList)
    async with aiohttp.ClientSession() as session:
        coroutines = []
        for i in range(numberReq):       
            coroutines.append(getResponse(session, hostsURList[(i % N)]))
        return await asyncio.gather(*coroutines, return_exceptions=True)
  
#random Policy using asynchronous http requests
async def randomPolicy(numberReq, hostsURList):
    N = len(hostsURList)
    async with aiohttp.ClientSession() as session:
        coroutines = []
        for i in range(numberReq):
            randomIndex = randrange(0, N - 1)  
            #each time a coroutine will be born 
            result = getResponse(session, hostsURList[randomIndex])
            coroutines.append(result)

        if(len(coroutines) != numberReq):
            print("Total packets:", str(numberReq), "Total packets processed:", str(len(coroutines)))

        return await asyncio.gather(*coroutines, return_exceptions=True)


#function with Round Robin using http_get
def serialRoundRobin(numberReq, hostsURList):
    N = len(hostsURList)
    requests = []
    for i in range(numberReq): 
        response = http_get(hostsURList[(i % N)])
        print(hostsURList[(i % N)], response)
        requests.append(response)
        #the case where the number of proceesed requests is not equal with the total number of requests
    if(len(requests) != numberReq):
            print("Total packets:", str(numberReq), "Total packets processed:", str(len(requests)))
    return

#this function will choose a random index from the host list and send a request
#using http_get function
def serialRandomPolicy(numberReq, hostsURList):
    N = len(hostsURList)
    requests = []
    for i in range(numberReq):
        randomIndex = randrange(0, N - 1)   
        response = http_get(hostsURList[randomIndex])
        print(hostsURList[randomIndex], response)
        requests.append(response)
    #the case where the number of proceesed requests is not equal with the total number of requests
    if(len(requests) != numberReq):
        print("Total packets:", str(numberReq), "Total packets processed:", str(len(requests)))


#function in which you can choose the policy from the console    
def loadBalancing(numberReq, protocol):
    #this dictionary will contain as the key the url of the host
    #and the value will be the latency 
    urlDictionaryCreate(protocol)
    #list with all url hosts
    hostsURList = list(dictionaryURL.keys())

    print("Choose the policy from the next list of policies, using the number")
    print("1 --> Policy with Threads")
    print("2 --> Policy with Round Robin asynchronous")
    print("3 --> Policy with URLs selected random asynchronous")
    print("4 --> Policy with URLs selected random synchronous")
    print("5 --> Policy with Round Robin synchronous")

    policySelected = int(input("Enter the number: "))
    #the menu 
    if policySelected == 1:
        start = timer()
        threadPolicy(numberReq, hostsURList)
        end = timer()
        threadTime = timedelta(seconds = end - start)

        print("Time of the Policy using Threads ", str(threadTime) + '\n')
    elif policySelected == 2:
        start = timer()
        asyncio.run(roundRobin(numberReq, hostsURList))
        end = timer()
        roundRobinTime = timedelta(seconds = end - start)

        print("Time of the Policy using Round Robin asynchronous", str(roundRobinTime), '\n')
    elif policySelected == 3:
        start = timer()
        asyncio.run(randomPolicy(numberReq, hostsURList))
        end = timer()
        randomTime = timedelta(seconds = end - start)

        print("Time of the Policy using random URLs asynchronous", str(randomTime),'\n')
    elif policySelected == 4:
        start = timer()
        serialRandomPolicy(numberReq, hostsURList)
        end = timer()
        randomTime = timedelta(seconds = end - start)

        print("Time of the Policy using random URLs synchronous", str(randomTime), '\n')
    elif policySelected == 5:
        start = timer()
        serialRoundRobin(numberReq, hostsURList)
        end = timer()
        roundRobinTime = timedelta(seconds = end - start)

        print("Time of the Policy using Round Robin synchronous", str(roundRobinTime) , '\n')
    else:
        print("Wrong index!")



def main():
    # parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--proto',
                        help='application protocol',
                        choices=[ 'http', 'https' ])
    parser.add_argument('-n', '--number', type=int, help='Number of requests')

    cfg = parser.parse_args()

    # select backend depending on protocol
    if cfg.proto == 'http':
        loadBalancing(cfg.number, 'http://')

    elif cfg.proto == 'https':
        loadBalancing(cfg.number, 'https://')

    elif cfg.proto == '':
        print('salut')
    else:
        parser.print_help()
        exit(-1)

if __name__ == '__main__':
    main()

