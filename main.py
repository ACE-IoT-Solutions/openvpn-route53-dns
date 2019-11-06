import boto3
import os
import ipaddress
import time

r53 = boto3.client('route53')

# results = r53.get_hosted_zone(Id='aceiot.cloud.')
def get_hosted_zone_id(name, private=True):
    results = r53.list_hosted_zones_by_name()
    for result in results['HostedZones']:
        if result['Name'] == name and result['Config']['PrivateZone'] is private:
            return result['Id']

def get_records():
    results = r53.list_hosted_zones_by_name()
    for result in results['HostedZones']:
        if result['Name'] == 'aceiot.cloud.' and result['Config']['PrivateZone'] is True:
            HZ = r53.get_hosted_zone(Id=result['Id'])

    return r53.list_resource_record_sets(HostedZoneId=HZ['HostedZone']['Id'])['ResourceRecordSets']

def get_edge_hosts():
    ips = []
    for root, subdirs, files in os.walk('/etc/openvpn/vpn.aceiot.cloud-ccd'):
        for path in files:
            with open(os.path.join(root, path), 'r') as f:
                if path != 'energy_data_test':
                    name_parts = path.split('-')
                    hostname = f"{name_parts[1].replace('_', '-')}.{name_parts[0]}"
                    for line in f:
                        segments = line.split()
                        if len(segments) > 2 and  segments[0] == 'ifconfig-push':
                            ips.append((hostname, ipaddress.ip_address(segments[1])))
    return ips

def get_edge_ips():
    ips = []
    for root, subdirs, files in os.walk('/etc/openvpn/vpn.aceiot.cloud-ccd'):
        for path in files:
            with open(os.path.join(root, path), 'r') as f:
                for line in f:
                    segments = line.split()
                    if len(segments) > 2 and  segments[0] == 'ifconfig-push':
                        ips.append(ipaddress.ip_address(segments[1]))
    return ips

def create_a_change_batch(hosts):
    ChangeBatch = {
        'Comment': "openvpn hosts update",
        'Changes': []
    }
    for host, ip in hosts:
        ChangeBatch['Changes'].append(
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': f"{host}.clients.aceiot.cloud.",
                    'Type': 'A',
                    'TTL': 300,
                    'ResourceRecords': [
                        {"Value": f"{ip}"}]
                }
            })
    return ChangeBatch

def create_srv_record_set(hosts):
    record_set = {
        'Name': "_prom-edge._tcp.aceiot.cloud.",
        'Type': 'SRV',
        'TTL': 300,
        'ResourceRecords': []
    }
    for host, ip in hosts:
        record_set['ResourceRecords'].append({
            "Value": f"0 100 9100 {host}.clients.aceiot.cloud"
        })
    return record_set


def set_change_batch(change_batch, zone_id):
    return r53.change_resource_record_sets(

        HostedZoneId=zone_id,
        ChangeBatch=change_batch)

def set_record_set(record_set, zone_id):
    return r53.change_resource_record_sets(

        HostedZoneId=zone_id,
        ChangeBatch={
            'Comment': "openvpn update",
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': record_set
                }
            ]
        })



if __name__ == '__main__':
    zid = get_hosted_zone_id('aceiot.cloud.', private=True)
    while True:
        try:
            hosts = get_edge_hosts()
            records = create_srv_record_set(hosts)
            results = set_record_set(records, zid)
            print(results)
            changes = create_a_change_batch(hosts)
            results = set_change_batch(changes, zid)
            print(results)

            waiter = r53.get_waiter('resource_record_sets_changed')
            waiter.wait(Id=results['ChangeInfo']['Id'])
            print('Successful update')
        except Exception as e:
            raise e
            pass
        time.sleep(300)

