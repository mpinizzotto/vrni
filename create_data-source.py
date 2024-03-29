#usr/bin/env python
#coding utf-8

_author_ = "mpinizzotto"

import re
import csv
import json
import requests
requests.packages.urllib3.disable_warnings()

"""

Create vRNI data sources from CSV

DS_TYPE = vc, nsx-t, nsxalb

DS_TYPE, FQDN, IP_ADDR, NICKNAME, ENABLED, USERNAME, PASSWORD, PROXY_NAME NOTES (optional)
Supports only FQDN or IP_ADDR, if both available will default to FQDN

csv examples:

vc,vcsa-01a.corp.local,192.168.110.22,my-vc,true,administrator@vsphere.local,VMware1!,NI-Collector_192.168.110.100,"my notes"
nsx-t,nsx-mgr-01a,192.168.110.21,my-nsx,admin,VMware1!,NI-Collector_192.168.110.101,"my notes"
nsxalb,avicon-01a,192.168.110.79,my-nsx-alb,admin,VMware1!,NI-Collector_192.168.110.101,"my notes"

"""

vrni = "192.168.110.89"
username = "admin@local"
password = "VMware1!"
headers = { 'content-type': 'application/json' }
file = "vrni.csv"

def read_from_csv(file):
    csvfile = open(file, 'r')
    with csvfile as f:
        reader = csv.reader(f)
        item_list = list(reader)
        return item_list
        csvfile.close()

def create_ds_list(item_list):
    ds_list = []
    for line in item_list:
        ds_info = {}
        ds_info['ds_type']= line[0]
        ds_info['fqdn'] = line[1]
        ds_info['ip_addr']= line[2]
        ds_info['nickname'] = line[3]
        ds_info['enabled']= line[4]
        ds_info['username'] = line[5]
        ds_info['password']= line[6]
        ds_info['proxy_name'] = line[7]
        ds_info['notes'] = line[8]
        ds_list.append(ds_info)
    return ds_list

def get_proxy_nodes(token_header):
    url = "https://" + vrni + "/api/ni/infra/nodes"
    response = requests.get(url, verify=False, headers=token_header)
    parse = json.loads(response.text)
    proxy_list = []
    for items in parse['results']:
        id = items.get('id')
        url = "https://" + vrni + "/api/ni/infra/nodes/" + id
        response = requests.get(url, verify=False, headers=token_header)
        parse = json.loads(response.text)
        proxy_list.append(parse)
    return proxy_list
		
def create_vc_datasource(payload,token_header):
    url = "https://" + vrni + "/api/ni/data-sources/vcenters"
    response = requests.post(url, data=json.dumps(payload), verify=False, headers=token_header)
    parse = json.loads(response.text)
    return parse

def create_nsxt_datasource(payload,token_header):
    url = "https://" + vrni + "/api/ni/data-sources/nsxt-managers"
    response = requests.post(url, data=json.dumps(payload), verify=False, headers=token_header)
    parse = json.loads(response.text)
    return parse
	
def create_nsxalb_datasource(payload,token_header):
    url = "https://" + vrni + "/api/ni/data-sources/nsxalb"
    response = requests.post(url, data=json.dumps(payload), verify=False, headers=token_header)
    parse = json.loads(response.text)
    return parse

def main():
    url = "https://" + vrni + "/api/ni/auth/token"
    payload =  {
                 "username" : username,
                 "password": password,
                 "domain": {
                   "domain_type": "LOCAL"
                 }
               }
    response = requests.post(url, data=json.dumps(payload), verify=False,  headers=headers)
    parse = json.loads(response.text)
    token = parse['token']
    token_header = {'Content-Type': 'application/json',
                    'Authorization': 'NetworkInsight {}'.format(token)}

    item_list = read_from_csv(file)
    ds_list = create_ds_list(item_list)
    proxy_list = get_proxy_nodes(token_header)
   
    for line in ds_list:
        proxy_name = line.get('proxy_name')
        for proxy in proxy_list:
            if proxy_name == proxy['name']:
                proxy_id = proxy['id']
            else:
                print ("Failed to deploy", line.get('fqdn'), "data-source.", proxy_name, "is not a valid vRNI collector.")
	        
            if line.get('ds_type') == "vc":
	    
                payload = {
                           "ip": line.get('ip_addr'),
                           "fqdn": line.get('fqdn'),
                           "proxy_id": proxy_id,
                           "nickname": line.get('nickname'),
                           "enabled": line.get("enabled"),
                           "notes": line.get("notes"),
                           "credentials": {
                               "username": line.get('username'),
                               "password": line.get('password')
                           },
                           "ipfix_request": {
                               "disable_all": "true"
                           },
                           "is_vmc": "false"
                       }
                resp = create_vc_datasource(payload,token_header)
                if 'entity_type' in resp:
                    print (resp['entity_type'], ": ",resp['fqdn'], " created successfully")
                else: 
                    print (line.get('fqdn'), resp['code'], resp['details'])
					
            elif line.get('ds_type') == "nsx-t":
    
                payload = {
                           #"ip": line.get("ip_addr"),
                           "fqdn": line.get("fqdn"),
                           "proxy_id": proxy_id,
                           "nickname": line.get("nickname"),
                           "enabled": line.get('enabled'),
                           "notes": line.get("notes"),
                           "credentials": {
                               "username": line.get("username"),
                               "password": line.get("password")
                          },
                           "ipfix_enabled": "true",
                           "latency_enabled": "false",
                           "nsxi_enabled": "false",
                       }
                
                resp = create_nsxt_datasource(payload,token_header)
                if 'entity_type' in resp:
                    print (resp['entity_type'], ": ",resp['fqdn'], " created successfully")
                else: 
                    print (line.get('fqdn'), resp['code'], resp['details'])


            elif line.get('ds_type') == "nsxalb":
    
                payload = {
                           #"ip": line.get("ip_addr"),
                           "fqdn": line.get("fqdn"),
                           "proxy_id": proxy_id,
                           "nickname": line.get("nickname"),
                           "enabled": line.get('enabled'),
                           "notes": line.get("notes"),
                           "credentials": {
                               "username": line.get("username"),
                               "password": line.get("password")
                          }
                       }
                
                resp = create_nsxalb_datasource(payload,token_header)
                if 'entity_type' in resp:
                    print (resp['entity_type'], ": ",resp['fqdn'], " created successfully")
                else: 
                    print (line.get('fqdn'), resp['code'], resp['details'])

            else:
                print ("Unsupported data-source Type")

if __name__ == '__main__':
       main()
