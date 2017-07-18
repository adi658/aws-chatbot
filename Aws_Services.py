import os, sys, datetime
import boto3
import csv
import re
from boto3.session import Session

REPLACE_ACCESS_KEY = "xxx"
REPLACE_SECRET_KEY = "xxx"
REPLACE_REGION = "eu-west-1"

MY_SESSION = Session(aws_access_key_id=REPLACE_ACCESS_KEY,aws_secret_access_key=REPLACE_SECRET_KEY,region_name=REPLACE_REGION)
response = ""
client = ""
routePub = ""
routePri = ""
secGrPriId = ""
secGrPubId = ""
eIP = ""
natGwID = ""
resp1 = ""

vpc_subnetArr = {}
pub_sub_arr = {}
pri_sub_arr = {}

#--------------------------------------------------- CONFIGURATIONS - START -------------------------------------------------------------

now = datetime.datetime.now()

#num_vpc = 1
#num_subnet_pri = 2
#num_subnet_pub = 2
#vpc_cidr = "10.10.0.0/16"
#vpc_name = "adi_test_vpc"

#if you dont want any service, set it to "NO"
vpc_flow_log = "YES"

#--------------------------------------------------- CONFIGURATIONS - END -------------------------------------------------------------


def lambda_handler(event, context):
    resp = ""
    #event = {'messageVersion': '1.0', 'invocationSource': 'FulfillmentCodeHook', 'userId': 'uwlfqtt43pgs71z0wxd4o5x2tnsv65jg', 'sessionAttributes': None, 'bot': {'name': 'AWS_Services', 'alias': None, 'version': '$LATEST'}, 'outputDialogMode': 'Text', 'currentIntent': {'name': 'aws_services', 'slots': {'num_subnet_pri': '2', 'num_vpc': '1', 'vpc_cidr': '10.0.0.0/16', 'num_subnet_pub': '2', 'vpc_name' : 'testVPC'}, 'confirmationStatus': 'None'}, 'inputTranscript': '10.0.0.0/16'}
    #event = {'messageVersion': '1.0', 'invocationSource': 'FulfillmentCodeHook', 'userId': '7syz2l3fb0odu7rss0ve21v2zq88r4qt', 'sessionAttributes': None, 'bot': {'name': 'AWS_Services', 'alias': None, 'version': '$LATEST'}, 'outputDialogMode': 'Text', 'currentIntent': {'name': 'create_bucket', 'slots': {'aws_region': 'eu-west-1', 'bucket_name': 'lambda-s3-aditya1', 'acl': 'public-read-write'}, 'confirmationStatus': 'Confirmed'}, 'inputTranscript': 'yes'}
    print(event)

    if event['currentIntent']['name'] == "aws_services":
        resp = create_network(event)
        resp1 = parseResp(resp,"network")
        print("Printing final resp1.......................")
        print(resp1)
        resp = {"dialogAction": {"type": "Close", "fulfillmentState": "Fulfilled", "message": {"contentType": "PlainText", "content": resp1 } } }

    elif event['currentIntent']['name'] == "create_bucket":
        resp1 = create_s3Bucket(event)
        resp2 = resp1['Location']
        resp1 = "Bucket created. The endpoint is: "+str(resp2)
        resp = {"dialogAction": { "type": "Close", "fulfillmentState": "Fulfilled", "message": { "contentType": "PlainText", "content": str(resp1) } } }
        
    elif event['currentIntent']['name'] == "generic_network_details":
        print("inside generic_network_details........................................")
        service_type = event['currentIntent']['slots']['service_type']
        master_service = event['currentIntent']['slots']['master_service']
        
        if service_type == "vpc":
            resp1 = describe_vpcs(master_service)
        elif service_type == "subnet":
            resp1 = describe_subnets(master_service)
        elif service_type == "security group":
            resp1 = describe_security_groups(master_service)
            
            
        resp1 = str(service_type)+" | "+str(master_service)
        resp = {"dialogAction": { "type": "Close", "fulfillmentState": "Fulfilled", "message": { "contentType": "PlainText", "content": resp1 } } }

    elif event['currentIntent']['name'] == "get_network_details":
        tagValue = (event['currentIntent']['slots']['tagValue'])
        tagType = (event['currentIntent']['slots']['tagType']).lower()
        if tagType == "vpc":
            resp = describe_vpcs(tagValue)
        elif tagType == "subnet":
            resp = describe_subnets(tagValue)
        elif tagType == "security group":
            resp = describe_security_groups(tagValue)
        resp = {"dialogAction": { "type": "Close", "fulfillmentState": "Fulfilled", "message": { "contentType": "PlainText", "content": str(resp) } } }

    print("Printing final response .......................")
    print(resp)
    return resp

