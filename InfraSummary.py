import os, sys, datetime
#import xlwt
import boto3
import csv
import re
import json
from boto3.session import Session
from operator import itemgetter

client = ""
now = datetime.datetime.now()

def lambda_handler(event, context):
    # TODO implement
    
    REPLACE_ACCESS_KEY = "AKIAIYA5FOJETXNSR44A"
    REPLACE_SECRET_KEY = "fSNSRITP9yvmuomn795KJCrn+UarN/Ag+A0DdN+p"
    #REPLACE_REGION = "eu-west-1"
    REPLACE_REGION = str(event['currentIntent']['slots']['region'])

    MY_SESSION = Session(aws_access_key_id=REPLACE_ACCESS_KEY,aws_secret_access_key=REPLACE_SECRET_KEY,region_name=REPLACE_REGION)
    client = MY_SESSION.resource("iam", aws_access_key_id=REPLACE_ACCESS_KEY, aws_secret_access_key=REPLACE_SECRET_KEY)
    aws_account_id = client.CurrentUser().arn.split(':')[4]
    
    response = ""
    resp1 = ""
    resp = ""
    routeTableArr =  []
    
    css = """<style> 
    			table,tr,td 
    			{ 
    				font-family:Arial;
    				font-size:10pt;
    				border:1px solid #000;
    				border-spacing: 0px;
    				border-collapse: collapse;
    				padding:3px;
    			} 
    			.header{
    				font-family:Arial;
    				font-size:10pt;
    				background-color:#ccc;
    				color:black;
    				font-weight:bold;
    			}
    			span{
    				font-family:Arial;
    				font-size:10pt;			
    			}
    		</style>"""
    
    purText = "<span><b>1. Purpose/Scope of this Document</b><br><br>This document outlines the infrastructure that is in use by the client (SSI ) and provides instructions and information on the infrastructure hosted out of Amazon Web Services (AWS).<br><br><table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'><tr class = 'header'><td width='33%'>Application/Website</td><td width = '33%'>Technology Stack</td><td width = '33%'>Framework</td></tr><td></td><td></td><td></td></table><br>The document is not intended to be a training guide and it is important that the audience has an understanding of Linux System Administration & AWS Services</span>"
    audText = "<span><b>2. Audience</b><br><br>The intended audience for this document are the following stake holders: <br><b>a.</b> Infrastructure Support Staff: Individuals monitoring server up time, availability and routine maintenance of the servers.<br><b>b.</b> Developers: To have an understanding of the overall infrastructure.</span>"
    arcText = "<span><b>3. Architecture Summary</b><br><br>Provided below is a high level schematic over-view of the various components of the corporate website portal. The number of components may increase or decrease as development progresses.</span>"
    serText = "<span><b>4. Services Used</b><br><br><table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'><tr><td width = '50%' class = 'header'>Services</td><td class = 'header'>Service Provider</td></tr><tr><td>Domain Registrar</td><td></td></tr><tr><td>DNS Services</td><td></td></tr><tr><td>Load Balancer</td><td></td></tr><tr><td>Infrastructure Hosting</td><td></td></tr><tr><td>Management Interface</td><td></td></tr></table></span>"
    accText = "<span><b>5. AWS Account Information</b><br><br><table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'><tr><td colspan = '2' class = 'header'>Instance Information</td></tr><tr><td width='50%'>Regions</td><td></td></tr><tr><td>Account ID</td><td>"+aws_account_id+"</td></tr></table><span>"
    vpcText = "<span><b>6. Virtual Private Cloud</b><br><br> Amazon Virtual Private Cloud (Amazon VPC) enables you to launch Amazon Web Services (AWS) resources into a virtual network that you've defined. This virtual network closely resembles a traditional network that would otherwise operate in a data center, with the benefits of using the scalable infrastructure of AWS. The Virtual Private cloud is created in AWS to ensure other servers are not able to access our servers which are in AWS.<span>"
    netText = "<span><b>7. Network Information</b><span><br><br>"
    s3Text =  "<span><b>10. Amazon S3</b></span><br><br>"
    iamText = "<span><b>11. IAM </b></span><br><br>"
    
    vpc_subnetArr = {}
    pub_sub_arr = {}
    pri_sub_arr = {}
    
    
    def describe_vpcs(vpcName,vpcId):
    	client = MY_SESSION.client('ec2')
    	resp = ""
    	if vpcId!="" and vpcName=="":
    		resp = client.describe_vpcs(DryRun=False,VpcIds=[str(vpcId)])
    	elif vpcId=="" and vpcName!="":
    		resp = client.describe_vpcs(DryRun=False,Filters=[{'Name': 'tag:Name','Values': [vpcName]}])
    	else:
    		resp = client.describe_vpcs(DryRun=False)
    	print("Printing response in describe_vpcs........................................................")
    	#print(resp)
    	return resp
    
    def describe_subnets():
    	client = MY_SESSION.client('ec2')
    	resp = client.describe_subnets(DryRun=False)
    	print("Printing response in describe_subnets........................................................")
    	#print(resp)
    	return resp
    
    def describe_security_groups():
    	client = MY_SESSION.client('ec2')
    	resp = client.describe_security_groups(DryRun=False)
    	print("Printing response in describe_security_groups........................................................")
    	#print(resp)
    	return resp
    
    #f = open('aws_resources.doc','w')
    
    str1 = css
    	
    ################ get all regions
    client = MY_SESSION.client('ec2')
    regions = client.describe_regions()
    response2 = describe_subnets()
    response3 = describe_security_groups()
    
    strVPC = ""
    strSub = """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    		<tr>
    			<td colspan = '2' class = 'header'>
    				<b>Infrastructure Information</b>
    			</td>
    		</tr>"""
    strRout = ""
    strRDS= ""
    
    for val in regions["Regions"]:
    	#if val["RegionName"] == "eu-west-1" or val["RegionName"] == "us-east-1":
    	if val["RegionName"] == REPLACE_REGION:
    		REPLACE_REGION = val["RegionName"]
    		strVPC += "<b>Region: </b>"+str(REPLACE_REGION)+"<br><br>"
    		MY_SESSION = Session(aws_access_key_id=REPLACE_ACCESS_KEY,aws_secret_access_key=REPLACE_SECRET_KEY,region_name=REPLACE_REGION)
    		
    		################ get VPCS
    		response1 = describe_vpcs('','')
    		for val in response1["Vpcs"]:
    			VpcId = val["VpcId"]
    			InstanceTenancy = val["InstanceTenancy"]
    			State = val["State"]
    			DhcpOptionsId = val["DhcpOptionsId"]
    			CidrBlock = val["CidrBlock"]
    			IsDefault = val["IsDefault"]
    
    			client1 = MY_SESSION.client('ec2')
    			vpcResp = client1.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id','Values': [VpcId]}])
    			InternetGatewayId = vpcResp['InternetGateways'][0]['InternetGatewayId']
    			InternetGatewayName = ""
    			if 'Tags' in vpcResp["InternetGateways"][0]:
    				for igVal in vpcResp["InternetGateways"][0]["Tags"]:
    					tagKey1 = igVal["Key"]
    					tagVal1 = igVal["Value"]
    					if tagKey1 == "Name":
    						InternetGatewayName = tagVal1
    						
    			VPCName = ""
    			vpcTagArr = []
    			if 'Tags' in val:
    				for val1 in val["Tags"]:
    					tagKey = val1["Key"]
    					tagVal = val1["Value"]
    					if tagKey == "Name":
    						VPCName = tagVal
    					tag = tagKey+" | "+tagVal
    					vpcTagArr.append(tag)
    					
    			strVPC +="""<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    			<tr>
    				<td colspan = '2' class = 'header'>
    					<b>VPC Details </b>
    				</td>
    			</tr>
    			<tr>
    				<td width = '50%'>
    					Type
    				</td>
    				<td>
    					On Demand
    				</td>
    			</tr>
    			<tr>
    				<td>
    					VPC Name
    				</td>
    				<td>
    					"""+str(VPCName)+"""
    				</td>
    			</tr>
    			<tr>
    				<td>
    					VPC ID
    				</td>
    				<td>
    					"""+str(VpcId)+"""
    				</td>
    			</tr>
    			<tr>
    				<td>
    					VPC CIDR
    				</td>
    				<td>
    					"""+str(CidrBlock)+"""
    				</td>
    			</tr>
    			<tr>
    				<td>
    					Internet Gateway
    				</td>
    				<td>
    					"""+str(InternetGatewayName)+""" | """ +str(InternetGatewayId)+ """
    				</td>
    			</tr>
    			</table><br>
    			"""
    
    		################ get Subnets
    		#for subVal in response2["Subnets"]:
    		prevAZ = ""
    		for subVal in sorted (response2["Subnets"], key=itemgetter ('AvailabilityZone')):
    			subNetName = ""
    			SubnetId1 = subVal["SubnetId"]
    			State1 = subVal["State"]
    			CidrBlock1 = subVal["CidrBlock"]
    			AvailableIpAddressCount1 = subVal["AvailableIpAddressCount"]
    			AvailabilityZone1 = subVal["AvailabilityZone"]
    			subnetTagArr = []
    			
    			################ get Route Table Details
    			routeResp = client.describe_route_tables(Filters=[{'Name': 'association.subnet-id','Values': [SubnetId1]}])
    			routeTableName = ""
    			routeTableID = ""
    			
    			sn=0
    			if len(routeResp['RouteTables'])>0:
    				if 'RouteTableId' in routeResp['RouteTables'][0]:
    					routeTableID = routeResp['RouteTables'][0]['RouteTableId']
    					routeTableArr.append(routeTableID)
    					sn=sn+1
    					if 'Tags' in routeResp['RouteTables'][0]:
    						for routeVal in routeResp['RouteTables'][0]['Tags']:
    							tagKey = routeVal["Key"]
    							tagVal = routeVal["Value"]
    							if tagKey == "Name":
    								routeTableName = tagVal
    			#exit(1)
    							
    			if 'Tags' in subVal:
    				for subVal1 in subVal["Tags"]:
    					tagKey = subVal1["Key"]
    					tagVal = subVal1["Value"]
    					if tagKey == "Name":
    						subNetName = tagVal
    						
    					tag = tagKey+" | "+tagVal
    					subnetTagArr.append(tag)
    					
    					if prevAZ != AvailabilityZone1:
    						strSub += """<tr>
    							<td width = '50%' class = 'header'>
    								Availability Zone
    							</td>
    							<td class = 'header'>
    								"""+AvailabilityZone1+"""
    							</td>
    						</tr>"""
    					else:
    						strSub += """<tr>
    							<td colspan = '2'>
    								
    							</td>
    						</tr>"""
    					strSub += """<tr>
    						<td width = '50%'>
    							Subnet Name
    						</td>
    						<td>
    							"""+subNetName+"""
    						</td>
    					</tr>
    					<tr>
    						<td width = '50%'>
    							Subnet ID
    						</td>
    						<td>
    							"""+SubnetId1+"""
    						</td>
    					</tr>
    					<tr>
    						<td width = '50%'>
    							Subnet Route Table Name
    						</td>
    						<td>
    							"""+routeTableName+"""
    						</td>
    					</tr>
    					<tr>
    						<td width = '50%'>
    							Subnet Route Table ID
    						</td>
    						<td>
    							"""+routeTableID+"""
    						</td>
    					</tr>
    					<tr>
    						<td width = '50%'>
    							Subnet CIDR
    						</td>
    						<td>
    							"""+CidrBlock1+"""
    						</td>
    					</tr>"""
    			prevAZ = AvailabilityZone1		
    			
    		for routeTVal in routeTableArr:
    			routeTableName = ""
    			routeTableID = ""
    			responseRoute = client.describe_route_tables(DryRun=False, RouteTableIds=[routeTVal])
    			if len(responseRoute['RouteTables'])>0:
    				if 'RouteTableId' in responseRoute['RouteTables'][0]:
    					routeTableID1 = responseRoute['RouteTables'][0]['RouteTableId']
    					if 'Tags' in responseRoute['RouteTables'][0]:
    						for routeVal1 in responseRoute['RouteTables'][0]['Tags']:
    							tagKey = routeVal1["Key"]
    							tagVal = routeVal1["Value"]
    							if tagKey == "Name":
    								routeTableName1 = tagVal
    			
    			strRout += """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    			<tr>
    				<td colspan = '2' class = 'header'>
    					<b>	"""+routeTableName1+""" - Route Table Information </b>
    				</td>
    			</tr>"""
    			
    			for routeVal2 in responseRoute['RouteTables'][0]['Routes']:
    				GatewayId2 = ""
    				DestinationCidrBlock2 = ""
    				State2 = ""
    				Origin2 = ""
    				if 'GatewayId' in routeVal2:
    					GatewayId2 = routeVal2["GatewayId"]
    					DestinationCidrBlock2 = routeVal2["DestinationCidrBlock"]
    					State2 = routeVal2["State"]
    					Origin2 = routeVal2["Origin"]
    					strRout += """<tr>
    							<td width = '50%'>
    								Network Destination
    							</td>
    							<td>
    								<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '100%'>
    									<tr>
    										<td width = '50%'> 
    											"""+GatewayId2+"""
    										</td>
    										<td>
    											"""+DestinationCidrBlock2+"""
    										</td>
    									</tr>
    									<tr>
    										<td>
    											"""+DestinationCidrBlock2+"""
    										</td>
    										<td>
    											"""+Origin2+"""
    										</td>
    									</tr>
    								</table>
    							</td>
    						</tr>
    						<tr>
    							<td>
    								Status
    							</td>
    							<td>
    								"""+State2+"""
    							</td>
    						</tr>"""
    			strRout += "</table><br>"
    		
    		#8. ELB
    		strELB = """<span><b>8.AWS Web Load Balancer</b></span><br><br>"""
    		client1 = MY_SESSION.client('elb')
    		responseELB = client1.describe_load_balancers()
    		for elb in responseELB['LoadBalancerDescriptions']:
    			elbDNSName = str(elb['DNSName'])
    			elbScheme = str(elb['Scheme'])
    			elbStatus = ""
    			elbPort_Configuration = str(elb['ListenerDescriptions'])
    			elbAvailability_Zones = str(elb['AvailabilityZones'])
    			elbSecurity_Group_Name = str(elb['SecurityGroups'][0])
    			elbTarget_Timeout_Interval = str(elb['HealthCheck']['Target']) + " / " + str(elb['HealthCheck']['Timeout']) + "secs / " + str(elb['HealthCheck']['Interval'])+"secs"
    			elbUnhealthy_Healthy_threshold = str(elb['HealthCheck']['UnhealthyThreshold']) + " / " + str(elb['HealthCheck']['HealthyThreshold'])
    			elbSecurityGroupID = str(elb['SecurityGroups'][0])
    			elbSecurityGroupName = str(elb['SourceSecurityGroup']['GroupName'])
    
    			strELB += """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '2' class = 'header'>
    							<b>AWS Elastic Load Balancer Information</b>
    						</td>
    					</tr>"""
    			strELB += """<tr><td>DNS Name</td><td>"""+elbDNSName+"""</td></tr>"""
    			strELB += """<tr><td>Scheme</td><td>"""+elbScheme+"""</td></tr>"""
    			strELB += """<tr><td>Status</td><td>"""+elbStatus+"""</td></tr>"""
    			strELB += """<tr><td>Port Configuration</td><td>"""+elbPort_Configuration+"""</td></tr>"""
    			strELB += """<tr><td>Availability Zones</td><td>"""+elbAvailability_Zones+"""</td></tr>"""
    			strELB += """<tr><td>Security Group Name</td><td>"""+elbSecurity_Group_Name+"""</td></tr>"""
    			strELB += """<tr><td>Target / Time out / Interval</td><td>"""+elbTarget_Timeout_Interval+"""</td></tr>"""
    			strELB += """<tr><td>Unhealthy / Healthy threshold</td><td>"""+elbUnhealthy_Healthy_threshold+"""</td></tr>"""
    			temp = ""
    
    			#sec groups
    			s1 = []
    			s1.append(elbSecurityGroupID)
    			client1 = MY_SESSION.client('ec2')
    			elbSGData = client1.describe_security_groups(GroupIds=s1)
    				
    			strELB += """<tr>
    						<td colspan = '2' class = 'header'>
    							<b>Security Group</b>
    						</td>
    					</tr>
    					<tr><td>Group name</td><td>"""+elbSecurityGroupID+"""</td></tr>
    					<tr><td>Group ID</td><td>"""+elbSecurityGroupName+"""</td></tr>
    				</table>
    				<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '5' class = 'header'>
    							<b>In Bound Rules</b>
    						</td>
    					</tr>
    					<tr><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td></tr>					
    				</table>
    				<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '4' class = 'header'>
    							<b>Out Bound Rules</b>
    						</td>
    					</tr>
    					<tr><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td></tr>					
    				</table><br><br>"""
    		
    		#9. EC2
    		strEc2 = """<span><b>9. Amazon - Ec2</b></span><br><br>"""
    		client1 = MY_SESSION.client('ec2')
    		responseEc2 = client1.describe_instances()
    		for ec2 in responseEc2['Reservations']:
    			
    			ec2type = ec2['Instances'][0]['InstanceType']
    			ec2OS = ""
    			ec2instanceNameArr = ""
    			ec2instanceName = ""
    			if 'Tags' in ec2['Instances'][0]:
    				ec2instanceNameArr = ec2['Instances'][0]['Tags']
    				for ec2Tags in ec2instanceNameArr:
    					if ec2Tags['Key'] == "Name":
    						ec2instanceName = ec2Tags['Value']
    
    			strEc2 += """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    			<tr>
    				<td colspan = '2' class = 'header'>
    					<b>"""+ec2instanceName+"""</b>
    				</td>
    			</tr>
    			<tr>
    				<td colspan = '2' class = 'header'>
    					<b>Instance Information</b>
    				</td>
    			</tr>"""
    
    			ec2imageType = ec2['Instances'][0]['ImageId']
    			ec2AZ = ec2['Instances'][0]['Placement']['AvailabilityZone']
    			ec2instanceType = ec2['Instances'][0]['InstanceType']
    			ec2instanceID = ec2['Instances'][0]['InstanceId']
    			ec2serverPubIP = "" 
    			ec2serverPubURL = ""
    			if 'Association' in ec2['Instances'][0]['NetworkInterfaces'][0]:
    				ec2serverPubIP = ec2['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
    				ec2serverPubURL = ec2['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicDnsName']
    			ec2serverLocalIP = ec2['Instances'][0]['PrivateIpAddress']
    			ec2launchTime = ec2['Instances'][0]['LaunchTime']
    			ec2accessMode = ""
    			ec2SecurityGroupID = ec2['Instances'][0]['SecurityGroups'][0]['GroupId']
    			
    			strEc2 += """<tr><td>Type</td><td>"""+str(ec2type)+"""</td></tr>"""
    			strEc2 += """<tr><td>Operating System</td><td>"""+str(ec2OS)+"""</td></tr>"""
    			strEc2 += """<tr><td>Instance Name</td><td>"""+str(ec2instanceName)+"""</td></tr>"""
    			strEc2 += """<tr><td>Image Type (AMI ID)</td><td>"""+str(ec2imageType)+"""</td></tr>"""
    			strEc2 += """<tr><td>Availability Zone</td><td>"""+str(ec2AZ)+"""</td></tr>"""
    			strEc2 += """<tr><td>Instance type</td><td>"""+str(ec2instanceType)+"""</td></tr>"""
    			strEc2 += """<tr><td>Instance ID</td><td>"""+str(ec2instanceID)+"""</td></tr>"""
    			strEc2 += """<tr><td>Server Public IP</td><td>"""+str(ec2serverPubIP)+"""</td></tr>"""
    			strEc2 += """<tr><td>Server Public URL</td><td>"""+str(ec2serverPubURL)+"""</td></tr>"""
    			strEc2 += """<tr><td>Server local IP</td><td>"""+str(ec2serverLocalIP)+"""</td></tr>"""
    			strEc2 += """<tr><td>Launch Time</td><td>"""+str(ec2launchTime)+"""</td></tr>"""
    			strEc2 += """<tr><td>Access mode</td><td>"""+str(ec2accessMode)+"""</td></tr>"""
    			strEc2 += "</table>"
    			
    			#sec groups
    			s2 = []
    			s2.append(ec2SecurityGroupID)
    			client1 = MY_SESSION.client('ec2')
    			temp = ""
    			ec2SGData = client1.describe_security_groups(GroupIds=s2)
    				
    			strEc2 += """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '2' class = 'header'>
    							<b>Security Group Details</b>
    						</td>
    					</tr>
    					<tr><td>Group name</td><td>"""+elbSecurityGroupID+"""</td></tr>
    					<tr><td>Group ID</td><td>"""+elbSecurityGroupName+"""</td></tr>
    				</table>
    				<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '5' class = 'header'>
    							<b>In Bound Rules</b>
    						</td>
    					</tr>
    					<tr><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td></tr>					
    				</table>
    				<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '4' class = 'header'>
    							<b>Out Bound Rules</b>
    						</td>
    					</tr>
    					<tr><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td></tr>					
    				</table><br><br>"""
    
    		
    		#13. cloudtrail
    		strTrail = """<span><b>13. Amazon - CloudTrail</b></span><br><br><table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '2' class = 'header'>
    							<b>Cloud-Trail Configuration</b>
    						</td>
    					</tr>"""
    		client1 = MY_SESSION.client('cloudtrail')
    		responseTrail = client1.describe_trails()
    		for trail in responseTrail['trailList']:
    			trailName = trail['Name']
    			trailS3BucketName = trail['S3BucketName']
    			trailHomeRegion = REPLACE_REGION
    			strTrail += """<tr><td>Name</td><td>"""+trailName+"""</td></tr>"""
    			strTrail += """<tr><td>Region</td><td>"""+trailHomeRegion+"""</td></tr>"""
    			strTrail += """<tr><td>S3 Bucket</td><td>"""+trailS3BucketName+"""</td></tr>"""
    		strTrail += "</table>"
    
    		#12. rds
    		client1 = MY_SESSION.client('rds')
    		responseRDS = client1.describe_db_instances()
    		for rds in responseRDS['DBInstances']:
    			rdsType = "RDS"
    			rdsEngineVer = str(rds['Engine'])+ " " +str(rds['EngineVersion'])
    			rdsInsClass = rds['DBInstanceClass']
    			rdsAZ = rds['MultiAZ']
    			rdsStorageType = rds['StorageType']
    			rdsAllocStorage = rds['AllocatedStorage']
    			rdsPubURL = str(rds['Endpoint']['Address']) + ":" + str(rds['Endpoint']['Port'])
    			rdsCreatedTime = rds['InstanceCreateTime']
    			rdsDBName = rds['DBName']
    			rdsSecurityGroupID = rds['VpcSecurityGroups'][0]['VpcSecurityGroupId']
    			rdsSecurityGroupName = ""
    			if 'DBSecurityGroupName' in rds['DBSecurityGroups']:
    				rdsSecurityGroupName = rds['DBSecurityGroups']['DBSecurityGroupName']
    			
    			strRDS = """<span><b>12. Amazon - RDS</b></span><br><br><table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '2' class = 'header'>
    							<b>RDS: """+str(rdsDBName)+"""</b>
    						</td>
    					</tr>"""
    			strRDS += """<tr><td>Type</td><td>"""+str(rdsType)+"""</td></tr>"""
    			strRDS += """<tr><td>DB Engine Version</td><td>"""+str(rdsEngineVer)+"""</td></tr>"""
    			strRDS += """<tr><td>DB Instance Class</td><td>"""+str(rdsInsClass)+"""</td></tr>"""
    			strRDS += """<tr><td>Multi-AZ Deployment</td><td>"""+str(rdsAZ)+"""</td></tr>"""
    			strRDS += """<tr><td>Storage Type</td><td>"""+str(rdsStorageType)+"""</td></tr>"""
    			strRDS += """<tr><td>Allocated Storage</td><td>"""+str(rdsAllocStorage)+"""</td></tr>"""
    			strRDS += """<tr><td>Server Public URL</td><td>"""+str(rdsPubURL)+"""</td></tr>"""
    			strRDS += """<tr><td>Created Time</td><td>"""+str(rdsCreatedTime)+"""</td></tr>"""
    			strRDS += "</table>"
    			
    			#sec groups
    			s3 = []
    			s3.append(rdsSecurityGroupID)
    			client1 = MY_SESSION.client('ec2')
    			temp = ""
    			rdsSGData = client1.describe_security_groups(GroupIds=s3)
    				
    			strRDS += """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '2' class = 'header'>
    							<b>Security Group Details</b>
    						</td>
    					</tr>
    					<tr><td>Group name</td><td>"""+rdsSecurityGroupID+"""</td></tr>
    					<tr><td>Group ID</td><td>"""+rdsSecurityGroupName+"""</td></tr>
    				</table>
    				<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '5' class = 'header'>
    							<b>In Bound Rules</b>
    						</td>
    					</tr>
    					<tr><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td></tr>					
    				</table>
    				<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    					<tr>
    						<td colspan = '4' class = 'header'>
    							<b>Out Bound Rules</b>
    						</td>
    					</tr>
    					<tr><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td><td>"""+temp+"""</td></tr>					
    				</table><br><br>"""
    
    			
    # 10. Get S3 Buckets
    strS3 = """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    			<tr>
    				<td colspan = '2' class = 'header'>
    					<b>	S3 Bucket Details </b>
    				</td>
    			</tr>"""
    client = MY_SESSION.client('s3')
    responseS3 = client.list_buckets()
    sn=0;
    for bucket in responseS3['Buckets']:
    	sn = sn + 1
    	bucketName = bucket['Name']
    	CreationDate = bucket['CreationDate']
    	strS3 += """<tr><td width = '50%'><b>S3 Bucket """+str(sn)+"""</b></td><td>"""+str(bucketName)+"""</td></tr>
    			<tr><td>Region</td><td></td></tr>
    			<tr><td>Owner</td><td></td></tr>
    			<tr><td>Creation Date</td><td>"""+str(CreationDate)+"""</td></tr>"""
    strS3 += "</table>"
    			
    			
    # 11. Get IAM Users
    strIAM = """<table border = '1px' cellpadding = '0px' cellspacing = '0px' width = '90%'>
    			<tr>
    				<td colspan = '5' class = 'header'>
    					<b>	IAM Information</b>
    				</td>
    			</tr>"""
    client = MY_SESSION.client('iam')
    responseIAM = client.list_users()
    strIAM += """<tr class = 'header'><td width = '50%'><b>Username</b></td><td>Password</td><td>Access Key</td><td>Secret Key</td><td>MFA</td></tr>"""
    for user in responseIAM['Users']:
    	userName = user['UserName']
    	strIAM += """<tr><td>"""+userName+"""</td><td></td><td></td><td></td></tr>"""
    strIAM += "</table>"
    
    str1 += purText+"<br><br>"
    str1 += audText+"<br><br>"
    str1 += arcText+"<br><br>"
    str1 += serText+"<br><br>"
    str1 += accText+"<br><br>"
    str1 += vpcText+"<br><br>"+strVPC+"<br><br>"
    str1 += netText+"<br><br>"+strSub+"</table><br><br>"
    str1 += strRout+"</table><br><br>"
    str1 += strELB+"<br><br>"
    str1 += strEc2+"<br><br>"
    str1 += strRDS+"<br><br>"
    str1 += s3Text+"<br><br>"+strS3+"<br><br>"
    str1 += iamText+"<br><br>"+strIAM+"<br><br>"
    str1 += strTrail+"<br><br>"
    
    #f.write(str1)
    #f.close()
    fileName = writeToS3(str1,MY_SESSION)
    fileName = "Please open this link in a new tab to download the file: https://s3.amazonaws.com/aditya.bhangle/"+fileName
    print(fileName)
    resp = {"dialogAction": { "type": "Close", "fulfillmentState": "Fulfilled", "message": { "contentType": "PlainText", "content": str(fileName) } } }
    return resp

def writeToS3(str1,MY_SESSION):
    s3 = MY_SESSION.resource('s3')
    keyVal = "InfraSummary-"+str(now)+".doc"
    s3.Bucket('aditya.bhangle').put_object(Key=keyVal, Body=str1, ACL='public-read')
    return keyVal
    
    
