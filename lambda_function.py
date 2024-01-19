import boto3

def send_sns_notification(topic_arn, subject, message):
    sns_client = boto3.client('sns')
    sns_client.publish(TopicArn=topic_arn, Subject=subject, Message=message)

def lambda_handler(event, context):
    sns_topic_arn = 'arn:aws:sns:ap-south-1:470949216523:MYSNS'
    ec2_regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]

    for region in ec2_regions:
        ec2 = boto3.client('ec2', region_name=region)

        response = ec2.describe_snapshots(OwnerIds=['self'])
        instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        active_instance_ids = set()

        for reservation in instances_response['Reservations']:
            for instance in reservation['Instances']:
                active_instance_ids.add(instance['InstanceId'])

        for snapshot in response['Snapshots']:
            snapshot_id = snapshot['SnapshotId']
            volume_id = snapshot.get('VolumeId')

            if not volume_id or (volume_id and volume_id not in active_instance_ids):
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                send_sns_notification(sns_topic_arn, f'EBS Snapshot Deleted in {region}', f"Deleted EBS snapshot {snapshot_id} in the {region} region as it was not attached to any volume or its associated volume was not attached to a running instance.")