def parseResp(resp,func_type):
    str1 = ""
    if func_type == "network":
        vpcId = resp["vpc"]
        igw = resp["igw"]
        privateSubnetRouteTable = resp["privateSubnetRouteTable"]
        privateSubnet = resp["privateSubnet"]
        privateSecGroup = resp["privateSecGroup"]
        publicSubnetRouteTable = resp["publicSubnetRouteTable"]
        publicSubnet = resp["publicSubnet"]
        publicSecGroup = resp["publicSecGroup"]
        natGatewayId = resp["natGatewayId"]
        natGatewayElasticIP = resp["natGatewayElasticIP"]
        str1 = "Network has been created. These are the details. VPC: "+str(vpcId)+" | IGW: "+str(igw)+" | privateSubnetRouteTable: "+str(privateSubnetRouteTable)+" | publicSubnetRouteTable: "+str(publicSubnetRouteTable)+" | privateSubnet: "+str(privateSubnet)+" | publicSubnet: "+str(publicSubnet)+" | privateSecGroup: "+str(privateSecGroup)+" | publicSecGroup: "+str(publicSecGroup)+" | natGatewayId: "+str(natGatewayId)+" | natGatewayElasticIP: "+str(natGatewayElasticIP)
        str1 = str1.replace("'", "")
        str1 = str1.replace('"', "")
        #str1 = str1.replace("}", "")
        #str1 = str1.replace("{", "")
        #str1 = str1.replace("'", '"')
    return str(str1)
    

