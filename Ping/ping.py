import subprocess
import csv
import re

addresses = [
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
    output = [['Domain Name', 'IP', 'Packages received', 'RTT']]

    for address in addresses:
        print(f'Site: {address}')
        result = subprocess.run(['ping', address], capture_output=True, text=True, encoding='CP866')
        # print(result.stdout)
        ip = re.findall(PATTERN_IP, result.stdout)[0]
        print(ip)
        try:
            packages = re.findall(PATTERN_PACK, result.stdout)[0]
            print(packages)
            round_travel_time = re.findall(PATTERN_TIME, result.stdout)[0]
            print(round_travel_time)
            output.append([address, ip, packages[0], round_travel_time])
        except Exception as e:
            print('No packages received')
            output.append([address, ip, 0, 'NaN'])

    with open('pings.csv', 'w') as file:
        csv_writer = csv.writer(file, lineterminator='\n')
        csv_writer.writerows(output)


if __name__ == '__main__':
    main()