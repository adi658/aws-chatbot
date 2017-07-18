def lambda_handler(event, context):
    # TODO implement
    print(event)
    resp = ""
    resp1 = ""
    if event['currentIntent']['name'] == "general_dis":
        opt = event['currentIntent']['slots']['general_service']
        if opt == "Infrastructure Summary Document Creation":
            resp1 = "I can create an infra summary document for {aws_region}"
        elif opt == "Network Creation":
            resp1 = "I can create a network with {vpc_count} vpc {public/private_subnets_count) public/private subnets"
        else: 
            resp1 = "I can create a bucket for you with {bucketName} and some other options."
        resp = {"dialogAction": {"type": "Close", "fulfillmentState": "Fulfilled", "message": {"contentType": "PlainText", "content": resp1 } } }
    return resp