def create_network(event):

        num_vpc = int(event['currentIntent']['slots']['num_vpc'])
        num_subnet_pri = int(event['currentIntent']['slots']['num_subnet_pri'])
        num_subnet_pub = int(event['currentIntent']['slots']['num_subnet_pub'])
        vpc_cidr = "10.10.0.0/16" #event['currentIntent']['slots']['vpc_cidr']
        vpc_name = event['currentIntent']['slots']['vpc_name']
        
        vpc_cidrArr = vpc_cidr.split('.')
        
        AvailabilityZoneArr1 = str(REPLACE_REGION+"a,"+REPLACE_REGION+"b,"+REPLACE_REGION+"c")
        AvailabilityZoneArr = AvailabilityZoneArr1.split(",")

        regex = "(?P<num>.*)\/(?P<num1>.*)"
        #cidr0 = re.search(regex, vpc_cidr)
        #cidr1 = int(cidr0.group("num1"))
        subnetRange = "24"

        for vpc in range(1, (num_vpc+1)):

                #create vpc
                vpcId = createVPC(vpc_cidr,vpc_name+"_"+str(vpc))

                print("Printing vpcId ..................................................................................")
                print(vpcId)
                #exit(1)

                #create internet gateway
                igwId = create_internetGateway()
                tag = vpc_name+"_IGW"
                addTag(str(igwId),tag)

                #attach internet gateway to the vpc
                attach_internetGateway(vpcId,igwId)


                #create route for public subnet
                if num_subnet_pub > 0:
                        routePub = create_routeTable(vpcId)
                        tag = vpc_name+"_publicRouteTable"
                        addTag(str(routePub),tag)

                        secGrPubId = create_securityGroups(vpcId,'public')
                        tag = vpc_name+"_publicSecurityGroup"
                        addTag(str(secGrPubId),tag)


                #create route for private subnet
                if num_subnet_pri > 0:
                        routePri = create_routeTable(vpcId)
                        tag = vpc_name+"_privateRouteTable"
                        addTag(str(routePri),tag)

                        secGrPriId = create_securityGroups(vpcId,'private')
                        tag = vpc_name+"_privateSecurityGroup"
                        addTag(str(secGrPriId),tag)

                        #create eIP for NAT gateway if there are private subnets
                        eIP = create_elasticIP()

                        #securityGroup_addRule(secGrPubId,'tcp','0.0.0.0/0',80,8080)

                print("")
                print("Private Subnets: ..................................................................................")

                #create private subnets
                for sub1 in range(1, (num_subnet_pri+1)):
                    cidr = str(vpc_cidrArr[0])+"."+str(vpc_cidrArr[1])+"."+str(sub1)+".0/"+subnetRange
                    AvailabilityZone = AvailabilityZoneArr[((sub1-1)%3)]
                    subnetId = createSubnet(vpcId,AvailabilityZone,cidr)

                    tag = vpc_name+"_privateSubnet_"+str(sub1)
                    addTag(str(subnetId),tag)
                    pri_sub_arr[(sub1-1)] = subnetId

                    #associate route table to subnet
                    associate_routeTable(subnetId,routePri)

                print("")
                print("Public Subnets: ..................................................................................")

                #create public subnets
                x=0
                for sub2 in range((num_subnet_pri+1), (num_subnet_pri+num_subnet_pub+1)):
                        cidr = str(vpc_cidrArr[0])+"."+str(vpc_cidrArr[1])+"."+str(sub2)+".0/"+subnetRange
                        AvailabilityZone = AvailabilityZoneArr[((sub2-1)%3)]
                        subnetId = createSubnet(vpcId,AvailabilityZone,cidr)

                        print(subnetId)
                        tag = vpc_name+"_publicSubnet_"+str(sub2)
                        addTag(str(subnetId),tag)
                        pub_sub_arr[x] = subnetId
                        x=x+1

                        #associate route table to subnet
                        associate_routeTable(subnetId,routePub)

                        #add the igw route
                        create_route("0.0.0.0/0",igwId,routePub)

                        if sub2 == (num_subnet_pri+1):
                                # associate nat gateway to private subnets
                                natGwID = create_natGateway(str(subnetId),str(eIP))

        #add natGateway to private route table
        #create_route("0.0.0.0/0",str(natGwID),routePri)

        if vpc_flow_log == "YES":
                #create loggroup for flowlogs
                logGroup = '/aws/'+vpc_name+'/flow_log_group'
                create_logGroup(logGroup)

                #create vpc flowlogs
                create_vpcFlowLogs(vpcId,'VPC','ALL',logGroup,'arn:aws:iam::106512724307:role/lambda-ses-test-role-aditya')

        vpc_subnetArr["vpc"] = vpcId
        vpc_subnetArr["igw"] = igwId
        vpc_subnetArr["privateSubnetRouteTable"] = routePri
        vpc_subnetArr["privateSubnet"] = pri_sub_arr
        vpc_subnetArr["privateSecGroup"] = secGrPriId

        vpc_subnetArr["publicSubnetRouteTable"] = routePub
        vpc_subnetArr["publicSubnet"] = pub_sub_arr
        vpc_subnetArr["publicSecGroup"] = secGrPubId

        vpc_subnetArr["natGatewayId"] = natGwID
        vpc_subnetArr["natGatewayElasticIP"] = eIP

        #print(vpc_subnetArr)
        return vpc_subnetArr

def addTag(resourceId,tagValue):
        client = MY_SESSION.resource('ec2')
        print("$########################################")
        print(tagValue)
        print(resourceId)
        response = client.create_tags(DryRun=False,Resources=[resourceId],Tags=[{'Key': 'Name','Value': tagValue}])

def createVPC(cidr,vpc_name):
        #print("")
        #print("inside createVPC")
        client = MY_SESSION.resource('ec2')
        response = client.create_vpc(DryRun=False,CidrBlock=cidr,InstanceTenancy='default')
        addTag(str(response.id),vpc_name)
        
        print("Printing reposne......................................................................")
        print(response)
        
        return response.id

def createSubnet(vpcId,AvailabilityZone,cidr):
        #print("")
        print("inside createSubnet")
        client = MY_SESSION.resource('ec2')
        response = "No valid VPC-ID"
        if(vpcId!=""):
                if(AvailabilityZone==""):
                        AvailabilityZone = str(REPLACE_REGION+"a")
                response = client.create_subnet(DryRun=False,VpcId=vpcId,CidrBlock=cidr,AvailabilityZone=AvailabilityZone)
        return response.id

