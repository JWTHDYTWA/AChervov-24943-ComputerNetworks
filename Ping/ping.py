import subprocess
import csv
import re


ADDRESSES = [
    'google.com',
    'gosuslugi.ru',
    'youtube.com',
    'reddit.com',
    'hh.ru',
    'habr.com',
    'metanit.com',
    'mangalib.me',
    'curseforge.com',
    'modrinth.com'
]

PATTERN_IP = R'\[(\d+\.\d+\.\d+\.\d+)\]'
PATTERN_PACK = R'получено = (\d+), потеряно = (\d+)'
PATTERN_TIME = R'Среднее = (\d+)'


def main():
    output = []

    for address in ADDRESSES:
        print(f'Site: {address}')
        result = subprocess.run(
            ['ping', address],
            capture_output=True,
            text=True,
            encoding='CP866')
        ip = re.findall(PATTERN_IP, result.stdout)[0]
        print(ip)
        try:
            packages = re.findall(PATTERN_PACK, result.stdout)[0]
            print(packages)
            round_travel_time = re.findall(PATTERN_TIME, result.stdout)[0]
            print(round_travel_time)
            output.append({
                'Domain Name': address,
                'IP': ip,
                'Packages received': packages[0],
                'RTT': round_travel_time
                })
        except Exception as e:
            print('No packages received')
            output.append({
                'Domain Name': address,
                'IP': ip,
                'Packages received': 0,
                'RTT': 'NaN'
                })

    with open('pings.csv', 'w') as file:
        csv_writer = csv.DictWriter(
            file,
            fieldnames=['Domain Name', 'IP', 'Packages received', 'RTT'],
            lineterminator='\n')
        csv_writer.writeheader()
        csv_writer.writerows(output)


if __name__ == '__main__':
    main()