def create_internetGateway():
        client = MY_SESSION.resource('ec2')
        response = client.create_internet_gateway(DryRun=False)
        return response.id

def attach_internetGateway(vpcId,igwId):
        client = MY_SESSION.resource('ec2')
        vpc = client.Vpc(vpcId)
        response = vpc.attach_internet_gateway(DryRun=False,InternetGatewayId=igwId)
        return response

def create_routeTable(vpcId):
        client = MY_SESSION.resource('ec2')
        response = client.create_route_table(DryRun=False,VpcId=vpcId)
        print("")
        print("Printing routeTable Id: "+str(response.id))
        return response.id


def associate_routeTable(subnetId,routeTableId):
        client = MY_SESSION.client('ec2')
        response = client.associate_route_table(DryRun=False,SubnetId=subnetId,RouteTableId=routeTableId)

def create_route(cidrBlock,igwId,routeTableId):
        print("")
        print("Printing route table..................................................................................")
        print(routeTableId)
        client = MY_SESSION.resource('ec2')
        route_table = client.RouteTable(routeTableId)
        route = route_table.create_route(DryRun=False,DestinationCidrBlock=cidrBlock,GatewayId=igwId)

def create_securityGroups(vpcId,subnetType):
        client = MY_SESSION.resource('ec2')
        groupName = vpcId+"_PublicSecGroup"
        desc = "Public security group for "+vpcId
        if subnetType=="private":
                groupName = vpcId+"_PrivateSecGroup"
                desc = "Private security group for "+vpcId
        response = client.create_security_group(DryRun=False,GroupName=str(groupName),Description=str(desc),VpcId=vpcId)

        return response.id

def securityGroup_addRule(secGroupId,ipProtocol,cidrIp,FromPort,ToPort):
        client = MY_SESSION.client('ec2')
        response = client.authorize_security_group_ingress(DryRun=False,GroupId=secGroupId,IpProtocol=ipProtocol,CidrIp=cidrIp,FromPort=FromPort,ToPort=ToPort)

def create_elasticIP():
        client = MY_SESSION.client('ec2')
        response = client.allocate_address(DryRun=False)
        print("")
        print("Printing repsonse in create elIP.................................................................................")
        print(response)
        return response['AllocationId']

def create_natGateway(subnetId,eIp):
        client = MY_SESSION.client('ec2')
        response = client.create_nat_gateway(SubnetId=subnetId,AllocationId=eIp)
        print("")
        print("Printing in create nat gateway..................................................................................")
        print(response)
        return response["NatGateway"]["NatGatewayId"]

def create_s3Bucket(event):
        acl = event['currentIntent']['slots']['acl']
        aws_region = event['currentIntent']['slots']['aws_region']
        bucket_name = event['currentIntent']['slots']['bucket']

        MY_SESSION = Session(aws_access_key_id=REPLACE_ACCESS_KEY,aws_secret_access_key=REPLACE_SECRET_KEY,region_name=aws_region)

        print("response in create s3 bucket........."+str(bucket_name))

        client = MY_SESSION.client('s3')
        response = client.create_bucket(
                ACL = str(acl),
                Bucket = str(bucket_name),
                CreateBucketConfiguration={
                    'LocationConstraint': str(aws_region)
                }
        )
    
        print("")
        print("############# response in create s3 bucket.........")
        return response

def create_logGroup(groupName):
        client = MY_SESSION.client('logs')
        response = client.create_log_group(
                logGroupName=groupName,
                tags={
                        'Name': groupName
                }
        )
        return response

def create_vpcFlowLogs(resourceId,resourceType,trafficType,logGroupName,arn):
        client = MY_SESSION.client('ec2')
        response = client.create_flow_logs(
                ResourceIds=[
                        resourceId
                ],
                ResourceType = resourceType,            #'VPC'|'Subnet'|'NetworkInterface',
                TrafficType = trafficType,              #'ACCEPT'|'REJECT'|'ALL',
                LogGroupName = logGroupName,            #'string',
                DeliverLogsPermissionArn = arn  #'string'
        )
        print("Printing in VPC Flow Logs .......................................................")
        print(response)
        return response

def describe_vpcs(vpcName):
        client = MY_SESSION.client('ec2')
        resp = ""
        if vpcName=="":
            resp = client.describe_vpcs(DryRun=False)
        else:
            regex1 = "(.*) (?P<vpc>vpc-\d*) (.*)*"
            res = re.search(regex1, vpcName)
            res1 = res.group("vpc")
            print("Printing resppppppppppppppppppppp..................................................... ")
            print(res)
            print(res1)
            resp = client.describe_vpcs(DryRun=False,Filters=[{'Name': 'tag:Name','Values': [vpcName]}])
        print("Printing response in describe_vpcs........................................................")
        print(resp)
        resp = parse_response(resp,"vpc")
        return str(resp)

def describe_vpcs_by_id(vpcId):
    client = MY_SESSION.client('ec2')
    resp = client.describe_vpcs(DryRun=False,VpcIds=[str(vpcId)])
    print("Printing response in describe_vpcs by id........................................................")
    print(resp)
    return resp
    
    
def describe_subnets(subnetName):
        client = MY_SESSION.client('ec2')
        resp = client.describe_subnets(DryRun=False,Filters=[{'Name': 'tag:Name','Values': [subnetName]}])
        print("")
        print("Printing response in describe_subnets........................................................")
        resp = parse_response(resp,"subnet")
        print(resp)
        return str(resp)

def describe_subnets_by_id(subnetId):
    client = MY_SESSION.client('ec2')
    resp = client.describe_subnets(DryRun=False,SubnetIds=[str(subnetId)])
    print("Printing response in describe_subnets by id........................................................")
    print(resp)
    return resp

def describe_security_groups(secGroupName):
        client = MY_SESSION.client('ec2')
        resp = client.describe_security_groups(DryRun=False,Filters=[{'Name': 'tag:Name','Values': [secGroupName]}])
        resp = parse_response(resp,"secGroup")
        print("Printing response in describe_security_groups........................................................")
        print(resp)
        return str(resp)

def describe_secGroups_by_id(secGroupId):
    client = MY_SESSION.client('ec2')
    resp = client.describe_security_groups(DryRun=False,GroupIds=[str(secGroupId)])
    print("Printing response in describe_secGroups by id........................................................")
    print(resp)
    return resp

def parse_response(resp,type):
        str1 = ""
        if type == "secGroup":
                str1 += "IpPermissionsEgress: "+ str(resp["SecurityGroups"][0]["IpPermissionsEgress"])
                str1 += "Description: "+ str(resp["SecurityGroups"][0]["Description"])
                str1 += "Tags: "+ str(resp["SecurityGroups"][0]["Tags"][0])
                str1 += "VpcId: "+ str(resp["SecurityGroups"][0]["VpcId"])
                str1 += "GroupId: "+ str(resp["SecurityGroups"][0]["GroupId"])
                    
        elif type == "subnet":
                str1 += "SubnetId: "+ str(resp["Subnets"][0]["SubnetId"])
                str1 += " | State: "+ str(resp["Subnets"][0]["State"])
                str1 += " | VpcId: "+ str(resp["Subnets"][0]["VpcId"])
                str1 += " | CidrBlock: "+ str(resp["Subnets"][0]["CidrBlock"])
                str1 += " | AvailableIpAddressCount: "+ str(resp["Subnets"][0]["AvailableIpAddressCount"])
                str1 += " | AvailabilityZone: "+ str(resp["Subnets"][0]["AvailabilityZone"])
                str1 += " | Tags: "+ str(resp["Subnets"][0]["Tags"])

        elif type == "vpc":
                str1 += "VPC ID: "+ str(resp["Vpcs"][0]["VpcId"])
                str1 += " | State: "+ str(resp["Vpcs"][0]["State"])
                str1 += " | CidrBlock: "+ str(resp["Vpcs"][0]["CidrBlock"])
                str1 += " | Tags: "+ str(resp["Vpcs"][0]["Tags"])
                str1 += " | InstanceTenancy: "+ str(resp["Vpcs"][0]["InstanceTenancy"])

        return str(str1)
        
#response = describe_vpcs(vpc_name)
#response = describe_subnets('adi_test_vpc_publicSubnet')
#response = describe_security_groups('adi_test_vpc_privateSecurityGroup')
